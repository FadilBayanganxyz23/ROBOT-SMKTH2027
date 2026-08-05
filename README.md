# ROBOT-SMKTH2027 - Editor Layout Lapangan & Simulator Robot

Aplikasi GUI desktop berbasis **Python + PyQt6** untuk mendesain layout lapangan kompetisi/testing robot. Mendukung konfigurasi lapangan, objek rintangan, kalibrasi sistem roda omni, penataan 9 sensor jarak sejajar, 2 sensor garis lantai, jarak aman robot, serta simulasi interaktif real-time.

---

## ✅ Fitur Utama & Pembaruan Terkini

### ⚙️ 1. Kalibrasi Sistem Roda Omni (Omni-Wheel Drive)
- **2 Mode Omni Drive**:
  - **4 Roda Omni (4-Omni Drive)**: Terpasang di 4 sudut diagonal ($45^\circ, 135^\circ, 225^\circ, 315^\circ$).
  - **3 Roda Omni (3-Omni Drive)**: Terpasang 2 di depan (Depan-Kiri $-60^\circ$, Depan-Kanan $+60^\circ$) dan 1 di belakang ($180^\circ$).
- **2 Pilihan Diameter Roda**: **100 mm (10 cm)** atau **50 mm (5 cm)**.
- **Visualisasi High-Detail**: Velg double-layer dengan sub-roller emas, pin as metallic, dan bracket sasis motor.
- Orientasi roda otomatis tangensial terhadap pusat bodi robot dan posisinya dinamis mengikuti perubahan diameter robot.
- Tersimpan otomatis dalam node `wheels` pada file YAML.

---

### 📡 2. Konfigurasi 9 Sensor Jarak Sejajar (Parallel 9-Distance Sensors)
- **9 Posisi Mounting Presisi**:
  - **Depan (3)**: Depan Kiri, Depan Tengah, Depan Kanan (Sejajar lurus menghadap $0^\circ$).
  - **Kiri (2)**: Kiri Depan, Kiri Belakang (Sejajar lurus menghadap $-90^\circ$).
  - **Kanan (2)**: Kanan Depan, Kanan Belakang (Sejajar lurus menghadap $+90^\circ$).
  - **Belakang (2)**: Belakang Kiri, Belakang Kanan (Sejajar lurus menghadap $180^\circ$).
- **2 Tipe Sensor Jarak**:
  - 📡 **Ultrasonic (US)**: Jangkauan hingga $400\text{ cm}$ (Visual ray cyan + konus pancar).
  - 🔴 **Infrared (IR)**: Jangkauan hingga $150\text{ cm}$ (Visual ray merah + pemancar IR).
- **2D Raycasting Distance Detection**: Mengukur jarak real-time terhadap bodi Stand Cube, Lemari, Tembok, dan Batas Luar Lapangan.
- **Status Summary Grouping**: Hasil ukur jarak & target rintangan dikelompokkan rapi per sisi (Depan, Kiri, Kanan, Belakang) di UI sidebar.

---

### 📏 3. 2 Sensor Garis Lantai (Line Sensors)
- **2 Sensor Garis Opsional**: Terpasang di bagian **Depan-Tengah Robot**, tepat di bawah sensor jarak depan-tengah (`line_left` & `line_right`).
- **Deteksi Garis Lantai**:
  - Garis solatif vertikal Stand Cube ($15 \times 2\text{ cm}$).
  - 3 Garis referensi Lemari ($2 \times 15\text{ cm}$).
  - Garis manual lapangan (`LineItem`).
- **Visualisasi Real-time**:
  - 🟢 **Hijau Cerah (`#00b894`)**: Sedang mendeteksi garis di bawahnya.
  - 🔘 **Abu-abu (`#2d3436`)**: Aktif dipasang namun tidak di atas garis.
  - ⚪ **Titik Samar**: Slot kosong (tidak dipasang).
- Pilihan pasang/tidak pasang via Checkbox GUI dan tersimpan pada node `line_sensors` di YAML.

---

### 🛡️ 4. Visual Jarak Aman Robot (Safety Clearance Zone)
- Cincin oval transparan di sekeliling bodi robot dengan margin jarak aman yang dapat diatur via SpinBox GUI (default **7.0 cm**).
- **Live Warning State**:
  - 🟢 **Hijau Transparan (`Aman: 7.0cm`)**: Robot berada di zona bebas rintangan.
  - 🔴 **Merah Menyala (`⚠️ BAHAYA: 7.0cm`)**: Ring menyentuh bodi fisik rintangan atau batas luar lapangan.
- Garis solatif/referensi lantai tidak memicu peringatan bahaya ring.
- Indikator visual real-time (tidak disimpan di file YAML).

---

### 🤖 5. Bodi Robot Oval & Ekspor `robot.yaml`
- Bodi robot berbentuk **Oval / Ellipse** presisi dengan diameter yang dapat diatur.
- Indikator heading panah kuning dan titik pusat (center dot).
- Pergerakan robot bebas (*unconstrained free movement*) dan selalu dirender di layer paling atas (ZValue = 100).
- **Ekspor/Impor Standalone `robot.yaml`**: Menyimpan/memuat templat hardware robot (diameter, roda omni, 9 sensor jarak, 2 sensor garis, dan jarak aman) tanpa koordinat $X, Y$ lapangan.

