"""
Field Items Module for Field Layout & Robot Simulator GUI.
Defines all draggable graphics items (Home Box, Stand Cube, Wall, Cabinet, Line, and Robot).
"""

import math
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsPolygonItem,
    QGraphicsItemGroup, QGraphicsTextItem, QGraphicsEllipseItem
)


class ItemSignals(QObject):
    itemMoved = pyqtSignal(object)
    itemSelected = pyqtSignal(object)
    itemChanged = pyqtSignal(object)


class BaseFieldItem(QGraphicsItem):
    """
    Base class for interactive field items on the canvas.
    Handles position conversion between pixels and real-world centimeters/mm.
    """
    def __init__(self, item_type: str, name: str, x_cm: float, y_cm: float,
                 width_cm: float, height_cm: float, px_per_cm: float = 2.5,
                 color: str = "#3498db"):
        super().__init__()
        self.item_type = item_type
        self.name = name
        self._x_cm = x_cm
        self._y_cm = y_cm
        self.width_cm = width_cm
        self.height_cm = height_cm
        self.px_per_cm = px_per_cm
        self.rotation_deg = 0.0
        self.item_color = QColor(color)
        
        self.signals = ItemSignals()

        # Flags for interaction
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        # Update initial pixel position
        self.update_pixel_transform()

    def update_pixel_transform(self):
        """Update item scale and position from cm coordinates."""
        px_x = self._x_cm * self.px_per_cm
        px_y = self._y_cm * self.px_per_cm
        self.setPos(px_x, px_y)
        self.setRotation(self.rotation_deg)
        self.update()

    def set_px_per_cm(self, scale: float):
        """Update scale factor (pixels per cm)."""
        self.px_per_cm = scale
        self.update_pixel_transform()

    def get_x_cm(self) -> float:
        return self.pos().x() / self.px_per_cm if self.px_per_cm > 0 else 0.0

    def get_y_cm(self) -> float:
        return self.pos().y() / self.px_per_cm if self.px_per_cm > 0 else 0.0

    def set_cm_pos(self, x_cm: float, y_cm: float):
        self._x_cm = x_cm
        self._y_cm = y_cm
        self.update_pixel_transform()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._x_cm = self.pos().x() / self.px_per_cm if self.px_per_cm > 0 else 0.0
            self._y_cm = self.pos().y() / self.px_per_cm if self.px_per_cm > 0 else 0.0
            self.signals.itemMoved.emit(self)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.signals.itemSelected.emit(self)
        return super().itemChange(change, value)

    def to_dict(self) -> dict:
        return {
            'type': self.item_type,
            'name': self.name,
            'x_cm': round(self.get_x_cm(), 2),
            'y_cm': round(self.get_y_cm(), 2),
            'width_cm': round(self.width_cm, 2),
            'height_cm': round(self.height_cm, 2),
            'rotation_deg': round(self.rotation(), 2)
        }


class RectFieldItem(BaseFieldItem):
    """General rectangular obstacle (Stand Cube, Wall, Cabinet, Home Box)."""
    def __init__(self, item_type: str, name: str, x_cm: float, y_cm: float,
                 width_cm: float, height_cm: float, px_per_cm: float = 2.5,
                 color: str = "#3498db", label: str = ""):
        self.label = label
        super().__init__(item_type, name, x_cm, y_cm, width_cm, height_cm, px_per_cm, color)

    def boundingRect(self) -> QRectF:
        w_px = self.width_cm * self.px_per_cm
        h_px = self.height_cm * self.px_per_cm
        margin = 4.0
        return QRectF(-margin, -margin, w_px + 2*margin, h_px + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        w_px = self.width_cm * self.px_per_cm
        h_px = self.height_cm * self.px_per_cm
        rect = QRectF(0, 0, w_px, h_px)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Body brush & pen
        if self.item_type == "home_box":
            fill_color = QColor("#ffffff")  # Pure White
            pen_color = QColor("#000000") if not self.isSelected() else QColor("#f1c40f")
            pen_width = 3.5 if not self.isSelected() else 4.0
        else:
            fill_color = QColor(self.item_color)
            fill_color.setAlpha(180)
            pen_color = QColor(self.item_color).lighter(130) if not self.isSelected() else QColor("#f1c40f")
            pen_width = 2.0 if not self.isSelected() else 3.5

        pen = QPen(pen_color, pen_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill_color))

        if self.item_type in ("wall", "line"):
            painter.drawRect(rect)  # Sharp-cornered rectangle for wall and line
        else:
            painter.drawRoundedRect(rect, 3.0, 3.0)

        # Internal hatch or accents depending on item type
        if self.item_type == "home_box":
            # Inner border line accent
            painter.setPen(QPen(QColor(0, 0, 0, 80), 1.0, Qt.PenStyle.DashLine))
            inner_rect = rect.adjusted(4, 4, -4, -4)
            painter.drawRect(inner_rect)

        # Draw resize/selection handles if selected
        if self.isSelected():
            handle_size = 6
            painter.setBrush(QBrush(QColor("#f1c40f")))
            painter.setPen(QPen(QColor("#000000"), 1))
            handles = [
                QPointF(0, 0), QPointF(w_px, 0),
                QPointF(0, h_px), QPointF(w_px, h_px)
            ]
            for h in handles:
                painter.drawRect(QRectF(h.x() - handle_size/2, h.y() - handle_size/2, handle_size, handle_size))


