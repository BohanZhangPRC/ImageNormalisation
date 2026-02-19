from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QFileDialog, QGraphicsScene, 
                             QGraphicsPixmapItem, QFrame, QStatusBar, QSlider, QLabel)
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from PySide6.QtCore import Qt
from PIL import Image
from PIL.ImageQt import ImageQt
from widgets import EnhancedGraphicsView


class TransformationWindow(QWidget):
    def __init__(self, pil_a, pil_b):
        super().__init__()
        self.setWindowTitle("Superimposition")
        layout = QVBoxLayout(self)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        layout.addWidget(QLabel("Image B Opacity"))
        layout.addWidget(self.slider)
        self.scene = QGraphicsScene()
        self.view = EnhancedGraphicsView(self.scene)
        layout.addWidget(self.view)
        self.item_a = QGraphicsPixmapItem(QPixmap.fromImage(ImageQt(pil_a.convert("RGB"))))
        self.item_b = QGraphicsPixmapItem(QPixmap.fromImage(ImageQt(pil_b.convert("RGB"))))
        self.item_b.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.item_b.setOpacity(0.5)
        self.scene.addItem(self.item_a)
        self.scene.addItem(self.item_b)
        self.slider.valueChanged.connect(lambda v: self.item_b.setOpacity(v/100))

class ImageNormalizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dual-Channel Image Normalizer")
        self.resize(1400, 850)
        
        # 1. Setup Status Bar ONCE
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # Combined message so it shows everything at once
        self.status_bar.showMessage("Ready. [Left Click] Drag | [Right Click] ROI | [Wheel] Zoom | [Ctrl+Z] Undo")
        
        # 2. Data Storage
        self.data = {
            "A": {"pil": None, "history": [], "scene": QGraphicsScene(), "view": None},
            "B": {"pil": None, "history": [], "scene": QGraphicsScene(), "view": None}
        }

        # 3. Setup Layout
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

        # 4. Proceed Button
        self.btn_proceed = QPushButton("PROCEED TO TRANSFORMATION")
        self.btn_proceed.setFixedHeight(50)
        self.btn_proceed.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_proceed.clicked.connect(self.open_transformation)
        self.main_layout.addWidget(self.btn_proceed)

        # 5. Shortcuts
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(lambda: self.undo_action("A"))
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(lambda: self.undo_action("B"))
        self.trans_win = None

        def resizeEvent(self, event):
            """Ensure the template image refits whenever the window is resized."""
            super().resizeEvent(event)
            if self.data["A"]["pil"] and self.data["A"]["scene"].items():
                template_item = self.data["A"]["scene"].items()[0]
                self.data["A"]["view"].fitInView(template_item, Qt.KeepAspectRatio)

    def setup_side(self, side):
        container = QVBoxLayout()
        ctrl_layout = QHBoxLayout()
    
        # Check if this is the template side to change the button name
        if side == "A":
            btn_name = "Import Template"
            container.addWidget(QLabel("<b>TEMPLATE (Side A)</b>"))
        else:
            btn_name = "Import Target Image"

        btn_load = QPushButton(btn_name)
        btn_load.clicked.connect(lambda: self.import_image(side))
        ctrl_layout.addWidget(btn_load)

        # Only add the Crop button if it's NOT the template side
        if side != "A":
            btn_crop = QPushButton(f"Crop ROI")
            btn_crop.setStyleSheet("font-weight: bold; background-color: #2c3e50; color: white;")
            btn_crop.clicked.connect(lambda: self.crop_image(side))
            ctrl_layout.addWidget(btn_crop)
    
        container.addLayout(ctrl_layout)
    
        view = EnhancedGraphicsView(self.data[side]["scene"])
        self.data[side]["view"] = view
        container.addWidget(view)
        self.viewer_container.addLayout(container)

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
            
            if side == "A":
                # Ensure the Template is NOT movable
                item.setFlag(QGraphicsPixmapItem.ItemIsMovable, False)
                scene.addItem(item)
                
                # Fit the image to the window view
                # AspectRatioMode.KeepAspectRatio ensures the image isn't stretched/distorted
                view = self.data[side]["view"]
                view.fitInView(item, Qt.KeepAspectRatio)
            else:
                # Side B remains movable for alignment/cropping
                item.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
                scene.addItem(item)

    def crop_image(self, side):
        view = self.data[side]["view"]
        pil_img = self.data[side]["pil"]
        if not view.rubber_band.isVisible() or not pil_img: return
        
        self.data[side]["history"].append(pil_img.copy())
        items = self.data[side]["scene"].items()
        if not items: return
        image_item = items[0]
        
        rect = view.rubber_band.geometry()
        scene_rect = view.mapToScene(rect).boundingRect()
        local_rect = image_item.mapFromScene(scene_rect).boundingRect()
        
        left, top = int(local_rect.x()), int(local_rect.y())
        right, bottom = int(left + local_rect.width()), int(top + local_rect.height())
        
        if right > left and bottom > top:
            self.data[side]["pil"] = pil_img.crop((left, top, right, bottom))
            self.update_display(side)
            view.rubber_band.hide()

    def undo_action(self, side):
        if self.data[side]["history"]:
            self.data[side]["pil"] = self.data[side]["history"].pop()
            self.update_display(side)

    def open_transformation(self):
        if self.data["A"]["pil"] and self.data["B"]["pil"]:
            self.trans_win = TransformationWindow(self.data["A"]["pil"], self.data["B"]["pil"])
            self.trans_win.show()
        else:
            self.status_bar.showMessage("Error: Please load and crop both images first!")