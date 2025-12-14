# AbsoluteCinematic - Web Application for Cinema Ticket Booking

## Deskripsi Proyek

AbsoluteCinematic adalah aplikasi web untuk pemesanan tiket bioskop yang dibangun menggunakan Flask. Aplikasi ini dikembangkan sebagai tugas UAS mata kuliah Pemrograman Berbasis Objek (PBO) dan mendemonstrasikan implementasi konsep-konsep Object-Oriented Programming, persistensi data, autentikasi pengguna, dan alur bisnis booking tiket.

**Platform**: Web Application (Python + Flask)  
**Database**: SQLite3  
**Frontend**: Jinja2 Templates + Bootstrap 5.3.0 + Custom CSS  
**Authentication**: Session-based dengan password hashing (Werkzeug)

---

## Tujuan Pembelajaran

Aplikasi ini dirancang untuk mendemonstrasikan:

1. **Object-Oriented Programming (OOP)**

   - Enkapsulasi melalui class `User`, `Customer`, `Admin`
   - Inheritance untuk hierarki pengguna
   - Polymorphism pada class `Ticket` dan `VIPTicket`
   - Design pattern Factory (`create_ticket()`)

2. **Persistensi Data**

   - Integrasi SQLite3 sebagai database relasional
   - Query dinamis dan transaction handling
   - Skema database dengan constraints dan relationships

3. **Keamanan Aplikasi**

   - Password hashing menggunakan `werkzeug.security`
   - Session management untuk autentikasi
   - Role-based access control (RBAC) dengan decorator `@admin_required`
   - Input validation dan SQL injection prevention

4. **Alur Bisnis Aplikasi**
   - User registration & authentication flow
   - Complete booking workflow (film selection → seat selection → payment → invoice)
   - Order management dan history tracking
   - Admin dashboard untuk monitoring

---

## Struktur File Proyek

```
AbsoluteCinematic/
├── app.py                          # Flask application utama (routes, business logic, database)
├── database.db                      # SQLite database (auto-generated)
├── README.md                        # Dokumentasi proyek (file ini)
├── templates/                       # Jinja2 HTML templates
│   ├── home.html                   # Landing page dengan daftar film
│   ├── login.html                  # Halaman login
│   ├── register.html               # Halaman registrasi
│   ├── book.html                   # Halaman pemilihan film & jadwal
│   ├── payment.html                # Halaman pemilihan metode pembayaran
│   ├── invoice.html                # Halaman invoice & konfirmasi
│   ├── profile.html                # Halaman riwayat pemesanan user
│   ├── admin.html                  # Dashboard admin (statistik)
│   └── users.html                  # Halaman manajemen user untuk admin
├── static/                          # File statis
│   ├── css/
│   │   └── style.css               # Custom CSS styling
│   ├── images/                     # Folder untuk gambar (movie posters, dll)
│   └── videos/                     # Folder untuk video (hero video, dll)
└── scripts/
    └── seed_admin.py               # Script untuk membuat user admin
```

---

## Fitur Utama Aplikasi

### 1. User Management

- Registrasi Pengguna: Form registrasi dengan validasi email unik
- Login/Logout: Session-based authentication dengan password hashing
- Profile Management: Lihat data pengguna dan riwayat pemesanan
- Role-Based Access: Admin dan Customer dengan privilege berbeda

### 2. Cinema Ticket Booking

- Film Listing: Daftar film dengan poster, sinopsis, jadwal
- Seat Selection: Pilih kursi dengan visualisasi real-time
- Dynamic Pricing: Harga ticket berdasarkan tipe (Regular/VIP)
- Membership Discount: Diskon otomatis untuk member VIP
- Snack Add-on: Opsi untuk menambahkan snack ke pemesanan

### 3. Payment & Invoice

- Payment Simulation: Pilih metode pembayaran (Cash, Card, E-wallet)
- Automatic Calculation: Total harga dengan pajak dan biaya admin
- Invoice Generation: Invoice detail setelah pembayaran berhasil
- Order Storage: Semua order tersimpan di database untuk audit trail

### 4. Admin Dashboard

- Order Monitoring: Lihat semua order dan detail pelanggan
- User Management: Lihat daftar user, upgrade ke VIP
- Statistics: Dashboard dengan statistik basic (total orders, revenue)
- Access Control: Hanya admin yang bisa mengakses fitur ini

### 5. Film Management (Admin Only)

- Add New Film: Admin dapat menambahkan film baru ke dalam sistem
- Edit Film: Ubah detail film seperti judul, genre, durasi, harga, jadwal tayang
- Delete Film: Hapus film dari sistem (hanya jika belum ada pemesanan)
- Dynamic Pricing: Atur harga Regular dan VIP untuk setiap film
- Showtime Management: Kelola jadwal tayang film
- Database Integration: Film disimpan di database, bukan hardcoded

