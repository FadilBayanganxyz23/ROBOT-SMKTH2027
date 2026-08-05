# ROBOT-SMKTH2027 - Editor Layout Lapangan & Simulator Robot

Aplikasi GUI desktop berbasis **Python + PyQt6** untuk mendesain layout lapangan kompetisi/testing robot. Mendukung konfigurasi lapangan, objek rintangan, dan simulasi posisi robot secara interaktif.

---

## ✅ Fitur & Pembaruan Terkini

### 🏟️ GUI Lapangan
- Canvas permukaan lapangan putih bersih dengan border hitam tebal
- Grid overlay dengan ukuran grid yang dapat diatur (default 10 cm)
- Ruler/mistar sumbu X & Y dalam satuan cm dengan titik asal `(0,0)`
- Zoom in/out (`Ctrl` + Scroll), Panning, dan Fit View
- Dark mode UI modern

### 🤖 Robot (Default Oval)
- Robot secara default berbentuk **Oval / Ellipse** yang mulus
- Diameter robot dapat diatur dalam cm
- Indikator arah heading (panah kuning) dan titik pusat (center dot)
- Robot **selalu berada di atas semua objek** (Z-layer teratas / ZValue = 100)
- Pergerakan robot tidak terikat grid (*unconstrained free movement*)

### 📍 Peletakan Objek Bebas & Berbagai Ukuran
- Objek (Stand Cube, Lemari, Tembok, Garis, Home Box) dapat diletakkan **di mana saja** termasuk di tengah-tengah sel grid
- Posisi ($X, Y$), Ukuran ($W, H$), dan Rotasi ($0^\circ-360^\circ$) seluruh objek dapat disesuaikan secara bebas via *Inspector Panel*

### 📦 Stand Cube
- Ukuran default 15x15 cm (dapat disesuaikan)
- Dilengkapi garis solatif vertikal 15x2 cm di bagian depan cube
- Dapat di-drag dan diputar bebas

### 🧱 Tembok (Wall) & 📏 Garis Lapangan
- Lebar/ketebalan 2 cm, panjang dan rotasi dapat disesuaikan bebas
- Rotasi presisi ($0^\circ, 45^\circ, 90^\circ, 135^\circ$) via tombol preset atau spinbox

### 🏠 Home Box & 🗄️ Lemari / Cabinet
- Home Box 50x50 cm (kotak putih border hitam tebal dengan aksen inner dash line)
- Lemari / Cabinet (default 40x60 cm, dapat disesuaikan)

### 💾 YAML Importer / Exporter (`maps.yaml`)
- Export & Import layout lapangan dari/ke file `maps.yaml`
- **Tanpa menyimpan warna (`color`)**, membuat isi file YAML lebih bersih dan ringkas
- Menjaga semua konfigurasi dimensi field, grid, robot, dan objek-objek

### ⌨️ Keyboard Shortcuts Global
- `Delete` / `Backspace` → Hapus objek terpilih
- `Ctrl + S` → Simpan layout ke `maps.yaml`
- `Ctrl + C` → Copy objek terpilih
- `Ctrl + V` → Paste objek hasil copy
- `Ctrl + N` → Buat layout baru (reset)
- `Ctrl + O` → Buka file `maps.yaml`

---

## 📁 Struktur Folder Proyek

```
Lapangan/
├── main.py                  ← Entry point launcher aplikasi
├── requirements.txt         ← Dependencies (PyQt6, PyYAML)
├── maps.yaml                ← File peta tersimpan
├── core/                    ← Logika inti & graphics items
│   ├── field_items.py       ← Objek grafis (HomeBox, StandCube, Wall, Line, Cabinet, Robot)
│   └── field_canvas.py      ← FieldScene & FieldView (canvas, grid, ruler, zoom)
├── gui/                     ← Antarmuka pengguna (UI)
│   └── main_window.py       ← MainWindow (toolbar, sidebar palette, inspector)
├── io_handler/              ← Input/Output
│   └── map_exporter.py      ← Parser Import & Export YAML
└── tests/                   ← Unit test suite
    ├── test_core.py          ← Tes ekspor & impor YAML
    └── test_app.py           ← Tes integrasi GUI
```

---

## 🚀 Cara Menjalankan Aplikasi

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Jalankan aplikasi
python main.py
```

### 🧪 Menjalankan Test Suite

```bash
# Run core logic tests
python -m tests.test_core

# Run GUI integration tests
python -X utf8 -m tests.test_app
```

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **PyQt6** - GUI Framework & Graphics View System
- **PyYAML** - YAML file handler
