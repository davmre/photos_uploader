#!/usr/bin/env python3
"""
Google Photos Uploader
Uploads images to Google Photos with captions extracted from EXIF metadata.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import piexif
import requests
from PIL import Image
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Photos API scopes (updated for 2025)
SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary.appendonly',
    'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata',
    'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata'
]

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp', '.heic', '.heif'}

# Credentials file path
CREDENTIALS_PATH = Path.home() / '.google_photos_credentials.json'
TOKEN_PATH = Path.home() / '.google_photos_token.json'


class GooglePhotosUploader:
    def __init__(self):
        self.service = None
        self.setup_authentication()
    
    def setup_authentication(self):
        """Set up Google Photos API authentication."""
        creds = None
        
        # Load existing token if available
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_PATH.exists():
                    self.prompt_for_credentials_setup()
                
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
    
    def prompt_for_credentials_setup(self):
        """Prompt user to set up OAuth2 credentials."""
        print("Google Photos API credentials not found.")
        print("\nTo set up credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Photos Library API")
        print("4. Go to 'Credentials' > 'Create Credentials' > 'OAuth client ID'")
        print("5. Select 'Desktop application'")
        print("6. Download the JSON file")
        print(f"7. Save it as: {CREDENTIALS_PATH}")
        print("\nPress Enter after you've saved the credentials file...")
        input()
        
        if not CREDENTIALS_PATH.exists():
            print(f"Error: Credentials file not found at {CREDENTIALS_PATH}")
            sys.exit(1)
    
    def extract_description_from_exif(self, image_path: Path) -> Optional[str]:
        """Extract description from EXIF UserComment or ImageDescription."""
        try:
            # Try using piexif first
            exif_dict = piexif.load(str(image_path))
            
            # Check UserComment first (preferred)
            if piexif.ExifIFD.UserComment in exif_dict.get('Exif', {}):
                user_comment = exif_dict['Exif'][piexif.ExifIFD.UserComment]
                if user_comment:
                    # UserComment often has encoding prefix, try to decode
                    if isinstance(user_comment, bytes):
                        try:
                            # Skip first 8 bytes which contain encoding info
                            decoded = user_comment[8:].decode('utf-8').strip()
                            if decoded:
                                return decoded[:1000]  # Limit to 1000 chars
                        except (UnicodeDecodeError, IndexError):
                            pass
            
            # Check ImageDescription as fallback
            if piexif.ImageIFD.ImageDescription in exif_dict.get('0th', {}):
                image_desc = exif_dict['0th'][piexif.ImageIFD.ImageDescription]
                if image_desc:
                    if isinstance(image_desc, bytes):
                        try:
                            decoded = image_desc.decode('utf-8').strip()
                            if decoded:
                                return decoded[:1000]
                        except UnicodeDecodeError:
                            pass
                    elif isinstance(image_desc, str) and image_desc.strip():
                        return image_desc.strip()[:1000]
        
        except Exception as e:
            print(f"Warning: Could not read EXIF from {image_path}: {e}")
        
        # Fallback to PIL for ImageDescription
        try:
            with Image.open(image_path) as img:
                exif = img.getexif()
                if exif:
                    # Check for ImageDescription (tag 270)
                    image_desc = exif.get(270)
                    if image_desc and image_desc.strip():
                        return image_desc.strip()[:1000]
        except Exception as e:
            print(f"Warning: Could not read PIL EXIF from {image_path}: {e}")
        
        return None
    
    def upload_image_bytes(self, image_path: Path) -> Optional[str]:
        """Upload image bytes and return the upload token."""
        try:
            # Get credentials for making direct HTTP request
            creds = self.service._http.credentials
            creds.refresh(Request())
            
            # Upload to the Photos Library API upload endpoint
            upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
            
            with open(image_path, 'rb') as f:
                headers = {
                    'Authorization': f'Bearer {creds.token}',
                    'Content-type': 'application/octet-stream',
                    'X-Goog-Upload-File-Name': image_path.name,
                    'X-Goog-Upload-Protocol': 'raw'
                }
                
                response = requests.post(upload_url, data=f.read(), headers=headers)
                
                if response.status_code == 200:
                    return response.text  # This is the upload token
                else:
                    print(f"Upload failed for {image_path.name}: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            print(f"Error uploading {image_path}: {e}")
            return None
    
    def create_media_item(self, upload_token: str, filename: str, description: Optional[str] = None, album_id: Optional[str] = None) -> Optional[str]:
        """Create a media item from an upload token. Returns media item ID if successful."""
        try:
            new_media_item = {
                'simpleMediaItem': {
                    'uploadToken': upload_token,
                    'fileName': filename
                }
            }
            
            if description:
                new_media_item['description'] = description
            
            request_body = {'newMediaItems': [new_media_item]}
            
            # Add to album if specified
            if album_id:
                request_body['albumId'] = album_id
            
            response = self.service.mediaItems().batchCreate(body=request_body).execute()
            
            if 'newMediaItemResults' in response:
                result = response['newMediaItemResults'][0]
                if 'status' in result and result['status'].get('message') == 'Success':
                    return result['mediaItem']['id']
                else:
                    print(f"Error creating media item for {filename}: {result.get('status', {})}")
            
            return None
        
        except HttpError as e:
            print(f"Error creating media item for {filename}: {e}")
            return None
    
    def create_album(self, album_name: str) -> Optional[str]:
        """Create a new album. Returns album ID."""
        try:
            print(f"Creating album: {album_name}")
            
            create_response = self.service.albums().create(
                body={'album': {'title': album_name}}
            ).execute()
            
            return create_response['id']
        
        except HttpError as e:
            print(f"Error creating album '{album_name}': {e}")
            return None
    
    def verify_album_exists(self, album_id: str) -> bool:
        """Verify that an album exists and is accessible."""
        try:
            album_response = self.service.albums().get(albumId=album_id).execute()
            album_title = album_response.get('title', 'Unknown')
            print(f"✓ Found album: '{album_title}'")
            return True
        
        except HttpError as e:
            print(f"Error accessing album {album_id}: {e}")
            return False
    
    def add_to_album(self, album_id: str, media_item_ids: List[str]) -> bool:
        """Add media items to an album."""
        try:
            self.service.albums().batchAddMediaItems(
                albumId=album_id,
                body={'mediaItemIds': media_item_ids}
            ).execute()
            return True
        
        except HttpError as e:
            print(f"Error adding items to album: {e}")
            return False
    
    def upload_images(self, image_paths: List[Path], album_name: str = None, album_id: str = None):
        """Upload multiple images to a Google Photos album."""
        if not image_paths:
            print("No images to upload.")
            return
        
        if album_name:
            print(f"Uploading {len(image_paths)} images to new album '{album_name}'...")
            album_id = self.create_album(album_name)
            if not album_id:
                print("Failed to create album. Aborting.")
                return
            print(f"✓ Created album '{album_name}' with ID: {album_id}")
            print(f"  Save this ID to add more photos later: --album-id {album_id}")
        elif album_id:
            print(f"Uploading {len(image_paths)} images to existing album (ID: {album_id})...")
            # Verify album exists
            if not self.verify_album_exists(album_id):
                print("Album ID not found or not accessible. Aborting.")
                return
        else:
            print("Error: Must specify either album_name or album_id")
            return
        
        successful_uploads = 0
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"Processing {i}/{len(image_paths)}: {image_path.name}")
            
            # Extract description from EXIF
            description = self.extract_description_from_exif(image_path)
            if description:
                print(f"  Found description: {description[:50]}{'...' if len(description) > 50 else ''}")
            
            # Upload image bytes
            upload_token = self.upload_image_bytes(image_path)
            if not upload_token:
                print(f"  Failed to upload {image_path.name}")
                continue
            
            # Create media item directly in album
            media_item_id = self.create_media_item(upload_token, image_path.name, description, album_id)
            if media_item_id:
                print(f"  Successfully uploaded {image_path.name} to album")
                successful_uploads += 1
            else:
                print(f"  Failed to create media item for {image_path.name}")
        
        print(f"Upload complete! {successful_uploads}/{len(image_paths)} images uploaded successfully.")


def get_image_files(path: Path) -> List[Path]:
    """Get all image files from a path (file or directory)."""
    if path.is_file():
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            return [path]
        else:
            print(f"Warning: {path} is not a recognized image file")
            return []
    
    elif path.is_dir():
        image_files = []
        for file_path in path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(file_path)
        return sorted(image_files)
    
    else:
        print(f"Error: {path} does not exist")
        return []


def main():
    parser = argparse.ArgumentParser(description='Upload images to Google Photos with EXIF captions')
    parser.add_argument('paths', nargs='+', help='Image files or directories to upload')
    parser.add_argument('--album', '-a', help='Album name to create (will print album ID for future use)')
    parser.add_argument('--album-id', help='Existing album ID to add photos to')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.album and not args.album_id:
        print("Error: Must specify either --album (to create new) or --album-id (to use existing)")
        return
    
    if args.album and args.album_id:
        print("Error: Cannot specify both --album and --album-id")
        return
    
    # Collect all image files
    all_images = []
    for path_str in args.paths:
        path = Path(path_str)
        images = get_image_files(path)
        all_images.extend(images)
    
    if not all_images:
        print("No image files found to upload.")
        return
    
    print(f"Found {len(all_images)} image(s) to upload")
    
    # Initialize uploader and upload
    uploader = GooglePhotosUploader()
    if args.album:
        uploader.upload_images(all_images, album_name=args.album)
    else:
        uploader.upload_images(all_images, album_id=args.album_id)


if __name__ == '__main__':
    main()