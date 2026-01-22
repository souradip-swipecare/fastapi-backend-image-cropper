from fastapi import APIRouter
from app.api.v1.endpoints import auth, upload, gallery

#  we add prefuix under this router also but further we include  using sub route
api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    upload.router,
    prefix="/uploads",
    tags=["uploads"]
)

api_router.include_router(
    gallery.router,
    prefix="/gallery",
    tags=["gallery"]
)