---

## Installation dan Setup

### Prerequisites

- Python 3.8 atau lebih baru
- pip package manager
- Windows PowerShell atau Command Prompt

### Langkah-Langkah Instalasi

#### 1. Clone Repository

```powershell
git clone https://github.com/MuhammadHaikhalAlHakim003/AbsoluteCinematic.git
cd AbsoluteCinematic
```

#### 2. Buat Virtual Environment (Rekomendasi)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### 3. Instal Dependencies

```powershell
pip install --upgrade pip
pip install flask werkzeug
```

Atau jika ada file requirements.txt:

```powershell
pip install -r requirements.txt
```

#### 4. Setup Database & Admin User (Opsional)

Database akan dibuat otomatis saat aplikasi pertama kali dijalankan. Untuk membuat user admin:

```powershell
python scripts/seed_admin.py --email admin@cinema.com --password admin123 --name "Admin Utama"
```

#### 5. Jalankan Aplikasi

```powershell
python app.py
```

Output yang diharapkan:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

#### 6. Akses Aplikasi di Browser

| Fitur           | URL                                      |
| --------------- | ---------------------------------------- |
| Homepage        | http://127.0.0.1:5000/                   |
| Register        | http://127.0.0.1:5000/register           |
| Login           | http://127.0.0.1:5000/login              |
| Book Ticket     | http://127.0.0.1:5000/book               |
| Payment         | http://127.0.0.1:5000/payment            |
| Invoice         | http://127.0.0.1:5000/invoice            |
| Profile         | http://127.0.0.1:5000/profile            |
| Admin Dashboard | http://127.0.0.1:5000/admin (admin only) |
| Manage Users    | http://127.0.0.1:5000/users (admin only) |

---

## Database Schema

### Tabel: users

Menyimpan data pengguna aplikasi

| Kolom      | Tipe                                | Deskripsi                           |
| ---------- | ----------------------------------- | ----------------------------------- |
| id         | INTEGER PRIMARY KEY                 | Unique identifier                   |
| name       | TEXT NOT NULL                       | Nama pengguna                       |
| email      | TEXT UNIQUE NOT NULL                | Email (unique)                      |
| password   | TEXT NOT NULL                       | Password (hashed dengan Werkzeug)   |
| membership | TEXT DEFAULT 'regular'              | Status membership: regular atau vip |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Tanggal registrasi                  |
| role       | TEXT DEFAULT 'user'                 | Role: user atau admin               |

### Tabel: movies

Menyimpan data film yang tersedia di bioskop (dapat dikelola admin)

| Kolom           | Tipe                  | Deskripsi                          |
| --------------- | --------------------- | ---------------------------------- |
| id              | INTEGER PRIMARY KEY   | Unique film ID                     |
| title           | TEXT NOT NULL         | Judul film                         |
| genre           | TEXT                  | Genre film (e.g., Action, Drama)   |
| duration        | INTEGER               | Durasi film dalam menit            |
| poster          | TEXT                  | URL poster film                    |
| showtimes       | TEXT                  | Jadwal tayang (comma-separated)    |
| regular_price   | INTEGER DEFAULT 50000 | Harga tiket regular dalam Rupiah   |
| vip_price       | INTEGER DEFAULT 75000 | Harga tiket VIP dalam Rupiah       |
| available_seats | INTEGER DEFAULT 50    | Jumlah kursi yang tersedia         |
| created_at      | TIMESTAMP             | Tanggal film ditambahkan ke sistem |
| updated_at      | TIMESTAMP             | Tanggal film terakhir di-update    |

### Tabel: orders

Menyimpan data pemesanan tiket

| Kolom          | Tipe                | Deskripsi                      |
| -------------- | ------------------- | ------------------------------ |
| id             | INTEGER PRIMARY KEY | Unique order ID                |
| movie_id       | INTEGER             | ID film yang dipesan           |
| movie_title    | TEXT                | Judul film                     |
| seat           | TEXT                | Nomor kursi (e.g., A1, B5)     |
| ticket_type    | TEXT                | Tipe tiket: regular atau vip   |
| showtime       | TEXT                | Jadwal tayang (e.g., 14:00)    |
| ticket_price   | REAL                | Harga dasar tiket              |
| admin_fee      | REAL                | Biaya admin yang ditambahkan   |
| price          | REAL                | Total harga yang dibayar       |
| membership     | TEXT                | Status membership saat membeli |
| snack_included | INTEGER (bool)      | 1 jika ada snack, 0 jika tidak |
| customer       | TEXT                | Nama customer                  |
| email          | TEXT                | Email customer                 |
| date           | TIMESTAMP           | Tanggal pemesanan              |
| payment_method | TEXT                | Metode pembayaran              |

