# Image Crop Assignment API

Created by Souradip Biswas

## Overview
This project is an image upload, detection, and cropping API built with FastAPI. It integrates Cloudinary for image storage and Firebase Firestore for metadata management. The API allows users to upload images, detect document corners, crop images, and manage their uploads securely.

## Folder Structure
```
readme.md
requirements.txt
souradip-opencv-assignment-serviceAccountKey.json
app/
    main.py
    api/
        v1/
            api.py
            endpoints/
                auth.py
                gallery.py
                upload.py
    core/
        config.py
        sequrity.py
    db/
    models/
    schemas/
        upload.py
    services/
        upload_service.py
        cv/
            confidence.py
            detector.py
            perspective.py
            pipeline.py
            preprocess.py
            preview.py
            scanner.py
            transform.py
            warp.py
        firebase/
            firestore.py
            storage.py
        pdf/
            convert.py
        tests/
        utils/
            image.py
            setting.py
uploads/
    cropped/
    previews/
testingimages/
```

## Workflow
1. **User Authentication**: Users authenticate using Firebase. Each upload is linked to a user.
2. **Image Upload**: Users upload images via the `/uploads/detect` endpoint. Images are stored in Cloudinary, and metadata is saved in Firestore.
3. **Detection**: The API detects document corners in the uploaded image and returns the detected points and preview URLs.
4. **Cropping**: Users can submit their own crop points via `/uploads/crop`. The API crops the image and saves the result.
5. **Listing Uploads**: Users can list their uploads using `/uploads/list`.
6. **Delete Uploads**: Users can soft-delete uploads using `/uploads/delete`.

## Technologies Used
- FastAPI
- Cloudinary
- Firebase Admin SDK
- Firestore
- OpenCV
- Python-dotenv

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in a `.env` file (Cloudinary, Firebase credentials).
3. Start the API: `uvicorn app.main:app --reload`

## Author
Souradip Biswas
