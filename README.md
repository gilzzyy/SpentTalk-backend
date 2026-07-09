# SpendTalk Backend

SpendTalk adalah platform manajemen keuangan personal berbasis web yang menggunakan chatbot bertenaga AI (Google Gemini API) untuk pencatatan transaksi secara natural. Backend ini dikembangkan menggunakan **FastAPI** dengan database **MySQL** dan berorientasi pada prinsip **Pemrograman Berorientasi Objek (PBO)**.

## Fitur Utama

1. **Autentikasi Pengguna**: Registrasi & Login (Password hashing bcrypt).
2. **Onboarding Keuangan**: Menentukan saldo awal, penghasilan bulanan, dan budget per kategori.
3. **Chatbot AI Parsing**: Menerima input natural language, diekstrak oleh Google Gemini API ke dalam data transaksi terstruktur.
4. **Dashboard Keuangan**: Saldo real-time, progress bar budget kategori, dan riwayat transaksi terakhir.
5. **Budget Tracker**: Manajemen budget dinamis (tambah, edit, hapus kategori & nominal budget).
6. **Ekspor Excel**: Laporan transaksi format `.xlsx` menggunakan openpyxl.

## Struktur Project & Prinsip OOP

Backend ini didesain menggunakan arsitektur berlapis yang mengedepankan prinsip OOP:

- **Encapsulation**: Atribut model dienkapsulasi menggunakan property decorator. Class Entity mengisolasi data dan perilakunya sendiri.
- **Inheritance**: Subclass `IncomeTransaction` dan `ExpenseTransaction` mewarisi properti dari parent class `Transaction`.
- **Polymorphic / Dynamic Behavior**: Penghitungan nilai nominal transaksi ter-signed berdasarkan tipe transaksi.
- **Abstraction**: Menggunakan Abstract Base Class (`abc.ABC`) di layer repository untuk decoupling business logic dengan ORM Database (SQLAlchemy).

## Cara Menjalankan Project

### 1. Prasyarat
- Python 3.9+
- MySQL Server

### 2. Setup Lingkungan (Environment)
1. Salin `.env.example` menjadi `.env`:
   ```bash
   cp .env.example .env
   ```
2. Sesuaikan konfigurasi di dalam file `.env` (Database URL, Secret Key, dan Gemini API Key).

### 3. Instalasi Dependensi
Buat virtual environment dan install paket yang dibutuhkan:
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 4. Menjalankan Server
Jalankan server menggunakan uvicorn:
```bash
uvicorn app.main:app --reload
```
Akses dokumentasi API interaktif Swagger UI di: [http://localhost:8000/docs](http://localhost:8000/docs)
