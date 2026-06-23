# Face Filter Game TCP

Aplikasi Python sederhana dengan arsitektur client-server menggunakan socket TCP.
Server mengirim target emoji, client membaca ekspresi wajah dari webcam memakai
MediaPipe FaceMesh, lalu mengirim hasil `MATCH` atau `NO_MATCH`.

## Struktur Folder

```text
project/
├── server.py
├── client.py
├── protocol.py
├── expression_detector.py
├── emoji_manager.py
├── requirements.txt
└── assets/
    └── game_music.mp3
```

`assets/game_music.mp3` bersifat opsional. Jika file belum ada, game tetap
berjalan tanpa musik.

## Instalasi

Gunakan Python 3.12, lalu buat virtual environment:

```bash
python -m venv .venv
```

Aktifkan virtual environment di Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependency:

```bash
pip install -r requirements.txt
```

## Cara Menjalankan

Jalankan server terlebih dahulu:

```bash
python server.py
```

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
