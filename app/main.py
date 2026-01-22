# app/main.py
from urllib.request import Request
from venv import logger
from app.api.v1 import api
from app.core.config import initialize_cloudinary, initialize_firebase
from app.utils.setting import settings
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

app = FastAPI(title="Document Scanner API")

@app.get("/health")
def health():
    return {"status": "ok"}

def create_app() -> FastAPI:
    #  set up firebase
    initialize_firebase()
    #  set up cloudinary
    initialize_cloudinary()
    
    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
    )
    

    

    # add cors middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # include routers v1 or v2 withou  loosin g old version
    app.include_router(api.api_router, prefix="/api/v1")


    # global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": str(exc) if settings.debug else None,
            },
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.app_title,
            "version": settings.app_version
        }
    
    return app


# Create app instance
app = create_app()