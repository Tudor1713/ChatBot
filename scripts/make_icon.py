from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPainter
from PySide6.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parents[1]
image=QImage(256,256,QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)
renderer=QSvgRenderer(str(root/'ui/mark.svg'))
assert renderer.isValid()
painter=QPainter(image);renderer.render(painter);painter.end()
assert image.save(str(root/'ui/icon.png'))
with Image.open(root/'ui/icon.png') as icon:
    icon.save(root/'ui/icon.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
