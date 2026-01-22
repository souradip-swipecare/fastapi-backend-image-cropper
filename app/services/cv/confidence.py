import cv2
import numpy as np
from .perspective import order_points


def score_quad(quad, image_area, image=None):
    """
    Calculate confidence score for a detected quadrilateral.
    
    Factors considered:
    1. Area ratio (larger = better)
    2. Angle regularity (closer to 90° corners = better)
    3. Edge straightness
    4. Paper color detection (if image provided)
    """
    quad = np.array(quad, dtype=np.float32)
    if quad.shape[0] != 4:
        return 0.0
    
    area = cv2.contourArea(quad)
    area_ratio = area / image_area
    if area_ratio < 0.1:
        area_score = area_ratio * 2  # Penalize very small
    elif area_ratio > 0.9:
        area_score = 0.5  # Penalize too large (likely whole image)
    else:
        area_score = min(1.0, area_ratio / 0.5)
    
    # Score 2: Angle regularity (corners should be ~90°)
    rect = order_points(quad.reshape(4, 2))
    angles = []
    
    for i in range(4):
        p0 = rect[i]
        p1 = rect[(i + 1) % 4]
        p2 = rect[(i + 2) % 4]
        
        v1 = p0 - p1
        v2 = p2 - p1
        
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        if norm_product < 1e-6:
            angles.append(90)
            continue
            
        cos = np.dot(v1, v2) / norm_product
        angle = np.degrees(np.arccos(np.clip(cos, -1, 1)))
        angles.append(angle)
    
    # All angles should be close to 90 degrees
    angle_deviations = [abs(a - 90) for a in angles]
    avg_deviation = np.mean(angle_deviations)
    angle_score = max(0, 1 - (avg_deviation / 45.0))  # 0 if deviation > 45°
    
    # Score 3: Aspect ratio (documents are typically portrait or landscape)
    widths = [np.linalg.norm(rect[1] - rect[0]), np.linalg.norm(rect[2] - rect[3])]
    heights = [np.linalg.norm(rect[3] - rect[0]), np.linalg.norm(rect[2] - rect[1])]
    
    avg_width = np.mean(widths)
    avg_height = np.mean(heights)
    
    if avg_width > 0 and avg_height > 0:
        aspect = max(avg_width, avg_height) / min(avg_width, avg_height)
        # Common document aspects: A4 (1.414), Letter (1.294), etc.
        if 1.2 <= aspect <= 2.0:
            aspect_score = 1.0
        elif 1.0 <= aspect < 1.2:
            aspect_score = 0.8
        elif 2.0 < aspect <= 3.0:
            aspect_score = 0.6
        else:
            aspect_score = 0.4
    else:
        aspect_score = 0.5
    
    # Score 4: Edge parallelism (opposite edges should be parallel)
    def edge_angle(p1, p2):
        return np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
    
    top_angle = edge_angle(rect[0], rect[1])
    bottom_angle = edge_angle(rect[3], rect[2])
    left_angle = edge_angle(rect[0], rect[3])
    right_angle = edge_angle(rect[1], rect[2])
    
    horizontal_diff = abs(np.degrees(top_angle - bottom_angle))
    vertical_diff = abs(np.degrees(left_angle - right_angle))
    
    horizontal_diff = min(horizontal_diff, 180 - horizontal_diff)
    vertical_diff = min(vertical_diff, 180 - vertical_diff)
    
    parallel_score = max(0, 1 - (horizontal_diff + vertical_diff) / 60.0)
    
    color_score = 0.5  # Default neutral
    if image is not None:
        color_score = _score_paper_color(image, quad)
    
    # Weighted combination
    final_score = (
        0.25 * area_score +
        0.25 * angle_score +
        0.15 * aspect_score +
        0.20 * parallel_score +
        0.15 * color_score
    )
    
    return round(min(0.99, max(0.0, final_score)), 3)


def _score_paper_color(image, quad):
    """
    Check if the region inside the quad looks like paper (high brightness, low saturation)
    """
    try:
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [quad.astype(int)], 255)
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Get mean values in the masked region
        mean_hsv = cv2.mean(hsv, mask=mask)
        h, s, v = mean_hsv[:3]
        
        # Paper characteristics:
        # - Low saturation (< 80)
        # - High value/brightness (> 100)
        sat_score = max(0, 1 - (s / 100.0)) if s < 100 else 0.2
        val_score = min(1.0, v / 180.0) if v > 80 else 0.3
        
        return 0.5 * sat_score + 0.5 * val_score
    except:
        return 0.5


def calculate_detection_confidence(corners, image_shape, method="unknown"):
    """
    Calculate overall confidence for document detection result.
    """
    h, w = image_shape[:2]
    image_area = h * w
    
    corners = np.array(corners, dtype=np.float32)
    base_score = score_quad(corners, image_area)
    
    # Method bonus
    method_bonus = {
        "lsd": 0.1,        # LSD is very reliable
        "contour": 0.05,   # Contour is good
        "hough": 0.03,     # Hough is decent
        "fallback": -0.3   # Fallback means detection failed
    }
    
    bonus = method_bonus.get(method, 0)
    final = min(0.99, max(0.0, base_score + bonus))
    
    return round(final, 3)

