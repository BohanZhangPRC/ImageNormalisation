from PySide6.QtWidgets import QGraphicsView, QRubberBand
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtCore import Signal, QPointF

class EnhancedGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

    # Create a custom signal to send coordinates when clicked
    pointClicked = Signal(QPointF)

    def reset_view(self):
        """Resets zoom and centers the image."""
        self.resetTransform()
        if self.scene():
            self.setSceneRect(self.scene().itemsBoundingRect())
            self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 1. Hide the ROI drag window if it's currently visible
            if self.rubber_band.isVisible():
                self.rubber_band.hide()
            
            # 2. Emit signal for point marking
            scene_pos = self.mapToScene(event.pos())
            self.pointClicked.emit(scene_pos)
        
            # 3. Standard processing (allows for item selection/dragging)
            super().mousePressEvent(event) 

        elif event.button() == Qt.RightButton:
            # Handle ROI Selection (Right-Click)
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
        else:
            super().mousePressEvent(event)

    def wheelEvent(self, event):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)

    def mouseMoveEvent(self, event):
        if self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)