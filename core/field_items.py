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
    Robot Item rendered as Oval / Ellipse shape with 9 Sensor Mount Positions.
    Front 3 sensors (front_left, front_center, front_right) are aligned parallel in a straight line.
    Includes 2D Raycasting Distance Detection against field boundaries and internal obstacles.
    Rendered on top of all field objects (ZValue = 100.0).
    """

    SENSOR_CONFIGS = {
        'front_left':   {'rel_x': -0.6,   'rel_y': -1.0, 'angle': 0.0},
        'front_center': {'rel_x':  0.0,   'rel_y': -1.0, 'angle': 0.0},
        'front_right':  {'rel_x':  0.6,   'rel_y': -1.0, 'angle': 0.0},
        'right_front':  {'rel_x':  0.866, 'rel_y': -0.5, 'angle': 60.0},
        'right_rear':   {'rel_x':  0.866, 'rel_y':  0.5, 'angle': 120.0},
        'back_right':   {'rel_x':  0.342, 'rel_y':  0.94, 'angle': 160.0},
        'back_left':    {'rel_x': -0.342, 'rel_y':  0.94, 'angle': -160.0},
        'left_rear':    {'rel_x': -0.866, 'rel_y':  0.5, 'angle': -120.0},
        'left_front':   {'rel_x': -0.866, 'rel_y': -0.5, 'angle': -60.0}
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

    def set_sensors(self, sensors_dict: dict):
        if sensors_dict:
            for k in self.sensors:
                if k in sensors_dict:
                    self.sensors[k] = sensors_dict[k]
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
                rect = item.boundingRect()
                c0 = item.mapToScene(rect.topLeft()) / px_per_cm
                c1 = item.mapToScene(rect.topRight()) / px_per_cm
                c2 = item.mapToScene(rect.bottomRight()) / px_per_cm
                c3 = item.mapToScene(rect.bottomLeft()) / px_per_cm

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

    def paint(self, painter: QPainter, option, widget=None):
        r_px = (self.diameter_cm / 2.0) * self.px_per_cm

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

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

        # 2. Render 7 Sensors on Robot Boundary
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
            'x_cm': round(self.get_x_cm(), 2),
            'y_cm': round(self.get_y_cm(), 2),
            'diameter_cm': round(self.diameter_cm, 2),
            'rotation_deg': round(self.rotation(), 2),
            'sensors': self.sensors.copy()
        }
