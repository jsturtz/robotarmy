from PyQt5.QtCore import QRect, QSize, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

class ClickQLabel(QLabel):

    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        QLabel.mousePressEvent(self, event)