---

## Konsep OOP yang Diimplementasikan

### 1. Class Hierarchy

```
User (base class)
├── Customer (user regular)
└── Admin (user dengan privilege admin)
```

### 2. Ticket Polymorphism

```
Ticket (base class)
├── RegularTicket (harga standard)
└── VIPTicket (harga premium + benefits)
```

### 3. Factory Pattern

```python
def create_ticket(ticket_type, price):
    if ticket_type == 'vip':
        return VIPTicket(price)
    else:
        return RegularTicket(price)
```

### 4. Encapsulation

- Attribute private dengan prefix underscore (e.g., \_password)
- Getter dan setter methods untuk controlled access

### 5. Business Logic Methods

- apply_membership_discount() - Hitung diskon berdasarkan membership
- calculate_admin_fee() - Hitung biaya admin (persentase dari total)
- validate_email() - Validasi format email sebelum simpan

---

## Security Implementation

### Password Hashing

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Generate
hashed = generate_password_hash('password123')

# Verify
check_password_hash(hashed, 'password123')  # True
```

### Session Management

- Session disimpan di memory (untuk development)
- Production: gunakan Redis atau database session store
- Cookie secure flag recommended untuk HTTPS

### Access Control

```python
@admin_required
def admin_dashboard():
    # Only accessible by users dengan role='admin'
    pass
```

### Input Validation

- Email format validation dengan regex
- SQL injection prevention dengan parameterized queries
- CSRF token dapat ditambahkan untuk production

---

## Workflow Diagram

### User Registration & Login Flow

```
User Input Email & Password
    ↓
Validate Format & Check Unique Email
    ↓
Hash Password dengan Werkzeug
    ↓
Save ke Database (users table)
    ↓
Success: Redirect to Login
```

### Booking & Payment Flow

```
Browse Films (home.html)
    ↓
Select Film & Showtime (book.html)
    ↓
Choose Seat & Ticket Type
    ↓
Select Payment Method (payment.html)
    ↓
Process Payment (simulasi - langsung sukses)
    ↓
Save Order ke Database (orders table)
    ↓
Generate Invoice (invoice.html)
    ↓
View Order History (profile.html)
```

---

## Testing dan Quality Assurance

### Manual Testing Checklist

- Registrasi dengan email valid berhasil
- Login dengan email/password benar berhasil
- Login dengan password salah ditolak
- Book tiket order tersimpan di database
- Invoice menampilkan detail lengkap
- Admin bisa lihat semua orders
- Regular user tidak bisa akses /admin
- Membership discount dihitung dengan benar
- Admin fee ditambahkan otomatis

### Automated Testing (Rekomendasi)

Untuk meningkatkan kualitas, tambahkan unit tests:

```powershell
pip install pytest
```

Contoh test file (tests/test_ticket.py):

```python
def test_regular_ticket_price():
    ticket = RegularTicket(100000)
    assert ticket.price == 100000

def test_vip_ticket_price():
    ticket = VIPTicket(100000)
    assert ticket.price == 150000  # 50% lebih mahal
