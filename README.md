# Google Photos Uploader

Upload images to Google Photos with captions extracted from EXIF metadata (UserComment and ImageDescription fields).

## Features

- Upload images to Google Photos with EXIF captions as descriptions
- Support for both UserComment and ImageDescription EXIF fields
- Create new albums or add to existing app-created albums
- Batch upload from directories or individual files
- Compatible with 2025 Google Photos API restrictions

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/google_photos_uploader.git
cd google_photos_uploader

# Install dependencies with uv
uv pip install -r requirements.txt
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/google_photos_uploader.git
cd google_photos_uploader

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Setup

### 1. Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Photos Library API**
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Select **Desktop application**
6. Download the JSON credentials file
7. Save it as `~/.google_photos_credentials.json`

### 2. First Run Authentication

On first run, the script will open a browser window for Google OAuth authentication. Follow the prompts to authorize the application.

## Usage

### Create a New Album

```bash
python3 google_photos_uploader.py image.jpg --album "My New Album"
```

This will:
- Create a new album called "My New Album"
- Upload the image with its EXIF caption as the description
- Print the album ID for future use

### Add to Existing Album

```bash
python3 google_photos_uploader.py image2.jpg --album-id "ALBUM_ID_FROM_PREVIOUS_COMMAND"
```

### Batch Upload Directory

```bash
python3 google_photos_uploader.py /path/to/photos/ --album "Vacation Photos"
```

### Upload Multiple Files

```bash
python3 google_photos_uploader.py photo1.jpg photo2.png photo3.jpeg --album "Mixed Photos"
```

## Command Line Options

```
positional arguments:
  paths                 Image files or directories to upload

options:
  -h, --help            show this help message and exit
  --album ALBUM, -a ALBUM
                        Album name to create (will print album ID for future use)
  --album-id ALBUM_ID   Existing album ID to add photos to
```

## EXIF Metadata Support

The script extracts captions from EXIF metadata in the following priority order:

1. **UserComment** field (preferred)
2. **ImageDescription** field (fallback)

If both fields are present, UserComment takes precedence. If neither field contains a caption, the image is uploaded without a description.

## 2025 Google Photos API Changes

This script is compatible with the Google Photos API changes implemented in 2025:

- **Album Restrictions**: Can only access albums created by this app
- **Scope Changes**: Uses the new restricted scopes (`photoslibrary.appendonly`, `photoslibrary.readonly.appcreateddata`, `photoslibrary.edit.appcreateddata`)
- **ID-based Album Management**: Uses album IDs instead of searching by name

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- BMP (.bmp)
- WebP (.webp)
- HEIC (.heic)
- HEIF (.heif)

## Troubleshooting

### Authentication Issues

If you get authentication errors:

1. Delete the token file: `rm ~/.google_photos_token.json`
2. Run the script again to re-authenticate
3. Ensure your credentials file is at `~/.google_photos_credentials.json`

### Album Access Issues

Due to 2025 API restrictions, you can only access albums created by this app. If you need to add photos to an existing album:

1. Use the album ID printed when the album was created
2. The script cannot access albums created through the Google Photos web interface

### EXIF Reading Issues

If EXIF captions aren't being detected:

- Verify the image has UserComment or ImageDescription fields
- Some image editors may remove or modify EXIF data
- The script will upload images without captions if no EXIF description is found

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for the 2025 Google Photos API
- Uses the Google Photos Library API
- EXIF metadata extraction with PIL and piexif