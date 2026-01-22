
# Image Crop Assignment API

Made by Souradip Biswas

## Introduction
This project is for uploading images, detecting document corners, and cropping images. It is made using FastAPI. Images are saved in Cloudinary, and all details are stored in Firebase Firestore. Users can upload, crop, and manage their images easily.
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

```

## How to Setup
1. First, install all requirements using:
   ```
   pip install -r requirements.txt
   ```
2. Make one `.env` file and put your Cloudinary and Firebase details inside.
3. To start the API, run:
   ```
   uvicorn app.main:app --reload
   ```

## How it Works
1. **Login**: User will login using Firebase. Every upload is linked to the user.
2. **Upload Image**: User uploads image using `/uploads/detect` endpoint. Image goes to Cloudinary, and details go to Firestore.
3. **Detect Corners**: API will find document corners in the image and give you the points and preview image link.
4. **Crop Image**: User can send their own crop points using `/uploads/crop`. API will crop and save the new image.
5. **List Uploads**: User can see all their uploads using `/uploads/list`.
6. **Delete Uploads**: User can delete their uploads using `/uploads/delete`. It is a soft delete, so data is not lost.

## Technologies Used
- FastAPI
- Cloudinary
- Firebase Admin SDK
- Firestore
- OpenCV
- python-dotenv

## Author
Souradip Biswas
