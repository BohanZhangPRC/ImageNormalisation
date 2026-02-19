# windows.py
from processing import apply_perspective_transform # Import your logic

class ImageNormalizer(QMainWindow):
    # ... (existing setup_side and import_image) ...

    def crop_image(self, side):
        if side == "A": return # Template is locked
        
        view = self.data[side]["view"]
        pil_img = self.data[side]["pil"]
        
        if not view.rubber_band.isVisible() or not pil_img:
            return

        # 1. Get the 4 corners of the ROI box
        rect = view.rubber_band.geometry()
        scene_rect = view.mapToScene(rect).boundingRect()
        
        # We need the 4 corners of the selection box for the perspective transform
        # For a standard rectangle selection, these are:
        quad_points = [
            [scene_rect.left(), scene_rect.top()],
            [scene_rect.right(), scene_rect.top()],
            [scene_rect.right(), scene_rect.bottom()],
            [scene_rect.left(), scene_rect.bottom()]
        ]

        # 2. Save history
        self.data[side]["history"].append(pil_img.copy())

        # 3. Apply the Perspective Transformation logic from processing.py
        try:
            transformed_pil = apply_perspective_transform(pil_img, quad_points)
            self.data[side]["pil"] = transformed_pil
            self.update_display(side)
            view.rubber_band.hide()
            self.status_bar.showMessage("Perspective Transformation Applied Successfully.")
        except Exception as e:
            self.status_bar.showMessage(f"Transformation Error: {str(e)}")