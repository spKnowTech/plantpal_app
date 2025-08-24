import uuid
from PIL import Image, ImageOps
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
import aiofiles
import os
from pathlib import Path
from settings import Setting
from models.user import User

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_SIZE = (1920, 1920)  # Max dimensions
THUMBNAIL_SIZE = (300, 300)

def ensure_upload_directories():
    """Ensure upload directories exist."""
    Path(Setting.gallery_dir).mkdir(parents=True, exist_ok=True)
    Path(Setting.thumbnail_dir).mkdir(parents=True, exist_ok=True)

def get_file_path(dest_dir: str, filename: str, user: User) -> str:
    username= user.email.split('@')[0]
    return os.path.join(dest_dir, f"{username}_id_{user.id}", filename)

def validate_image_file(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded image file.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        return False, f"File size too large. Maximum allowed: {MAX_FILE_SIZE // (1024 * 1024)}MB"

    # Check file extension
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"Invalid file type. Expected image file."

    return True, None


def generate_unique_filename(original_filename: str, user: User) -> str:
    """Generate unique filename for uploaded image."""
    file_ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    timestamp = str(int(uuid.uuid1().time))
    return f"user_{user.id}_{timestamp}_{unique_id}{file_ext}"


async def save_uploaded_image(file: UploadFile, user: User) -> Tuple[str, dict]:
    """
    Save uploaded image and create thumbnail.

    Returns:
        Tuple of (file_path, file_info_dict)
    """
    ensure_upload_directories()

    # Validate file
    is_valid, error_msg = validate_image_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename, user)
    file_path = get_file_path(Setting.gallery_dir, filename=unique_filename, user=user)
    thumbnail_path = get_file_path(Setting.thumbnail_dir, filename=f"thumb_{unique_filename}", user=user)

    try:
        # Save original file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Process image (resize if needed and create thumbnail)
        process_saved_image(file_path, thumbnail_path)

        # Get file info
        file_info = {
            'file_size': len(content),
            'mime_type': file.content_type,
            'original_filename': file.filename,
            'processed_path': file_path,
            'thumbnail_path': thumbnail_path
        }

        return file_path, file_info

    except Exception as e:
        # Cleanup on error
        cleanup_file(file_path)
        cleanup_file(thumbnail_path)
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")


def process_saved_image(image_path: str, thumbnail_path: str) -> None:
    """
    Process saved image: resize if needed and create thumbnail.

    Args:
        image_path: Path to the saved image
        thumbnail_path: Path where thumbnail will be saved
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img

            # Auto-rotate based on EXIF data
            img = ImageOps.exif_transpose(img)

            # Resize if image is too large
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                img.save(image_path, optimize=True, quality=85)

            # Create thumbnail
            img_copy = img.copy()
            img_copy.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img_copy.save(thumbnail_path, optimize=True, quality=80)

    except Exception as e:
        raise Exception(f"Failed to process image: {str(e)}")


def cleanup_file(file_path: str) -> None:
    """Remove file if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Ignore cleanup errors


def delete_image_files(image_path: str) -> None:
    """Delete image and its thumbnail."""
    # Delete main image
    cleanup_file(image_path)

    # Delete thumbnail
    filename = os.path.basename(image_path)
    thumbnail_path = os.path.join(Setting.thumbnail_dir, f"thumb_{filename}")
    cleanup_file(thumbnail_path)


def get_image_url(image_path: str, thumbnail: bool = False) -> str:
    """
    Convert file path to URL for frontend.

    Args:
        image_path: Full path to image file
        thumbnail: Whether to return thumbnail URL

    Returns:
        URL string for accessing the image
    """
    if thumbnail:
        filename = os.path.basename(image_path)
        return f"/static/uploads/thumbnails/thumb_{filename}"
    else:
        # Convert absolute path to relative URL
        if image_path.startswith(Setting.gallery_dir):
            filename = os.path.basename(image_path)
            return f"/static/uploads/plant_photos/{filename}"
        return image_path


def validate_image_exists(image_path: str) -> bool:
    """Check if image file exists."""
    return os.path.exists(image_path) and os.path.isfile(image_path)


def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
    """Get image dimensions without loading full image into memory."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return None


def extract_image_metadata(image_path: str) -> dict:
    """Extract metadata from image file."""
    metadata = {
        'dimensions': None,
        'format': None,
        'mode': None,
        'has_transparency': False,
        'exif_data': {}
    }

    try:
        with Image.open(image_path) as img:
            metadata['dimensions'] = img.size
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['has_transparency'] = img.mode in ('RGBA', 'LA') or 'transparency' in img.info

            # Extract basic EXIF data if available
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                if exif:
                    # Extract common EXIF tags
                    exif_tags = {
                        'DateTime': 306,
                        'Make': 271,
                        'Model': 272,
                        'Orientation': 274,
                        'XResolution': 282,
                        'YResolution': 283
                    }

                    for tag_name, tag_id in exif_tags.items():
                        if tag_id in exif:
                            metadata['exif_data'][tag_name] = exif[tag_id]

    except Exception as e:
        # Return basic metadata on error
        metadata['error'] = str(e)

    return metadata


def is_image_corrupted(image_path: str) -> bool:
    """Check if image file is corrupted."""
    try:
        with Image.open(image_path) as img:
            img.verify()  # This will raise an exception if corrupted
        return False
    except Exception:
        return True


def compress_image(image_path: str, quality: int = 85, max_size: Optional[Tuple[int, int]] = None) -> bool:
    """
    Compress existing image file.

    Args:
        image_path: Path to image file
        quality: JPEG quality (1-100)
        max_size: Optional maximum dimensions

    Returns:
        True if compression was successful
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img

            # Resize if max_size is specified
            if max_size and (img.size[0] > max_size[0] or img.size[1] > max_size[1]):
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save with compression
            img.save(image_path, 'JPEG', optimize=True, quality=quality)

        return True
    except Exception:
        return False