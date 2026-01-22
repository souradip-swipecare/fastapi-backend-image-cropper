from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from app.services.cv.warp import four_point_transform, auto_crop_borders, enhance_document
from app.services.cloud_storage.uploader import upload_image_to_cloudinary
from app.services.firebase.firestore import (
    save_detect_record, 
    get_detect_record, 
    update_detect_record,
    get_user_image_detections,
    soft_delete_record
)
from app.core.sequrity import get_current_user
import numpy as np
import cv2
import json
import uuid
import os
import requests

from app.services.cv.scanner import DocScanner
from app.services.cv.preview import save_preview

router = APIRouter()
scanner = DocScanner()


def flatten_corners(corners):
    """Flatten OpenCV corners to simple [[x,y], [x,y], ...] format"""
    if corners is None:
        return None
    corners_list = corners.tolist() if hasattr(corners, 'tolist') else corners
    flat_corners = []
    for point in corners_list:
        if isinstance(point, list) and len(point) == 1 and isinstance(point[0], list):
            flat_corners.append([float(point[0][0]), float(point[0][1])])
        elif isinstance(point, list) and len(point) == 2:
            flat_corners.append([float(point[0]), float(point[1])])
        else:
            flat_corners.append(point)
    return flat_corners


@router.post("/uploads/detect")
async def detect(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):

    user_id = current_user["uid"]
    file_id = str(uuid.uuid4())
    
    data = await file.read()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    
    if image is None:
        return {"error": "Invalid image file", "success": False}
    try:
        raw_result = upload_image_to_cloudinary(
            image_bytes=data,
            user_id=user_id,
            file_id=file_id,
            folder="originals"
        )
        original_url = raw_result.get("url", "")
    except Exception as e:
        return {"error": f"Failed to upload raw image to Cloudinary: {str(e)}", "success": False}
    corners, confidence, method = scanner.detect(image)
    image_size = {"width": int(image.shape[1]), "height": int(image.shape[0])}
    
    preview_path = save_preview(image, corners, confidence)
    preview_url = ""
    if preview_path and os.path.exists(preview_path):
        try:
            with open(preview_path, 'rb') as f:
                preview_data = f.read()
            preview_result = upload_image_to_cloudinary(
                image_bytes=preview_data,
                user_id=user_id,
                file_id=f"{file_id}_preview",
                folder="previews"
            )
            preview_url = preview_result.get("url", "")
        except Exception as e:
            print(f"Failed to upload preview: {e}")
    flat_corners = flatten_corners(corners)
    detect_points = None
    if corners is not None:
        detect_points = {
            "corners": json.dumps(flat_corners),  # Store as JSON string
            "confidence": float(confidence) if confidence else 0.0,
            "method": method
        }
    warning = None
    if corners is None:
        warning = "Could not detect document edges. Try better lighting or clearer background."
    elif confidence < 0.4:
        warning = "Low confidence detection. Please adjust corners manually."
    elif confidence < 0.7:
        warning = "Moderate confidence. Review detected edges."

    # save to firebase
    detect_record = save_detect_record(
        user_id=user_id,
        file_id=file_id,
        filename=file.filename or "unknown",
        original_url=original_url,
        preview_url=preview_url,
        cropped_url="",  # Will be set after crop
        status="pending",
        is_processed=False,
        detect_points=detect_points,
        user_crop_data=None,  # Will be set by user in crop
        confidence=float(confidence) if confidence else 0.0,
        method=method,
        image_size=image_size
    )

    return {
        "success": corners is not None,
        "fileId": file_id,
        "userId": user_id,
        "originalUrl": original_url,
        "previewUrl": preview_url,
        "croppedUrl": "",
        "status": "pending",
        "isProcessed": False,
        "corners": flat_corners,
        "confidence": float(confidence) if confidence else 0.0,
        "method": method,
        "warning": warning,
        "imageSize": image_size
    }


@router.post("/uploads/crop")
async def crop(
    file_id: str = Form(...),
    user_crop_data: str = Form(...),
    enhance: bool = Form(True),
    auto_trim: bool = Form(True),
    current_user: dict = Depends(get_current_user),
):

    user_id = current_user["uid"]
    
    # 1. Get record from Firebase
    record = get_detect_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Verify the record belongs to this user
    if record.get("userId") != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this record")
    
    original_url = record.get("originalUrl", "")
    if not original_url:
        raise HTTPException(status_code=400, detail="Original image URL not found")
    try:
        user_corners = json.loads(user_crop_data)
        corner_points = np.array(user_corners, dtype=np.float32)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid crop data: {str(e)}")
    try:
        response = requests.get(original_url)
        response.raise_for_status()
        image_data = response.content
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch raw image: {str(e)}")
    
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to decode image")
    warped = four_point_transform(image, corner_points)
    if auto_trim:
        warped = auto_crop_borders(warped)
    if enhance:
        warped = enhance_document(warped)
    _, cropped_buffer = cv2.imencode('.jpg', warped, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
    cropped_bytes = cropped_buffer.tobytes()
    try:
        cropped_result = upload_image_to_cloudinary(
            image_bytes=cropped_bytes,
            user_id=user_id,
            file_id=f"{file_id}_cropped",
            folder="cropped"
        )
        cropped_url = cropped_result.get("url", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload cropped image: {str(e)}")
    output_dir = "uploads/cropped"
    os.makedirs(output_dir, exist_ok=True)
    local_path = f"{output_dir}/{file_id}.jpg"
    cv2.imwrite(local_path, warped, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
    update_detect_record(file_id, {
        "userCropData": json.dumps(user_corners),  # Store as JSON string
        "croppedUrl": cropped_url,
        "status": "processed",
        "isProcessed": True
    })
    
    return {
        "success": True,
        "fileId": file_id,
        "croppedUrl": cropped_url,
        "localPath": local_path,
        "status": "processed",
        "isProcessed": True,
        "dimensions": {
            "width": int(warped.shape[1]),
            "height": int(warped.shape[0])
        },
        "enhanced": enhance,
        "userCropData": user_corners
    }




@router.post("/uploads/list")
async def list_user_uploads(
    current_user: dict = Depends(get_current_user),
    limit: int = Form(default=10),
    cursor: str = Form(default=None),
):
    
    user_id = current_user["uid"]
    
    result = get_user_image_detections(
        user_id=user_id, 
        limit=limit, 
        last_file_id=cursor
    )
    
    uploads = []
    for record in result["records"]:
        uploads.append({
            "fileId": record.get("fileId"),
            "filename": record.get("filename"),
            "originalUrl": record.get("originalUrl", ""),
            "previewUrl": record.get("previewUrl", ""),
            "croppedUrl": record.get("croppedUrl", ""),
            "status": record.get("status"),
            "isProcessed": record.get("isProcessed", False),
            "createdAt": record.get("createdAt"),
        })
    
    return {
        "success": True,
        "userId": user_id,
        "count": len(uploads),
        "uploads": uploads,
        "hasMore": result["hasMore"],
        "nextCursor": result["nextCursor"]
    }


@router.post("/uploads/delete")
async def delete_upload(
    file_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["uid"]
    success = soft_delete_record(user_id, file_id)
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Record not found or you don't have permission to delete it"
        )
    return {
        "success": True,
        "message": "Record deleted successfully",
        "fileId": file_id
    }