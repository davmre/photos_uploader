# Google Photos Uploader
Script to upload images to Google Photos with captions extracted from EXIF
metadata.

For some reason, Google Photos does not populate its "description" field from
EXIF. If you have a bunch of Exif-tagged images you'd like to upload to
Google Photos, this script will do that, and automatically set the descriptions
based on the EXIF `UserComment` or `ImageDescription` fields.

This whole thing was vibecoded in about half an hour with Claude 4 Sonnet. If
it doesn't do what you want, try asking Claude to fix it?

## Features

- Upload images to Google Photos with EXIF captions as descriptions
- Support for both UserComment and ImageDescription EXIF fields
- Create new albums or add to existing app-created albums
- Batch upload from directories or individual files
- Compatible with 2025 Google Photos API restrictions

## Running

Using `uv` (recommended, [install
it](https://docs.astral.sh/uv/getting-started/installation/) if you don't have
it):

```bash
git clone https://github.com/davmre/google_photos_uploader.git
cd google_photos_uploader
uv run google_photos_uploader.py ~/your_images_dir/ --album "Album To Create"
```

On first run, the script will prompt you through the OAth2 authentication
process to connect to the Google Photos API. Follow the prompts to authorize the
script.

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