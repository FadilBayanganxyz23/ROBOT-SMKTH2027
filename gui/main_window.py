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
from io_handler.map_exporter import export_to_yaml, import_from_yaml


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
        """Apply modern dark-theme stylesheet."""
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
        QGroupBox {
            font-weight: bold;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 12px;
            background-color: #161b22;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: #58a6ff;
        }
        QPushButton {
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 5px;
            padding: 6px 12px;
            color: #c9d1d9;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #30363d;
            border-color: #8b949e;
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
        }
        QPushButton#dangerBtn {
            background-color: #da3633;
            border-color: #f85149;
            color: #ffffff;
        }
        QPushButton#dangerBtn:hover {
            background-color: #f85149;
        }
        QDoubleSpinBox, QSpinBox, QComboBox {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 4px 8px;
            color: #c9d1d9;
        }
        QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
            border-color: #58a6ff;
        }
        QLabel {
            color: #8b949e;
        }
        QLabel#highlightVal {
            color: #58a6ff;
            font-weight: bold;
        }
        QToolBar {
            background-color: #161b22;
            border-bottom: 1px solid #30363d;
            spacing: 6px;
            padding: 4px;
        }
        QStatusBar {
            background-color: #161b22;
            border-top: 1px solid #30363d;
            color: #8b949e;
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
        right_layout.setSpacing(10)

        right_layout.addWidget(self.build_robot_config_box())
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
        layout.setSpacing(8)

        # Add Home Box (50x50 cm)
        btn_home = QPushButton("🟢 Home Box (50x50 cm)")
        btn_home.setStyleSheet("text-align: left; padding: 8px;")
        btn_home.clicked.connect(self.add_home_box)
        layout.addWidget(btn_home)

        # Add Stand Cube (15x15 cm with 15x2 cm vertical solatif line)
        btn_cube = QPushButton("🟧 Stand Cube (15x15 cm)")
        btn_cube.setStyleSheet("text-align: left; padding: 8px;")
        btn_cube.clicked.connect(self.add_stand_cube)
        layout.addWidget(btn_cube)

        # Add Wall / Tembok (Lebar 2cm, Rotasi & Panjang dapat disesuaikan)
        btn_wall = QPushButton("🧱 Tembok (Lebar 2 cm)")
        btn_wall.setStyleSheet("text-align: left; padding: 8px;")
        btn_wall.clicked.connect(self.add_wall)
        layout.addWidget(btn_wall)

        # Add Line / Garis (Lebar 2cm, Rotasi & Panjang dapat disesuaikan)
        btn_line = QPushButton("📏 Garis (Lebar 2 cm)")
        btn_line.setStyleSheet("text-align: left; padding: 8px;")
        btn_line.clicked.connect(self.add_line)
        layout.addWidget(btn_line)

        # Add Cabinet / Lemari (15x45 cm)
        btn_cabinet = QPushButton("🗄️ Lemari (15x45 cm)")
        btn_cabinet.setStyleSheet("text-align: left; padding: 8px;")
        btn_cabinet.clicked.connect(self.add_cabinet)
        layout.addWidget(btn_cabinet)

        layout.addSpacing(10)
        lbl_hint = QLabel("💡 Petunjuk:\nKlik tombol di atas untuk membuat objek baru. Objek dapat di-drag & diputar di lapangan.")
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #8b949e; font-size: 11px; font-style: italic;")
        layout.addWidget(lbl_hint)

        return box

    def build_field_settings_box(self) -> QGroupBox:
        """Create Field dimensions & pixel conversion scale panel."""
        box = QGroupBox("⚙️ Dimensi & Konversi Pixel")
        grid = QGridLayout(box)
        grid.setSpacing(8)

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

    def build_robot_config_box(self) -> QGroupBox:
        """Create Robot diameter & orientation configuration panel (Default Oval Robot)."""
        box = QGroupBox("🤖 Konfigurasi Robot (Default Oval)")
        grid = QGridLayout(box)
        grid.setSpacing(8)

        # Robot Diameter (cm)
        grid.addWidget(QLabel("Diameter Robot (cm):"), 0, 0)
        self.spn_robot_diam = QDoubleSpinBox()
        self.spn_robot_diam.setRange(5.0, 200.0)
        self.spn_robot_diam.setSingleStep(5.0)
        self.spn_robot_diam.setValue(30.0)
        self.spn_robot_diam.valueChanged.connect(self.on_robot_config_changed)
        grid.addWidget(self.spn_robot_diam, 0, 1)

        # Robot Orientation Angle (deg)
        grid.addWidget(QLabel("Sudut Orientasi (°):"), 1, 0)
        self.spn_robot_rot = QDoubleSpinBox()
        self.spn_robot_rot.setRange(0.0, 360.0)
        self.spn_robot_rot.setSingleStep(5.0)
        self.spn_robot_rot.setValue(0.0)
        self.spn_robot_rot.valueChanged.connect(self.on_robot_rot_changed)
        grid.addWidget(self.spn_robot_rot, 1, 1)

        # Robot Color Button
        grid.addWidget(QLabel("Warna Robot:"), 2, 0)
        self.btn_robot_color = QPushButton("🎨 Pilih Warna")
        self.btn_robot_color.clicked.connect(self.choose_robot_color)
        grid.addWidget(self.btn_robot_color, 2, 1)

        # Robot Live Position Readout
        self.lbl_robot_pos = QLabel("Posisi: X = 100 cm, Y = 50 cm")
        self.lbl_robot_pos.setObjectName("highlightVal")
        grid.addWidget(self.lbl_robot_pos, 3, 0, 1, 2)

        # --- Simplified 9 Sensor Configuration Panel ---
        lbl_sensors_title = QLabel("📡 Konfigurasi Sensor Robot:")
        lbl_sensors_title.setStyleSheet("font-weight: bold; color: #58a6ff; margin-top: 8px;")
        grid.addWidget(lbl_sensors_title, 4, 0, 1, 2)

        # Dropdown 1: Select Sensor Position
        grid.addWidget(QLabel("Pilih Posisi Sensor:"), 5, 0)
        self.cb_sensor_pos = QComboBox()
        self.sensor_pos_keys = [
            ('front_left', '📍 Depan Kiri'),
            ('front_center', '📍 Depan Tengah'),
            ('front_right', '📍 Depan Kanan'),
            ('left_front', '📍 Kiri Depan'),
            ('left_rear', '📍 Kiri Belakang'),
            ('back_left', '📍 Belakang Kiri'),
            ('back_right', '📍 Belakang Kanan'),
            ('right_rear', '📍 Kanan Belakang'),
            ('right_front', '📍 Kanan Depan')
        ]
        for key, label_str in self.sensor_pos_keys:
            self.cb_sensor_pos.addItem(label_str, userData=key)
        self.cb_sensor_pos.currentIndexChanged.connect(self.on_sensor_pos_changed)
        grid.addWidget(self.cb_sensor_pos, 5, 1)

        # Dropdown 2: Select Installed Sensor Type
        grid.addWidget(QLabel("Pasang Sensor:"), 6, 0)
        self.cb_sensor_type = QComboBox()
        self.cb_sensor_type.addItems([
            "❌ Tidak Dipasang",
            "📡 Ultrasonic (US)",
            "🔴 Infrared (IR)"
        ])
        self.cb_sensor_type.currentIndexChanged.connect(self.on_sensor_type_changed)
        grid.addWidget(self.cb_sensor_type, 6, 1)

        # Live Sensor Status & Readout Summary
        lbl_summary_title = QLabel("📊 Status & Hasil Ukur Sensor:")
        lbl_summary_title.setStyleSheet("font-weight: bold; color: #58a6ff; margin-top: 8px;")
        grid.addWidget(lbl_summary_title, 7, 0, 1, 2)

        self.sensor_summary_labels = {}
        row = 8
        st_layout = QVBoxLayout()
        st_layout.setSpacing(3)

        for key, label_str in self.sensor_pos_keys:
            lbl = QLabel(f"{label_str}: Nonaktif")
            lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            st_layout.addWidget(lbl)
            self.sensor_summary_labels[key] = (label_str, lbl)

        grid.addLayout(st_layout, 8, 0, 1, 2)

        return box

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
        """Update live sensor distance readouts in sidebar panel."""
        if not hasattr(self, 'robot_item') or not self.robot_item:
            return
        readouts = self.robot_item.get_sensor_readouts()
        for pos_key, (name_str, lbl) in self.sensor_summary_labels.items():
            info = readouts.get(pos_key, {})
            stype = info.get('type', 'none')
            if stype == 'none':
                lbl.setText(f"{name_str}: Nonaktif")
                lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            else:
                dist = info.get('distance_cm', 0.0)
                target = info.get('target_name', 'Batas')
                icon = "📡 US" if stype == 'ultrasonic' else "🔴 IR"
                color_code = "#00cec9" if stype == 'ultrasonic' else "#ff4757"
                lbl.setText(f"{name_str} [{icon}]: <b>{dist:.1f} cm</b> ({target})")
                lbl.setStyleSheet(f"color: {color_code}; font-size: 11px;")

    def build_inspector_box(self) -> QGroupBox:
        """Create Selected Item Property Inspector panel."""
        box = QGroupBox("🔍 Inspektur Objek Terpilih")
        grid = QGridLayout(box)
        grid.setSpacing(8)

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

        self.lbl_status_mouse = QLabel("Kursor: X = 0.0 cm, Y = 0.0 cm")
        self.lbl_status_grid = QLabel("1 Grid = 10.0 cm")
        self.lbl_status_scale = QLabel("Skala: 1 mm = 0.25 px")

        self.statusbar.addPermanentWidget(self.lbl_status_grid)
        self.statusbar.addPermanentWidget(QLabel(" | "))
        self.statusbar.addPermanentWidget(self.lbl_status_scale)
        self.statusbar.addPermanentWidget(QLabel(" | "))
        self.statusbar.addWidget(self.lbl_status_mouse)

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
            self.robot_item = RobotItem(
                x_cm=r_cfg.get('x_cm', 100.0),
                y_cm=r_cfg.get('y_cm', 50.0),
                diameter_cm=r_cfg.get('diameter_cm', 30.0),
                px_per_cm=self.scene.px_per_cm,
                color=r_cfg.get('color', '#e74c3c'),
                sensors=sensors_cfg
            )
            self.robot_item.setRotation(r_cfg.get('rotation_deg', 0.0))
            self.connect_item_signals(self.robot_item)
            self.scene.addItem(self.robot_item)
            self.spn_robot_rot.setValue(r_cfg.get('rotation_deg', 0.0))

            # Update UI dropdown & live readouts
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
