"""Google Drive integration service."""
import os
import io
import json
import streamlit as st
from typing import Optional, Tuple
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from config.settings import settings


class GoogleDriveService:
    """Service for Google Drive operations."""
    
    def __init__(self):
        """Initialize Google Drive service."""
        self.service = None
        self.folder_id = settings.google_drive_folder_id
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive API service using OAuth2 or Service Account."""
        try:
            creds = None
            # 1. Try OAuth2 (Personal Account)
            token_data = None
            if os.path.exists(settings.google_drive_token_file):
                try:
                    with open(settings.google_drive_token_file, 'r') as f:
                        token_data = json.load(f)
                except Exception:
                    pass
            elif "GOOGLE_TOKEN_JSON" in st.secrets:
                try:
                    token_data = json.loads(st.secrets["GOOGLE_TOKEN_JSON"])
                except Exception:
                    pass
            
            if token_data:
                creds = Credentials.from_authorized_user_info(
                    token_data,
                    ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
                )
            
            # If no valid credentials, try to refresh
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Update token file with refreshed credentials (if local)
                    if os.path.exists(settings.google_drive_token_file) or not "GOOGLE_TOKEN_JSON" in st.secrets:
                        with open(settings.google_drive_token_file, 'w') as token:
                            token.write(creds.to_json())
                except Exception:
                    creds = None

            # 2. Try Service Account (Fallback) if no personal creds
            if not creds and os.path.exists(settings.google_drive_credentials_file):
                try:
                    creds = service_account.Credentials.from_service_account_file(
                        settings.google_drive_credentials_file,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                except Exception:
                    pass
            
            if creds and creds.valid:
                self.service = build('drive', 'v3', credentials=creds)
                # If we have service, ensure target folder exists
                try:
                    self._ensure_folder_exists()
                except Exception:
                    pass
            
        except Exception as e:
            # Failed to initialize Google Drive service - silent fail to prevent crash
            self.service = None
            print(f"Error initializing Drive service: {e}")

    def is_configured(self) -> bool:
        """Check if Google Drive is properly configured."""
        return self.service is not None

    def get_auth_url(self):
        """Generate authorization URL for manual authentication."""
        try:
            scopes = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
            
            if "GOOGLE_CLIENT_SECRETS_JSON" in st.secrets:
                client_config = json.loads(st.secrets["GOOGLE_CLIENT_SECRETS_JSON"])
                flow = InstalledAppFlow.from_client_config(
                    client_config, 
                    scopes=scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
            elif os.path.exists(settings.google_drive_client_secrets_file):
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_drive_client_secrets_file,
                    scopes=scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
            else:
                return None, "Missing GOOGLE_CLIENT_SECRETS_JSON in secrets or client_secrets.json file."

            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='consent'
            )
            return auth_url, None
        except Exception as e:
            return None, str(e)

    def authenticate_with_code(self, code):
        """Exchange authorization code for credentials."""
        try:
            scopes = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
            
            if "GOOGLE_CLIENT_SECRETS_JSON" in st.secrets:
                client_config = json.loads(st.secrets["GOOGLE_CLIENT_SECRETS_JSON"])
                flow = InstalledAppFlow.from_client_config(
                    client_config, 
                    scopes=scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
            elif os.path.exists(settings.google_drive_client_secrets_file):
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_drive_client_secrets_file,
                    scopes=scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
            else:
                return False, "Configuration not found."

            flow.fetch_token(code=code)
            creds = flow.credentials
            
            # Save credentials
            with open(settings.google_drive_token_file, 'w') as token:
                token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            self._ensure_folder_exists()
            return True, "Authenticated successfully"
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"

    def _ensure_folder_exists(self):
        """Check if target folder exists, if not create it."""
        if not self.service:
            return
        
        folder_name = settings.google_drive_folder_name
        
        # If we already have a folder_id, verify it exists
        if self.folder_id:
            try:
                self.service.files().get(fileId=self.folder_id).execute()
                return # Folder exists
            except:
                self.folder_id = None # Reset if not found
        
        # Search for folder by name
        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            
            if items:
                self.folder_id = items[0].get('id')
            else:
                # Create folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                self.folder_id = file.get('id')
        except Exception as e:
            pass

    def upload_file(
        self,
        file_path: str = None,
        file_content: bytes = None,
        filename: str = None,
        mime_type: str = 'application/octet-stream'
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload file to Google Drive.
        
        Returns:
            Tuple: (success, file_id, shareable_link)
        """
        if not self.service:
            return False, None, "Google Drive service not initialized"
        
        try:
            # Re-ensure folder id before upload
            if not self.folder_id:
                self._ensure_folder_exists()
                
            file_metadata = {
                'name': filename or os.path.basename(file_path),
            }
            
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]
            
            if file_path:
                media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            elif file_content:
                media = MediaIoBaseUpload(
                    io.BytesIO(file_content),
                    mimetype=mime_type,
                    resumable=True
                )
            else:
                return False, None, "No file path or content provided"
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            file_id = file.get('id')
            
            # Make file shareable (anyone with link can view)
            try:
                self.service.permissions().create(
                    fileId=file_id,
                    body={'type': 'anyone', 'role': 'reader'}
                ).execute()
            except:
                # Might fail if restricted by domain policy, but we proceed
                pass
            
            shareable_link = file.get('webViewLink')
            return True, file_id, shareable_link
            
        except HttpError as e:
            return False, None, f"HTTP error: {str(e)}"
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def delete_file(self, file_id: str) -> Tuple[bool, str]:
        """Delete file from Google Drive."""
        if not self.service:
            return False, "Google Drive service not initialized"
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True, "File deleted successfully"
        except HttpError as e:
            return False, f"HTTP error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def list_files(self, query: str) -> list:
        """List files in Google Drive based on query."""
        if not self.service:
            return []
        
        try:
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime)",
                orderBy="modifiedTime desc"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from Google Drive to local path."""
        if not self.service:
            return False
            
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            with open(local_path, 'wb') as f:
                f.write(fh.getbuffer())
            return True
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    def upload_database(self, local_path: str, filename: str = "expenses.db") -> Tuple[bool, str]:
        """
        Upload database file to Google Drive.
        Overwrites existing file if exists in the folder to avoid duplicates.
        """
        if not self.service:
            return False, "Google Drive service not initialized"
            
        try:
            # Re-ensure folder id before upload
            if not self.folder_id:
                self._ensure_folder_exists()
            
            if not self.folder_id:
                 return False, "Could not determine target folder"

            # Check if file exists in the folder
            query = f"name = '{filename}' and '{self.folder_id}' in parents and trashed = false"
            existing_files = self.list_files(query)
            
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(local_path, mimetype='application/x-sqlite3', resumable=True)
            
            if existing_files:
                # Update existing file
                file_id = existing_files[0]['id']
                # When updating, we don't supply 'parents'
                update_metadata = {'name': filename} 
                self.service.files().update(
                    fileId=file_id,
                    body=update_metadata,
                    media_body=media
                ).execute()
                return True, "Đã cập nhật file database thành công!"
            else:
                # Create new file
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                return True, "Đã tạo backup file database mới thành công!"
                
        except Exception as e:
            return False, f"Upload error: {str(e)}"

