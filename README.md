# 💻 Financial Tracker Web (Frontend)

Client-side application berbasis web untuk Financial Tracker. Dibangun menggunakan **Python Flask** dengan desain responsif menggunakan **Bootstrap 5**.

Aplikasi ini berfungsi sebagai antarmuka (User Interface) yang mengonsumsi REST API dari Backend Java.

## 🎨 Features
- **Secure Login:** Form Login terintegrasi dengan JWT Auth Backend.
- **Dashboard:** Menampilkan total aset dan ringkasan dompet.
- **Data Visualization:** Grafik Donut Chart (Chart.js) untuk analisis pengeluaran.
- **Transaction History:** Tabel riwayat transaksi dengan indikator warna (Hijau/Merah).
- **Multi-User Friendly:** Data yang tampil dinamis sesuai user yang login.

## 🚀 Tech Stack
- **Core:** Python 3.10+
- **Web Framework:** Flask
- **Styling:** Bootstrap 5 (CDN)
- **Charting:** Chart.js (CDN)
- **HTTP Client:** Python Requests

## ⚙️ Prerequisites
1. Python 3.x terinstall.
2. Backend Java (`financial-tracker-backend`) harus sedang berjalan di port `8080`.

## 🛠️ Installation & Setup

### 1. Install Dependencies
Buka terminal di folder project ini, lalu install library yang dibutuhkan:

```bash
pip install -r requirements.txt
