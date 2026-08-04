"""
Field Canvas Module for Field Layout & Robot Simulator GUI.
Implements QGraphicsScene and QGraphicsView with background grid rendering,
rulers (axis tick marks), scale conversion, snap-to-grid, and mouse tracking.
"""

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QTransform, QPainterPath
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from core.field_items import BaseFieldItem


class FieldScene(QGraphicsScene):
    """
    Custom graphics scene representing the competition/test field.
    Draws background, grid overlay, and axis rulers.
    """
    mouseMoved = pyqtSignal(float, float)  # Emits (x_cm, y_cm)

    def __init__(self, width_m: float = 2.0, height_m: float = 4.0,
                 px_per_mm: float = 0.25, grid_size_cm: float = 10.0):
        super().__init__()
        self.width_cm = width_m * 100.0
        self.height_cm = height_m * 100.0
        self.px_per_mm = px_per_mm
        self.px_per_cm = px_per_mm * 10.0
        self.grid_size_cm = grid_size_cm
        self.snap_enabled = True
        
        self.ruler_size = 30  # pixels reserved for rulers on top & left

        self.update_scene_rect()

    def update_field_dimensions(self, width_m: float, height_m: float,
                                px_per_mm: float = None, grid_size_cm: float = None):
        self.width_cm = max(10.0, width_m * 100.0)
        self.height_cm = max(10.0, height_m * 100.0)
        if px_per_mm is not None:
            self.px_per_mm = max(0.01, px_per_mm)
            self.px_per_cm = self.px_per_mm * 10.0
        if grid_size_cm is not None:
            self.grid_size_cm = max(1.0, grid_size_cm)
            
        self.update_scene_rect()

        # Update scale for all items in scene
        for item in self.items():
            if isinstance(item, BaseFieldItem):
                item.set_px_per_cm(self.px_per_cm)

        self.update()

    def update_scene_rect(self):
        w_px = self.width_cm * self.px_per_cm
        h_px = self.height_cm * self.px_per_cm
        # Margin around field for rulers and padding
        pad = 40.0
        self.setSceneRect(-self.ruler_size - pad, -self.ruler_size - pad,
                          w_px + self.ruler_size + 2*pad, h_px + self.ruler_size + 2*pad)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Soft neutral light outer canvas background
        painter.fillRect(rect, QColor("#e5e7eb"))

        w_px = self.width_cm * self.px_per_cm
        h_px = self.height_cm * self.px_per_cm
        field_rect = QRectF(0, 0, w_px, h_px)

        # 2. Main Field Surface Background - PURE WHITE LAPANGAN
        field_brush = QBrush(QColor("#ffffff"))
        painter.fillRect(field_rect, field_brush)

        # 3. Outer Field Boundary Line - Thick Black Border
        border_pen = QPen(QColor("#000000"), 3.5)
        painter.setPen(border_pen)
        painter.drawRect(field_rect)

        # 4. Grid Lines (Subtle light gray grid lines on white canvas)
        grid_px = self.grid_size_cm * self.px_per_cm
        if grid_px >= 3.0:
            minor_pen = QPen(QColor(210, 215, 220), 1.0, Qt.PenStyle.SolidLine)
            major_pen = QPen(QColor(100, 110, 120), 1.5, Qt.PenStyle.SolidLine)

            # Draw vertical grid lines
            x = 0.0
            step_idx = 0
            while x <= w_px + 0.1:
                is_major = (step_idx % 5 == 0) or (abs(x - w_px) < 0.1) or (x == 0)
                painter.setPen(major_pen if is_major else minor_pen)
                painter.drawLine(QPointF(x, 0), QPointF(x, h_px))
                x += grid_px
                step_idx += 1

            # Draw horizontal grid lines
            y = 0.0
            step_idx = 0
            while y <= h_px + 0.1:
                is_major = (step_idx % 5 == 0) or (abs(y - h_px) < 0.1) or (y == 0)
                painter.setPen(major_pen if is_major else minor_pen)
                painter.drawLine(QPointF(0, y), QPointF(w_px, y))
                y += grid_px
                step_idx += 1

        # 5. Draw Rulers (Mistar Sumbu X & Y)
        self.draw_rulers(painter, w_px, h_px)

    def draw_rulers(self, painter: QPainter, w_px: float, h_px: float):
        r_size = self.ruler_size
        ruler_bg = QColor("#f1f5f9")
        ruler_border = QColor("#cbd5e1")
        text_color = QColor("#334155")

        painter.setFont(QFont("Consolas", 8))

        # --- Top Ruler (X-Axis) ---
        top_rect = QRectF(0, -r_size, w_px, r_size)
        painter.fillRect(top_rect, ruler_bg)
        painter.setPen(QPen(ruler_border, 1.0))
        painter.drawRect(top_rect)

        # X-Axis Ticks
        step_cm = 10.0 if self.px_per_cm >= 1.5 else 50.0
        step_px = step_cm * self.px_per_cm
        x = 0.0
        while x <= w_px + 0.1:
            val_cm = int(round(x / self.px_per_cm))
            is_major = (val_cm % 50 == 0) or (val_cm == 0) or (abs(x - w_px) < 0.1)
            tick_h = r_size * 0.6 if is_major else r_size * 0.3
            
            painter.setPen(QPen(QColor("#000000") if is_major else text_color, 1.0))
            painter.drawLine(QPointF(x, -tick_h), QPointF(x, 0))

            if is_major or (step_px >= 30.0 and val_cm % 20 == 0):
                txt = f"{val_cm}cm"
                t_rect = QRectF(x - 25, -r_size, 50, r_size - tick_h - 2)
                painter.drawText(t_rect, Qt.AlignmentFlag.AlignCenter, txt)
            x += step_px

        # --- Left Ruler (Y-Axis) ---
        left_rect = QRectF(-r_size, 0, r_size, h_px)
        painter.fillRect(left_rect, ruler_bg)
        painter.setPen(QPen(ruler_border, 1.0))
        painter.drawRect(left_rect)

        # Y-Axis Ticks
        y = 0.0
        while y <= h_px + 0.1:
            val_cm = int(round(y / self.px_per_cm))
            is_major = (val_cm % 50 == 0) or (val_cm == 0) or (abs(y - h_px) < 0.1)
            tick_w = r_size * 0.6 if is_major else r_size * 0.3

            painter.setPen(QPen(QColor("#000000") if is_major else text_color, 1.0))
            painter.drawLine(QPointF(-tick_w, y), QPointF(0, y))

            if is_major or (step_px >= 30.0 and val_cm % 20 == 0):
                txt = f"{val_cm}"
                t_rect = QRectF(-r_size, y - 10, r_size - tick_w - 2, 20)
                painter.drawText(t_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, txt)
            y += step_px

        # Origin corner box (0,0 indicator)
        origin_rect = QRectF(-r_size, -r_size, r_size, r_size)
        painter.fillRect(origin_rect, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#000000"), 1.5))
        painter.drawRect(origin_rect)
        painter.setPen(QPen(QColor("#000000")))
        painter.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        painter.drawText(origin_rect, Qt.AlignmentFlag.AlignCenter, "(0,0)")

    def snap_point(self, pt: QPointF) -> QPointF:
        """Snap a pixel coordinate point to the nearest grid step in cm."""
        if not self.snap_enabled or self.grid_size_cm <= 0:
            return pt
        grid_px = self.grid_size_cm * self.px_per_cm
        snapped_x = round(pt.x() / grid_px) * grid_px
        snapped_y = round(pt.y() / grid_px) * grid_px
        return QPointF(snapped_x, snapped_y)

    def mouseMoveEvent(self, event):
        pos = event.scenePos()
        x_cm = max(0.0, min(self.width_cm, pos.x() / self.px_per_cm))
        y_cm = max(0.0, min(self.height_cm, pos.y() / self.px_per_cm))
        self.mouseMoved.emit(x_cm, y_cm)
        super().mouseMoveEvent(event)


class FieldView(QGraphicsView):
    """
    Graphics View container with pan, zoom, and interactive object manipulation.
    """
    def __init__(self, scene: FieldScene):
        super().__init__(scene)
        self.field_scene = scene

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("QGraphicsView { border: none; background-color: #e5e7eb; }")

        self.zoom_factor = 1.0

    def wheelEvent(self, event):
        """Zoom in / zoom out with Ctrl + Mouse Wheel or pinch."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 0.85
            new_zoom = self.zoom_factor * factor
            if 0.2 <= new_zoom <= 5.0:
                self.zoom_factor = new_zoom
                self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def fit_in_view(self):
        """Fit entire field inside current view viewport."""
        self.fitInView(self.field_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_factor = 1.0

    def keyPressEvent(self, event):
        """Pass key press events to parent window for global shortcuts."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) or (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            event.ignore()
            if self.window():
                self.window().keyPressEvent(event)
            return
        super().keyPressEvent(event)
