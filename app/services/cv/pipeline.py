from app.services.cv.transform import four_point_transform
import cv2
import numpy  as np
import io
JPEG_PARAMS = [int(cv2.IMWRITE_JPEG_QUALITY), 95]


def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Better for notebook paper + shadows
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    blur = cv2.GaussianBlur(thresh, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    # 🔥 CONNECT BROKEN EDGES
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=2)
    edges = cv2.erode(edges, kernel, iterations=1)

    return edges


def process_image_bytes(image_bytes: bytes):
    image = cv2.imdecode(
        np.frombuffer(image_bytes, np.uint8),
        cv2.IMREAD_COLOR
    )

    h, w = image.shape[:2]
    image_area = h * w

    edges = preprocess_image(image)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    page_contours = []

    for c in contours:
        area = cv2.contourArea(c)

        # 🔥 LOWERED threshold (CRITICAL FIX)
        if area < image_area * 0.02:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)

        if len(approx) >= 4:
            page_contours.append(approx)

    # 🔥 STRONG FAIL-SAFE (MANDATORY BY SPEC)
    if not page_contours:
        margin_x = int(w * 0.1)
        margin_y = int(h * 0.1)

        fallback = np.array([
            [margin_x, margin_y],
            [w - margin_x, margin_y],
            [w - margin_x, h - margin_y],
            [margin_x, h - margin_y]
        ], dtype="float32")


        warped = four_point_transform(image, fallback)
        _, buf = cv2.imencode(".jpg", warped, JPEG_PARAMS)


        return [buf.tobytes()], "Low confidence fallback"

    processed_images = []

    # Take top 2 largest contours (for notebook case)
    page_contours = sorted(
        page_contours,
        key=cv2.contourArea,
        reverse=True
    )[:2]

    for approx in page_contours:
        warped = four_point_transform(image, approx.reshape(-1, 2))
        _, buf = cv2.imencode(".jpg", warped, JPEG_PARAMS)
        processed_images.append(buf.tobytes())

    return processed_images, None
