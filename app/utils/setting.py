import configparser
import os
from typing import Optional


class Settings:
    """Application configuration settings"""
    
    def __init__(self):
        
        
        
        
        # Application Settings
        self.app_title = "Souradip Image Processing Api"
        self.app_description = "FastAPI backend for image processing"
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # CORS Settings
        self.cors_origins = ["*"]
        self.cors_allow_credentials = True
        self.cors_allow_methods = ["*"]
        self.cors_allow_headers = ["*"]
    



settings = Settings()
