"""
Main GUI Window Module for Field Layout Editor & Robot Simulator.
Combines Toolbar, Object Palette Sidebar, Settings Panel, Canvas Viewport, and maps.yaml export/import.
"""

import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
    QCheckBox, QComboBox, QFileDialog, QMessageBox, QFrame,
    QSplitter, QStatusBar, QToolBar, QColorDialog, QScrollArea
)

from core.field_canvas import FieldScene, FieldView
from core.field_items import (
    BaseFieldItem, HomeBoxItem, StandCubeItem, WallItem,
    LineItem, CabinetItem, RobotItem
)
from io_handler.map_exporter import (
    export_to_yaml, import_from_yaml,
    export_robot_to_yaml, import_robot_from_yaml
)


class MainWindow(QMainWindow):
    """Main application window for Field Layout Editor & Robot Simulator."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor Layout Lapangan & Simulator Robot (maps.yaml)")
        self.resize(1350, 850)

        # Default Parameters
        self.field_width_m = 2.0     # 2 meters (200 cm / 2000 mm)
        self.field_height_m = 4.0    # 4 meters (400 cm / 4000 mm)
        self.px_per_mm = 0.25        # 1 mm = 0.25 px (1 cm = 2.5 px)
        self.grid_size_cm = 10.0     # 1 grid square = 10 cm

        self.selected_item = None
        self.robot_item = None

        # Setup Core Canvas & Scene
        self.scene = FieldScene(
            width_m=self.field_width_m,
            height_m=self.field_height_m,
            px_per_mm=self.px_per_mm,
            grid_size_cm=self.grid_size_cm
        )
        self.view = FieldView(self.scene)

        # Connect scene signals
        self.scene.mouseMoved.connect(self.on_mouse_moved)

        self.copied_item_data = None

        # Build UI Structure
        self.init_stylesheet()
        self.init_toolbar()
        self.init_ui()
        self.init_default_items()
        self.init_statusbar()

    def keyPressEvent(self, event):
        """Backup global key press event handler for shortcuts."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.selected_item and self.selected_item != self.robot_item:
                self.delete_selected_item()
                event.accept()
                return
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_S:
                self.export_yaml()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_C:
                self.copy_selected_item()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_V:
                self.paste_copied_item()
                event.accept()
                return
        super().keyPressEvent(event)

    def init_stylesheet(self):
        """Apply modern dark-theme stylesheet with comprehensive widget styling."""
        dark_style = """
        QMainWindow {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            color: #c9d1d9;
        }

        /* ── Group Boxes ── */
        QGroupBox {
            font-weight: bold;
            font-size: 12px;
            border: 1px solid #30363d;
            border-radius: 8px;
            margin-top: 14px;
            padding: 14px 10px 10px 10px;
            background-color: #161b22;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 3px 10px;
            color: #58a6ff;
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 4px;
            font-size: 12px;
        }

        /* ── Buttons ── */
        QPushButton {
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 7px 14px;
            color: #c9d1d9;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #30363d;
            border-color: #58a6ff;
        }
        QPushButton:pressed {
            background-color: #1f6feb;
            color: #ffffff;
        }
        QPushButton#primaryBtn {
            background-color: #238636;
            border-color: #2ea043;
            color: #ffffff;
            font-weight: bold;
        }
        QPushButton#primaryBtn:hover {
            background-color: #2ea043;
            border-color: #3fb950;
        }
        QPushButton#dangerBtn {
            background-color: #da3633;
            border-color: #f85149;
            color: #ffffff;
        }
        QPushButton#dangerBtn:hover {
            background-color: #f85149;
        }

        /* ── Spin Boxes & Combo Boxes ── */
        QDoubleSpinBox, QSpinBox, QComboBox {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 5px;
            padding: 5px 8px;
            color: #c9d1d9;
            min-height: 20px;
        }
        QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
            border-color: #58a6ff;
        }
        QDoubleSpinBox::up-button, QSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #30363d;
            background-color: #21262d;
            border-top-right-radius: 4px;
        }
        QDoubleSpinBox::down-button, QSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            border-left: 1px solid #30363d;
            background-color: #21262d;
            border-bottom-right-radius: 4px;
        }
        QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
        QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
            background-color: #30363d;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-left: 1px solid #30363d;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            background-color: #21262d;
        }
        QComboBox::down-arrow {
            image: none;
            width: 0; height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #8b949e;
        }
        QComboBox QAbstractItemView {
            background-color: #161b22;
            border: 1px solid #30363d;
            color: #c9d1d9;
            selection-background-color: #1f6feb;
            selection-color: #ffffff;
            padding: 4px;
        }

        /* ── Labels ── */
        QLabel {
            color: #8b949e;
        }
        QLabel#highlightVal {
            color: #58a6ff;
            font-weight: bold;
        }
        QLabel#sectionHeader {
            color: #58a6ff;
            font-weight: bold;
            font-size: 12px;
            padding: 2px 0px;
        }

        /* ── Checkbox ── */
        QCheckBox {
            spacing: 8px;
            color: #c9d1d9;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid #30363d;
            background-color: #0d1117;
        }
        QCheckBox::indicator:checked {
            background-color: #238636;
            border-color: #2ea043;
        }
        QCheckBox::indicator:hover {
            border-color: #58a6ff;
        }

        /* ── Toolbar ── */
        QToolBar {
            background-color: #161b22;
            border-bottom: 1px solid #30363d;
            spacing: 2px;
            padding: 3px 6px;
        }
        QToolBar QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 5px;
            padding: 5px 10px;
            color: #c9d1d9;
            font-size: 12px;
        }
        QToolBar QToolButton:hover {
            background-color: #21262d;
            border-color: #30363d;
        }
        QToolBar QToolButton:pressed {
            background-color: #1f6feb;
            color: #ffffff;
        }
        QToolBar::separator {
            width: 1px;
            background-color: #30363d;
            margin: 4px 6px;
        }

        /* ── Status Bar ── */
        QStatusBar {
            background-color: #161b22;
            border-top: 1px solid #30363d;
            color: #8b949e;
            font-size: 12px;
            padding: 2px 6px;
        }
        QStatusBar QLabel {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            color: #8b949e;
            padding: 0 4px;
        }

        /* ── Scroll Bars ── */
        QScrollBar:vertical {
            background: #0d1117;
            width: 8px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background: #30363d;
            min-height: 30px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background: #484f58;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar:horizontal {
            background: #0d1117;
            height: 8px;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background: #30363d;
            min-width: 30px;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #484f58;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }

        /* ── Splitter ── */
        QSplitter::handle {
            background-color: #21262d;
            width: 2px;
        }
        QSplitter::handle:hover {
            background-color: #58a6ff;
        }
        """
        self.setStyleSheet(dark_style)

    def init_toolbar(self):
        """Build top toolbar actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # File Actions
        act_new = QAction("📄 Baru (Reset)", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self.new_map)
        toolbar.addAction(act_new)

        act_open = QAction("📂 Buka maps.yaml", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.import_yaml)
        toolbar.addAction(act_open)

        act_save = QAction("💾 Simpan (Ctrl+S)", self)
        act_save.triggered.connect(self.export_yaml)
        toolbar.addAction(act_save)

        toolbar.addSeparator()

        # Edit Actions (Copy, Paste, Delete) - shortcuts handled by keyPressEvent
        act_copy = QAction("📋 Copy (Ctrl+C)", self)
        act_copy.triggered.connect(self.copy_selected_item)
        toolbar.addAction(act_copy)

        act_paste = QAction("📋 Paste (Ctrl+V)", self)
        act_paste.triggered.connect(self.paste_copied_item)
        toolbar.addAction(act_paste)

        act_del = QAction("🗑️ Delete (Del)", self)
        act_del.triggered.connect(self.delete_selected_item)
        toolbar.addAction(act_del)

        toolbar.addSeparator()

        # View Actions
        act_fit = QAction("🔍 Fit View", self)
        act_fit.triggered.connect(self.view.fit_in_view)
        toolbar.addAction(act_fit)

        act_export_img = QAction("🖼️ Ekspor Gambar (PNG)", self)
        act_export_img.triggered.connect(self.export_image)
        toolbar.addAction(act_export_img)

    def init_ui(self):
        """Construct main layout: Left (Field & Object Inspector), Center (Canvas), Right (Robot & Field Settings)."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- LEFT SIDEBAR: Edit Kondisi Lapangan & Inspektur Objek ---
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        left_layout.addWidget(self.build_palette_box())
        left_layout.addWidget(self.build_inspector_box())
        left_layout.addStretch()

        left_scroll.setWidget(left_widget)
        left_scroll.setFixedWidth(280)

        # --- CENTER VIEWPORT: Field Scene & View ---
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.view)

        # --- RIGHT SIDEBAR: Edit Robot & Pengaturan Lapangan ---
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        right_layout.addWidget(self.build_robot_main_box())
        right_layout.addWidget(self.build_robot_wheels_box())
        right_layout.addWidget(self.build_robot_sensors_box())
        right_layout.addWidget(self.build_robot_line_sensors_box())
        right_layout.addWidget(self.build_robot_actions_box())
        right_layout.addWidget(self.build_field_settings_box())
        right_layout.addStretch()

        right_scroll.setWidget(right_widget)
        right_scroll.setFixedWidth(340)

        # Add to splitter (Left, Center, Right)
        splitter.addWidget(left_scroll)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_scroll)

        # Set stretch factors (Center view gets max space)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        main_layout.addWidget(splitter)

    def build_palette_box(self) -> QGroupBox:
        """Create Palette sidebar for adding items to field."""
        box = QGroupBox("➕ Tambah Objek Lapangan")
        layout = QVBoxLayout(box)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        palette_items = [
            ("🟢  Home Box (50x50 cm)", "#2ecc71", self.add_home_box),
            ("🟧  Stand Cube (15x15 cm)", "#e67e22", self.add_stand_cube),
            ("🧱  Tembok (Lebar 2 cm)", "#7f8c8d", self.add_wall),
            ("📏  Garis (Lebar 2 cm)", "#3498db", self.add_line),
            ("🗄️  Lemari (15x45 cm)", "#9b59b6", self.add_cabinet),
        ]

        for label, accent_color, handler in palette_items:
            btn = QPushButton(label)
            btn.setStyleSheet(
                f"text-align: left; padding: 8px 12px; border-left: 3px solid {accent_color};"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        # Visual separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #30363d; max-height: 1px; margin: 4px 0;")
        layout.addWidget(sep)

        lbl_hint = QLabel("💡 Klik tombol di atas untuk menambah objek.\nObjek dapat di-drag & diputar.")
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #6e7681; font-size: 11px; font-style: italic; padding: 2px 4px;")
        layout.addWidget(lbl_hint)

        return box

    def build_field_settings_box(self) -> QGroupBox:
        """Create Field dimensions & pixel conversion scale panel."""
        box = QGroupBox("📐 Dimensi & Konversi Pixel")
        grid = QGridLayout(box)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 10, 10, 10)

        # Field Width (meters)
        grid.addWidget(QLabel("Lebar Lapangan (m):"), 0, 0)
        self.spn_field_w = QDoubleSpinBox()
        self.spn_field_w.setRange(0.5, 50.0)
        self.spn_field_w.setSingleStep(0.5)
        self.spn_field_w.setValue(self.field_width_m)
        self.spn_field_w.valueChanged.connect(self.on_field_settings_changed)
        grid.addWidget(self.spn_field_w, 0, 1)

        # Field Height (meters)
        grid.addWidget(QLabel("Panjang Lapangan (m):"), 1, 0)
        self.spn_field_h = QDoubleSpinBox()
        self.spn_field_h.setRange(0.5, 50.0)
        self.spn_field_h.setSingleStep(0.5)
        self.spn_field_h.setValue(self.field_height_m)
        self.spn_field_h.valueChanged.connect(self.on_field_settings_changed)
        grid.addWidget(self.spn_field_h, 1, 1)

        # Scale Factor: Pixels per mm
        grid.addWidget(QLabel("Skala Pixel (px/mm):"), 2, 0)
        self.spn_scale_px_mm = QDoubleSpinBox()
        self.spn_scale_px_mm.setRange(0.01, 10.0)
        self.spn_scale_px_mm.setSingleStep(0.05)
        self.spn_scale_px_mm.setDecimals(3)
        self.spn_scale_px_mm.setValue(self.px_per_mm)
        self.spn_scale_px_mm.valueChanged.connect(self.on_field_settings_changed)
        grid.addWidget(self.spn_scale_px_mm, 2, 1)

        # Grid Size (cm)
        grid.addWidget(QLabel("Ukuran Grid (cm):"), 3, 0)
        self.spn_grid_cm = QDoubleSpinBox()
        self.spn_grid_cm.setRange(1.0, 200.0)
        self.spn_grid_cm.setSingleStep(5.0)
        self.spn_grid_cm.setValue(self.grid_size_cm)
        self.spn_grid_cm.valueChanged.connect(self.on_field_settings_changed)
        grid.addWidget(self.spn_grid_cm, 3, 1)

        # Snap to Grid Checkbox (Default False for unconstrained free placement anywhere on field)
        self.chk_snap = QCheckBox("Snap to Grid")
        self.chk_snap.setChecked(False)
        self.chk_snap.toggled.connect(self.on_snap_toggled)
        grid.addWidget(self.chk_snap, 4, 0, 1, 2)

        # Live Pixel Conversion Display Panel
        self.lbl_conv_summary = QLabel()
        self.lbl_conv_summary.setObjectName("highlightVal")
        self.lbl_conv_summary.setWordWrap(True)
        self.lbl_conv_summary.setStyleSheet(
            "background-color: #0d1117; border: 1px solid #30363d; "
            "border-radius: 4px; padding: 6px; font-size: 11px;"
        )
        grid.addWidget(self.lbl_conv_summary, 5, 0, 1, 2)

        self.update_pixel_conversion_labels()
        return box

    def build_robot_main_box(self) -> QGroupBox:
        """Create Robot main configuration panel: diameter, safety margin, orientation, color, position."""
        box = QGroupBox("🤖 Robot Utama")
        grid = QGridLayout(box)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 10, 10, 10)

        # Row 0: Diameter
        grid.addWidget(QLabel("Diameter (cm):"), 0, 0)
        self.spn_robot_diam = QDoubleSpinBox()
        self.spn_robot_diam.setRange(5.0, 200.0)
        self.spn_robot_diam.setSingleStep(5.0)
        self.spn_robot_diam.setValue(30.0)
        self.spn_robot_diam.valueChanged.connect(self.on_robot_config_changed)
        grid.addWidget(self.spn_robot_diam, 0, 1)

        # Row 1: Safety Margin
        grid.addWidget(QLabel("Jarak Aman (cm):"), 1, 0)
        self.spn_robot_safety_margin = QDoubleSpinBox()
        self.spn_robot_safety_margin.setRange(0.0, 100.0)
        self.spn_robot_safety_margin.setSingleStep(1.0)
        self.spn_robot_safety_margin.setValue(7.0)
        self.spn_robot_safety_margin.valueChanged.connect(self.on_safety_margin_changed)
        grid.addWidget(self.spn_robot_safety_margin, 1, 1)

        # Row 2: Orientation
        grid.addWidget(QLabel("Orientasi (°):"), 2, 0)
        self.spn_robot_rot = QDoubleSpinBox()
        self.spn_robot_rot.setRange(0.0, 360.0)
        self.spn_robot_rot.setSingleStep(5.0)
        self.spn_robot_rot.setValue(0.0)
        self.spn_robot_rot.valueChanged.connect(self.on_robot_rot_changed)
        grid.addWidget(self.spn_robot_rot, 2, 1)

        # Row 3: Color Picker
        grid.addWidget(QLabel("Warna:"), 3, 0)
        self.btn_robot_color = QPushButton("🎨 Pilih Warna")
        self.btn_robot_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_robot_color.clicked.connect(self.choose_robot_color)
        grid.addWidget(self.btn_robot_color, 3, 1)

        # Row 4: Live Position Readout
        self.lbl_robot_pos = QLabel("Posisi: X = 100 cm, Y = 50 cm")
        self.lbl_robot_pos.setStyleSheet(
            "color: #58a6ff; font-size: 11px; font-weight: bold; "
            "background-color: #0d1117; border: 1px solid #30363d; "
            "border-radius: 4px; padding: 5px 8px;"
        )
        grid.addWidget(self.lbl_robot_pos, 4, 0, 1, 2)

        return box

    def build_robot_wheels_box(self) -> QGroupBox:
        """Create Omni Wheel configuration panel: mode (3/4) and diameter (50mm/100mm)."""
        box = QGroupBox("⚙️ Roda Omni")
        grid = QGridLayout(box)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 10, 10, 10)

        # Row 0: Wheel Mode
        grid.addWidget(QLabel("Mode Roda:"), 0, 0)
        self.cb_wheel_mode = QComboBox()
        self.cb_wheel_mode.addItems([
            "4 Roda Omni (4-Omni)",
            "3 Roda Omni (3-Omni)"
        ])
        self.cb_wheel_mode.currentIndexChanged.connect(self.on_wheel_config_changed)
        grid.addWidget(self.cb_wheel_mode, 0, 1)

        # Row 1: Wheel Diameter
        grid.addWidget(QLabel("Diameter Roda:"), 1, 0)
        self.cb_wheel_diam = QComboBox()
        self.cb_wheel_diam.addItems([
            "100 mm (10 cm)",
            "50 mm (5 cm)"
        ])
        self.cb_wheel_diam.currentIndexChanged.connect(self.on_wheel_config_changed)
        grid.addWidget(self.cb_wheel_diam, 1, 1)

        return box

    def build_robot_sensors_box(self) -> QGroupBox:
        """Create 9-Sensor configuration panel with grouped readout display by side."""
        box = QGroupBox("📡 Sensor Robot")
        layout = QVBoxLayout(box)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Sensor Position & Type Selector ---
        selector_grid = QGridLayout()
        selector_grid.setSpacing(6)

        selector_grid.addWidget(QLabel("Posisi Sensor:"), 0, 0)
        self.cb_sensor_pos = QComboBox()
        self.sensor_pos_keys = [
            ('front_left', 'Depan Kiri'),
            ('front_center', 'Depan Tengah'),
            ('front_right', 'Depan Kanan'),
            ('left_front', 'Kiri Depan'),
            ('left_rear', 'Kiri Belakang'),
            ('back_left', 'Belakang Kiri'),
            ('back_right', 'Belakang Kanan'),
            ('right_rear', 'Kanan Belakang'),
            ('right_front', 'Kanan Depan')
        ]
        for key, label_str in self.sensor_pos_keys:
            self.cb_sensor_pos.addItem(label_str, userData=key)
        self.cb_sensor_pos.currentIndexChanged.connect(self.on_sensor_pos_changed)
        selector_grid.addWidget(self.cb_sensor_pos, 0, 1)

        selector_grid.addWidget(QLabel("Tipe Sensor:"), 1, 0)
        self.cb_sensor_type = QComboBox()
        self.cb_sensor_type.addItems([
            "❌ Tidak Dipasang",
            "📡 Ultrasonic (US)",
            "🔴 Infrared (IR)"
        ])
        self.cb_sensor_type.currentIndexChanged.connect(self.on_sensor_type_changed)
        selector_grid.addWidget(self.cb_sensor_type, 1, 1)
        layout.addLayout(selector_grid)

        # --- Visual Separator ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #30363d; max-height: 1px; margin: 6px 0;")
        layout.addWidget(sep)

        # --- Grouped Sensor Readout Summary ---
        lbl_title = QLabel("📊 Status & Hasil Ukur:")
        lbl_title.setObjectName("sectionHeader")
        layout.addWidget(lbl_title)

        self.sensor_summary_labels = {}

        sensor_groups = [
            ("▸ DEPAN", [
                ('front_left', 'Kiri'),
                ('front_center', 'Tengah'),
                ('front_right', 'Kanan'),
            ]),
            ("▸ KIRI", [
                ('left_front', 'Depan'),
                ('left_rear', 'Belakang'),
            ]),
            ("▸ KANAN", [
                ('right_front', 'Depan'),
                ('right_rear', 'Belakang'),
            ]),
            ("▸ BELAKANG", [
                ('back_left', 'Kiri'),
                ('back_right', 'Kanan'),
            ]),
        ]

        for group_title, sensors in sensor_groups:
            grp_lbl = QLabel(group_title)
            grp_lbl.setStyleSheet(
                "color: #e6edf3; font-weight: bold; font-size: 11px; "
                "margin-top: 3px; padding: 0;"
            )
            layout.addWidget(grp_lbl)

            for key, short_name in sensors:
                full_label = short_name
                for pk, pl in self.sensor_pos_keys:
                    if pk == key:
                        full_label = pl
                        break
                lbl = QLabel(f"   {short_name}: Nonaktif")
                lbl.setStyleSheet("color: #484f58; font-size: 11px; padding-left: 12px;")
                layout.addWidget(lbl)
                self.sensor_summary_labels[key] = (full_label, lbl)

        return box

    def build_robot_line_sensors_box(self) -> QGroupBox:
        """Create 2 Line Sensors (downward-facing) configuration & readout panel."""
        box = QGroupBox("📏 Sensor Garis (Line Sensor)")
        layout = QVBoxLayout(box)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl_desc = QLabel("2 Sensor Garis di Bawah Sensor Depan-Tengah (Opsional):")
        lbl_desc.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(lbl_desc)

        chk_layout = QGridLayout()
        chk_layout.setSpacing(6)

        self.chk_line_left = QCheckBox("Center Kiri")
        self.chk_line_left.toggled.connect(self.on_line_sensor_toggled)
        chk_layout.addWidget(self.chk_line_left, 0, 0)

        self.chk_line_right = QCheckBox("Center Kanan")
        self.chk_line_right.toggled.connect(self.on_line_sensor_toggled)
        chk_layout.addWidget(self.chk_line_right, 0, 1)

        layout.addLayout(chk_layout)

        # Status & Readout
        self.lbl_line_left_status = QLabel("• Center Kiri: Nonaktif")
        self.lbl_line_left_status.setStyleSheet("color: #484f58; font-size: 11px; padding-left: 4px;")
        self.lbl_line_right_status = QLabel("• Center Kanan: Nonaktif")
        self.lbl_line_right_status.setStyleSheet("color: #484f58; font-size: 11px; padding-left: 4px;")

        st_layout = QVBoxLayout()
        st_layout.setSpacing(2)
        st_layout.addWidget(self.lbl_line_left_status)
        st_layout.addWidget(self.lbl_line_right_status)
        layout.addLayout(st_layout)

        return box

    def build_robot_actions_box(self) -> QGroupBox:
        """Create Robot YAML Save/Load action buttons panel."""
        box = QGroupBox("💾 Simpan / Buka Robot")
        layout = QHBoxLayout(box)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        btn_robot_save = QPushButton("💾 Simpan Robot")
        btn_robot_save.setObjectName("primaryBtn")
        btn_robot_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_robot_save.clicked.connect(self.export_robot_yaml)
        layout.addWidget(btn_robot_save)

        btn_robot_load = QPushButton("📂 Buka Robot")
        btn_robot_load.setStyleSheet(
            "background-color: #1f6feb; color: white; font-weight: bold; "
            "padding: 7px 14px; border-radius: 6px; border: 1px solid #388bfd;"
        )
        btn_robot_load.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_robot_load.clicked.connect(self.import_robot_yaml)
        layout.addWidget(btn_robot_load)

        return box

    def on_safety_margin_changed(self, value: float):
        """Triggered when user changes robot safety clearance margin."""
        if hasattr(self, 'robot_item') and self.robot_item:
            self.robot_item.set_safety_margin(value)
            self.scene.update()

    def on_wheel_config_changed(self):
        """Triggered when user changes Omni wheel mode or wheel diameter."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            return
        count = 4 if self.cb_wheel_mode.currentIndex() == 0 else 3
        diameter_mm = 100 if self.cb_wheel_diam.currentIndex() == 0 else 50
        self.robot_item.set_wheel_config(count, diameter_mm)
        self.scene.update()

    def export_robot_yaml(self):
        """Export current robot configuration and sensors to robot.yaml."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            QMessageBox.warning(self, "Peringatan", "Robot belum dibuat!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Simpan Konfigurasi Robot YAML", "robot.yaml", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            try:
                robot_data = self.robot_item.to_dict()
                # Remove field position coordinates for standalone robot specification
                robot_data.pop('x_cm', None)
                robot_data.pop('y_cm', None)

                export_robot_to_yaml(file_path, robot_data)
                QMessageBox.information(
                    self, "Sukses Simpan Robot",
                    f"Konfigurasi spesifikasi robot berhasil disimpan ke:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error Simpan Robot", f"Gagal menyimpan robot YAML:\n{e}")

    def import_robot_yaml(self):
        """Import robot configuration and sensors from a robot.yaml file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Buka Konfigurasi Robot YAML", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            try:
                r_cfg = import_robot_from_yaml(file_path)
                if not r_cfg:
                    QMessageBox.warning(self, "File Kosong", "Data robot tidak ditemukan pada file YAML.")
                    return

                if hasattr(self, 'robot_item') and self.robot_item:
                    diam = r_cfg.get('diameter_cm', 30.0)
                    rot = r_cfg.get('rotation_deg', 0.0)
                    sensors_cfg = r_cfg.get('sensors', {})
                    w_cfg = r_cfg.get('wheels', {})
                    w_count = w_cfg.get('count', 4)
                    w_diam = w_cfg.get('diameter_mm', 100)
                    safety_m = r_cfg.get('safety_margin_cm', 5.0)
                    x_cm = r_cfg.get('x_cm', self.robot_item.get_x_cm())
                    y_cm = r_cfg.get('y_cm', self.robot_item.get_y_cm())

                    line_cfg = r_cfg.get('line_sensors', {})
                    self.spn_robot_diam.setValue(diam)
                    self.spn_robot_rot.setValue(rot)
                    self.spn_robot_safety_margin.setValue(safety_m)
                    self.robot_item.set_shape_params(diameter_cm=diam)
                    self.robot_item.set_safety_margin(safety_m)
                    self.robot_item.set_cm_pos(x_cm, y_cm)
                    self.robot_item.setRotation(rot)
                    self.robot_item.set_sensors(sensors_cfg)
                    self.robot_item.set_line_sensors(line_cfg)
                    self.robot_item.set_wheel_config(w_count, w_diam)

                    self.chk_line_left.blockSignals(True)
                    self.chk_line_right.blockSignals(True)
                    self.chk_line_left.setChecked(bool(line_cfg.get('line_left', False)))
                    self.chk_line_right.setChecked(bool(line_cfg.get('line_right', False)))
                    self.chk_line_left.blockSignals(False)
                    self.chk_line_right.blockSignals(False)

                    self.cb_wheel_mode.blockSignals(True)
                    self.cb_wheel_mode.setCurrentIndex(0 if w_count == 4 else 1)
                    self.cb_wheel_mode.blockSignals(False)

                    self.cb_wheel_diam.blockSignals(True)
                    self.cb_wheel_diam.setCurrentIndex(0 if w_diam == 100 else 1)
                    self.cb_wheel_diam.blockSignals(False)

                    self.on_sensor_pos_changed(self.cb_sensor_pos.currentIndex())
                    self.update_robot_pos_label()
                    self.update_sensor_readouts_ui()
                    self.scene.update()

                QMessageBox.information(
                    self, "Sukses Buka Robot",
                    f"Berhasil memuat konfigurasi robot dari:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error Memuat Robot", f"Gagal membaca robot YAML:\n{e}")

    def on_sensor_pos_changed(self, index: int):
        """Triggered when user selects a different sensor position in dropdown."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            return
        pos_key = self.cb_sensor_pos.currentData()
        stype = self.robot_item.sensors.get(pos_key, 'none')
        stype_map = {'none': 0, 'ultrasonic': 1, 'infrared': 2}

        self.cb_sensor_type.blockSignals(True)
        self.cb_sensor_type.setCurrentIndex(stype_map.get(stype, 0))
        self.cb_sensor_type.blockSignals(False)

    def on_line_sensor_toggled(self):
        """Triggered when user checks or unchecks line sensor checkboxes."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            return
        cfg = {
            'line_left': self.chk_line_left.isChecked(),
            'line_right': self.chk_line_right.isChecked()
        }
        self.robot_item.set_line_sensors(cfg)
        self.update_sensor_readouts_ui()

    def on_sensor_type_changed(self, index: int):
        """Triggered when user installs/changes sensor type for selected position."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            return
        pos_key = self.cb_sensor_pos.currentData()
        stypes = ['none', 'ultrasonic', 'infrared']
        stype = stypes[index] if 0 <= index < len(stypes) else 'none'

        self.robot_item.sensors[pos_key] = stype
        self.robot_item.update()
        self.update_sensor_readouts_ui()

    def update_sensor_readouts_ui(self):
        """Update live sensor distance readouts in grouped sidebar panel."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            return
        readouts = self.robot_item.get_sensor_readouts()

        # Short names matching the grouped display
        short_names = {
            'front_left': 'Kiri', 'front_center': 'Tengah', 'front_right': 'Kanan',
            'left_front': 'Depan', 'left_rear': 'Belakang',
            'right_front': 'Depan', 'right_rear': 'Belakang',
            'back_left': 'Kiri', 'back_right': 'Kanan',
        }

        for pos_key, (name_str, lbl) in self.sensor_summary_labels.items():
            info = readouts.get(pos_key, {})
            stype = info.get('type', 'none')
            short = short_names.get(pos_key, name_str)
            if stype == 'none':
                lbl.setText(f"   {short}: Nonaktif")
                lbl.setStyleSheet("color: #484f58; font-size: 11px; padding-left: 12px;")
            else:
                dist = info.get('distance_cm', 0.0)
                target = info.get('target_name', 'Batas')
                tag = "US" if stype == 'ultrasonic' else "IR"
                color = "#00cec9" if stype == 'ultrasonic' else "#ff6b6b"
                lbl.setText(f"   {short} [{tag}]: {dist:.1f} cm \u2192 {target}")
                lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; padding-left: 12px;")

        # Update 2 Line Sensors Status Readouts
        if hasattr(self, 'chk_line_left') and hasattr(self, 'chk_line_right'):
            line_readouts = self.robot_item.get_line_sensor_readouts()
            for key, (chk, lbl, name_str) in [
                ('line_left', (self.chk_line_left, self.lbl_line_left_status, 'Center Kiri')),
                ('line_right', (self.chk_line_right, self.lbl_line_right_status, 'Center Kanan'))
            ]:
                info = line_readouts.get(key, {})
                installed = info.get('installed', False)
                if not installed:
                    lbl.setText(f"• {name_str}: Nonaktif")
                    lbl.setStyleSheet("color: #484f58; font-size: 11px; padding-left: 4px;")
                else:
                    detecting = info.get('detecting', False)
                    target = info.get('target', '')
                    if detecting:
                        lbl.setText(f"• {name_str}: DETEKSI GARIS ({target})")
                        lbl.setStyleSheet("color: #00b894; font-size: 11px; font-weight: bold; padding-left: 4px;")
                    else:
                        lbl.setText(f"• {name_str}: Aktif (Bebas)")
                        lbl.setStyleSheet("color: #0984e3; font-size: 11px; padding-left: 4px;")

    def build_inspector_box(self) -> QGroupBox:
        """Create Selected Item Property Inspector panel."""
        box = QGroupBox("🔍 Inspektur Objek Terpilih")
        grid = QGridLayout(box)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 10, 10, 10)

        self.lbl_insp_name = QLabel("Tidak ada objek dipilih")
        self.lbl_insp_name.setStyleSheet("font-weight: bold; color: #58a6ff;")
        grid.addWidget(self.lbl_insp_name, 0, 0, 1, 2)

        # Item X Position (cm)
        grid.addWidget(QLabel("Posisi X (cm):"), 1, 0)
        self.spn_item_x = QDoubleSpinBox()
        self.spn_item_x.setRange(-500.0, 5000.0)
        self.spn_item_x.setSingleStep(1.0)
        self.spn_item_x.setEnabled(False)
        self.spn_item_x.valueChanged.connect(self.on_inspector_changed)
        grid.addWidget(self.spn_item_x, 1, 1)

        # Item Y Position (cm)
        grid.addWidget(QLabel("Posisi Y (cm):"), 2, 0)
        self.spn_item_y = QDoubleSpinBox()
        self.spn_item_y.setRange(-500.0, 5000.0)
        self.spn_item_y.setSingleStep(1.0)
        self.spn_item_y.setEnabled(False)
        self.spn_item_y.valueChanged.connect(self.on_inspector_changed)
        grid.addWidget(self.spn_item_y, 2, 1)

        # Item Width (cm)
        grid.addWidget(QLabel("Lebar (cm):"), 3, 0)
        self.spn_item_w = QDoubleSpinBox()
        self.spn_item_w.setRange(1.0, 1000.0)
        self.spn_item_w.setSingleStep(5.0)
        self.spn_item_w.setEnabled(False)
        self.spn_item_w.valueChanged.connect(self.on_inspector_changed)
        grid.addWidget(self.spn_item_w, 3, 1)

        # Item Height (cm)
        grid.addWidget(QLabel("Panjang/Tinggi (cm):"), 4, 0)
        self.spn_item_h = QDoubleSpinBox()
        self.spn_item_h.setRange(1.0, 1000.0)
        self.spn_item_h.setSingleStep(5.0)
        self.spn_item_h.setEnabled(False)
        self.spn_item_h.valueChanged.connect(self.on_inspector_changed)
        grid.addWidget(self.spn_item_h, 4, 1)

        # Item Rotation (deg)
        grid.addWidget(QLabel("Rotasi (°):"), 5, 0)
        self.spn_item_rot = QDoubleSpinBox()
        self.spn_item_rot.setRange(-360.0, 360.0)
        self.spn_item_rot.setSingleStep(5.0)
        self.spn_item_rot.setEnabled(False)
        self.spn_item_rot.valueChanged.connect(self.on_inspector_changed)
        grid.addWidget(self.spn_item_rot, 5, 1)

        # Quick Preset Rotation Buttons (Horizontal / Vertikal / Miring)
        rot_box = QHBoxLayout()
        rot_box.setSpacing(4)
        for angle in [0, 45, 90, 135]:
            btn_r = QPushButton(f"{angle}°")
            btn_r.setStyleSheet("padding: 4px; font-size: 11px;")
            btn_r.clicked.connect(lambda checked, a=angle: self.set_item_rotation_preset(a))
            rot_box.addWidget(btn_r)
        grid.addLayout(rot_box, 6, 0, 1, 2)

        # Delete Item Button
        self.btn_delete_item = QPushButton("🗑️ Hapus Objek")
        self.btn_delete_item.setObjectName("dangerBtn")
        self.btn_delete_item.setEnabled(False)
        self.btn_delete_item.clicked.connect(self.delete_selected_item)
        grid.addWidget(self.btn_delete_item, 7, 0, 1, 2)

        return box

    def init_statusbar(self):
        """Create bottom status bar for coordinate tracking."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.lbl_status_mouse = QLabel("Kursor: X = 0.0 cm | Y = 0.0 cm")
        self.lbl_status_grid = QLabel("1 Grid = 10.0 cm")
        self.lbl_status_scale = QLabel("Skala: 1 mm = 0.25 px")

        sep_style = "color: #30363d; font-size: 11px;"
        sep1 = QLabel("│")
        sep1.setStyleSheet(sep_style)
        sep2 = QLabel("│")
        sep2.setStyleSheet(sep_style)

        self.statusbar.addWidget(self.lbl_status_mouse)
        self.statusbar.addPermanentWidget(self.lbl_status_grid)
        self.statusbar.addPermanentWidget(sep1)
        self.statusbar.addPermanentWidget(self.lbl_status_scale)

    def init_default_items(self):
        """Initialize default field setup: Home box and Robot."""
        self.selected_item = None
        self.robot_item = None
        self.scene.clear()

        # Add Home Box (50x50 cm) at top-left start area (25, 25 cm)
        home = HomeBoxItem(x_cm=25.0, y_cm=25.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(home)
        self.scene.addItem(home)

        # Add Robot
        self.robot_item = RobotItem(
            x_cm=100.0,
            y_cm=50.0,
            diameter_cm=self.spn_robot_diam.value(),
            px_per_cm=self.scene.px_per_cm
        )
        self.connect_item_signals(self.robot_item)
        self.scene.addItem(self.robot_item)

        # Add initial sample Stand Cube
        cube = StandCubeItem(x_cm=80.0, y_cm=150.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(cube)
        self.scene.addItem(cube)

        self.update_robot_pos_label()
        self.view.fit_in_view()

    def connect_item_signals(self, item: BaseFieldItem):
        """Connect item interaction signals."""
        item.signals.itemMoved.connect(self.on_item_moved)
        item.signals.itemSelected.connect(self.on_item_selected)

    def update_pixel_conversion_labels(self):
        """Update live scale & conversion display info."""
        w_cm = self.spn_field_w.value() * 100.0
        h_cm = self.spn_field_h.value() * 100.0
        w_mm = w_cm * 10.0
        h_mm = h_cm * 10.0
        
        px_mm = self.spn_scale_px_mm.value()
        px_cm = px_mm * 10.0

        w_px = int(w_mm * px_mm)
        h_px = int(h_mm * px_mm)

        info_text = (
            f"<b>📐 Konversi Ukuran:</b><br>"
            f"• Lapangan Real: <b>{self.spn_field_w.value()}m × {self.spn_field_h.value()}m</b> ({int(w_cm)}×{int(h_cm)} cm)<br>"
            f"• Rasio Skala: <b>1 mm = {px_mm:.3f} px</b> (1 cm = {px_cm:.2f} px)<br>"
            f"• Ukuran Canvas Pixel: <b>{w_px} × {h_px} px</b><br>"
            f"• Grid: 1 kotak = <b>{self.spn_grid_cm.value()} cm</b> ({int(self.spn_grid_cm.value() * px_cm)} px)"
        )
        self.lbl_conv_summary.setText(info_text)

        if hasattr(self, 'lbl_status_scale'):
            self.lbl_status_scale.setText(f"Skala: 1 mm = {px_mm:.3f} px ({w_px}x{h_px}px)")
            self.lbl_status_grid.setText(f"1 Grid = {self.spn_grid_cm.value()} cm")

    # --- Signal Handlers & Logic ---

    def on_field_settings_changed(self):
        """Triggered when field size or scale factor changes."""
        w_m = self.spn_field_w.value()
        h_m = self.spn_field_h.value()
        px_mm = self.spn_scale_px_mm.value()
        grid_cm = self.spn_grid_cm.value()

        self.scene.update_field_dimensions(w_m, h_m, px_mm, grid_cm)
        self.update_pixel_conversion_labels()

    def on_snap_toggled(self, checked: bool):
        self.scene.snap_enabled = checked

    def on_mouse_moved(self, x_cm: float, y_cm: float):
        x_mm = x_cm * 10.0
        y_mm = y_cm * 10.0
        self.lbl_status_mouse.setText(
            f"Kursor: X = {x_cm:.1f} cm ({x_mm:.0f} mm) | Y = {y_cm:.1f} cm ({y_mm:.0f} mm)"
        )

    def on_robot_config_changed(self):
        diam = self.spn_robot_diam.value()
        if self.robot_item:
            self.robot_item.set_shape_params(diameter_cm=diam)
            self.scene.update()
            self.update_sensor_readouts_ui()

    def on_robot_rot_changed(self):
        if self.robot_item:
            self.robot_item.setRotation(self.spn_robot_rot.value())
            self.robot_item.update()
            self.update_sensor_readouts_ui()

    def choose_robot_color(self):
        if self.robot_item:
            color = QColorDialog.getColor(self.robot_item.item_color, self, "Pilih Warna Robot")
            if color.isValid():
                self.robot_item.set_shape_params(
                    diameter_cm=self.spn_robot_diam.value(),
                    color=color.name()
                )

    def on_item_moved(self, item: BaseFieldItem):
        # All objects move 100% freely without grid snapping (unconstrained free movement)
        if item == self.robot_item:
            self.update_robot_pos_label()
        
        if item == self.selected_item:
            self.update_inspector_fields(item)

        self.update_sensor_readouts_ui()

    def on_item_selected(self, item: BaseFieldItem):
        if item.isSelected():
            self.selected_item = item
            self.update_inspector_fields(item)
        else:
            if self.selected_item == item:
                self.selected_item = None
                self.clear_inspector_fields()

    def update_robot_pos_label(self):
        if self.robot_item:
            x_cm = self.robot_item.get_x_cm()
            y_cm = self.robot_item.get_y_cm()
            rot = self.robot_item.rotation()
            self.lbl_robot_pos.setText(f"Posisi: X = {x_cm:.1f} cm, Y = {y_cm:.1f} cm ({rot:.0f}°)")

    def update_inspector_fields(self, item: BaseFieldItem):
        self.lbl_insp_name.setText(f"Objek: {item.name} ({item.item_type})")

        self.spn_item_x.blockSignals(True)
        self.spn_item_y.blockSignals(True)
        self.spn_item_w.blockSignals(True)
        self.spn_item_h.blockSignals(True)
        self.spn_item_rot.blockSignals(True)

        self.spn_item_x.setValue(item.get_x_cm())
        self.spn_item_y.setValue(item.get_y_cm())
        self.spn_item_w.setValue(item.width_cm)
        self.spn_item_h.setValue(item.height_cm)
        self.spn_item_rot.setValue(item.rotation())

        self.spn_item_x.blockSignals(False)
        self.spn_item_y.blockSignals(False)
        self.spn_item_w.blockSignals(False)
        self.spn_item_h.blockSignals(False)
        self.spn_item_rot.blockSignals(False)

        self.spn_item_x.setEnabled(True)
        self.spn_item_y.setEnabled(True)
        self.spn_item_w.setEnabled(True)
        self.spn_item_h.setEnabled(True)
        self.spn_item_rot.setEnabled(True)
        self.btn_delete_item.setEnabled(item != self.robot_item)

    def clear_inspector_fields(self):
        self.lbl_insp_name.setText("Tidak ada objek dipilih")
        self.spn_item_x.setEnabled(False)
        self.spn_item_y.setEnabled(False)
        self.spn_item_w.setEnabled(False)
        self.spn_item_h.setEnabled(False)
        self.spn_item_rot.setEnabled(False)
        self.btn_delete_item.setEnabled(False)

    def on_inspector_changed(self):
        if not self.selected_item:
            return
        item = self.selected_item
        x_cm = self.spn_item_x.value()
        y_cm = self.spn_item_y.value()
        w_cm = self.spn_item_w.value()
        h_cm = self.spn_item_h.value()
        rot = self.spn_item_rot.value()

        item.set_cm_pos(x_cm, y_cm)
        item.width_cm = w_cm
        item.height_cm = h_cm
        item.setRotation(rot)
        item.prepareGeometryChange()
        item.update()

        if item == self.robot_item:
            self.spn_robot_rot.setValue(rot)
            self.update_robot_pos_label()

    def set_item_rotation_preset(self, angle: float):
        if self.selected_item:
            self.spn_item_rot.setValue(angle)

    def delete_selected_item(self):
        if self.selected_item and self.selected_item != self.robot_item:
            self.scene.removeItem(self.selected_item)
            self.selected_item = None
            self.clear_inspector_fields()

    def copy_selected_item(self):
        """Copy currently selected item data to internal clipboard (Ctrl+C)."""
        if self.selected_item and self.selected_item != self.robot_item:
            self.copied_item_data = self.selected_item.to_dict()
            self.statusbar.showMessage(f"📋 Objek '{self.selected_item.name}' disalin (Ctrl+C).", 3000)

    def paste_copied_item(self):
        """Paste copied item onto field with offset (Ctrl+V)."""
        if not self.copied_item_data:
            return

        c_data = self.copied_item_data
        o_type = c_data.get('type', '')
        x = c_data.get('x_cm', 10.0) + 10.0
        y = c_data.get('y_cm', 10.0) + 10.0
        w = c_data.get('width_cm', 30.0)
        h = c_data.get('height_cm', 30.0)
        rot = c_data.get('rotation_deg', 0.0)

        count = sum(1 for it in self.scene.items() if getattr(it, 'item_type', '') == o_type)
        name = f"{c_data.get('name', 'Item')} (Copy {count+1})"

        item = None
        if o_type == 'home_box':
            item = HomeBoxItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
        elif o_type == 'stand_cube':
            item = StandCubeItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
        elif o_type == 'wall':
            item = WallItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
        elif o_type == 'line':
            item = LineItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
        elif o_type == 'cabinet':
            item = CabinetItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)

        if item:
            item.setRotation(rot)
            self.connect_item_signals(item)
            self.scene.addItem(item)

            # Select newly pasted item
            for it in self.scene.items():
                it.setSelected(False)
            item.setSelected(True)
            self.selected_item = item
            self.update_inspector_fields(item)
            self.statusbar.showMessage(f"📋 Objek ditempel (Ctrl+V) di X={x:.1f}cm, Y={y:.1f}cm.", 3000)

    # --- Item Add Handlers ---

    def add_home_box(self):
        item = HomeBoxItem(x_cm=20.0, y_cm=20.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(item)
        self.scene.addItem(item)

    def add_stand_cube(self):
        count = sum(1 for it in self.scene.items() if getattr(it, 'item_type', '') == 'stand_cube')
        item = StandCubeItem(name=f"Stand Cube {count+1}", x_cm=50.0, y_cm=100.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(item)
        self.scene.addItem(item)

    def add_wall(self):
        count = sum(1 for it in self.scene.items() if getattr(it, 'item_type', '') == 'wall')
        item = WallItem(name=f"Tembok {count+1}", x_cm=0.0, y_cm=200.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(item)
        self.scene.addItem(item)

    def add_line(self):
        count = sum(1 for it in self.scene.items() if getattr(it, 'item_type', '') == 'line')
        item = LineItem(name=f"Garis {count+1}", x_cm=20.0, y_cm=180.0, width_cm=100.0, height_cm=2.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(item)
        self.scene.addItem(item)

    def add_cabinet(self):
        count = sum(1 for it in self.scene.items() if getattr(it, 'item_type', '') == 'cabinet')
        item = CabinetItem(name=f"Lemari {count+1}", x_cm=120.0, y_cm=250.0, width_cm=15.0, height_cm=45.0, px_per_cm=self.scene.px_per_cm)
        self.connect_item_signals(item)
        self.scene.addItem(item)

    # --- YAML Import & Export Handlers ---

    def new_map(self):
        reply = QMessageBox.question(
            self, "Reset Lapangan",
            "Apakah Anda yakin ingin mereset layout lapangan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.init_default_items()

    def build_map_data(self) -> dict:
        """Collect all map configurations into dict for export."""
        w_cm = self.spn_field_w.value() * 100.0
        h_cm = self.spn_field_h.value() * 100.0
        w_mm = w_cm * 10.0
        h_mm = h_cm * 10.0
        px_mm = self.spn_scale_px_mm.value()

        objects_list = []
        robot_data = {}

        for item in self.scene.items():
            if isinstance(item, BaseFieldItem):
                if item == self.robot_item:
                    robot_data = item.to_dict()
                else:
                    objects_list.append(item.to_dict())

        return {
            'field': {
                'width_m': round(self.spn_field_w.value(), 2),
                'height_m': round(self.spn_field_h.value(), 2),
                'width_cm': round(w_cm, 1),
                'height_cm': round(h_cm, 1),
                'width_mm': round(w_mm, 0),
                'height_mm': round(h_mm, 0),
                'scale_px_per_mm': round(px_mm, 4),
                'scale_px_per_cm': round(px_mm * 10.0, 3),
                'width_px': int(w_mm * px_mm),
                'height_px': int(h_mm * px_mm)
            },
            'grid': {
                'size_cm': round(self.spn_grid_cm.value(), 1),
                'snap_enabled': self.chk_snap.isChecked()
            },
            'robot': robot_data,
            'objects': objects_list
        }

    def export_yaml(self):
        """Export current map configuration to maps.yaml."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Simpan Map Configuration", "maps.yaml", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            data = self.build_map_data()
            try:
                export_to_yaml(file_path, data)
                QMessageBox.information(
                    self, "Sukses Simpan",
                    f"File map berhasil disimpan ke:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error Simpan", f"Gagal menyimpan YAML:\n{e}")

    def import_yaml(self):
        """Import map configuration from maps.yaml."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Buka Map Configuration", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            try:
                data = import_from_yaml(file_path)
                self.load_map_data(data)
                QMessageBox.information(
                    self, "Sukses Buka Map",
                    f"Berhasil memuat map dari:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error Memuat Map", f"Gagal membaca YAML:\n{e}")

    def load_map_data(self, data: dict):
        """Load data dict into GUI layout and scene."""
        field_cfg = data.get('field', {})
        if 'width_m' in field_cfg:
            self.spn_field_w.setValue(field_cfg['width_m'])
        if 'height_m' in field_cfg:
            self.spn_field_h.setValue(field_cfg['height_m'])
        if 'scale_px_per_mm' in field_cfg:
            self.spn_scale_px_mm.setValue(field_cfg['scale_px_per_mm'])

        grid_cfg = data.get('grid', {})
        if 'size_cm' in grid_cfg:
            self.spn_grid_cm.setValue(grid_cfg['size_cm'])
        if 'snap_enabled' in grid_cfg:
            self.chk_snap.setChecked(grid_cfg['snap_enabled'])

        # Clear existing scene & references
        self.selected_item = None
        self.robot_item = None
        self.scene.clear()

        # Load Robot
        r_cfg = data.get('robot', {})
        if r_cfg:
            self.spn_robot_diam.setValue(r_cfg.get('diameter_cm', 30.0))
            sensors_cfg = r_cfg.get('sensors', {})
            line_cfg = r_cfg.get('line_sensors', {})
            wheels_cfg = r_cfg.get('wheels', {})
            w_count = wheels_cfg.get('count', 4)
            w_diam = wheels_cfg.get('diameter_mm', 100)
            safety_m = r_cfg.get('safety_margin_cm', 5.0)

            self.robot_item = RobotItem(
                x_cm=r_cfg.get('x_cm', 100.0),
                y_cm=r_cfg.get('y_cm', 50.0),
                diameter_cm=r_cfg.get('diameter_cm', 30.0),
                safety_margin_cm=safety_m,
                px_per_cm=self.scene.px_per_cm,
                color=r_cfg.get('color', '#e74c3c'),
                sensors=sensors_cfg,
                line_sensors=line_cfg,
                wheels=wheels_cfg
            )
            self.robot_item.setRotation(r_cfg.get('rotation_deg', 0.0))
            self.connect_item_signals(self.robot_item)
            self.scene.addItem(self.robot_item)
            self.spn_robot_rot.setValue(r_cfg.get('rotation_deg', 0.0))
            self.spn_robot_safety_margin.setValue(safety_m)

            # Sync Line Sensor Checkboxes
            if hasattr(self, 'chk_line_left') and hasattr(self, 'chk_line_right'):
                self.chk_line_left.blockSignals(True)
                self.chk_line_right.blockSignals(True)
                self.chk_line_left.setChecked(bool(line_cfg.get('line_left', False)))
                self.chk_line_right.setChecked(bool(line_cfg.get('line_right', False)))
                self.chk_line_left.blockSignals(False)
                self.chk_line_right.blockSignals(False)

            # Update UI dropdowns & live readouts
            self.cb_wheel_mode.blockSignals(True)
            self.cb_wheel_mode.setCurrentIndex(0 if w_count == 4 else 1)
            self.cb_wheel_mode.blockSignals(False)

            self.cb_wheel_diam.blockSignals(True)
            self.cb_wheel_diam.setCurrentIndex(0 if w_diam == 100 else 1)
            self.cb_wheel_diam.blockSignals(False)

            self.on_sensor_pos_changed(self.cb_sensor_pos.currentIndex())
            self.update_sensor_readouts_ui()

        # Load Objects
        for obj in data.get('objects', []):
            o_type = obj.get('type', '')
            x = obj.get('x_cm', 0.0)
            y = obj.get('y_cm', 0.0)
            w = obj.get('width_cm', 30.0)
            h = obj.get('height_cm', 30.0)
            rot = obj.get('rotation_deg', 0.0)
            name = obj.get('name', '')

            item = None
            if o_type == 'home_box':
                item = HomeBoxItem(x_cm=x, y_cm=y, px_per_cm=self.scene.px_per_cm)
            elif o_type == 'stand_cube':
                item = StandCubeItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
            elif o_type == 'wall':
                item = WallItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
            elif o_type == 'line':
                item = LineItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)
            elif o_type == 'cabinet':
                item = CabinetItem(name=name, x_cm=x, y_cm=y, width_cm=w, height_cm=h, px_per_cm=self.scene.px_per_cm)

            if item:
                item.setRotation(rot)
                self.connect_item_signals(item)
                self.scene.addItem(item)

        self.update_robot_pos_label()
        self.view.fit_in_view()

    def export_image(self):
        """Export current field layout view to PNG image."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Ekspor Gambar Lapangan", "field_layout.png", "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if file_path:
            try:
                rect = self.scene.sceneRect()
                from PyQt6.QtGui import QImage, QPainter
                img = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
                img.fill(QColor("#1e1e24"))
                p = QPainter(img)
                self.scene.render(p)
                p.end()
                img.save(file_path)
                QMessageBox.information(self, "Sukses Ekspor Gambar", f"Gambar disimpan ke:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Ekspor", f"Gagal mengekspor gambar:\n{e}")
