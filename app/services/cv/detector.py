# import cv2
# import numpy as np

# from .preprocess import preprocess_image
# from .confidence import score_quad
# from .perspective import order_points


# # =========================================================
# # ORIENTATION NORMALIZATION (SAFE)
# # =========================================================
# def normalize_orientation(image):
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 50, 150)

#     lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
#     if lines is None or len(lines) < 5:
#         return image

#     angles = []
#     for i in range(min(20, len(lines))):
#         rho, theta = lines[i][0]
#         angle = (theta - np.pi / 2) * 180 / np.pi
#         angles.append(angle)

#     if not angles:
#         return image

#     median_angle = np.median(angles)
#     if abs(median_angle) < 5:
#         return image

#     h, w = image.shape[:2]
#     M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
#     return cv2.warpAffine(image, M, (w, h))


# # =========================================================
# # GEOMETRY + COLOR VALIDATION (CRITICAL)
# # =========================================================
# def is_reasonable_size(quad, image_area):
#     return cv2.contourArea(quad) < image_area * 0.88


# def has_document_aspect_ratio(quad):
#     rect = order_points(quad.reshape(4, 2))
#     w = np.linalg.norm(rect[0] - rect[1])
#     h = np.linalg.norm(rect[0] - rect[3])
#     ratio = max(w, h) / (min(w, h) + 1e-6)
#     return 1.2 < ratio < 2.5


# def looks_like_paper(image, quad):
#     mask = np.zeros(image.shape[:2], dtype=np.uint8)
#     cv2.fillPoly(mask, [quad.astype(int)], 255)

#     hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#     saturation = hsv[:, :, 1]
#     mean_sat = cv2.mean(saturation, mask=mask)[0]

#     return mean_sat < 80  # paper is low saturation


# def valid_document_quad(image, quad, image_area):
#     return (
#         is_reasonable_size(quad, image_area)
#         and has_document_aspect_ratio(quad)
#         and looks_like_paper(image, quad)
#     )


# # =========================================================
# # BRIGHTNESS FALLBACK (CONSTRAINED)
# # =========================================================
# def brightness_fallback(image, image_area):
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     blur = cv2.GaussianBlur(gray, (21, 21), 0)

#     _, thresh = cv2.threshold(
#         blur, 0, 255,
#         cv2.THRESH_BINARY + cv2.THRESH_OTSU
#     )

#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
#     thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

#     contours, _ = cv2.findContours(
#         thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
#     )

#     if not contours:
#         return None

#     contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]

#     for c in contours:
#         peri = cv2.arcLength(c, True)
#         approx = cv2.approxPolyDP(c, 0.02 * peri, True)

#         if len(approx) == 4 and valid_document_quad(image, approx, image_area):
#             return approx

#         hull = cv2.convexHull(c)
#         rect = cv2.minAreaRect(hull)
#         box = cv2.boxPoints(rect).astype("int")

#         if valid_document_quad(image, box, image_area):
#             return box

#     return None


# # =========================================================
# # MAIN DETECTION (CAMSCANNER-STYLE)
# # =========================================================
# def detect_documents(image):
#     image = normalize_orientation(image)

#     h, w = image.shape[:2]
#     image_area = h * w

#     results = []

#     # ---------- 1. EDGE-BASED DETECTION ----------
#     edges = preprocess_image(image)
#     contours, _ = cv2.findContours(
#         edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
#     )

#     for c in contours:
#         peri = cv2.arcLength(c, True)
#         approx = cv2.approxPolyDP(c, 0.02 * peri, True)

#         if len(approx) != 4:
#             continue

#         area = cv2.contourArea(approx)
#         if area < image_area * 0.12:
#             continue

#         if not valid_document_quad(image, approx, image_area):
#             continue

#         conf = score_quad(approx, image_area)
#         rect = order_points(approx.reshape(4, 2)).astype(int)

#         results.append({
#             "corners": rect.tolist(),
#             "confidence": round(conf, 3)
#         })

#     results.sort(key=lambda x: x["confidence"], reverse=True)

#     # ---------- 2. BRIGHTNESS FALLBACK (ONLY IF NONE FOUND) ----------
#     if not results:
#         quad = brightness_fallback(image, image_area)
#         if quad is not None:
#             rect = order_points(np.array(quad).reshape(4, 2)).astype(int)
#             results.append({
#                 "corners": rect.tolist(),
#                 "confidence": 0.45
#             })

#     # ---------- 3. HARD FAIL-SAFE ----------
#     if not results:
#         m = int(min(h, w) * 0.08)
#         results.append({
#             "corners": [
#                 [m, m],
#                 [w - m, m],
#                 [w - m, h - m],
#                 [m, h - m]
#             ],
#             "confidence": 0.0
#         })

