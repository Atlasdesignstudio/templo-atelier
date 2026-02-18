"""
Templo Atelier — Drive Watcher
================================
Polls a Google Drive "Inbox" folder for new meeting transcripts.
When a new file is found, downloads it, processes it through the
Intake Agent + full creative pipeline, then moves it to "Processed".

Usage:
    python -m src.operative_core.drive_watcher

Runs continuously in the background (every 5 minutes).
"""

import os
import io
import sys
import json
import time
import logging
from pathlib import Path
from typing import Optional, Set

# Shared Drive utilities
from src.shared.drive_utils import (  # type: ignore
    get_credentials,
    get_drive_service,
    find_folder as _find_folder_id,
    ensure_folder as _find_or_create_folder,
    create_google_doc
)

def _download_file_text(drive, file_id: str, mime_type: str) -> Optional[str]:
    """Download file content as text."""
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore

    try:
        if 'google-apps' in mime_type:
            # Export Google Docs/Sheets as plain text
            if 'document' in mime_type:
                request = drive.files().export_media(fileId=file_id, mimeType='text/plain')
            elif 'spreadsheet' in mime_type:
                request = drive.files().export_media(fileId=file_id, mimeType='text/csv')
            else:
                request = drive.files().export_media(fileId=file_id, mimeType='text/plain')
        else:
            request = drive.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        return fh.getvalue().decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {e}")
        return None


logging.basicConfig(level=logging.INFO, format="%(asctime)s [DriveWatcher] %(message)s")
logger = logging.getLogger(__name__)

# How often to check Drive (seconds)
POLL_INTERVAL = 300  # 5 minutes

# Local state file to track processed files (survives restarts)
STATE_FILE = Path(__file__).parent.parent.parent / "drive_watcher_state.json"

# Drive folder names (inside Templo Atelier/05_Projects/)
INBOX_FOLDER = "Inbox"
PROCESSED_FOLDER = "Processed"




def _move_file(drive, file_id: str, current_parent: str, new_parent: str):
    """Move a file from one folder to another."""
    try:
        drive.files().update(
            fileId=file_id,
            addParents=new_parent,
            removeParents=current_parent,
            fields='id, parents'
        ).execute()
    except Exception as e:
        logger.error(f"Failed to move file {file_id}: {e}")



