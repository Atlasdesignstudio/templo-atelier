import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

from src.shared.drive_utils import get_drive_service, find_folder

def cleanup_drive():
    print("--- [Reset] Templo Atelier: Google Drive Cleanup ---")
    
    try:
        drive = get_drive_service()
        
        # 1. Find the root 'Templo Atelier' folder
        root_id = find_folder(drive, "Templo Atelier")
        if not root_id:
            print("❌ Root folder 'Templo Atelier' not found on Drive.")
            return

        # 2. Find the '05_Projects' folder
        projects_id = find_folder(drive, "05_Projects", root_id)
        if not projects_id:
            print("❌ Folder '05_Projects' not found on Drive.")
            return

        # 3. List all folders/files in '05_Projects'
        query = f"'{projects_id}' in parents and trashed = false"
        results = drive.files().list(q=query, spaces='drive', fields='files(id, name, mimeType)').execute()
        items = results.get('files', [])

        if not items:
            print("✅ No projects found in '05_Projects'. Drive is already clean.")
            return

        print(f"♻️ Found {len(items)} items to clean in '05_Projects'...")

        # 4. Trash each item
        for item in items:
            name = item['name']
            file_id = item['id']
            print(f"   - Trashing: {name} ({file_id})")
            drive.files().update(fileId=file_id, body={'trashed': True}).execute()

        print("\n✅ Google Drive cleanup complete.")

    except Exception as e:
        print(f"❌ Error during Drive cleanup: {e}")

if __name__ == "__main__":
    cleanup_drive()
