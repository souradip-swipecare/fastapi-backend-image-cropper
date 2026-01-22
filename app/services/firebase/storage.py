import uuid
from firebase_admin import storage



def get_bucket():
    return storage.bucket()

def upload_bytes(
    # user_id: str,
    upload_id: str,
    data: bytes,
    folder: str,
    content_type: str
) -> str:
    bucket = get_bucket()   # ✅ now safe
    path = f"users/234434/{folder}/{upload_id}.jpg"
    # path = f"users/{user_id}/{folder}/{upload_id}.jpg"
    blob = bucket.blob(path)

    blob.upload_from_string(data, content_type=content_type)
    blob.make_public()

    return blob.public_url

