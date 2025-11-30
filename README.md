# AbsoluteCinema

AbsoluteCinema adalah aplikasi web sederhana berbasis Flask untuk pemesanan tiket bioskop. Aplikasi ini dibuat untuk kebutuhan tugas UAS mata kuliah Pemrograman Berbasis Objek dan mendemonstrasikan konsep OOP, persistensi data, autentikasi, serta alur booking sederhana.

File penting di repo:

- `app.py` — aplikasi Flask utama (routes, OOP classes, helper, DB helpers)
- `templates/` — folder template Jinja2 (home, book, login, register, profile, admin, invoice, dll.)
- `static/` — file statis (css, images, videos)
- `database.db` — SQLite database (dibuat otomatis saat pertama kali menjalankan app)
- `scripts/seed_admin.py` — script untuk membuat/mengubah user menjadi admin
- `docs/class_diagram.puml` — file PlantUML untuk class diagram (OOP)

---

## Ringkasan Fitur

- Registrasi dan login pengguna (password di-hash menggunakan Werkzeug)
- Booking tiket: pilih film, jadwal, kursi; hitung harga termasuk diskon membership dan biaya admin
- Payment (simulasi): menyimpan order ke SQLite dan menampilkan invoice
- Profile: menampilkan riwayat pemesanan pengguna
- Admin: melihat semua orders dan daftar users; meng-upgrade user menjadi VIP
- OOP: kelas `User`, `Customer`, `Admin`, `Ticket`, `VIPTicket` dan factory `create_ticket()` (polymorphism)

---

## Persiapan & Instalasi (Windows, PowerShell)

1. Buka PowerShell, pindah ke direktori proyek:

```powershell
cd "c:\Disc D\Kuliah\Kuliah Semester 3\Pemrograman Berbasis Objek\UAS\AbsoluteCinematic"
```

2. (Rekomendasi) Buat dan aktifkan virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Instal dependensi (minimal):

```powershell
pip install --upgrade pip
pip install flask werkzeug
```

Jika ada file `requirements.txt`, jalankan `pip install -r requirements.txt`.

4. (Opsional) Buat akun admin awal menggunakan seed script:

```powershell
python scripts\seed_admin.py --email admin@example.com --password secret --name "Admin Utama"
```

Script akan membuat user baru atau meng-update user yang sudah ada menjadi `role='admin'`.

5. Jalankan aplikasi:

```powershell
python app.py
```

6. Buka browser dan akses:

- Home: `http://127.0.0.1:5000/`
- Login: `http://127.0.0.1:5000/login`
- Register: `http://127.0.0.1:5000/register`
- Admin (hanya untuk admin): `http://127.0.0.1:5000/admin` atau `http://127.0.0.1:5000/users`

---

## Struktur Database (singkat)

- Tabel `users`:
  - `id, name, email, password, membership, created_at, role`
- Tabel `orders`:
  - `id, movie_id, movie_title, seat, ticket_type, showtime, ticket_price, admin_fee, price, membership, snack_included, customer, email, date, payment_method`

Catatan: skema dibuat otomatis oleh fungsi `init_db()` pada `app.py`.

---

## Keamanan & Catatan Penting

- Jangan commit `database.db` ke repository publik.
- Simpan `app.secret_key` dan credential sensitif melalui environment variables jika melakukan deploy.
- Endpoint admin dilindungi oleh decorator `admin_required`, tetapi untuk produksi sebaiknya tambahkan CSRF protection, validasi input yang lebih ketat, dan HTTPS.

---

## Untuk laporan UAS (bagian yang sebaiknya Anda sertakan)

Masukkan bagian-bagian berikut di laporan UAS Anda:

- Tujuan & ruang lingkup aplikasi
- Diagram kelas (sudah ada di `docs/class_diagram.puml`) — sertakan gambar PNG atau PlantUML
- ER Diagram (tabel `users` dan `orders`) — Anda bisa buat `docs/er_diagram.puml` atau jelaskan skema tabel
- Sequence diagram untuk alur booking → payment → invoice (`docs/sequence_diagram.puml` direkomendasikan)
- Penjelasan OOP: jelaskan kelas `User/Customer/Admin`, polymorphism pada `Ticket`/`VIPTicket`, dan factory `create_ticket()`
- Penjelasan alur: register → login → book → payment → invoice
- Pengujian: sertakan screenshot manual dari alur dan, bila ada, hasil unit tests
- Kekurangan & pengembangan lanjutan (e.g. migrasi ke PostgreSQL, menambahkan tests, memperkuat keamanan)

---

## Testing

Saat ini belum ada file test otomatis di repo. Rekomendasi untuk laporan:

- Tambahkan `tests/test_ticket.py` untuk memeriksa harga tiket (Regular vs VIP)
- Tambahkan `tests/test_discounts.py` untuk memeriksa `apply_membership_discount()`
- Jalankan dengan `pytest` setelah menginstall `pytest`:

```powershell
pip install pytest
pytest -q
```

Jika Anda mau, saya bisa membuat file test dasar dan `requirements.txt`.

---

## Deployment singkat (opsional)

Untuk selalu online tanpa menyalakan PC lokal, rekomendasi:

- Deploy ke Railway / Render / Heroku / PythonAnywhere — mudah untuk proyek Flask kecil
- Atau gunakan VPS dan systemd/NSSM untuk menjalankan aplikasi sebagai service

Contoh menjalankan dengan port berbeda:

```powershell
python app.py # default 5000
# atau ubah app.run di app.py menjadi app.run(host='0.0.0.0', port=8000)
```

---

## Known issues & TODO

- Unit tests belum ditambahkan (rekomendasi prioritas).
- Beberapa page memiliki aturan navbar yang berbeda (fixed vs non-fixed) — sudah sebagian disesuaikan.
- Admin endpoints sekarang dilindungi, tapi bisa ditingkatkan lagi (CSRF, RBAC penuh).

---

Jika Anda ingin, saya dapat:

- Menambahkan `requirements.txt` dan file test dasar (opsi: saya kerjakan sekarang),
- Membuat ER diagram dan sequence diagram di `docs/` (PlantUML),
- Membantu deploy ke layanan seperti Railway atau PythonAnywhere.

Beritahu saya opsi mana yang ingin Anda lanjutkan.

1. Aktifkan virtualenv dan jalankan seed script untuk membuat akun admin awal:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\seed_admin.py --email admin@example.com --password secret
```

2. Login dengan email `admin@example.com` dan password `secret`, lalu akses `/users` dan `/admin`.

Catatan keamanan: Ganti password default dan simpan kredensial menggunakan environment variables pada deploy.
