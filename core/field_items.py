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
    Stand cube obstacle item with customizable width, height, and front vertical solatif line length.
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
        self.tape_length_cm = max(1.0, float(kwargs.get('tape_length_cm', 15.0)))
        self.tape_width_cm = 2.0  # Lebar/ketebalan garis 2 cm

    def set_tape_length(self, tape_len_cm: float):
        self.tape_length_cm = max(1.0, tape_len_cm)
        self.prepareGeometryChange()
        self.update()

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
        tape_w_px = self.tape_width_cm * self.px_per_cm
        tape_h_px = self.tape_length_cm * self.px_per_cm
        tape_x_px = (cube_w_px - tape_w_px) / 2.0

        # 1. Render Stand Cube Block
        cube_rect = QRectF(0, 0, cube_w_px, cube_h_px)
        fill_color = QColor(self.item_color)
        fill_color.setAlpha(200)
        pen_color = QColor("#f1c40f") if self.isSelected() else QColor(self.item_color).lighter(130)
        pen_width = 3.5 if self.isSelected() else 2.0

        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(cube_rect, 3.0, 3.0)

        # 2. Render Vertical Solatif Line extending forward/down from front of cube
        tape_rect = QRectF(tape_x_px, cube_h_px, tape_w_px, tape_h_px)
        painter.setPen(QPen(QColor("#000000"), 1.2))
        painter.setBrush(QBrush(QColor(30, 30, 30, 230)))
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

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['tape_length_cm'] = round(self.tape_length_cm, 2)
        return d


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
    Cabinet / Lemari obstacle item with customizable dimensions, shelf tiers, and placed object layout.
    Supports object placement parameters along cabinet length:
    Pattern: [spacing_cm] [object_size_cm] [spacing_cm] [object_size_cm] [spacing_cm]...
    User can configure object count, object size, and spacing distance.
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
        self.tier_count = max(1, int(kwargs.get('tier_count', 3)))
        raw_heights = kwargs.get('tier_heights', [])
        if isinstance(raw_heights, list) and len(raw_heights) == self.tier_count:
            self.tier_heights = [max(1.0, float(h)) for h in raw_heights]
        else:
            eq_h = self.height_cm / float(self.tier_count)
            self.tier_heights = [round(eq_h, 1)] * self.tier_count

        # Object Placement Parameters along cabinet length
        self.object_count = max(0, int(kwargs.get('object_count', 2)))
        self.object_size_cm = max(1.0, float(kwargs.get('object_size_cm', 10.0)))
        self.spacing_cm = max(0.0, float(kwargs.get('spacing_cm', 5.0)))

    def get_calculated_length_cm(self) -> float:
        """Calculate required cabinet length (height_cm) for the current object count, size, and spacing."""
        if self.object_count <= 0:
            return self.height_cm
        return self.spacing_cm + self.object_count * (self.object_size_cm + self.spacing_cm)

    def set_object_params(self, count: int, size_cm: float, spacing_cm: float, auto_fit_length: bool = True):
        self.object_count = max(0, count)
        self.object_size_cm = max(1.0, size_cm)
        self.spacing_cm = max(0.0, spacing_cm)
        if auto_fit_length and self.object_count > 0:
            self.height_cm = self.get_calculated_length_cm()
        self.prepareGeometryChange()
        self.update()

    def get_total_height_cm(self) -> float:
        return sum(self.tier_heights) if self.tier_heights else 45.0

    def set_tiers(self, count: int, heights: list = None):
        self.tier_count = max(1, count)
        if heights and len(heights) == self.tier_count:
            self.tier_heights = [max(1.0, float(h)) for h in heights]
        else:
            self.tier_heights = [15.0] * self.tier_count
        self.prepareGeometryChange()
        self.update()

    def boundingRect(self) -> QRectF:
        cab_w_px = self.width_cm * self.px_per_cm
        cab_h_px = self.height_cm * self.px_per_cm
        margin = 4.0
        return QRectF(-margin, -margin, cab_w_px + 2*margin, cab_h_px + 2*margin)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cab_w_px = self.width_cm * self.px_per_cm
        cab_h_px = self.height_cm * self.px_per_cm

        # 1. Outer Cabinet Main Block (Top-Down Footprint)
        cab_rect = QRectF(0, 0, cab_w_px, cab_h_px)
        fill_color = QColor(self.item_color)
        fill_color.setAlpha(220)
        pen_color = QColor("#f1c40f") if self.isSelected() else QColor(self.item_color).lighter(130)
        pen_width = 3.5 if self.isSelected() else 2.0

        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(cab_rect, 4.0, 4.0)

        # 2. Inner Door / Top Rim Accent Detail
        inner_margin = 3.0
        if cab_w_px > 2 * inner_margin and cab_h_px > 2 * inner_margin:
            inner_rect = QRectF(inner_margin, inner_margin, cab_w_px - 2*inner_margin, cab_h_px - 2*inner_margin)
            painter.setPen(QPen(QColor("#ffffff"), 1.0, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(inner_rect, 2.0, 2.0)

        # 3. Render Top-Down Object Placement Boxes & Spacing along Cabinet Length
        if self.object_count > 0 and self.object_size_cm > 0:
            px_per_cm = self.px_per_cm
            obj_h_px = self.object_size_cm * px_per_cm
            obj_w_px = max(4.0, cab_w_px - 8.0)
            obj_x_px = (cab_w_px - obj_w_px) / 2.0

            for i in range(self.object_count):
                obj_y_cm = self.spacing_cm + i * (self.object_size_cm + self.spacing_cm)
                obj_y_px = obj_y_cm * px_per_cm
                if obj_y_px + obj_h_px <= cab_h_px + 2.0:
                    o_rect = QRectF(obj_x_px, obj_y_px, obj_w_px, obj_h_px)

                    # Object Box (Amber / Orange Accent)
                    painter.setPen(QPen(QColor("#ffffff"), 1.2))
                    painter.setBrush(QBrush(QColor(230, 126, 34, 210)))
                    painter.drawRoundedRect(o_rect, 2.0, 2.0)

                    # Object Label
                    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    painter.setPen(QPen(QColor("#ffffff")))
                    painter.drawText(o_rect, Qt.AlignmentFlag.AlignCenter, f"Obj {i+1}")

        # Selection handles if selected
        if self.isSelected():
            handle_size = 6
            painter.setBrush(QBrush(QColor("#f1c40f")))
            painter.setPen(QPen(QColor("#000000"), 1))
            handles = [
                QPointF(0, 0), QPointF(cab_w_px, 0),
                QPointF(0, cab_h_px), QPointF(cab_w_px, cab_h_px)
            ]
            for h in handles:
                painter.drawRect(QRectF(h.x() - handle_size/2, h.y() - handle_size/2, handle_size, handle_size))

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['tier_count'] = self.tier_count
        d['tier_heights'] = [round(h, 1) for h in self.tier_heights]
        d['object_count'] = self.object_count
        d['object_size_cm'] = round(self.object_size_cm, 1)
        d['spacing_cm'] = round(self.spacing_cm, 1)
        return d


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
    Robot Item rendered as Oval / Ellipse shape with 9 Sensor Mount Positions.
    Front 3 sensors (front_left, front_center, front_right) are aligned parallel in a straight line.
    Includes 2D Raycasting Distance Detection against field boundaries and internal obstacles.
    Rendered on top of all field objects (ZValue = 100.0).
    """

    SENSOR_CONFIGS = {
        # Front 3 Sensors (Parallel straight line facing 0° Forward)
        'front_left':   {'rel_x': -0.6, 'rel_y': -1.0, 'angle': 0.0},
        'front_center': {'rel_x':  0.0, 'rel_y': -1.0, 'angle': 0.0},
        'front_right':  {'rel_x':  0.6, 'rel_y': -1.0, 'angle': 0.0},

        # Right 2 Sensors (Parallel straight line facing +90° Right)
        'right_front':  {'rel_x':  1.0, 'rel_y': -0.5, 'angle': 90.0},
        'right_rear':   {'rel_x':  1.0, 'rel_y':  0.5, 'angle': 90.0},

        # Back 2 Sensors (Parallel straight line facing 180° Backward)
        'back_right':   {'rel_x':  0.5, 'rel_y':  1.0, 'angle': 180.0},
        'back_left':    {'rel_x': -0.5, 'rel_y':  1.0, 'angle': 180.0},

        # Left 2 Sensors (Parallel straight line facing -90° Left)
        'left_rear':    {'rel_x': -1.0, 'rel_y':  0.5, 'angle': -90.0},
        'left_front':   {'rel_x': -1.0, 'rel_y': -0.5, 'angle': -90.0}
    }

    # 2 Line Sensors: mounted side-by-side directly under the front center distance sensor (front_center)
    LINE_SENSOR_CONFIGS = {
        'line_left':  {'rel_x': -0.15, 'rel_y': -0.85},
        'line_right': {'rel_x':  0.15, 'rel_y': -0.85},
    }

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

        # 9 Sensor Mount Positions: 'none', 'ultrasonic', 'infrared'
        self.sensors = {
            'front_left': 'none',
            'front_center': 'none',
            'front_right': 'none',
            'right_front': 'none',
            'right_rear': 'none',
            'back_right': 'none',
            'back_left': 'none',
            'left_rear': 'none',
            'left_front': 'none'
        }
        if 'sensors' in kwargs and isinstance(kwargs['sensors'], dict):
            self.set_sensors(kwargs['sensors'])

        # 2 Line Sensors (downward-facing): True = installed, False = not installed
        self.line_sensors = {
            'line_left': False,
            'line_right': False
        }
        if 'line_sensors' in kwargs and isinstance(kwargs['line_sensors'], dict):
            for k in self.line_sensors:
                if k in kwargs['line_sensors']:
                    self.line_sensors[k] = bool(kwargs['line_sensors'][k])

        # Omni-wheel Configuration: count (3 or 4), diameter_mm (50 or 100)
        wheels_cfg = kwargs.get('wheels', {})
        if isinstance(wheels_cfg, dict):
            self.wheel_count = wheels_cfg.get('count', 4)
            self.wheel_diameter_mm = wheels_cfg.get('diameter_mm', 100)
        else:
            self.wheel_count = 4
            self.wheel_diameter_mm = 100

        # Safety Clearance Margin (cm) - Default 7.0 cm
        self.safety_margin_cm = max(0.0, float(kwargs.get('safety_margin_cm', 7.0)))

    def set_sensors(self, sensors_dict: dict):
        if sensors_dict:
            for k in self.sensors:
                if k in sensors_dict:
                    self.sensors[k] = sensors_dict[k]
        self.update()

    def set_wheel_config(self, count: int, diameter_mm: int):
        self.wheel_count = 4 if count == 4 else 3
        self.wheel_diameter_mm = 100 if diameter_mm == 100 else 50
        self.prepareGeometryChange()
        self.update()

    def set_line_sensors(self, config: dict):
        """Set line sensor installation state from dict."""
        if config:
            for k in self.line_sensors:
                if k in config:
                    self.line_sensors[k] = bool(config[k])
        self.prepareGeometryChange()
        self.update()

    def get_line_sensor_readouts(self) -> dict:
        """
        Check if each installed line sensor is currently over a floor line.
        Detects: StandCube solatif tape, Cabinet reference lines, LineItem.
        Returns {key: {'installed': bool, 'detecting': bool, 'target': str}}
        """
        readouts = {}
        scene = self.scene()

        for ls_key, cfg in self.LINE_SENSOR_CONFIGS.items():
            installed = self.line_sensors.get(ls_key, False)
            if not installed:
                readouts[ls_key] = {'installed': False, 'detecting': False, 'target': ''}
                continue

            if not scene:
                readouts[ls_key] = {'installed': True, 'detecting': False, 'target': ''}
                continue

            # Calculate world position of this sensor
            r_cm = self.diameter_cm / 2.0
            loc_x_cm = cfg['rel_x'] * r_cm
            loc_y_cm = cfg['rel_y'] * r_cm
            rot_rad = math.radians(self.rotation())
            wx = self.get_x_cm() + (loc_x_cm * math.cos(rot_rad) - loc_y_cm * math.sin(rot_rad))
            wy = self.get_y_cm() + (loc_x_cm * math.sin(rot_rad) + loc_y_cm * math.cos(rot_rad))

            px_per_cm = self.px_per_cm if self.px_per_cm > 0 else 2.5
            sensor_scene_pt = QPointF(wx * px_per_cm, wy * px_per_cm)

            detecting = False
            target_name = ''

            for item in scene.items():
                if item is self or not isinstance(item, BaseFieldItem):
                    continue
                itype = getattr(item, 'item_type', '')

                if itype == 'line':
                    # LineItem: full rectangle is a detectable line
                    w_px = item.width_cm * px_per_cm
                    h_px = item.height_cm * px_per_cm
                    local_pt = item.mapFromScene(sensor_scene_pt)
                    if 0 <= local_pt.x() <= w_px and 0 <= local_pt.y() <= h_px:
                        detecting = True
                        target_name = getattr(item, 'name', 'Garis')
                        break

                elif itype == 'stand_cube':
                    # StandCube solatif tape: 2cm wide x tape_length_cm tall, centered below cube body
                    tape_w = getattr(item, 'tape_width_cm', 2.0) * px_per_cm
                    tape_h = getattr(item, 'tape_length_cm', 15.0) * px_per_cm
                    cube_w_px = item.width_cm * px_per_cm
                    cube_h_px = item.height_cm * px_per_cm
                    tape_x = (cube_w_px - tape_w) / 2.0
                    tape_rect = QRectF(tape_x, cube_h_px, tape_w, tape_h)
                    local_pt = item.mapFromScene(sensor_scene_pt)
                    if tape_rect.contains(local_pt):
                        detecting = True
                        target_name = getattr(item, 'name', 'Stand Cube') + ' (Solatif)'
                        break

            readouts[ls_key] = {'installed': True, 'detecting': detecting, 'target': target_name}

        return readouts

    def set_safety_margin(self, margin_cm: float):
        self.safety_margin_cm = max(0.0, margin_cm)
        self.prepareGeometryChange()
        self.update()

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
        margin = 350.0
        return QRectF(-r_px - margin, -r_px - margin, 2*r_px + 2*margin, 2*r_px + 2*margin)

    def shape(self) -> QPainterPath:
        """
        Define exact mouse interaction / hit-testing boundary for the robot.
        Matches physical oval body (+ 4px edge) so clicking outside the robot
        never selects or drags it.
        """
        r_px = (self.diameter_cm / 2.0) * self.px_per_cm
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), r_px + 4.0, r_px + 4.0)
        return path

    def get_sensor_readouts(self) -> dict:
        """
        Calculate 2D Raycast distances for all active sensors on the robot against:
        1. Outer field boundary walls
        2. Field obstacles (StandCube, Wall, Cabinet, HomeBox, etc.)
        """
        readouts = {}
        scene = self.scene()
        if not scene:
            return readouts

        r_cm = self.diameter_cm / 2.0
        rob_rot = self.rotation()
        rob_x_cm = self.get_x_cm()
        rob_y_cm = self.get_y_cm()

        field_w_cm = getattr(scene, 'width_cm', 200.0)
        field_h_cm = getattr(scene, 'height_cm', 400.0)
        px_per_cm = self.px_per_cm if self.px_per_cm > 0 else 2.5

        # 1. Collect all obstacle line segments in scene cm
        segments = [
            ((0.0, 0.0), (field_w_cm, 0.0), "Batas Lapangan (Atas)"),
            ((field_w_cm, 0.0), (field_w_cm, field_h_cm), "Batas Lapangan (Kanan)"),
            ((field_w_cm, field_h_cm), (0.0, field_h_cm), "Batas Lapangan (Bawah)"),
            ((0.0, field_h_cm), (0.0, 0.0), "Batas Lapangan (Kiri)")
        ]

        for item in scene.items():
            if isinstance(item, BaseFieldItem) and item != self:
                item_type = getattr(item, 'item_type', '')

                # Skip non-detectable items: Home Area (home_box) and Manual Lines (line)
                if item_type in ('home_box', 'line'):
                    continue

                # For solid obstacles (StandCube, Cabinet, Wall), use main body rect (excluding floor tape lines)
                w_px = item.width_cm * px_per_cm
                h_px = item.height_cm * px_per_cm
                body_rect = QRectF(0, 0, w_px, h_px)

                c0 = item.mapToScene(body_rect.topLeft()) / px_per_cm
                c1 = item.mapToScene(body_rect.topRight()) / px_per_cm
                c2 = item.mapToScene(body_rect.bottomRight()) / px_per_cm
                c3 = item.mapToScene(body_rect.bottomLeft()) / px_per_cm

                p0 = (c0.x(), c0.y())
                p1 = (c1.x(), c1.y())
                p2 = (c2.x(), c2.y())
                p3 = (c3.x(), c3.y())

                name = getattr(item, 'name', 'Objek')
                segments.append((p0, p1, name))
                segments.append((p1, p2, name))
                segments.append((p2, p3, name))
                segments.append((p3, p0, name))

        # 2. Perform raycast for each active sensor
        for pos_key, cfg in self.SENSOR_CONFIGS.items():
            stype = self.sensors.get(pos_key, 'none')
            if stype == 'none':
                readouts[pos_key] = {'type': 'none'}
                continue

            max_range_cm = 400.0 if stype == 'ultrasonic' else 150.0

            loc_x_cm = cfg['rel_x'] * r_cm
            loc_y_cm = cfg['rel_y'] * r_cm
            sensor_angle = cfg['angle']

            rot_rad = math.radians(rob_rot)
            gx_cm = rob_x_cm + (loc_x_cm * math.cos(rot_rad) - loc_y_cm * math.sin(rot_rad))
            gy_cm = rob_y_cm + (loc_x_cm * math.sin(rot_rad) + loc_y_cm * math.cos(rot_rad))

            global_angle_deg = rob_rot + sensor_angle
            angle_rad = math.radians(global_angle_deg - 90.0)
            dx = math.cos(angle_rad)
            dy = math.sin(angle_rad)

            closest_dist = max_range_cm
            hit_target = "Di Luar Jangkauan"
            hit_px = gx_cm + dx * max_range_cm
            hit_py = gy_cm + dy * max_range_cm

            for (p1, p2, seg_name) in segments:
                x1, y1 = p1
                x2, y2 = p2

                det = dx * (y2 - y1) - dy * (x2 - x1)
                if abs(det) < 1e-6:
                    continue

                t = ((x1 - gx_cm) * (y2 - y1) - (y1 - gy_cm) * (x2 - x1)) / det
                u = ((x1 - gx_cm) * dy - (y1 - gy_cm) * dx) / det

                if t >= 0.05 and 0.0 <= u <= 1.0:
                    if t < closest_dist:
                        closest_dist = t
                        hit_target = seg_name
                        hit_px = gx_cm + dx * t
                        hit_py = gy_cm + dy * t

            readouts[pos_key] = {
                'type': stype,
                'distance_cm': round(closest_dist, 1),
                'target_name': hit_target,
                'start_cm': (gx_cm, gy_cm),
                'hit_cm': (hit_px, hit_py),
                'max_range_cm': max_range_cm
            }

        return readouts

    def check_safety_collision(self) -> bool:
        """
        Check if the robot's safety clearance zone intersects any physical obstacle
        (Wall, Stand Cube body, Cabinet body, or Outer Field Boundary Walls).
        Reference solatif lines on Stand Cube & Cabinet are ignored.
        Returns True if collision / safety distance violation occurs.
        """
        if self.safety_margin_cm <= 0 or not self.scene():
            return False

        r_safe_cm = (self.diameter_cm / 2.0) + self.safety_margin_cm
        rob_x_cm = self.get_x_cm()
        rob_y_cm = self.get_y_cm()
        scene = self.scene()

        # 1. Check against Field Outer Boundary Walls
        field_w_cm = getattr(scene, 'width_cm', 200.0)
        field_h_cm = getattr(scene, 'height_cm', 400.0)

        if (rob_x_cm - r_safe_cm <= 0.0 or rob_x_cm + r_safe_cm >= field_w_cm or
            rob_y_cm - r_safe_cm <= 0.0 or rob_y_cm + r_safe_cm >= field_h_cm):
            return True

        # 2. Check against Field Items (Wall, StandCube body, Cabinet body)
        for item in scene.items():
            if item is self or not getattr(item, 'isVisible', lambda: False)():
                continue

            itype = getattr(item, 'item_type', '')
            if itype not in ['wall', 'stand_cube', 'cabinet']:
                continue

            w_cm = getattr(item, 'width_cm', 0.0)
            h_cm = getattr(item, 'height_cm', 0.0)
            if w_cm <= 0 or h_cm <= 0:
                continue

            ix_cm = getattr(item, 'get_x_cm', lambda: 0.0)()
            iy_cm = getattr(item, 'get_y_cm', lambda: 0.0)()
            rot_deg = getattr(item, 'rotation', lambda: 0.0)()

            # Physical body rectangle local corners span (0,0) to (w_cm, h_cm)
            corners_local = [
                (0.0, 0.0),
                (w_cm, 0.0),
                (w_cm, h_cm),
                (0.0, h_cm)
            ]
            rot_rad = math.radians(rot_deg)
            cos_r = math.cos(rot_rad)
            sin_r = math.sin(rot_rad)

            world_corners = []
            for (lx, ly) in corners_local:
                wx = ix_cm + (lx * cos_r - ly * sin_r)
                wy = iy_cm + (lx * sin_r + ly * cos_r)
                world_corners.append((wx, wy))

            for i in range(4):
                p1 = world_corners[i]
                p2 = world_corners[(i + 1) % 4]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                if dx == 0 and dy == 0:
                    dist = math.hypot(rob_x_cm - p1[0], rob_y_cm - p1[1])
                else:
                    t = ((rob_x_cm - p1[0]) * dx + (rob_y_cm - p1[1]) * dy) / (dx * dx + dy * dy)
                    t = max(0.0, min(1.0, t))
                    cx = p1[0] + t * dx
                    cy = p1[1] + t * dy
                    dist = math.hypot(rob_x_cm - cx, rob_y_cm - cy)

                if dist <= r_safe_cm:
                    return True

        return False

    def paint(self, painter: QPainter, option, widget=None):
        r_px = (self.diameter_cm / 2.0) * self.px_per_cm

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 0. Render Safety Clearance Oval Zone (Green when Safe, Red when Warning/Collision)
        if self.safety_margin_cm > 0:
            is_collision = self.check_safety_collision()

            safe_r_px = (self.diameter_cm / 2.0 + self.safety_margin_cm) * self.px_per_cm
            safe_path = QPainterPath()
            safe_path.addEllipse(QPointF(0, 0), safe_r_px, safe_r_px)

            if is_collision:
                safe_pen = QPen(QColor("#ff4757"), 2.2, Qt.PenStyle.DashLine)
                safe_fill = QColor(255, 71, 87, 55)
                text_color = QColor("#ff4757")
                status_txt = f"⚠️ BAHAYA: {self.safety_margin_cm:.1f}cm"
                badge_w = 110.0
            else:
                safe_pen = QPen(QColor("#2ecc71"), 1.8, Qt.PenStyle.DashLine)
                safe_fill = QColor(46, 204, 113, 35)
                text_color = QColor("#2ecc71")
                status_txt = f"Aman: {self.safety_margin_cm:.1f}cm"
                badge_w = 85.0

            painter.setPen(safe_pen)
            painter.setBrush(QBrush(safe_fill))
            painter.drawPath(safe_path)

            # Safety Zone Distance Badge at Bottom of Ring
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            lbl_rect = QRectF(-badge_w / 2.0, safe_r_px + 3.0, badge_w, 14.0)
            painter.fillRect(lbl_rect, QColor(0, 0, 0, 180))
            painter.setPen(QPen(text_color))
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, status_txt)

        # 1. Render Default Oval / Ellipse Robot Body
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), r_px, r_px)

        fill_color = QColor(self.item_color)
        fill_color.setAlpha(220)

        pen_color = QColor("#f39c12") if self.isSelected() else QColor("#ffffff")
        pen_width = 3.0 if self.isSelected() else 2.0

        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(path)

        # 1.5. Render Omni Wheels (4-Omni or 3-Omni Drive Calibration matching user references)
        w_diam_cm = self.wheel_diameter_mm / 10.0  # 10 cm or 5 cm
        w_len_px = w_diam_cm * self.px_per_cm
        w_width_px = max(4.0, w_len_px * 0.4)

        if self.wheel_count == 4:
            # 4-Omni Drive: 4 corner diagonal wheels (45°, 135°, 225°, 315°)
            wheels_setup = [
                {'pos_angle': 45.0,   'wheel_rot': 45.0 + 90.0},
                {'pos_angle': 135.0,  'wheel_rot': 135.0 + 90.0},
                {'pos_angle': -135.0, 'wheel_rot': -135.0 + 90.0},
                {'pos_angle': -45.0,  'wheel_rot': -45.0 + 90.0}
            ]
        else:
            # 3-Omni Drive: 2 wheels in front (Front-Left -60°, Front-Right +60°) & 1 wheel at back (Back-Center 180°)
            # Rims are tangential (perpendicular to radial shaft extending from center)
            wheels_setup = [
                {'pos_angle': -60.0, 'wheel_rot': -60.0 + 90.0}, # Front-Left (30°)
                {'pos_angle': 60.0,  'wheel_rot': 60.0 + 90.0},  # Front-Right (150°)
                {'pos_angle': 180.0, 'wheel_rot': 180.0 + 90.0} # Back-Center (270° / horizontal)
            ]

        for w_info in wheels_setup:
            pos_deg = w_info['pos_angle']
            rot_deg = w_info['wheel_rot']

            rad = math.radians(pos_deg - 90.0)
            xs = r_px * math.cos(rad)
            ys = r_px * math.sin(rad)

            painter.save()
            painter.translate(xs, ys)

            # Motor Chassis Bracket extending inward to center
            painter.setPen(QPen(QColor("#1e272e"), 1.2))
            painter.setBrush(QBrush(QColor("#2f3542")))
            motor_w = w_width_px * 1.1
            motor_l = r_px * 0.35
            painter.drawRect(QRectF(-motor_w / 2.0, -motor_l / 2.0, motor_w, motor_l))

            painter.rotate(rot_deg)

            # Omni Wheel Rim Body
            wheel_rect = QRectF(-w_width_px / 2.0, -w_len_px / 2.0, w_width_px, w_len_px)
            painter.setPen(QPen(QColor("#1e272e"), 1.2))
            painter.setBrush(QBrush(QColor("#2d3436")))
            painter.drawRoundedRect(wheel_rect, 2.0, 2.0)

            # Metallic Axle Pin
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#a4b0be")))
            painter.drawRect(QRectF(-w_width_px * 0.65, -2.0, w_width_px * 1.3, 4.0))

            # Double-Layer Omni Sub-Rollers (Mini Rollers along Rim Edge)
            num_rollers = 5 if self.wheel_diameter_mm == 100 else 4
            roller_h = w_len_px / (num_rollers * 1.35)
            painter.setPen(QPen(QColor("#000000"), 0.8))
            painter.setBrush(QBrush(QColor("#e1b12c")))  # Gold sub-roller pins

            for i in range(num_rollers):
                ry = -w_len_px / 2.0 + (i + 0.2) * (w_len_px / num_rollers)
                painter.drawRoundedRect(QRectF(-w_width_px / 2.0 - 1.8, ry, 2.8, roller_h), 1, 1)
                painter.drawRoundedRect(QRectF(w_width_px / 2.0 - 1.0, ry, 2.8, roller_h), 1, 1)

            painter.restore()

        # 2. Render 9 Sensors on Robot Boundary
        for pos_key, cfg in self.SENSOR_CONFIGS.items():
            stype = self.sensors.get(pos_key, 'none')
            xs = cfg['rel_x'] * r_px
            ys = cfg['rel_y'] * r_px
            angle_deg = cfg['angle']

            painter.save()
            painter.translate(xs, ys)
            painter.rotate(angle_deg)

            if stype == 'ultrasonic':
                # --- Ultrasonic Sensor (Cyan Dual-Cylinder Module + Beam Cone) ---
                beam_path = QPainterPath()
                beam_path.moveTo(0, 0)
                beam_path.lineTo(-12, -35)
                beam_path.lineTo(12, -35)
                beam_path.closeSubpath()
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 206, 201, 55)))
                painter.drawPath(beam_path)

                mod_rect = QRectF(-10, -6, 20, 10)
                painter.setPen(QPen(QColor("#008080"), 1.2))
                painter.setBrush(QBrush(QColor("#00cec9")))
                painter.drawRoundedRect(mod_rect, 2, 2)

                painter.setPen(QPen(QColor("#2d3436"), 1))
                painter.setBrush(QBrush(QColor("#dfe6e9")))
                painter.drawEllipse(QPointF(-4.5, -3), 3.0, 3.0)
                painter.drawEllipse(QPointF(4.5, -3), 3.0, 3.0)

            elif stype == 'infrared':
                # --- Infrared Sensor (Red IR Module + Narrow Beam Ray) ---
                beam_path = QPainterPath()
                beam_path.moveTo(0, 0)
                beam_path.lineTo(-5, -30)
                beam_path.lineTo(5, -30)
                beam_path.closeSubpath()
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 107, 107, 65)))
                painter.drawPath(beam_path)

                mod_rect = QRectF(-8, -5, 16, 9)
                painter.setPen(QPen(QColor("#900c3f"), 1.2))
                painter.setBrush(QBrush(QColor("#ff4757")))
                painter.drawRoundedRect(mod_rect, 2, 2)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#2ed573")))
                painter.drawEllipse(QPointF(-3, -2.5), 2.2, 2.2)
                painter.setBrush(QBrush(QColor("#2f3542")))
                painter.drawEllipse(QPointF(3, -2.5), 2.2, 2.2)

            else:
                # --- Empty Slot Mount Indicator (Subtle Gray Dot/Slot) ---
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1.0, Qt.PenStyle.DotLine))
                painter.setBrush(QBrush(QColor(0, 0, 0, 90)))
                painter.drawEllipse(QPointF(0, 0), 2.5, 2.5)

            painter.restore()

        # 2b. Render 2 Line Sensors (front center, facing downward)
        line_readouts = self.get_line_sensor_readouts()
        for ls_key, ls_cfg in self.LINE_SENSOR_CONFIGS.items():
            installed = self.line_sensors.get(ls_key, False)
            lx = ls_cfg['rel_x'] * r_px
            ly = ls_cfg['rel_y'] * r_px

            painter.save()
            painter.translate(lx, ly)

            if installed:
                ls_info = line_readouts.get(ls_key, {})
                is_detecting = ls_info.get('detecting', False)

                if is_detecting:
                    # Detecting line — bright green glow
                    painter.setPen(QPen(QColor("#00b894"), 1.5))
                    painter.setBrush(QBrush(QColor("#00b894")))
                else:
                    # Installed but not detecting — dim gray module
                    painter.setPen(QPen(QColor("#636e72"), 1.2))
                    painter.setBrush(QBrush(QColor("#2d3436")))

                # Line sensor module: small rectangle with LED dot
                mod_rect = QRectF(-4.5, -3.0, 9.0, 6.0)
                painter.drawRoundedRect(mod_rect, 1.5, 1.5)

                # LED indicator dot
                led_color = QColor("#55efc4") if is_detecting else QColor("#b2bec3")
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(led_color))
                painter.drawEllipse(QPointF(0, 0), 1.8, 1.8)
            else:
                # Not installed — subtle empty slot indicator
                painter.setPen(QPen(QColor(255, 255, 255, 80), 0.8, Qt.PenStyle.DotLine))
                painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
                painter.drawEllipse(QPointF(0, 0), 2.0, 2.0)

            painter.restore()

        # 3. Render Live Distance Rays & Hit Dots on Canvas
        readouts = self.get_sensor_readouts()
        px_scale = self.px_per_cm if self.px_per_cm > 0 else 2.5

        for pos_key, info in readouts.items():
            if info.get('type') == 'none':
                continue

            dist = info.get('distance_cm', 0.0)
            stype = info.get('type')
            start_cm = info.get('start_cm')
            hit_cm = info.get('hit_cm')

            if start_cm and hit_cm:
                start_px_scene = QPointF(start_cm[0] * px_scale, start_cm[1] * px_scale)
                hit_px_scene = QPointF(hit_cm[0] * px_scale, hit_cm[1] * px_scale)

                p_start = self.mapFromScene(start_px_scene)
                p_hit = self.mapFromScene(hit_px_scene)

                # Laser Ray Line
                laser_color = QColor("#00cec9") if stype == 'ultrasonic' else QColor("#ff4757")
                ray_pen = QPen(laser_color, 1.8, Qt.PenStyle.DashLine)
                painter.setPen(ray_pen)
                painter.drawLine(p_start, p_hit)

                # Target Hit Dot Indicator
                painter.setPen(QPen(QColor("#ffffff"), 1.0))
                painter.setBrush(QBrush(laser_color))
                painter.drawEllipse(p_hit, 4.0, 4.0)

                # Distance Text Badge
                painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                txt = f"{dist:.1f}cm"
                badge_rect = QRectF(p_hit.x() + 4, p_hit.y() - 10, 48, 14)
                painter.fillRect(badge_rect, QColor(0, 0, 0, 180))
                painter.setPen(QPen(QColor("#ffffff")))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, txt)

        # 4. Heading Direction Arrow (points forward towards 0 deg / top)
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
            'shape': 'oval',
            'x_cm': round(self.get_x_cm(), 2),
            'y_cm': round(self.get_y_cm(), 2),
            'diameter_cm': round(self.diameter_cm, 2),
            'safety_margin_cm': round(self.safety_margin_cm, 2),
            'rotation_deg': round(self.rotation(), 2),
            'wheels': {
                'count': self.wheel_count,
                'diameter_mm': self.wheel_diameter_mm
            },
            'sensors': self.sensors.copy(),
            'line_sensors': self.line_sensors.copy()
        }
