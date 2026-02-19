import cv2
import numpy as np
from PIL import Image

def order_points(pts):
    """Orders coordinates: top-left, top-right, bottom-right, bottom-left."""
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    tl = pts[np.argmin(s)] #
    br = pts[np.argmax(s)] #
    tr = pts[np.argmin(diff)] #
    bl = pts[np.argmax(diff)] #
    return np.array([tl, tr, br, bl], dtype=np.float32)

def run_homography(pil_image, src_quad):
    """
    Applies homography to a PIL image using 4 source points.
    Returns a warped PIL image.
    """
    # Convert PIL Image to OpenCV BGR format
    img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # Define Target Dimensions (Template Size)
    W, H = 400, 300 #
    dst_pts = np.array([[0, 0], [W, 0], [W, H], [0, H]], dtype=np.float32) #
    
    # Order points and compute Homography Matrix
    ordered_src = order_points(np.array(src_quad, dtype=np.float32)) #
    H_matrix = cv2.getPerspectiveTransform(ordered_src, dst_pts) #
    
    # Compute full transformed bounds (No Cropping logic)
    h_img, w_img = img_cv.shape[:2]
    img_corners = np.array([[0, 0], [w_img, 0], [w_img, h_img], [0, h_img]], dtype=np.float32) #
    
    # Perspective projection calculation
    corners_h = np.hstack([img_corners, np.ones((4,1))])
    transformed = (H_matrix @ corners_h.T).T
    transformed = transformed[:, :2] / transformed[:, 2:3] #

    min_x, min_y = np.floor(transformed.min(axis=0)).astype(int) #
    max_x, max_y = np.ceil(transformed.max(axis=0)).astype(int) #

    # Translation to keep all coordinates positive
    T = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]], dtype=np.float32) #
    H_full = T @ H_matrix #

    # Warp the full image
    warped_cv = cv2.warpPerspective(
        img_cv, H_full, (max_x - min_x, max_y - min_y), borderValue=(255, 255, 255)
    )

    # Convert back to PIL Image
    return Image.fromarray(cv2.cvtColor(warped_cv, cv2.COLOR_BGR2RGB))