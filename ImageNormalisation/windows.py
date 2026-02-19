import cv2
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QFileDialog, QGraphicsScene, 
                             QGraphicsPixmapItem, QFrame, QStatusBar, QSlider, 
                             QLabel, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsRectItem)
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut, QPen, QFont, QColor
from PySide6.QtCore import Qt, QPointF, QLineF
import math
from PIL import Image
from PIL.ImageQt import ImageQt
from widgets import EnhancedGraphicsView

class RotationHandle(QGraphicsEllipseItem):
    """A larger, constant-size handle that rotates its parent item."""
    def __init__(self, parent, target_item):
        # Increased radius to 15 (30px diameter) for easier grabbing
        self.r = 15
        super().__init__(-self.r, -self.r, self.r * 2, self.r * 2, parent)
        
        self.setBrush(QColor("#3498db")) # Blue color for visibility
        self.setPen(QPen(Qt.white, 3))   # White border
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsScenePositionChanges)
        
        # KEY: Keep the handle the same size on screen regardless of zoom
        self.setFlag(QGraphicsEllipseItem.ItemIgnoresTransformations)
        
        self.target_item = target_item

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionChange and self.scene():
            # Calculate angle based on the handle's position relative to image center
            center = self.target_item.transformOriginPoint()
            # Map handle position to the item's coordinate space
            handle_pos = value
            
            line = QLineF(center, handle_pos)
            # -angle + 90 aligns the handle to the top of the image (0 degrees)
            angle = -line.angle() + 90 
            self.target_item.setRotation(angle)
        return super().itemChange(change, value)

class TransformationWindow(QWidget):
    def __init__(self, pil_a, pil_b):
        super().__init__()
        self.setWindowTitle("Superimposition - Alignment Mode")
        self.resize(1100, 850)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Top Controls: Opacity
        controls = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        
        label_info = QLabel("<b>Target Opacity:</b>")
        self.val_label = QLabel("50%")
        
        controls.addWidget(label_info)
        controls.addWidget(self.slider)
        controls.addWidget(self.val_label)
        layout.addLayout(controls)
        
        instruction = QLabel("<i>Drag image to move | Drag BLUE circle to rotate</i>")
        instruction.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction)

        # Scene and View
        self.scene = QGraphicsScene()
        self.view = EnhancedGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        # 1. Template Image (Side A) - Fixed in place
        qim_a = ImageQt(pil_a.convert("RGB"))
        self.item_a = QGraphicsPixmapItem(QPixmap.fromImage(qim_a))
        self.item_a.setZValue(0) # Bottom layer
        self.item_a.setFlag(QGraphicsPixmapItem.ItemIsMovable, False)
        self.scene.addItem(self.item_a)
        
        # 2. Target Image (Side B) - Movable and Rotatable
        qim_b = ImageQt(pil_b.convert("RGB"))
        self.item_b = QGraphicsPixmapItem(QPixmap.fromImage(qim_b))
        self.item_b.setZValue(1) # Top layer
        self.item_b.setOpacity(0.5)
        self.item_b.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        
        # Set rotation center to the middle of the image
        rect_b = self.item_b.boundingRect()
        center_b = rect_b.center()
        self.item_b.setTransformOriginPoint(center_b)
        self.scene.addItem(self.item_b)
        
        # 3. Add Rotation Handle
        # Positioned ~50 pixels above the top-center of the image
        self.handle = RotationHandle(self.item_b, self.item_b)
        self.handle.setPos(center_b.x(), rect_b.top() - 50)
        
        # Connect slider
        self.slider.valueChanged.connect(self.update_opacity)

    def update_opacity(self, value):
        self.item_b.setOpacity(value / 100)
        self.val_label.setText(f"{value}%")

class ImageNormalizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dual-Channel Image Normalizer")
        self.resize(1400, 900)
        
        # 1. Point Configuration
        self.points = {"A": [None]*4, "B": [None]*4}
        self.point_config = {
        "A": {"color": QColor("red"), "label": "A"},
        "B": {"color": QColor("green"), "label": "B"},
        "C": {"color": QColor("blue"), "label": "C"},
        "D": {"color": QColor("yellow"), "label": "D"}
        }

        # 2. Data Storage
        self.data = {
            "A": {"pil": None, "history": [], "scene": QGraphicsScene(), "view": None, "active_idx": 0},
            "B": {"pil": None, "history": [], "scene": QGraphicsScene(), "view": None, "active_idx": 0}
        }

        # 3. UI Setup
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Select a point button (A-D) then click the image.")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.viewer_container = QHBoxLayout()
        self.setup_side("A")
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        self.viewer_container.addWidget(line)
        self.setup_side("B")
        self.main_layout.addLayout(self.viewer_container)

        self.btn_proceed = QPushButton("PROCEED TO TRANSFORMATION")
        self.btn_proceed.setFixedHeight(50)
        self.btn_proceed.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 14px;")
        self.btn_proceed.clicked.connect(self.run_manual_transformation)
        self.main_layout.addWidget(self.btn_proceed)

        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(lambda: self.undo_action("A"))
        self.trans_win = None

    def setup_side(self, side):
        container = QVBoxLayout()
        
        # Title
        title = "TEMPLATE (Side A)" if side == "A" else "TARGET (Side B)"
        container.addWidget(QLabel(f"<b>{title}</b>"))

        # Row 1: File Controls
        file_layout = QHBoxLayout()
        btn_load = QPushButton(f"Import Image {side}")
        btn_load.clicked.connect(lambda _, s=side: self.import_image(s))
        file_layout.addWidget(btn_load)
        
        btn_reset_zoom = QPushButton("Reset Zoom")
        btn_reset_zoom.clicked.connect(lambda _, s=side: self.data[s]["view"].reset_view())
        file_layout.addWidget(btn_reset_zoom)
        
        if side == "B":
            btn_crop = QPushButton("Crop ROI")
            btn_crop.setStyleSheet("background-color: #2c3e50; color: white;")
            btn_crop.clicked.connect(lambda: self.crop_image(side))
            file_layout.addWidget(btn_crop)
        
        container.addLayout(file_layout)

        # Row 2: Point Controls
        point_layout = QHBoxLayout()
        labels = ["A", "B", "C", "D"]
        for i, label in enumerate(labels):
            btn = QPushButton(label)
            btn.setFixedWidth(40)
    
            # This will now work because self.point_config[label]["color"] is a QColor
            color_hex = self.point_config[label]["color"].name() 
    
            btn.setStyleSheet(f"background-color: {color_hex}; color: black; font-weight: bold;")
            btn.clicked.connect(lambda checked, s=side, idx=i: self.set_active_point(s, idx))
            point_layout.addWidget(btn)
            
        btn_clear = QPushButton("Clear Points")
        btn_clear.clicked.connect(lambda _, s=side: self.clear_points(s))
        point_layout.addWidget(btn_clear)
        container.addLayout(point_layout)
    
        # Graphics View
        view = EnhancedGraphicsView(self.data[side]["scene"])
        view.pointClicked.connect(lambda pos: self.handle_point_click(side, pos))
        self.data[side]["view"] = view
        container.addWidget(view)
        
        self.viewer_container.addLayout(container)

    def set_active_point(self, side, idx):
        self.data[side]["active_idx"] = idx
        labels = ["A", "B", "C", "D"]
        self.status_bar.showMessage(f"Side {side}: Ready to place Point {labels[idx]}")

    def clear_points(self, side):
        """Resets points for one side and clears graphics."""
        # Reset the list to four None values
        self.points[side] = [None] * 4 
        # Update the UI to remove the circles/labels
        self.refresh_point_visuals(side) 
        self.status_bar.showMessage(f"Side {side}: Points cleared.")

    def handle_point_click(self, side, pos):
        idx = self.data[side]["active_idx"]
        self.points[side][idx] = [pos.x(), pos.y()]
        
        # Auto-advance to next point for convenience
        if idx < 3:
            self.data[side]["active_idx"] += 1
            
        self.refresh_point_visuals(side)
        labels = ["A", "B", "C", "D"]
        self.status_bar.showMessage(f"Side {side}: Set Point {labels[idx]}. Next: {labels[self.data[side]['active_idx']]}")

    def refresh_point_visuals(self, side):
        scene = self.data[side]["scene"]
        for item in scene.items():
            if isinstance(item, (QGraphicsEllipseItem, QGraphicsTextItem)):
                scene.removeItem(item)

        labels = ["A", "B", "C", "D"]
        for i, pt in enumerate(self.points[side]):
            if pt is not None:
                label_char = labels[i]
                color = self.point_config[label_char]["color"]
            
                # 1. Create Marker centered at (0,0) then move it to pt
                r = 10
                # Define ellipse around (0,0) so the center is the anchor
                ellipse = QGraphicsEllipseItem(-r, -r, r*2, r*2)
                ellipse.setPen(QPen(Qt.black, 2))
                ellipse.setBrush(color)
                ellipse.setPos(pt[0], pt[1]) # Set actual position in scene
            
                # 2. Fix Scaling and Shifting
                ellipse.setFlag(QGraphicsEllipseItem.ItemIgnoresTransformations)
                scene.addItem(ellipse)
            
                # 3. Create the Text Label
                text = QGraphicsTextItem(label_char)
                text.setFont(QFont("Arial", 12, QFont.Bold))
                text.setDefaultTextColor(color)
            
                # Anchor text to the same point
                text.setFlag(QGraphicsTextItem.ItemIgnoresTransformations)
                text.setPos(pt[0] + r, pt[1] - r)
                scene.addItem(text)
    def import_image(self, side):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open Image {side}")
        if file_path:
            self.data[side]["history"] = []
            self.data[side]["pil"] = Image.open(file_path)
            self.update_display(side)

    def update_display(self, side):
        pil_img = self.data[side]["pil"]
        if pil_img:
            qim = ImageQt(pil_img.convert("RGB"))
            scene = self.data[side]["scene"]
            scene.clear()
            
            item = QGraphicsPixmapItem(QPixmap.fromImage(qim))
            item.setFlag(QGraphicsPixmapItem.ItemIsMovable, side != "A")
            scene.addItem(item)
            self.data[side]["view"].rubber_band.hide()
            # Restore points if they existed
            self.refresh_point_visuals(side)

    def crop_image(self, side):
        view = self.data[side]["view"]
        pil_img = self.data[side]["pil"]
        if not view.rubber_band.isVisible() or not pil_img: return
        
        self.data[side]["history"].append(pil_img.copy())
        rect = view.rubber_band.geometry()
        scene_rect = view.mapToScene(rect).boundingRect()
        
        left, top = int(scene_rect.left()), int(scene_rect.top())
        right, bottom = int(scene_rect.right()), int(scene_rect.bottom())
        
        if right > left and bottom > top:
            self.data[side]["pil"] = pil_img.crop((left, top, right, bottom))
            self.update_display(side)
            view.rubber_band.hide()

    def undo_action(self, side):
        if self.data[side]["history"]:
            self.data[side]["pil"] = self.data[side]["history"].pop()
            self.update_display(side)

    def run_manual_transformation(self):
        # Check if all 4 points are set for both sides
        if any(p is None for p in self.points["A"]) or any(p is None for p in self.points["B"]):
            self.status_bar.showMessage("Error: Please set all 4 points (A, B, C, D) on BOTH images.")
            return

        img_a = np.array(self.data["A"]["pil"])
        img_b = cv2.cvtColor(np.array(self.data["B"]["pil"]), cv2.COLOR_RGB2BGR)
        
        src_pts = np.array(self.points["B"], dtype=np.float32)
        dst_pts = np.array(self.points["A"], dtype=np.float32)
        
        # Calculate Homography and Warp
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        h, w = img_a.shape[:2]
        warped_cv = cv2.warpPerspective(img_b, M, (w, h))
        
        warped_pil = Image.fromarray(cv2.cvtColor(warped_cv, cv2.COLOR_BGR2RGB))
        self.trans_win = TransformationWindow(self.data["A"]["pil"], warped_pil)
        self.trans_win.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)