"""
Document Scanner - Simple and robust detection.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DocScanner:
    """Simple document scanner."""
    
    def detect(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], float, str]:
        """
        Detect document in image.
        Returns (corners, confidence, method).
        """
        if image is None or image.size == 0:
            return None, 0.0, "none"
        
        h, w = image.shape[:2]
        
        # Check if this is a white background document (scanned/screenshot)
        if self._is_white_background(image):
            # For white background, return full image with small margin
            margin = 5
            corners = np.array([
                [margin, margin],
                [w - margin, margin],
                [w - margin, h - margin],
                [margin, h - margin]
            ], dtype=np.float32)
            return corners, 0.95, "fullpage"
        
        best_quad = None
        best_score = 0.0
        best_method = "none"
        
        # Method 1: Edge detection
        quads = self._find_by_edges(image)
        for quad in quads:
            score = self._score_quad(quad, image)
            if score > best_score:
                best_quad = quad
                best_score = score
                best_method = "edge"
        
        # Method 2: Contour detection
        if best_score < 0.8:
            quads = self._find_by_contours(image)
            for quad in quads:
                score = self._score_quad(quad, image)
                if score > best_score:
                    best_quad = quad
                    best_score = score
                    best_method = "contour"
        
        # Method 3: Threshold detection
        if best_score < 0.8:
            quads = self._find_by_threshold(image)
            for quad in quads:
                score = self._score_quad(quad, image)
                if score > best_score:
                    best_quad = quad
                    best_score = score
                    best_method = "threshold"
        
        if best_quad is not None:
            best_quad = self._order_points(best_quad)
            return best_quad, best_score, best_method
        
        return None, 0.0, "none"
    
    def _is_white_background(self, image: np.ndarray) -> bool:
        """Check if image has white/uniform background (scanned doc or screenshot)."""
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Check corners - if all corners are very bright, likely white background
        margin = 30
        corners = [
            gray[0:margin, 0:margin].mean(),           # TL
            gray[0:margin, w-margin:w].mean(),         # TR
            gray[h-margin:h, 0:margin].mean(),         # BL
            gray[h-margin:h, w-margin:w].mean()        # BR
        ]
        
        # All corners should be very bright (>240)
        if all(c > 240 for c in corners):
            # Also check overall brightness
            mean_brightness = gray.mean()
            if mean_brightness > 220:
                return True
        
        return False
    
    def _find_by_edges(self, image: np.ndarray) -> List[np.ndarray]:
        """Find document using Canny edges."""
        results = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        for thresh1, thresh2 in [(50, 150), (30, 100), (75, 200)]:
            edges = cv2.Canny(gray, thresh1, thresh2)
            edges = cv2.dilate(edges, None, iterations=2)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
            
            for cnt in contours:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    results.append(approx.reshape(4, 2).astype(np.float32))
        
        return results
    
    def _find_by_contours(self, image: np.ndarray) -> List[np.ndarray]:
        """Find document using morphological operations."""
        results = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Morphological gradient
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
        
        _, thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            
            if len(approx) == 4 and cv2.isContourConvex(approx):
                results.append(approx.reshape(4, 2).astype(np.float32))
            elif len(approx) > 4:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                results.append(box.astype(np.float32))
        
        return results
    
    def _find_by_threshold(self, image: np.ndarray) -> List[np.ndarray]:
        """Find document using adaptive threshold."""
        results = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        for block in [11, 21, 31]:
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, block, 2
            )
            
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            
            for cnt in contours:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    results.append(approx.reshape(4, 2).astype(np.float32))
        
        return results
    
    def _score_quad(self, quad: np.ndarray, image: np.ndarray) -> float:
        """Score a quad - higher is better."""
        if quad is None or len(quad) != 4:
            return 0.0
        
        h, w = image.shape[:2]
        img_area = h * w
        
        # Area ratio
        area = cv2.contourArea(quad)
        area_ratio = area / img_area
        
        # Skip if too small or too large
        if area_ratio < 0.05 or area_ratio > 0.95:
            return 0.0
        
        # Skip if it covers almost the entire image
        margin = 10
        corners_on_edge = 0
        for pt in quad:
            x, y = pt
            if x < margin or x > w - margin or y < margin or y > h - margin:
                corners_on_edge += 1
        
        if corners_on_edge == 4 and area_ratio > 0.9:
            return 0.0
        
        # Area score - prefer medium sized documents (20-70%)
        if 0.2 <= area_ratio <= 0.7:
            area_score = 1.0
        elif area_ratio < 0.2:
            area_score = area_ratio / 0.2
        else:
            area_score = max(0.5, 1.0 - (area_ratio - 0.7) / 0.25)
        
        # Rectangularity - check angles
        angles = []
        for i in range(4):
            p1 = quad[(i - 1) % 4]
            p2 = quad[i]
            p3 = quad[(i + 1) % 4]
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
            angles.append(angle)
        
        # All angles should be close to 90 degrees
        angle_devs = [abs(a - 90) for a in angles]
        avg_dev = sum(angle_devs) / 4
        
        if avg_dev > 40:  # Too skewed
            return 0.0
        
        rect_score = max(0, 1.0 - avg_dev / 30)
        
        # Combined score
        score = 0.5 * area_score + 0.5 * rect_score
        
        return score
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points: TL, TR, BR, BL."""
        pts = pts.astype(np.float32)
        rect = np.zeros((4, 2), dtype=np.float32)
        
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # Top-left
        rect[2] = pts[np.argmax(s)]  # Bottom-right
        
        d = np.diff(pts, axis=1).flatten()
        rect[1] = pts[np.argmin(d)]  # Top-right
        rect[3] = pts[np.argmax(d)]  # Bottom-left
        
        return rect


def scan_document(image: np.ndarray) -> Tuple[Optional[np.ndarray], float, str]:
    """Legacy function."""
    scanner = DocScanner()
    return scanner.detect(image)
