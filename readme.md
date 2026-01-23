# Image Crop Assignment API

**Made by Souradip Biswas**

---



## How to Run

### Step 1: Create a virtual environment
```bash
python3 -m venv venv
```

### Step 2: Activate the virtual environment
```bash
source venv/bin/activate
```

### Step 3: Install all dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create a `.env` file
Create a `.env` file in the root folder with your credentials:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=your_client_cert_url
FIREBASE_UNIVERSE_DOMAIN=googleapis.com
```

### Step 5: Start the server
```bash
uvicorn app.main:app --reload
```

The API will be running at `http://localhost:8000`

### To deactivate the virtual environment (when done)
```bash
deactivate
```

---
## Authentication

**All APIs require a Firebase token.**

You need to send a `Bearer` token in the header for every request:
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

To check if your token is working:
- **GET** `/api/v1/auth/me` → Returns your user ID and email

---

## API Endpoints

### 1. Upload & Detect Document

**POST** `/api/v1/uploads/uploads/detect`

This is the first step. Upload your image and the system will try to find the document corners automatically.

**What to send:**
- `file` (form-data) - Your image file

**What you get back:**
```json
{
  "success": true,
  "fileId": "abc-123-xyz",
  "originalUrl": "https://cloudinary.com/...",
  "previewUrl": "https://cloudinary.com/...",
  "corners": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
  "confidence": 0.85,
  "imageSize": {"width": 1920, "height": 1080},
  "warning": null
}
```

**What the response means:**
| Field | Meaning |
|-------|---------|
| `fileId` | Save this! You need it for cropping |
| `originalUrl` | Link to your uploaded image |
| `previewUrl` | Link to preview with detected corners drawn |
| `corners` | The 4 corner points detected (can be adjusted) |
| `confidence` | How sure the system is (0 to 1). Higher is better |
| `warning` | If something looks off, you'll see a message here |

---

### 2. Crop the Document

**POST** `/api/v1/uploads/uploads/crop`

After detecting, use this to crop the document. You can use the auto-detected corners or provide your own.

**What to send (form-data):**
| Field | Required | Description |
|-------|----------|-------------|
| `file_id` | Yes | The `fileId` from detect step |
| `user_crop_data` | Yes | JSON string of 4 corner points, e.g. `[[0,0], [100,0], [100,100], [0,100]]` |
| `enhance` | No | `true` or `false` - Makes the document clearer (default: true) |
| `auto_trim` | No | `true` or `false` - Removes extra borders (default: true) |

**What you get back:**
```json
{
  "success": true,
  "fileId": "abc-123-xyz",
  "croppedUrl": "https://cloudinary.com/...",
  "status": "processed",
  "dimensions": {"width": 800, "height": 1000}
}
```

---

### 3. List Your Uploads

**POST** `/api/v1/uploads/uploads/list`

See all the images you have uploaded.

**What to send (form-data):**
| Field | Required | Description |
|-------|----------|-------------|
| `limit` | No | How many to show (default: 10) |
| `cursor` | No | For pagination - use `nextCursor` from previous response |

**What you get back:**
```json
{
  "success": true,
  "count": 5,
  "uploads": [
    {
      "fileId": "abc-123",
      "filename": "receipt.jpg",
      "originalUrl": "...",
      "previewUrl": "...",
      "croppedUrl": "...",
      "status": "processed",
      "createdAt": "2024-01-15T10:30:00"
    }
  ],
  "hasMore": true,
  "nextCursor": "xyz-789"
}
```

---

### 4. Delete an Upload

**POST** `/api/v1/uploads/uploads/delete`

Delete one of your uploads. This is a "soft delete" - the data is marked as deleted but not actually removed.

**What to send (form-data):**
| Field | Required | Description |
|-------|----------|-------------|
| `file_id` | Yes | The `fileId` you want to delete |

**What you get back:**
```json
{
  "success": true,
  "message": "Record deleted successfully",
  "fileId": "ghfffgfffgfghfghf"
}
```

---

## Typical Flow

Here's how a normal user would use this:

```
1. User logs in with Firebase → Gets a token

2. User uploads a photo of a document
   → POST /api/v1/uploads/uploads/detect
   → Gets back corners and preview

3. User looks at preview, adjusts corners if needed

4. User sends the final corners to crop
   → POST /api/v1/uploads/uploads/crop
   → Gets back the clean, cropped document

5. User can view all uploads anytime
   → POST /api/v1/uploads/uploads/list

6. User can delete if needed
   → POST /api/v1/uploads/uploads/delete
```

---

## Tech Stack

| What | Why |
|------|-----|
| **FastAPI** | Fast Python web framework |
| **OpenCV** | Image processing and corner detection |
| **Cloudinary** | Cloud storage for images |
| **Firebase Auth** | User authentication |
| **Firebase Firestore** | Database for storing records |

---

## Error Handling

If something goes wrong, you'll get:

```json
{
  "detail": "Error message explaining what happened"
}
```

Common errors:
- `401` - Your token is invalid or expired
- `403` - You're trying to access someone else's data
- `404` - The file ID doesn't exist
- `400` - Bad request (check your input data)

---

## Author

**Souradip Biswas**