class HomeBoxItem(RectFieldItem):
    """50x50 cm Home Box zone item."""
    def __init__(self, name: str = "Home Area", x_cm: float = 25.0, y_cm: float = 25.0,
                 width_cm: float = 50.0, height_cm: float = 50.0, px_per_cm: float = 2.5, **kwargs):
        super().__init__(
            item_type="home_box",
            name=name,
            x_cm=x_cm,
            y_cm=y_cm,
            width_cm=width_cm if width_cm else 50.0,
            height_cm=height_cm if height_cm else 50.0,
            px_per_cm=px_per_cm,
            color="#ffffff",  # Pure White
            label=""
        )


class StandCubeItem(BaseFieldItem):
    """
    15x15 cm Stand cube obstacle item with 15x2 cm VERTICAL solatif line located in front of the cube.
    """
    def __init__(self, name: str = "Stand Cube", x_cm: float = 80.0, y_cm: float = 100.0,
                 width_cm: float = 15.0, height_cm: float = 15.0, px_per_cm: float = 2.5, **kwargs):
        super().__init__(
            item_type="stand_cube",
            name=name,
            x_cm=x_cm,
            y_cm=y_cm,
            width_cm=width_cm if width_cm else 15.0,
            height_cm=height_cm if height_cm else 15.0,
            px_per_cm=px_per_cm,
            color="#e67e22"
        )
        self.tape_length_cm = 15.0   # Panjang garis vertikal 15 cm
        self.tape_width_cm = 2.0     # Lebar/ketebalan garis 2 cm

    def boundingRect(self) -> QRectF:
        cube_w_px = self.width_cm * self.px_per_cm
        cube_h_px = self.height_cm * self.px_per_cm
        tape_h_px = self.tape_length_cm * self.px_per_cm
        
        margin = 4.0
        return QRectF(-margin, -margin, cube_w_px + 2*margin, (cube_h_px + tape_h_px) + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cube_w_px = self.width_cm * self.px_per_cm
        cube_h_px = self.height_cm * self.px_per_cm
        tape_w_px = self.tape_width_cm * self.px_per_cm     # Lebar 2 cm
        tape_h_px = self.tape_length_cm * self.px_per_cm    # Panjang vertikal 15 cm
        tape_x_px = (cube_w_px - tape_w_px) / 2.0          # Berada tepat di tengah (center)

        # 1. Render 15x15 cm Stand Cube Block
        cube_rect = QRectF(0, 0, cube_w_px, cube_h_px)
        fill_color = QColor(self.item_color)
        fill_color.setAlpha(200)
        pen_color = QColor("#f1c40f") if self.isSelected() else QColor(self.item_color).lighter(130)
        pen_width = 3.5 if self.isSelected() else 2.0

        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(cube_rect, 3.0, 3.0)

        # 2. Render 15x2 cm Vertical Solatif Line extending forward/down from front of cube
        tape_rect = QRectF(tape_x_px, cube_h_px, tape_w_px, tape_h_px)
        painter.setPen(QPen(QColor("#000000"), 1.2))
        painter.setBrush(QBrush(QColor(30, 30, 30, 230)))  # Dark solatif line
        painter.drawRect(tape_rect)

        # Draw selection handles if selected
        if self.isSelected():
            handle_size = 6
            painter.setBrush(QBrush(QColor("#f1c40f")))
            painter.setPen(QPen(QColor("#000000"), 1))
            handles = [
                QPointF(0, 0), QPointF(cube_w_px, 0),
                QPointF(0, cube_h_px), QPointF(cube_w_px, cube_h_px),
                QPointF(tape_x_px + tape_w_px/2, cube_h_px + tape_h_px)
            ]
            for h in handles:
                painter.drawRect(QRectF(h.x() - handle_size/2, h.y() - handle_size/2, handle_size, handle_size))


class WallItem(RectFieldItem):
    """Wall obstacle item with 2cm thickness, adjustable length and arbitrary rotation angle."""
    def __init__(self, name: str = "Tembok", x_cm: float = 0.0, y_cm: float = 200.0,
                 width_cm: float = 100.0, height_cm: float = 2.0, px_per_cm: float = 2.5, **kwargs):
        super().__init__(
            item_type="wall",
            name=name,
            x_cm=x_cm,
            y_cm=y_cm,
            width_cm=width_cm,
            height_cm=height_cm if height_cm else 2.0,
            px_per_cm=px_per_cm,
            color="#34495e",  # Slate Dark Gray
            label=""
        )


class CabinetItem(BaseFieldItem):
    """
    15x45 cm Cabinet / Lemari obstacle item.
    Segment pattern: 5cm - 10cm - 5cm - 10cm - 5cm - 10cm (Total length 45 cm).
    Each 10cm segment has a 2x15cm reference solatif line at its midpoint extending forward.
    """
    def __init__(self, name: str = "Lemari", x_cm: float = 120.0, y_cm: float = 250.0,
                 width_cm: float = 15.0, height_cm: float = 45.0, px_per_cm: float = 2.5, **kwargs):
        super().__init__(
            item_type="cabinet",
            name=name,
            x_cm=x_cm,
            y_cm=y_cm,
            width_cm=width_cm if width_cm else 15.0,
            height_cm=height_cm if height_cm else 45.0,
            px_per_cm=px_per_cm,
            color="#8e44ad"
        )
        self.tape_length_cm = 15.0  # Panjang garis referensi 15 cm
        self.tape_width_cm = 2.0    # Lebar/ketebalan garis 2 cm

    def boundingRect(self) -> QRectF:
        cab_w_px = self.width_cm * self.px_per_cm
        cab_h_px = self.height_cm * self.px_per_cm
        tape_len_px = self.tape_length_cm * self.px_per_cm
        margin = 6.0
        return QRectF(-margin, -margin, cab_w_px + tape_len_px + 2*margin, cab_h_px + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cab_w_px = self.width_cm * self.px_per_cm
        cab_h_px = self.height_cm * self.px_per_cm
        tape_w_px = self.tape_width_cm * self.px_per_cm    # Lebar/tebal 2 cm
        tape_l_px = self.tape_length_cm * self.px_per_cm   # Panjang 15 cm

        # 1. Render 15x45 cm Cabinet Main Block
        cab_rect = QRectF(0, 0, cab_w_px, cab_h_px)
        fill_color = QColor(self.item_color)
        fill_color.setAlpha(200)
        pen_color = QColor("#f1c40f") if self.isSelected() else QColor(self.item_color).lighter(130)
        pen_width = 3.5 if self.isSelected() else 2.0

        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(cab_rect, 3.0, 3.0)

        # 2. Render 2x15 cm Solatif Reference Lines in front of 10cm segment midpoints (10cm, 25cm, 40cm)
        midpoints_cm = [10.0, 25.0, 40.0]
        painter.setPen(QPen(QColor("#000000"), 1.2))
        painter.setBrush(QBrush(QColor(30, 30, 30, 230)))  # Dark solatif line

        for mid_y_cm in midpoints_cm:
            mid_y_px = mid_y_cm * self.px_per_cm
            tape_rect = QRectF(cab_w_px, mid_y_px - tape_w_px / 2.0, tape_l_px, tape_w_px)
            painter.drawRect(tape_rect)

        # 4. Selection handles if selected
        if self.isSelected():
            handle_size = 6
            painter.setBrush(QBrush(QColor("#f1c40f")))
            painter.setPen(QPen(QColor("#000000"), 1))
            handles = [
                QPointF(0, 0), QPointF(cab_w_px, 0),
                QPointF(0, cab_h_px), QPointF(cab_w_px, cab_h_px)
            ]
            for mid_y_cm in midpoints_cm:
                mid_y_px = mid_y_cm * self.px_per_cm
                handles.append(QPointF(cab_w_px + tape_l_px, mid_y_px))

            for h in handles:
                painter.drawRect(QRectF(h.x() - handle_size/2, h.y() - handle_size/2, handle_size, handle_size))


class LineItem(RectFieldItem):
    """Field marker line item with 2cm thickness and adjustable length (matches Wall dimensions)."""
    def __init__(self, name: str = "Garis", x_cm: float = 20.0, y_cm: float = 150.0,
                 width_cm: float = 100.0, height_cm: float = 2.0, px_per_cm: float = 2.5, **kwargs):
        super().__init__(
            item_type="line",
            name=name,
            x_cm=x_cm,
            y_cm=y_cm,
            width_cm=width_cm if width_cm else 100.0,
            height_cm=height_cm if height_cm else 2.0,  # Lebar 2 cm (sama dengan tembok)
            px_per_cm=px_per_cm,
            color="#3498db",  # Bright Blue
            label=""
        )
        self.setZValue(2.0)


class RobotItem(BaseFieldItem):
    """
    Robot Item rendered as Oval / Ellipse shape.
    Moves interactively on field with heading direction indicator.
    Rendered on top of all field objects (ZValue = 100.0).
    """
    def __init__(self, x_cm: float = 100.0, y_cm: float = 50.0,
                 diameter_cm: float = 30.0, px_per_cm: float = 2.5,
                 color: str = "#e74c3c", **kwargs):
        self.diameter_cm = max(5.0, diameter_cm)
        super().__init__(
            item_type="robot",
            name="Robot",
            x_cm=x_cm,
            y_cm=y_cm,
            width_cm=self.diameter_cm,
            height_cm=self.diameter_cm,
            px_per_cm=px_per_cm,
            color=color
        )
        self.setZValue(100.0)  # Always stay on top of all other objects

    def set_shape_params(self, diameter_cm: float, color: str = None):
        self.diameter_cm = max(5.0, diameter_cm)
        self.width_cm = self.diameter_cm
        self.height_cm = self.diameter_cm
        if color:
            self.item_color = QColor(color)
        self.prepareGeometryChange()
        self.update_pixel_transform()

    def boundingRect(self) -> QRectF:
        r_px = (self.diameter_cm / 2.0) * self.px_per_cm
        margin = 10.0
        return QRectF(-r_px - margin, -r_px - margin, 2*r_px + 2*margin, 2*r_px + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        r_px = (self.diameter_cm / 2.0) * self.px_per_cm

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Render Default Oval / Ellipse Robot Body
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), r_px, r_px)

        # Body Brush & Pen
        fill_color = QColor(self.item_color)
        fill_color.setAlpha(220)

        pen_color = QColor("#f39c12") if self.isSelected() else QColor("#ffffff")
        pen_width = 3.0 if self.isSelected() else 2.0

        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(path)

        # Heading Direction Arrow (points forward towards 0 deg / top)
        arrow_len = r_px * 0.85
        arrow_pen = QPen(QColor("#f1c40f"), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arrow_pen)
        painter.drawLine(QPointF(0, 0), QPointF(0, -arrow_len))

        # Arrow head tip
        arrow_head = QPolygonF([
            QPointF(0, -r_px * 1.05),
            QPointF(-r_px * 0.2, -r_px * 0.75),
            QPointF(r_px * 0.2, -r_px * 0.75)
        ])
        painter.setBrush(QBrush(QColor("#f1c40f")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow_head)

        # Center dot
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QPointF(0, 0), 3.5, 3.5)

    def to_dict(self) -> dict:
        return {
            'type': self.item_type,
            'name': self.name,
            'x_cm': round(self.get_x_cm(), 2),
            'y_cm': round(self.get_y_cm(), 2),
            'diameter_cm': round(self.diameter_cm, 2),
            'rotation_deg': round(self.rotation(), 2)
        }
