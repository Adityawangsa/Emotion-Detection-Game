# Real-time Face Expression Detection Game

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-green)
![OpenCV](https://img.shields.io/badge/OpenCV-Latest-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Deskripsi

Aplikasi interaktif berbasis client-server untuk mendeteksi ekspresi wajah secara real-time menggunakan teknologi MediaPipe FaceMesh. Server mengirimkan emoji target (😀 senyum, 😮 terkejut, 😐 netral), dan client menggunakan webcam untuk mendeteksi ekspresi wajah kemudian mencocokkannya dengan target dalam 60 detik per putaran.

**Cocok untuk:** Proyek pembelajaran computer vision, networking, dan pengembangan game interaktif.

---

## ✨ Fitur Utama

- ✅ **Deteksi Ekspresi Real-time** - Menggunakan MediaPipe FaceMesh untuk analisis landmark wajah
- ✅ **Arsitektur Client-Server** - Komunikasi TCP socket yang reliable
- ✅ **Tiga Tipe Ekspresi** - Senyum, Terkejut, Netral
- ✅ **Game Mode 60 Detik** - Putaran permainan dengan penghitungan skor otomatis
- ✅ **Musik Latar** - Dukungan audio Pygame (opsional)
- ✅ **Protocol Berbasis Baris** - Implementasi protocol custom yang sederhana namun robust

---

## 🛠️ Tech Stack

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| Python | 3.12+ | Bahasa utama |
| MediaPipe | 0.10.14 | Deteksi face mesh landmark |
| OpenCV | Latest | Pemrosesan video real-time |
| Pygame | Latest | Audio & multimedia |
| Socket TCP | Native | Komunikasi jaringan |

---

## 📁 Struktur Folder

```
face-expression-game/
├── server.py                   # Server yang mengirim target emoji
├── client.py                   # Client yang mendeteksi ekspresi
├── protocol.py                 # Protokol komunikasi TCP
├── expression_detector.py      # Module deteksi ekspresi wajah
├── emoji_manager.py            # Manager untuk emoji & ekspresi
├── requirements.txt            # Dependency project
├── README.md                   # Dokumentasi ini
└── assets/
    └── game_music.mp3          # File musik (opsional)
```

> **Catatan:** File `assets/game_music.mp3` bersifat opsional. Game tetap berjalan normal tanpa musik.

---

## 🚀 Instalasi & Setup

### Prasyarat
- Python 3.12 atau lebih baru
- Webcam/Camera yang berfungsi
- Virtual environment (recommended)

### Langkah Instalasi

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/face-expression-game.git
cd face-expression-game
```

#### 2. Buat Virtual Environment
```bash
python -m venv .venv
```

#### 3. Aktifkan Virtual Environment

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🎮 Cara Menjalankan

### 1. Jalankan Server (Terminal 1)
```bash
python server.py
```

Output yang diharapkan:
```
Server berjalan di 127.0.0.1:5050
Menunggu client terhubung...
```

### 2. Jalankan Client (Terminal 2)
```bash
python client.py
```

Output yang diharapkan:
```
Terhubung ke server di 127.0.0.1:5050
Memulai permainan... Target: 😀
```

### 3. Mainkan Game
- Hadapkan wajah ke webcam
- Cocokkan ekspresi wajah Anda dengan emoji target
- Sistem akan mendeteksi dan mengirim `MATCH` atau `NO_MATCH` ke server
- Lanjutkan hingga waktu 60 detik habis

---

## 📊 Cara Kerja Sistem

```
┌─────────────────┐
│    Server       │
│  - Kirim target │
│  - Hitung skor  │
└────────┬────────┘
         │ TCP Socket
         │
┌────────▼────────────────────┐
│      Client                 │
│  1. Capture webcam         │
│  2. Deteksi ekspresi       │
│  3. Cocokkan dengan target │
│  4. Kirim hasil MATCH/NO   │
└─────────────────────────────┘
```

### Flow Protocol
```
Client → Server: START
Server → Client: TARGET|😀
Client → Client: Deteksi ekspresi
Client → Server: RESULT|MATCH/NO_MATCH
Server → Client: TARGET|😮
... (loop selama 60 detik)
Server → Client: GAME_END|score
```

---

## ⚙️ Konfigurasi

Edit parameter di `protocol.py` untuk customize game:

```python
HOST = "127.0.0.1"                    # Alamat server
PORT = 5050                            # Port koneksi
GAME_DURATION_SECONDS = 60             # Durasi permainan
NEXT_TARGET_DELAY_SECONDS = 1.0        # Delay antar target
```

---

## 🐛 Troubleshooting

| Problem | Solusi |
|---------|--------|
| **"No module named mediapipe"** | Run: `pip install -r requirements.txt` |
| **Client tidak bisa connect** | Pastikan server sudah running terlebih dahulu |
| **Webcam tidak terdeteksi** | Cek permission webcam & coba camera lain |
| **Ekspresi tidak terdeteksi** | Perbaiki pencahayaan, dekatkan wajah ke kamera |
| **Error audio** | Hapus file musik atau install pygame: `pip install pygame` |

---

## 📝 Protokol Komunikasi

Format message: `COMMAND|value_1|value_2\n`

**Contoh:**
```
START\n
TARGET|😀\n
RESULT|MATCH\n
GAME_END|8\n
```

Untuk detail lengkap, lihat `protocol.py`

---

## 🔄 Dependencies

```
opencv-python          # Pemrosesan video
mediapipe==0.10.14     # Face mesh detection
pygame                 # Audio & multimedia
```

Install semua dengan:
```bash
pip install -r requirements.txt
```

---

## 📌 Catatan Penting

- **Privasi:** Project ini berjalan lokal (`127.0.0.1`). Data video tidak disimpan atau dikirim ke server eksternal
- **Performance:** Untuk webcam berkualitas rendah, tingkatkan toleransi threshold di `expression_detector.py`
- **Multi-player:** Saat ini hanya support single client. Untuk multi-player, perlu refactor server

---

## 🎓 Use Cases

✅ Proyek pembelajaran Computer Vision  
✅ Demonstrasi TCP Socket Programming  
✅ Game interaktif berbasis gesture  
✅ Educational AI/ML project  
✅ Research facial expression recognition  

---

## 📄 License

Proyek ini menggunakan lisensi **MIT**. Silakan gunakan, modifikasi, dan distribusikan dengan menyertakan attribution.

---

## 👨‍💻 Author

**Aditya Wangsa**  
Emotional Detection Project v1

---

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:
1. Fork repository
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

---

## 📧 Kontak & Support

Untuk pertanyaan atau saran, silakan buka GitHub Issues atau hubungi maintainer.

---

**Last Updated:** June 2026

Lalu buka terminal kedua dan jalankan client:

```bash
python client.py
```

Setelah client terhubung, tekan tombol `START GAME` di server.

## Cara Kerja Singkat

1. Server menunggu koneksi client di `127.0.0.1:5050`.
2. Server memilih emoji target secara acak: 😀, 😮, atau 😐.
3. Client membuka webcam ketika menerima `START_GAME`.
4. Client mendeteksi ekspresi dari rasio landmark mulut:
   - `smile`: mulut melebar.
   - `surprise`: mulut terbuka besar.
   - `neutral`: ekspresi normal.
5. Jika ekspresi cocok, client mengirim `MATCH`.
6. Server menambah skor, memilih emoji baru, lalu mengirim target baru.
7. Game berakhir otomatis setelah 40 detik.

## Catatan Belajar

Project ini memperkenalkan beberapa konsep penting:

- TCP adalah stream, jadi pesan perlu delimiter seperti newline.
- GUI tidak boleh diblokir oleh socket atau kamera, sehingga proses jaringan
  berjalan di thread terpisah.
- Deteksi ekspresi sederhana bisa dibuat dari geometri landmark wajah tanpa
  model AI tambahan.
- State game sebaiknya dimiliki server agar skor lebih konsisten.