```

Jalankan tests:

```powershell
pytest -v
```

---

## API Endpoints Reference

### Authentication Routes

| Method | Route     | Deskripsi                   | Auth Required |
| ------ | --------- | --------------------------- | ------------- |
| GET    | /         | Homepage dengan daftar film | Tidak         |
| GET    | /register | Tampilkan form registrasi   | Tidak         |
| POST   | /register | Submit registrasi baru      | Tidak         |
| GET    | /login    | Tampilkan form login        | Tidak         |
| POST   | /login    | Submit login                | Tidak         |
| GET    | /logout   | Logout dan clear session    | Ya            |

### User Routes

| Method | Route    | Deskripsi                        | Auth Required |
| ------ | -------- | -------------------------------- | ------------- |
| GET    | /profile | Lihat profile & order history    | Ya            |
| GET    | /book    | Halaman booking tiket            | Ya            |
| POST   | /book    | Submit booking                   | Ya            |
| GET    | /payment | Halaman pemilihan payment method | Ya            |
| POST   | /payment | Process payment                  | Ya            |
| GET    | /invoice | Tampilkan invoice order terakhir | Ya            |

### Admin Routes

| Method | Route                     | Deskripsi             | Auth Required | Admin Only |
| ------ | ------------------------- | --------------------- | ------------- | ---------- |
| GET    | /admin                    | Admin dashboard       | Ya            | Ya         |
| GET    | /users                    | Daftar semua users    | Ya            | Ya         |
| POST   | /upgrade_user             | Upgrade user ke VIP   | Ya            | Ya         |
| GET    | /admin/movies             | Daftar semua film     | Ya            | Ya         |
| GET    | /admin/movies/add         | Form tambah film baru | Ya            | Ya         |
| POST   | /admin/movies/add         | Submit film baru      | Ya            | Ya         |
| GET    | /admin/movies/edit/<id>   | Form edit film        | Ya            | Ya         |
| POST   | /admin/movies/edit/<id>   | Submit perubahan film | Ya            | Ya         |
| POST   | /admin/movies/delete/<id> | Hapus film            | Ya            | Ya         |

---

## Deployment Guide

### Option 1: Local Development (Current Setup)

`powershell
python app.py
`

### Option 2: Production Server Preparation

Untuk deploy ke production server:

1. requirements.txt - Dokumentasi semua dependencies
2. Environment Variables - Simpan config sensitif
3. WSGI Server - Gunakan Gunicorn atau Waitress

---

## File Documentation

### app.py

Main Flask application dengan database initialization, authentication, CRUD operations, dan business logic.

### templates/

Jinja2 HTML templates dengan Bootstrap 5 styling:

- home.html - Landing page dengan daftar film terbaru
- register.html - Form registrasi user baru
- login.html - Form login untuk user yang sudah terdaftar
- book.html - Interface booking (pilih film, kursi, jadwal tayang)
- payment.html - Halaman pemilihan metode pembayaran
- invoice.html - Tampilan invoice/konfirmasi order
- profile.html - Halaman profil user dengan order history
- admin.html - Dashboard admin untuk monitoring orders
- users.html - Halaman manajemen user (upgrade VIP)
- admin_movies.html - Halaman daftar film yang dapat dikelola admin
- movie_form.html - Form untuk tambah/edit film (digunakan admin)

### scripts/seed_admin.py

Utility script untuk membuat user admin awal.

---

## Cara Menggunakan Film Management Admin

### Akses Film Management

1. Login sebagai admin
2. Klik "Admin Panel" di navbar
3. Klik "Kelola Film" untuk masuk ke halaman manajemen film

### Menambah Film Baru

1. Di halaman "Kelola Film", klik tombol "Tambah Film Baru"
2. Isi form dengan data film:
   - Judul Film (wajib)
   - Genre (contoh: Action, Drama, Comedy)
   - Durasi (dalam menit, harus angka)
   - URL Poster (link gambar film)
   - Jadwal Tayang (pisahkan dengan koma, contoh: "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM")
   - Harga Regular (dalam Rupiah)
   - Harga VIP (dalam Rupiah)
3. Klik "Simpan" untuk menambahkan film

### Mengedit Film yang Sudah Ada

1. Di halaman "Kelola Film", cari film yang ingin diedit
2. Klik tombol "Edit" pada film tersebut
3. Ubah data sesuai kebutuhan
4. Klik "Simpan" untuk menyimpan perubahan

### Menghapus Film

1. Di halaman "Kelola Film", cari film yang ingin dihapus
2. Klik tombol "Hapus"
3. Konfirmasi penghapusan (tidak dapat dibatalkan)
4. Film akan dihapus dari sistem

### Catatan Penting

- Film hanya dapat dihapus jika belum memiliki pemesanan
- Harga film (regular dan VIP) akan otomatis ditampilkan saat user membooking
- Jadwal tayang yang diinput akan tampil di dropdown pemilihan showtime
- Default film dari sistem akan otomatis dimuat saat aplikasi pertama kali dijalankan

---

## Troubleshooting

### Issue: Database Lock Error

Solusi: Pastikan tidak ada instance Flask lain yang running

### Issue: Module Not Found

Solusi: Jalankan pip install flask werkzeug

### Issue: Port 5000 Already in Use

Solusi: Edit app.py dan ubah port

---

## Checklist untuk Presentasi UAS

- Aplikasi dapat dijalankan tanpa error
- Semua fitur berjalan sesuai requirement
- Admin login dan dashboard berfungsi
- User dapat register, login, booking, dan invoice
- OOP concepts jelas dalam code
- README dokumentasi lengkap
- Code clean dan well-structured
- Git history bersih
- Security best practices

---

## License dan Author

Proyek ini dibuat untuk tujuan akademis sebagai tugas UAS mata kuliah Pemrograman Berbasis Objek.

Developed by: 2024 A Kelompok 2
Institution: Universitas Negeri Surabaya
Course: Pemrograman Berbasis Objek (PBO)
Term: Semester 3, 2025

Last Updated: December 2025
Version: 1.4.1
Repository: https://github.com/MuhammadHaikhalAlHakim003/AbsoluteCinematic
