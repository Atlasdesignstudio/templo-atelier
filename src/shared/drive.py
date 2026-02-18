import os
import io
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveService:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.creds = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._authenticate()

    def _authenticate(self):
        """Authenticates the user using OAuth2."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.creds = None
            
            if not self.creds and os.path.exists(self.credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                # Run local server for auth (requires user interaction in browser)
                # In a headless environment, this needs a different flow or pre-generated token.
                try:
                    self.creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())
                except Exception as e:
                    print(f"Failed to authenticate: {e}")

    def list_files(self, folder_id: Optional[str] = None, page_size: int = 10) -> List[Dict]:
        """Lists files in a specific folder or root."""
        if not self.creds:
            print("Drive Service not authenticated.")
            return []

        try:
            service = build('drive', 'v3', credentials=self.creds)
            
            query = "trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            results = service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, createdTime)"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            print(f"Drive API Error: {e}")
            return []

    def download_file_content(self, file_id: str) -> Optional[str]:
        """Downloads a file and returns its content as string (assuming text/doc)."""
        if not self.creds:
            return None
            
        try:
            service = build('drive', 'v3', credentials=self.creds)
            
            # Check mime type first
            file_meta = service.files().get(fileId=file_id).execute()
            mime_type = file_meta.get('mimeType')
            
            request = None
            if 'application/vnd.google-apps' in mime_type:
                # Export Google Docs
                if 'document' in mime_type:
                    request = service.files().export_media(fileId=file_id, mimeType='text/plain')
            else:
                # Download binary
                request = service.files().get_media(fileId=file_id)
                
            if not request:
                return None

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            return fh.getvalue().decode('utf-8', errors='ignore')
            
        except Exception as e:
            print(f"Download Error: {e}")
            return None
