from datetime import datetime
from firebase_admin import firestore
import numpy as np
import json


def get_db():
    return firestore.client()


def convert_to_firestore_safe(obj):
    """Convert numpy types and nested structures to Firestore-safe Python types.
    For deeply nested arrays, convert to JSON string to avoid Firestore nesting limits.
    """
    if obj is None:
        return None
    if isinstance(obj, np.ndarray):
        # Convert numpy array to list first
        converted = obj.tolist()
        # If it's deeply nested (more than 2 levels), store as JSON string
        if _get_nesting_depth(converted) > 2:
            return json.dumps(converted)
        return converted
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: convert_to_firestore_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        converted = [convert_to_firestore_safe(item) for item in obj]
        # Check if result is too deeply nested
        if _get_nesting_depth(converted) > 2:
            return json.dumps(converted)
        return converted
    return obj


def _get_nesting_depth(obj, current_depth=0):
    if isinstance(obj, dict):
        if not obj:
            return current_depth + 1
        return max(_get_nesting_depth(v, current_depth + 1) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        if not obj:
            return current_depth + 1
        return max(_get_nesting_depth(item, current_depth + 1) for item in obj)
    return current_depth


def save_upload_record(
    user_id: str,
    upload_id: str,
    filename: str,
    original_url: str,
    processed_urls: list,
    status: str,
    warning: str | None
):  
    db = get_db()
    db.collection("uploads").document(upload_id).set({
        "userId": user_id,
        "filename": filename,
        "original_url": original_url,
        "processed_urls": processed_urls,
        "status": status,
        "warning": warning,
        "createdAt": datetime.utcnow()
    })


def save_detect_record(
    user_id: str,
    file_id: str,
    filename: str,
    original_url: str,
    preview_url: str = "",
    cropped_url: str = "",
    status: str = "pending",
    is_processed: bool = False,
    detect_points: dict | None = None,
    user_crop_data: dict | None = None,
    confidence: float = 0.0,
    method: str | None = None,
    image_size: dict | None = None
):

    db = get_db()
    record = {
        "userId": user_id,
        "fileId": file_id,
        "filename": filename,
        "originalUrl": original_url,
        "previewUrl": preview_url,
        "croppedUrl": cropped_url,
        "status": status,
        "isProcessed": is_processed,
        "detectPoints": convert_to_firestore_safe(detect_points),
        "userCropData": convert_to_firestore_safe(user_crop_data),
        "confidence": float(confidence) if confidence else 0.0,
        "method": method,
        "imageSize": convert_to_firestore_safe(image_size),
        "is_deleted": False,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    db.collection("image_detections").document(file_id).set(record)
    return record


def update_detect_record(file_id: str, updates: dict):
    db = get_db()
    safe_updates = convert_to_firestore_safe(updates)
    safe_updates["updatedAt"] = datetime.utcnow()
    db.collection("image_detections").document(file_id).update(safe_updates)


def get_detect_record(file_id: str):
    db = get_db()
    doc = db.collection("image_detections").document(file_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

# fetch images with pagination
def get_user_image_detections(
    user_id: str, 
    limit: int = 10, 
    last_file_id: str | None = None
) -> dict:
    """
    Get user's image detections with cursor-based pagination.
    
    Args:
        user_id: Firebase user ID
        limit: Number of records per page
        last_file_id: The fileId of the last record from previous page (cursor)
    
    Returns:
        dict with 'records', 'hasMore', and 'nextCursor'
    """
    db = get_db()
    
    query = (
        db.collection("image_detections")
        .where("userId", "==", user_id)
        .where("is_deleted", "==", False)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
    )
    
    # If cursor provided, start after that document
    if last_file_id:
        last_doc = db.collection("image_detections").document(last_file_id).get()
        if last_doc.exists:
            query = query.start_after(last_doc)
    
    # Fetch one extra to check if there are more
    docs = list(query.limit(limit + 1).stream())
    
    has_more = len(docs) > limit
    records = [doc.to_dict() for doc in docs[:limit]]
    
    next_cursor = None
    if has_more and records:
        next_cursor = records[-1].get("fileId")
    
    return {
        "records": records,
        "hasMore": has_more,
        "nextCursor": next_cursor
    }


def soft_delete_record(user_id: str, file_id: str) -> bool:
    db = get_db()
    doc_ref = db.collection("image_detections").document(file_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return False
    
    record = doc.to_dict()
    if record.get("userId") != user_id:
        return False
    
    doc_ref.update({
        "is_deleted": True,
        "updatedAt": datetime.utcnow()
    })
    return True
