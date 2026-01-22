import uuid
from datetime import datetime
from app.services.firebase.storage import upload_bytes
from app.services.firebase.firestore import save_upload_record
from app.services.pdf.convert import pdf_to_image_bytes
from app.services.cv.pipeline import process_image_bytes


# async def handle_upload(file):
#     upload_id = str(uuid.uuid4())

#     # 1. Read file bytes
#     file_bytes = await file.read()

#     # 2. Save original file
#     original_url = upload_bytes(
#         # user_id=user_id,
#         upload_id=upload_id,
#         data=file_bytes,
#         folder="original",
#         content_type=file.content_type
#     )

#     # 3. Convert PDF → image (first page only)
#     if file.content_type == "application/pdf":
#         image_bytes = pdf_to_image_bytes(file_bytes)
#     else:
#         image_bytes = file_bytes

#     # 4. Run OpenCV pipeline
#     processed_images, warning = process_image_bytes(image_bytes)

#     # 5. Save processed images
#     processed_urls = []
#     for idx, img_bytes in enumerate(processed_images):
#         url = upload_bytes(
#             # user_id=user_id,
#             upload_id=f"{upload_id}_{idx}",
#             data=img_bytes,
#             folder="processed",
#             content_type="image/jpeg"
#         )
#         processed_urls.append(url)

#     # 6. Save Firestore metadata
#     save_upload_record(
#         # user_id=user_id,
#         upload_id=upload_id,
#         filename=file.filename,
#         original_url=original_url,
#         processed_urls=processed_urls,
#         status="processed",
#         warning=warning
#     )

#     return {
#         "success": True,
#         "original_url": original_url,
#         "processed_urls": processed_urls,
#         "warning": warning
#     }
import uuid
from pathlib import Path

UPLOAD_DIR = Path("uploads")

async def handle_upload(file):
    upload_id = str(uuid.uuid4())

    # Ensure folders exist
    original_dir = UPLOAD_DIR / "original"
    processed_dir = UPLOAD_DIR / "processed"
    original_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read file bytes
    file_bytes = await file.read()

    # 2. Save original file locally
    original_ext = Path(file.filename).suffix or ".bin"
    original_path = original_dir / f"{upload_id}{original_ext}"

    with open(original_path, "wb") as f:
        f.write(file_bytes)

    original_url = f"/uploads/original/{original_path.name}"

    # 3. Convert PDF → image (first page only)
    if file.content_type == "application/pdf":
        image_bytes = pdf_to_image_bytes(file_bytes)
    else:
        image_bytes = file_bytes

    # 4. Run OpenCV pipeline
    processed_images, warning = process_image_bytes(image_bytes)

    # 5. Save processed images locally
    processed_urls = []

    for idx, img_bytes in enumerate(processed_images):
        processed_path = processed_dir / f"{upload_id}_{idx}.jpg"

        with open(processed_path, "wb") as f:
            f.write(img_bytes)

        processed_urls.append(f"/uploads/processed/{processed_path.name}")

    return {
        "success": True,
        "original_url": original_url,
        "processed_urls": processed_urls,
        "warning": warning
    }
