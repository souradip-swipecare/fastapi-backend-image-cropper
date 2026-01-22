import cv2
import os
import uuid
import numpy as np


import cv2
import numpy as np
import uuid
import os


def save_preview(image, corners, confidence):
   
    preview = image.copy()
    h, w = preview.shape[:2]
    
    # Handle no detection case
    if corners is None or len(corners) != 4:
        # Save original with "No detection" message
        cv2.putText(preview, "No document detected", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        output_dir = "uploads/previews"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, preview, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
        return output_path
    
    # Draw detection overlay
    overlay = preview.copy()
    pts = np.array(corners, dtype=np.int32)
    
    if confidence >= 0.7:
        color = (0, 255, 0)      # Green - high confidence
        border_color = (0, 200, 0)
    elif confidence >= 0.4:
        color = (0, 165, 255)    # Orange - moderate
        border_color = (0, 140, 255)
    else:
        color = (0, 0, 255)      # Red - low confidence
        border_color = (0, 0, 200)
    
    cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, 0.25, preview, 0.75, 0, preview)
    
    edge_colors = [
        (255, 0, 0),    # Blue - top
        (0, 255, 0),    # Green - right
        (0, 0, 255),    # Red - bottom
        (255, 0, 255)   # Magenta - left
    ]
    
    for i in range(4):
        pt1 = tuple(pts[i])
        pt2 = tuple(pts[(i + 1) % 4])
        cv2.line(preview, pt1, pt2, edge_colors[i], 3)
    
    # Draw corners
    labels = ['TL', 'TR', 'BR', 'BL']
    for i, (point, label) in enumerate(zip(corners, labels)):
        x, y = int(point[0]), int(point[1])
        
        # Outer circle
        cv2.circle(preview, (x, y), 15, (255, 255, 255), -1)
        cv2.circle(preview, (x, y), 15, border_color, 3)
        
        # Inner circle
        cv2.circle(preview, (x, y), 8, border_color, -1)
        
        # Label
        label_x = x + 20 if x < w - 50 else x - 40
        label_y = y - 10 if y > 30 else y + 30
        cv2.putText(preview, label, (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(preview, label, (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Confidence display
    conf_text = f"Confidence: {confidence:.1%}"
    
    # Background for text
    (text_w, text_h), _ = cv2.getTextSize(conf_text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
    cv2.rectangle(preview, (5, 5), (text_w + 15, text_h + 15), (0, 0, 0), -1)
    cv2.putText(preview, conf_text, (10, text_h + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    # Save
    output_dir = "uploads/previews"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{uuid.uuid4().hex}.jpg"
    output_path = os.path.join(output_dir, filename)
    
    cv2.imwrite(output_path, preview, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
    
    return output_path

def draw_detection_debug(image, corners, method=None):
    """
    Create a debug visualization showing detection details.
    """
    debug = image.copy()
    h, w = debug.shape[:2]
    
    corners = np.array(corners, dtype=np.int32)
    
    # Draw grid for reference
    for i in range(0, w, w // 10):
        cv2.line(debug, (i, 0), (i, h), (128, 128, 128), 1)
    for i in range(0, h, h // 10):
        cv2.line(debug, (0, i), (w, i), (128, 128, 128), 1)
    
    # Draw detected quad
    cv2.polylines(debug, [corners], True, (0, 255, 255), 3)
    
    # Draw corner coordinates
    for i, pt in enumerate(corners):
        cv2.circle(debug, tuple(pt), 8, (0, 0, 255), -1)
        coord_text = f"({pt[0]}, {pt[1]})"
        cv2.putText(debug, coord_text, (pt[0] + 10, pt[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Add method label
    if method:
        cv2.putText(debug, f"Method: {method}", (10, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return debug

