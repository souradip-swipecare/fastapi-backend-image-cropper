import os
from dotenv import load_dotenv
import cloudinary
import firebase_admin
from firebase_admin import credentials

# load environment variables from .env file
load_dotenv()


def initialize_firebase():
    try :
        if firebase_admin._apps:
            return  
        print("firebase loaded started")   
        cred = credentials.Certificate("souradip-opencv-assignment-serviceAccountKey.json")
        firebase_admin.initialize_app(cred,{
        "storageBucket": "souradip-opencv-assignment.appspot.com"
    })

        print("firebase loaded")
        return
    except Exception as e :
        raise Exception(e)

def initialize_cloudinary():
    try:
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name"),
            api_key=os.getenv("CLOUDINARY_API_KEY", "your_api_key"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET", "your_api_secret"),
            secure=True
        )
    except Exception as e :
        print(e)
        print("Failed to initialize cloudinary")