#     # ---------- 4. WARNING LOGIC ----------
#     warning = None
#     if results[0]["confidence"] < 0.7:
#         warning = "low_confidence"
#     preview_path = None
#     if results:
#         preview_path = save_preview_with_overlay(
#             image,
#             results[0]["corners"]
#         )
#     return {
#         "documents": results,
#         "warning": warning
#     }
# import os
# import uuid


# def save_preview_with_overlay(image, quad, output_dir="uploads/preview"):
#     """
#     Draws detected document quad in yellow and saves preview image
#     """
#     os.makedirs(output_dir, exist_ok=True)

#     preview = image.copy()
#     quad = np.array(quad, dtype="int32")

#     # Draw polygon (yellow)
#     cv2.polylines(
#         preview,
#         [quad],
#         isClosed=True,
#         color=(0, 255, 255),  # BGR: Yellow
#         thickness=4
#     )

#     filename = f"{uuid.uuid4().hex}_preview.jpg"
#     path = os.path.join(output_dir, filename)

#     cv2.imwrite(path, preview)
#     return path



import cv2
import numpy as np
import os
import uuid

from .perspective import order_points
from .confidence import score_quad, calculate_detection_confidence
from .scanner import DocScanner


# Initialize global scanner instance
_scanner = DocScanner()


def detect_documents(image):
    """
    Detect documents in an image using advanced multi-method detection.
    
    Returns:
        dict with:
        - documents: list of detected documents with corners and confidence
        - warning: optional warning message
        - preview_path: path to preview image
    """
    h, w = image.shape[:2]
    image_area = h * w
    
    # Use the enhanced scanner
    corners, confidence, method = _scanner.detect(image)
    
    # Order corners consistently
    corners_ordered = order_points(corners.astype(np.float32)).astype(int)
    
    # Calculate refined confidence
    final_confidence = calculate_detection_confidence(corners_ordered, image.shape, method)
    
    documents = [{
        "corners": corners_ordered.tolist(),
        "confidence": final_confidence,
        "method": method
    }]
    
    # Generate warning if confidence is low
    warning = None
    if final_confidence < 0.5:
        warning = "low_confidence"
    elif final_confidence < 0.7:
        warning = "moderate_confidence"
    
    # Save preview
    preview_path = save_preview_with_overlay(image, corners_ordered, final_confidence)
    
    return {
        "documents": documents,
        "warning": warning,
        "preview_path": preview_path
    }


def save_preview_with_overlay(image, corners, confidence=None, output_dir="uploads/previews"):

    os.makedirs(output_dir, exist_ok=True)
    
    preview = image.copy()
    corners = np.array(corners, dtype=np.int32)
    
    # Semi-transparent fill
    overlay = preview.copy()
    cv2.fillPoly(overlay, [corners], (0, 255, 255))
    preview = cv2.addWeighted(overlay, 0.15, preview, 0.85, 0)
    
    # Draw polygon outline (yellow)
    cv2.polylines(
        preview,
        [corners],
        isClosed=True,
        color=(0, 255, 255),
        thickness=4
    )
    
    # Draw corner markers
    for i, pt in enumerate(corners):
        # Outer circle
        cv2.circle(preview, tuple(pt), 15, (0, 255, 0), 3)
        # Inner filled circle
        cv2.circle(preview, tuple(pt), 6, (0, 255, 0), -1)
    
    # Add confidence text
    if confidence is not None:
        h, w = preview.shape[:2]
        conf_text = f"Confidence: {confidence:.0%}"
        
        # Choose color based on confidence
        if confidence >= 0.7:
            color = (0, 255, 0)  # Green
        elif confidence >= 0.4:
            color = (0, 165, 255)  # Orange
        else:
            color = (0, 0, 255)  # Red
        
        # Background box
        text_size = cv2.getTextSize(conf_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        cv2.rectangle(preview, (5, 5), (text_size[0] + 25, text_size[1] + 25), (0, 0, 0), -1)
        cv2.putText(preview, conf_text, (15, text_size[1] + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    
    filename = f"{uuid.uuid4().hex}_preview.jpg"
    path = os.path.join(output_dir, filename)
    
    cv2.imwrite(path, preview, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    return path


def save_preview(image, quad, path):
    """Legacy function for compatibility"""
    preview = image.copy()
    quad = np.array(quad, dtype="int32")
    cv2.polylines(preview, [quad], True, (0, 255, 255), 4)
    cv2.imwrite(path, preview)
