# ROBOT-SMKTH2027 - Editor Layout Lapangan & Simulator Robot

Aplikasi GUI desktop berbasis **Python + PyQt6** untuk mendesain layout lapangan kompetisi/testing robot. Mendukung konfigurasi lapangan, objek rintangan, dan simulasi posisi robot secara interaktif.

---

## ✅ Fitur yang Telah Dikerjakan

### 🏟️ GUI Lapangan
- Canvas lapangan putih dengan border hitam tebal
- Grid overlay dengan ukuran grid yang dapat diatur (default 10 cm)
- Ruler/mistar sumbu X & Y dalam satuan cm
- Zoom in/out (Ctrl + Scroll) dan Fit View
- Dark mode UI modern

### 🤖 Robot
- Robot dengan bentuk polygon yang dapat dikonfigurasi (3-36 sisi)
- Diameter robot dapat diatur dalam cm
- Indikator arah heading (panah kuning)
- Robot selalu berada di atas semua objek (Z-layer tertinggi)
- Pergerakan robot tidak terikat grid (free movement)

### 📦 Stand Cube
- Ukuran 15x15 cm
- Dilengkapi garis solatif vertikal 15x2 cm di depan cube
- Dapat di-drag dan diputar bebas

### 🧱 Tembok (Wall)
- Lebar/ketebalan 2 cm, panjang dapat disesuaikan
- Rotasi bebas di berbagai derajat (0°, 45°, 90°, 135°, dll)

### 📏 Garis Lapangan
- Ukuran sama dengan tembok (lebar 2 cm, panjang adjustable)
- Rotasi bebas

### 🏠 Home Box
- Ukuran 50x50 cm
- Kotak putih dengan pinggiran hitam tebal

### 🗄️ Lemari / Cabinet
- Ukuran default 40x60 cm, dapat disesuaikan

### 💾 YAML (maps.yaml)
- Export layout lapangan ke file `maps.yaml`
- Import/load layout dari file `maps.yaml`
- Menyimpan semua konfigurasi: field, grid, robot, dan objek-objek

### ⌨️ Keyboard Shortcuts
- `Delete` / `Backspace` → Hapus objek terpilih
- `Ctrl+S` → Simpan ke maps.yaml
- `Ctrl+C` → Copy objek terpilih
- `Ctrl+V` → Paste objek
- `Ctrl+N` → Buat layout baru (reset)
- `Ctrl+O` → Buka file maps.yaml

---

## 📁 Struktur Folder

```
Lapangan/
├── main.py                  ← Entry point
├── requirements.txt         ← Dependencies (PyQt6, PyYAML)
├── maps.yaml                ← File peta tersimpan
├── core/                    ← Logika inti
│   ├── field_items.py       ← Kelas item (HomeBox, StandCube, Wall, dll)
│   └── field_canvas.py      ← FieldScene & FieldView (canvas, grid, ruler)
├── gui/                     ← Antarmuka pengguna
│   └── main_window.py       ← MainWindow (toolbar, sidebar, inspector)
├── io_handler/              ← Input/Output
│   └── map_exporter.py      ← Export & Import YAML
└── tests/                   ← Unit test
    ├── test_core.py          ← Tes YAML export/import
    └── test_app.py           ← Tes integrasi GUI
```

---

## 🚀 Cara Menjalankan

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
python main.py
```

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **PyQt6** - GUI Framework
- **PyYAML** - YAML parser
