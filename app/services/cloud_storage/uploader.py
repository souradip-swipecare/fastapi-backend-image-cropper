import cloudinary
import cloudinary.uploader
import uuid
import os





def upload_image_to_cloudinary(
    image_bytes: bytes,
    user_id: str,
    file_id: str,
    folder: str = "uploads"
) -> dict:
    """
    Upload raw image to Cloudinary preserving original quality and resolution.
    """
    result = cloudinary.uploader.upload(
        image_bytes,
        folder=f"document_scanner/{user_id}/{folder}",
        public_id=file_id,
        resource_type="image",
        # Preserve original quality - no compression or resizing
        quality=100,  # Maximum quality (no compression)
        overwrite=True,
        invalidate=True,
        # Prevent any automatic transformations
        transformation=None,
        use_filename=False,
        unique_filename=False,
    )
    
    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "format": result.get("format"),
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
        "original_filename": result.get("original_filename")
    }