---

### 🎨 6. Desain GUI Modern & Ergonomis
- **Organisasi Sidebar Kanan (5 QGroupBox)**:
  1. 🤖 *Robot Utama* (Diameter, Jarak Aman, Orientasi, Warna, Posisi Live)
  2. ⚙️ *Roda Omni* (Mode 3/4 Roda, Diameter 50/100mm)
  3. 📡 *Sensor Robot* (Dropdown Posisi, Tipe Sensor, Status Readout per Sisi)
  4. 📏 *Sensor Garis* (Checkbox Depan-Tengah Kiri/Kanan & Status Deteksi)
  5. 💾 *Simpan / Buka Robot* (Tombol Aksi YAML Robot)
  6. 📐 *Dimensi & Konversi Pixel* (Pengaturan Ukuran Lapangan & Skala)
- **Palette Objek Kiri**: Tombol berwarna dengan *accent left-border* khas tiap rintangan.
- **Enhanced Dark Theme**: Custom scrollbar tipis, QComboBox dropdown, QCheckBox, splitter handle, dan statusbar koordinat monospace.

---

### 🧱 7. Rintangan Lapangan & YAML Importer/Exporter (`maps.yaml`)
- **Home Box**: 50x50 cm (putih border hitam tebal dengan aksen inner dash line).
- **Stand Cube**: Ukuran (lebar & tinggi) dapat disesuaikan bebas, dilengkapi garis solatif vertikal di depan yang panjangnya (`tape_length_cm`) dapat diatur via Inspector.
- **Tembok (Wall)** & **Garis (Line)**: Lebar 2 cm, panjang & rotasi presisi ($0^\circ, 45^\circ, 90^\circ, 135^\circ$) via tombol preset.
- **Lemari / Cabinet**: Lebar & tinggi dapat disesuaikan bebas **tanpa garis referensi solatif**. Mendukung **Konfigurasi Tingkat/Rak Lemari (Cabinet Tiers)** serta **Penataan Objek & Spasi**:
  - Pola tata letak: `[Spasi] [Objek 1] [Spasi] [Objek 2] [Spasi]...`
  - Parameter terkonfigurasi: Jumlah Objek (`object_count`), Ukuran Objek (`object_size_cm`), dan Spasi Margin (`spacing_cm`, default $5\text{ cm}$).
  - Panjang lemari menyesuaikan otomatis dengan kebutuhan objek & spasi.
- **Export & Import `maps.yaml`**: Menyimpan seluruh susunan lapangan & spesifikasi robot **tanpa menyimpan properti warna (`color`)**, menjaga file YAML tetap bersih dan standar.

---

## ⌨️ Keyboard Shortcuts Global

| Shortcut | Aksi |
|---|---|
| `Delete` / `Backspace` | Hapus objek terpilih |
| `Ctrl + S` | Simpan layout ke `maps.yaml` |
| `Ctrl + C` | Copy objek terpilih |
| `Ctrl + V` | Paste objek hasil copy |
| `Ctrl + N` | Buat layout baru (reset) |
| `Ctrl + O` | Buka file `maps.yaml` |

---

## 📁 Struktur Folder Proyek

```
Lapangan/
├── .venv/                   ← Python virtual environment
├── core/                    ← Logika inti & graphics items
│   ├── __init__.py
│   ├── field_canvas.py      ← FieldScene & FieldView (canvas, grid, ruler, zoom)
│   └── field_items.py       ← Objek grafis (HomeBox, StandCube, Wall, Line, Cabinet, Robot)
├── gui/                     ← Antarmuka pengguna (UI)
│   ├── __init__.py
│   └── main_window.py       ← MainWindow (toolbar, sidebar palette, inspector, sensor controls)
├── io_handler/              ← Input/Output
│   ├── __init__.py
│   └── map_exporter.py      ← Parser Import & Export YAML (maps & robot)
├── Lapangan/                ← Folder penyimpanan layout peta
│   └── maps.yaml            ← File layout peta tersimpan
├── lance_tools/             ← Sub-proyek Lance Tools (Utilitas & Subsystem)
│   ├── __init__.py
│   ├── main.py              ← Launcher Lance Tools
│   └── README.md            ← Dokumentasi Lance Tools
├── Robot/                   ← Folder penyimpanan spesifikasi robot
│   └── robot.yaml           ← File templat spesifikasi hardware robot
├── tests/                   ← Unit test suite
│   ├── __init__.py
│   ├── test_app.py           ← Tes integrasi GUI
│   └── test_core.py          ← Tes ekspor & impor YAML
├── .gitignore
├── field_layout.png         ← Hasil ekspor gambar layout
├── main.py                  ← Entry point launcher aplikasi
├── maps.yaml                ← File map default
├── Prompt.txt               ← Catatan spesifikasi & prompt
├── README.md                ← Dokumentasi proyek
└── requirements.txt         ← Dependencies (PyQt6, PyYAML)
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
