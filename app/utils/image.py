import cv2


def resize(image, height):
    h, w = image.shape[:2]
    ratio = height / float(h)
    return cv2.resize(image, (int(w * ratio), height))
