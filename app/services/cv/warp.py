
import cv2
import numpy as np


def four_point_transform(image, pts, output_size=None):

    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    # Compute dimensions
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    # Use provided size or calculated
    if output_size:
        maxWidth, maxHeight = output_size
    
    # Destination points (perfect rectangle)
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype=np.float32)
    
    # Transform
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped


def order_points(pts):
    pts = np.array(pts, dtype=np.float32)
    rect = np.zeros((4, 2), dtype=np.float32)
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    
    return rect


def auto_crop_borders(image, threshold=10):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Find non-border region
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # Find bounding box of content
    coords = cv2.findNonZero(binary)
    if coords is None:
        return image
    
    x, y, w, h = cv2.boundingRect(coords)
    
    # Add small margin
    margin = 2
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(image.shape[1] - x, w + 2 * margin)
    h = min(image.shape[0] - y, h + 2 * margin)
    
    return image[y:y+h, x:x+w]


def enhance_document(image, mode="auto"):

    if image is None or image.size == 0:
        return image
    
    enhanced = image.copy()
    
    # Convert to LAB
    lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply mild CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Merge back
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    # Very light sharpening
    kernel = np.array([
        [0, -0.5, 0],
        [-0.5, 3, -0.5],
        [0, -0.5, 0]
    ], dtype=np.float32)
    enhanced = cv2.filter2D(enhanced, -1, kernel)
    
    return enhanced


def enhance_document_bw(image):

    if image is None or image.size == 0:
        return image
    
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Apply adaptive thresholding for clean text
    # Use Gaussian adaptive threshold for smooth results
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, 10
    )
    
    # Clean up small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Convert back to BGR for consistency
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    return result


def enhance_document_gray(image):
    
    if image is None or image.size == 0:
        return image
    
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 8, 7, 21)
    
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Stretch histogram
    p2, p98 = np.percentile(enhanced, (2, 98))
    enhanced = np.clip((enhanced - p2) * 255.0 / (p98 - p2 + 1e-6), 0, 255).astype(np.uint8)
    
    # Sharpen
    sharpen_kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ], dtype=np.float32)
    enhanced = cv2.filter2D(enhanced, -1, sharpen_kernel)
    
    # Convert back to BGR
    result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    return result