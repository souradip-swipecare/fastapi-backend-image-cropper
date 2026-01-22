from fastapi import APIRouter, Depends
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/")
def list_uploads(user=Depends(get_current_user)):
    return {
        "user_id": user["uid"],
        "uploads": []
    }