def _load_processed_ids() -> Set[str]:
    """Load set of already-processed file IDs."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    return set()


def _save_processed_id(file_id: str):
    """Add a file ID to the processed set."""
    processed = _load_processed_ids()
    processed.add(file_id)
    with open(STATE_FILE, 'w') as f:
        json.dump({"processed_ids": list(processed)}, f, indent=2)


class DriveWatcher:
    """
    Watches a Google Drive "Inbox" folder for new meeting transcripts.
    When found, processes them and triggers the full creative pipeline.
    """

    def __init__(self):
        self.creds = get_credentials()
        if not self.creds:
            raise RuntimeError("Could not authenticate. Run create_drive_docs.py first.")

        self.drive = get_drive_service(self.creds)
        self.inbox_id: Optional[str] = None
        self.processed_id: Optional[str] = None

    def setup_folders(self):
        """Locate (or create) the Inbox and Processed folders in Drive."""
        # Find Templo Atelier root
        root_id = _find_folder_id(self.drive, "Templo Atelier")
        if not root_id:
            logger.error("'Templo Atelier' folder not found in Drive. Run create_drive_docs.py first.")
            raise RuntimeError("Templo Atelier folder not found")

        # Find 05_Projects
        projects_id = _find_folder_id(self.drive, "05_Projects", root_id)
        if not projects_id:
            logger.error("'05_Projects' folder not found. Run create_drive_docs.py first.")
            raise RuntimeError("05_Projects folder not found")

        # Create/find Inbox and Processed
        self.inbox_id = _find_or_create_folder(self.drive, INBOX_FOLDER, projects_id)
        self.processed_id = _find_or_create_folder(self.drive, PROCESSED_FOLDER, projects_id)

        logger.info(f"📥 Inbox folder ID: {self.inbox_id}")
        logger.info(f"📦 Processed folder ID: {self.processed_id}")

    def check_inbox(self):
        """Check for new files in the Inbox folder."""
        if not self.inbox_id:
            return

        processed_ids = _load_processed_ids()

        # List all files in Inbox
        query = f"'{self.inbox_id}' in parents and trashed=false"
        results = self.drive.files().list(
            q=query,
            fields='files(id, name, mimeType, createdTime)',
            orderBy='createdTime'
        ).execute()

        files = results.get('files', [])

        if not files:
            logger.info("📭 Inbox empty — nothing to process.")
            return

        for file in files:
            file_id = file['id']
            file_name = file['name']
            mime_type = file['mimeType']

            # Skip already processed
            if file_id in processed_ids:
                continue

            logger.info(f"📄 New file found: {file_name} ({mime_type})")

            # 1. Download content
            content = _download_file_text(self.drive, file_id, mime_type)
            if not content or not content.strip():
                logger.warning(f"Could not read content from {file_name}, skipping.")
                continue

            logger.info(f"📝 Downloaded {len(content)} chars from {file_name}")

            # 2. Process through Intake Agent
            try:
                if content is not None and len(content) > 0:  # type: ignore
                    self._process_transcript(content, file_name)
                else:
                    logger.warning(f"Skipping {file_name} due to empty content.")
            except Exception as e:
                logger.error(f"❌ Pipeline failed for {file_name}: {e}")
                _save_processed_id(file_id)  # Don't retry failed files
                continue

            # 3. Move to Processed folder
            if self.inbox_id and self.processed_id:
                _move_file(self.drive, file_id, self.inbox_id, self.processed_id)  # type: ignore
            _save_processed_id(file_id)
            logger.info(f"✅ {file_name} → Processed")

    def _process_transcript(self, content: str, filename: str):
        """Run the transcript through Intake Agent → Studio Pipeline."""
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()

        # Use Intake Agent to extract project context
        from src.operative_core.intake import IntakeAgent  # type: ignore
        # Use Intake Agent to extract project context
        intake = IntakeAgent()
        context = intake.analyze_input(content)

        logger.info(f"🔍 Extracted project: {context.project_name}")
        
        # Determine Agents & Methodology
        assignments = intake.assign_missions(context)
        methodology = assignments["methodology"]
        logger.info(f"📐 Assigned Methodology: {methodology}")

        # Scaffold local project folders
        intake.process_project(context)

        # Determine budget from transcript or use default
        budget = 1000.0
        if context.budget_hint:
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', context.budget_hint.replace(',', ''))
            if numbers:
                try:
                    budget = float(numbers[0])
                except ValueError:
                    pass

        # Trigger the full creative pipeline
        logger.info(f"🚀 Launching pipeline: {context.project_name} (${budget:.2f} budget)")

        from src.studio import run_studio_pipeline  # type: ignore
        # Trigger the Studio Pipeline
        run_studio_pipeline(
            brief=context.json(), 
            budget=budget,
            project_name=context.project_name,
            methodology=methodology,
            clarifying_questions=context.clarifying_questions
        )

        logger.info(f"🏁 Pipeline complete for: {context.project_name}")
        return

    def run_forever(self):
        """Main loop — polls Drive every POLL_INTERVAL seconds."""
        logger.info("=" * 50)
        logger.info("🏛️  TEMPLO ATELIER — Drive Watcher")
        logger.info(f"   Polling every {POLL_INTERVAL // 60} minutes")
        logger.info("=" * 50)

        self.setup_folders()

        while True:
            try:
                self.check_inbox()
            except Exception as e:
                logger.error(f"Error during inbox check: {e}")

            logger.info(f"💤 Sleeping {POLL_INTERVAL // 60} min...")
            time.sleep(POLL_INTERVAL)


def main():
    """Entry point for the Drive Watcher."""
    watcher = DriveWatcher()
    watcher.run_forever()


if __name__ == "__main__":
    main()
