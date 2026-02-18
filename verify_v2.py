import os
import sys
from pathlib import Path

# Add src to path
import sys
import os
sys.path.insert(0, os.getcwd())

from src.shared.drive_utils import get_drive_service, find_folder, ensure_folder  # type: ignore

def upload_v2_test():
    drive = get_drive_service()
    
    # Locate Inbox
    root_id = find_folder(drive, "Templo Atelier")
    projects_id = find_folder(drive, "05_Projects", root_id)
    inbox_id = find_folder(drive, "Inbox", projects_id)
    
    if not inbox_id:
        print("Inbox not found!")
        return
        
    print(f"Uploading v2 test transcript to Inbox...")
    
    # We use a name that is clearly new
    content = """
Project: Solaris Glow
Client: Martian Tech

Goals:
- Create a luxury skincare brand for extreme environments
- Aesthetics: Iridescent, high-gloss, premium
- Target: Digital nomads in high-altitude locations

Deliverables:
- Logo and packaging
- Web UI
- Social launch campaign

Budget: $2500
    """
    
    file_metadata = {
        'name': 'Kickoff_Solaris_Glow.txt',
        'parents': [inbox_id],
        'mimeType': 'text/plain'
    }
    
    from googleapiclient.http import MediaInMemoryUpload # type: ignore
    media = MediaInMemoryUpload(content.encode('utf-8'), mimetype='text/plain')
    
    file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Uploaded test file: {file['id']}")

if __name__ == "__main__":
    upload_v2_test()
