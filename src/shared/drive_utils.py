import os
import json
import logging
import time
import random
from functools import wraps
from pathlib import Path
from typing import Optional, Dict, List, Any

# Third-party imports
from google.auth.transport.requests import Request  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore

def retry_drive_op(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator for exponential backoff on Drive operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        print(f"[Drive] Operation failed after {max_retries} attempts: {e}")
                        raise
                    jitter = random.uniform(0, 0.1 * delay)
                    sleep_time = delay + jitter
                    print(f"[Drive] Error: {e}. Retrying in {sleep_time:.2f}s (Attempt {retries}/{max_retries})")
                    time.sleep(sleep_time)
                    delay *= 2
            return None
        return wrapper
    return decorator

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
]

def get_credentials():
    """Handles OAuth2 authentication flow and returns credentials."""
    # Look for token.json in root
    base_dir = Path(__file__).parent.parent.parent
    token_path = base_dir / "token.json"
    credentials_path = base_dir / "credentials.json"

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not credentials_path.exists():
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")

            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    return creds

def get_drive_service(creds=None):
    """Builds and returns the Drive API service."""
    if not creds:
        creds = get_credentials()
    return build('drive', 'v3', credentials=creds)

def get_docs_service(creds=None):
    """Builds and returns the Docs API service."""
    if not creds:
        creds = get_credentials()
    return build('docs', 'v1', credentials=creds)

@retry_drive_op()
def find_folder(drive, name: str, parent_id: Optional[str] = None) -> Optional[str]:
    """Finds a folder by name, optionally within a parent."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = drive.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

@retry_drive_op()
def create_folder(drive, name: str, parent_id: Optional[str] = None) -> str:
    """Creates a folder in Drive."""
    metadata: Dict[str, Any] = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    folder = drive.files().create(body=metadata, fields='id').execute()
    return folder['id']

def ensure_folder(drive, name: str, parent_id: Optional[str] = None) -> str:
    """Ensures a folder exists, creating it if necessary."""
    folder_id = find_folder(drive, name, parent_id)
    if folder_id:
        return folder_id
    return create_folder(drive, name, parent_id)

@retry_drive_op()
def upload_file(drive, file_path: str, parent_id: str) -> Optional[str]:
    """Uploads a local file to a specific Google Drive folder, updating if it already exists."""
    from googleapiclient.http import MediaFileUpload  # type: ignore
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return None

    # Check if file already exists in this folder
    query = f"name='{path.name}' and '{parent_id}' in parents and trashed=false"
    results = drive.files().list(q=query, spaces='drive', fields='files(id)').execute()
    existing_files = results.get('files', [])

    file_metadata = {
        'name': path.name,
        'parents': [parent_id]
    }
    
    # Basic MIME type detection
    mime_type = 'text/plain'
    if path.suffix == '.json':
        mime_type = 'application/json'
    elif path.suffix == '.md':
        mime_type = 'text/markdown'
    elif path.suffix == '.png':
        mime_type = 'image/png'
    elif path.suffix == '.svg':
        mime_type = 'image/svg+xml'
    elif path.suffix == '.pdf':
        mime_type = 'application/pdf'

    try:
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        
        if existing_files:
            file_id = existing_files[0]['id']
            # Update existing file
            file = drive.files().update(fileId=file_id, media_body=media, fields='id').execute() # type: ignore
            return file.get('id')
        else:
            # Create new file
            file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute() # type: ignore
            return file.get('id')
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        return None

def create_google_doc(drive, docs, title: str, parent_id: str, content: str) -> str:
    """Creates a Google Doc with content."""
    # Check if doc already exists
    query = f"name='{title}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
    results = drive.files().list(q=query, spaces='drive', fields='files(id)').execute()
    existing = results.get('files', [])

    if existing:
        return existing[0]['id']

    # Create the doc
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [parent_id],
    }
    file = drive.files().create(body=file_metadata, fields='id').execute()
    doc_id = file['id']

    # Write content using Docs API
    requests = [{
        'insertText': {
            'location': {'index': 1},
            'text': content
        }
    }]
    docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    return doc_id
