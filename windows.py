from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QFileDialog, QGraphicsScene, 
                             QGraphicsPixmapItem, QFrame, QStatusBar, QSlider, QLabel)
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from PySide6.QtCore import Qt
from PIL import Image
from PIL.ImageQt import ImageQt
from widgets import EnhancedGraphicsView  # Import from your other file

class TransformationWindow(QWidget):
    def __init__(self, pil_a, pil_b):
        super().__init__()
        self.setWindowTitle("Superimposition")
        layout = QVBoxLayout(self)
        
        # Opacity slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        layout.addWidget(QLabel("Image B Opacity"))
        layout.addWidget(self.slider)

        self.scene = QGraphicsScene()
        self.view = EnhancedGraphicsView(self.scene)
        layout.addWidget(self.view)

        # Layers
        self.item_a = QGraphicsPixmapItem(QPixmap.fromImage(ImageQt(pil_a.convert("RGB"))))
        self.item_b = QGraphicsPixmapItem(QPixmap.fromImage(ImageQt(pil_b.convert("RGB"))))
        self.item_b.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.item_b.setOpacity(0.5)
        
        self.scene.addItem(self.item_a)
        self.scene.addItem(self.item_b)
        self.slider.valueChanged.connect(lambda v: self.item_b.setOpacity(v/100))

class ImageNormalizer(QMainWindow):
    # ... (The rest of the ImageNormalizer logic from before goes here)
    # Ensure you use 'from widgets import EnhancedGraphicsView' at the top
    pass