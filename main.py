import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Now your existing import will work

from PySide6.QtWidgets import QApplication
from windows import ImageNormalizer  # Import the main window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageNormalizer()
    window.show()
    sys.exit(app.exec())