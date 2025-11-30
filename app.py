from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Diperlukan untuk menggunakan session

# Database file
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            membership TEXT NOT NULL DEFAULT 'member',
            created_at TEXT
        )
        '''
    )
    # Ensure 'role' column exists for admin/user roles
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    if 'role' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except Exception:
            pass
    # orders table
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            movie_title TEXT,
            seat TEXT,
            ticket_type TEXT,
            showtime TEXT,
            ticket_price INTEGER,
            admin_fee INTEGER,
            price INTEGER,
            membership TEXT,
            snack_included INTEGER DEFAULT 0,
            customer TEXT,
            email TEXT,
            date TEXT,
            payment_method TEXT
        )
        '''
    )
    conn.commit()
    conn.close()


def create_user(name, email, password, membership='member'):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed = generate_password_hash(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        cur.execute("INSERT INTO users (name, email, password, membership, created_at, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, email, hashed, membership, now, 'user'))
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return None
    conn.close()
    return get_user_by_id(user_id)


def get_user_by_email(email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def save_order_db(order):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO orders (movie_id, movie_title, seat, ticket_type, showtime, ticket_price, admin_fee, price, membership, snack_included, customer, email, date, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order.get('movie_id'),
            order.get('movie_title'),
            order.get('seat'),
            order.get('ticket_type'),
            order.get('showtime'),
            order.get('ticket_price'),
            order.get('admin_fee'),
            order.get('price'),
            order.get('membership'),
            1 if order.get('snack_included') else 0,
            order.get('customer'),
            order.get('email'),
            order.get('date'),
            order.get('payment_method', '')
        )
    )
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return oid


def get_all_orders_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_orders_by_user_email(email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE email = ? ORDER BY id DESC", (email,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_booked_seats_db(movie_id, showtime, ticket_type):
    conn = get_db_connection()
    cur = conn.cursor()
    # Select seats from orders that match movie_id and showtime; ticket_type optional
    if ticket_type:
        cur.execute("SELECT seat FROM orders WHERE movie_id = ? AND showtime = ? AND ticket_type = ?", (movie_id, showtime, ticket_type))
    else:
        cur.execute("SELECT seat FROM orders WHERE movie_id = ? AND showtime = ?", (movie_id, showtime))
    rows = cur.fetchall()
    conn.close()
    seats = []
    for r in rows:
        s = r['seat'] or ''
        for part in s.split(','):
            p = part.strip()
            if p and p not in seats:
                seats.append(p)
    return seats


def apply_membership_discount(price, membership):
    """Return price after applying membership discount (member=2%, vip=5%)."""
    if membership == 'member':
        return int(price * 0.98)
    if membership == 'vip':
        return int(price * 0.95)
    return price


# HELPER FUNCTION
def generate_seats(rows=14, seats_per_row=20):
    """Generate seat list from A1-A20, B1-B20, ..., N1-N20"""
    seat_rows = [chr(65 + i) for i in range(rows)]  # A to N (14 rows)
    seats = []
    for row in seat_rows:
        for seat_num in range(1, seats_per_row + 1):
            seats.append(f"{row}{seat_num}")
    return seats

def format_currency(value):
    """Format number with thousand separator (dot)"""
    try:
        return "{:,.0f}".format(int(value)).replace(",", ".")
    except:
        return str(value)

# Register filter
app.jinja_env.filters['format_currency'] = format_currency


# --- Authorization helpers ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get('user')
        if not user:
            flash('Silakan login terlebih dulu')
            return redirect(url_for('login'))
        # check role from session; fallback to DB lookup
        if user.get('role') == 'admin':
            return f(*args, **kwargs)
        # try retrieving fresh role from DB
        db_user = get_user_by_id(user.get('id'))
        if db_user and 'role' in db_user.keys() and db_user['role'] == 'admin':
            # refresh session role
            session['user']['role'] = 'admin'
            return f(*args, **kwargs)
        flash('Akses ditolak: hanya admin yang dapat mengakses halaman ini')
        return redirect(url_for('home'))
    return decorated


# DATA FILM (STATIC)
movies = [
    {
        "id": 1,
        "title": "Avengers: Doomsday",
        "genre": "Action / Superhero",
        "duration": 165,
        "seats": generate_seats(),
        "poster": "https://posterspy.com/wp-content/uploads/2024/10/Doomsday-by-VISCOM.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 2,
        "title": "Superman: Legacy",
        "genre": "Action / Superhero",
        "duration": 145,
        "seats": generate_seats(),
        "poster": "https://posterspy.com/wp-content/uploads/2023/11/20231130_142631_0-glazed-intensity-10-V1.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 3,
        "title": "Spider-Man: No Way Home",
        "genre": "Action / Sci-Fi",
        "duration": 135,
        "seats": generate_seats(),
        "poster": "https://cdn.marvel.com/content/2x/spider-mannowayhome_lob_crd_03.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 4,
        "title": "Batman: The Brave and The Bold",
        "genre": "Action / Crime",
        "duration": 150,
        "seats": generate_seats(),
        "poster": "https://i.pinimg.com/736x/c4/8b/ed/c48bedde3a9cb8b745a71369627a5005.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 5,
        "title": "Avatar 3",
        "genre": "Sci-Fi / Adventure",
        "duration": 170,
        "seats": generate_seats(),
        "poster": "https://m.media-amazon.com/images/M/MV5BZDYxY2I1OGMtN2Y4MS00ZmU1LTgyNDAtODA0MzAyYjI0N2Y2XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 6,
        "title": "How to Train Your Dragon: Live-Action",
        "genre": "Adventure / Fantasy",
        "duration": 140,
        "seats": generate_seats(),
        "poster": "https://m.media-amazon.com/images/M/MV5BODA5Y2M0NjctNWQzMy00ODRhLWE0MzUtYmE1YTAzZjYyYmQyXkEyXkFqcGc@._V1_.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 7,
        "title": "Frozen 2",
        "genre": "Animation / Family",
        "duration": 120,
        "seats": generate_seats(),
        "poster": "https://myhotposters.com/cdn/shop/products/mL3767_grande.jpg?v=1748534166",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 8,
        "title": "Inside Out 2",
        "genre": "Animation / Family",
        "duration": 110,
        "seats": generate_seats(),
        "poster": "https://upload.wikimedia.org/wikipedia/id/thumb/9/9f/Inside_Out_2_Poster_Indonesian.webp/1000px-Inside_Out_2_Poster_Indonesian.webp.png",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 9,
        "title": "Mission Impossible: Reckoning Part 2",
        "genre": "Action / Thriller",
        "duration": 160,
        "seats": generate_seats(),
        "poster": "https://posterspy.com/wp-content/uploads/2023/06/M.I7v4-1.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 10,
        "title": "Mufasa: The Lion King",
        "genre": "Drama / Family",
        "duration": 130,
        "seats": generate_seats(),
        "poster": "https://www.laughingplace.com/uploads/ddimages/2024/12/06/7-new-posters-released-for-mufasa-the-lion-king-including-imax-dolby-4dx-and-other-special-formats.jpeg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 11,
        "title": "Sonic the Hedgehog 3",
        "genre": "Action / Comedy",
        "duration": 120,
        "seats": generate_seats(),
        "poster": "https://i0.wp.com/mynintendonews.com/wp-content/uploads/2024/11/sonic_movie_3-poster.jpeg?resize=691%2C1024&ssl=1",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    },
    {
        "id": 12,
        "title": "Deadpool & Wolverine",
        "genre": "Action / Comedy",
        "duration": 130,
        "seats": generate_seats(),
        "poster": "https://cdn.marvel.com/content/2x/dp3_1sht_digital_srgb_ka_swords_v5_resized.jpg",
        "showtimes": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM", "10:00 PM"]
    }
]


orders = []  # tempat penyimpanan sementara


# OOP CLASSES
class User:
    def __init__(self, name, email):
        self.__name = name
        self.__email = email

    def get_name(self):
        return self.__name

    def get_email(self):
        return self.__email


class Customer(User):
    def __init__(self, name, email):
        super().__init__(name, email)
        self.history = []

    def book_ticket(self, movie_id, seat, ticket_type):
        ticket = create_ticket(ticket_type, seat)
        price = ticket.calculate_price()

        # ambil judul film untuk disimpan di order
        movie_title = next((m['title'] for m in movies if m['id'] == movie_id), "")

        order = {
            "id": len(orders) + 1,
            "movie_id": movie_id,
            "movie_title": movie_title,
            "seat": seat,
            "ticket_type": ticket_type,
            "price": price,
            "customer": self.get_name(),
            "email": self.get_email(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        self.history.append(order)
        orders.append(order)
        return order


class Admin(User):
    def view_all_orders(self):
        return orders


class Ticket:
    def __init__(self, seat, ticket_type):
        self.seat = seat
        self.ticket_type = ticket_type

    def calculate_price(self):
        return 75000 if self.ticket_type == "VIP" else 50000


class VIPTicket(Ticket):
    def calculate_price(self):
        return 75000


def create_ticket(ticket_type, seat):
    """Factory to create appropriate Ticket subclass based on ticket_type.

    Polymorphism: VIP seat type has its own subclass; membership discounts are
    applied during booking (guest/member/vip).
    """
    if not ticket_type:
        return Ticket(seat, "Regular")

    t = ticket_type.strip().lower()
    if t == "vip":
        return VIPTicket(seat, "VIP")
    return Ticket(seat, "Regular")



# ROUTES
@app.route('/')
def home():
    return render_template('home.html', movies=movies)


@app.route('/book/<int:movie_id>', methods=['GET', 'POST'])
def book(movie_id):
    movie = next((m for m in movies if m['id'] == movie_id), None)

    if not movie:
        return "Movie not found", 404

    if request.method == 'POST':
        # If user logged in, use their account info; otherwise use form inputs
        user = session.get('user')
        if user:
            name = user.get('name')
            email = user.get('email')
            membership = user.get('membership', 'member')
        else:
            name = request.form['name']
            email = request.form['email']
            membership = 'guest'

        seats_input = request.form['seat'].strip()
        ticket_type = request.form['ticket_type']
        showtime = request.form.get('showtime', '')  # Get showtime from form

        # Parse multiple seats (separated by comma and space)
        seat_list = [s.strip() for s in seats_input.split(',') if s.strip()]

        if not seat_list:
            error = "Pilih minimal satu kursi!"
            # Build booked_seats_by_showtime for error case
            booked_seats_by_showtime = {}
            for st in movie['showtimes']:
                booked_seats_by_showtime[st] = {"Regular": [], "VIP": []}
                for order in orders:
                    if order['movie_id'] == movie_id and order['showtime'] == st:
                        ticket_type = order.get('ticket_type', 'Regular')
                        seats = [s.strip() for s in order['seat'].split(',')]
                        for seat in seats:
                            if seat not in booked_seats_by_showtime[st][ticket_type]:
                                booked_seats_by_showtime[st][ticket_type].append(seat)
            return render_template("book.html", movie=movie, error=error, booked_seats_by_showtime=booked_seats_by_showtime)

        # ====== VALIDASI SEAT SUDAH DIPESAN (menggunakan DB) ======
        booked_seats = get_booked_seats_db(movie_id, showtime, ticket_type)
        unavailable_seats = [seat for seat in seat_list if seat in booked_seats]

        if unavailable_seats:
            error = f"Kursi {', '.join(unavailable_seats)} sudah dipesan!"
            # Build booked_seats_by_showtime for error case using DB
            booked_seats_by_showtime = {}
            for st in movie['showtimes']:
                booked_seats_by_showtime[st] = {"Regular": [], "VIP": []}
                for ttype in ["Regular", "VIP"]:
                    seats = get_booked_seats_db(movie_id, st, ttype)
                    booked_seats_by_showtime[st][ttype] = seats
            return render_template("book.html", movie=movie, error=error, booked_seats_by_showtime=booked_seats_by_showtime)

        # Create customer and book tickets for each seat
        customer = Customer(name, email)
        
        # For simplicity, we'll create one order entry with all seats
        # You can modify this to create separate orders per seat if needed
        ticket = create_ticket(ticket_type, seat_list[0])
        ticket_price_per_seat = ticket.calculate_price()
        # Apply membership discount via helper
        discounted_price_per_seat = apply_membership_discount(ticket_price_per_seat, membership)
        admin_fee_per_seat = 5000  # Biaya admin per kursi
        ticket_price = discounted_price_per_seat * len(seat_list)  # Total harga tiket tanpa admin
        admin_fee_total = admin_fee_per_seat * len(seat_list)  # Total biaya admin
        price = ticket_price + admin_fee_total  # Total pembayaran (termasuk admin)
        snack_included = True if membership == 'vip' else False

        # ambil judul film untuk disimpan di order
        movie_title = next((m['title'] for m in movies if m['id'] == movie_id), "")

        order = {
            "id": len(orders) + 1,
            "movie_id": movie_id,
            "movie_title": movie_title,
            "seat": ", ".join(seat_list),  # Multiple seats
            "ticket_type": ticket_type,
            "showtime": showtime,  # Add showtime
            "ticket_price": ticket_price,  # Harga tiket tanpa admin
            "admin_fee": admin_fee_total,  # Biaya admin total
            "price": price,  # Total pembayaran (termasuk admin)
            "membership": membership,
            "snack_included": snack_included,
            "customer": customer.get_name(),
            "email": customer.get_email(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "payment_method": ""  # Will be set during payment
        }

        # Simpan order di session (pending) sampai pembayaran selesai
        session['pending_order'] = order

        # kirim seat dan price eksplisit supaya payment.html bisa menggunakan {{ seat }} dan {{ price }}
        return render_template('payment.html', order=order, movie=movie, seat=order['seat'], price=order['price'])

    # GET request: collect booked seats for this movie, showtime, and ticket type
    # Parse all booked seats (handle both single and multiple seats per order)
    # Structure: { "10:00 AM": { "Regular": ["A1", "A2"], "VIP": ["B1"] }, ... }
    booked_seats_by_showtime = {}
    for showtime in movie['showtimes']:
        booked_seats_by_showtime[showtime] = {"Regular": [], "VIP": []}
        for order in orders:
            if order['movie_id'] == movie_id and order['showtime'] == showtime:
                # Split comma-separated seats and add each to set based on ticket type
                ticket_type = order.get('ticket_type', 'Regular')
                seats = [s.strip() for s in order['seat'].split(',')]
                for seat in seats:
                    if seat not in booked_seats_by_showtime[showtime][ticket_type]:
                        booked_seats_by_showtime[showtime][ticket_type].append(seat)
    
    # Pass current user's membership to template (for client-side price preview)
    membership = session.get('user', {}).get('membership') if session.get('user') else 'guest'
    return render_template('book.html', movie=movie, booked_seats_by_showtime=booked_seats_by_showtime, membership=membership)


# route fallback (tetap ada)
@app.route('/book', methods=['GET', 'POST'])
def book_no_id():
    return redirect(url_for('home'))


# Tambahkan route untuk finish (konfirmasi akhir)
@app.route('/finish', methods=['POST'])
def finish():
    # Ambil order dari session (pending order yang belum dikonfirmasi pembayaran)
    if 'pending_order' not in session:
        return redirect(url_for('home'))
    
    pending_order = session['pending_order']
    
    # Update order dengan payment method dari form
    payment_method = request.form.get('payment_method', 'N/A')
    pending_order['payment_method'] = payment_method
    
    # Sekarang simpan order ke database (pembayaran sudah dikonfirmasi)
    oid = save_order_db(pending_order)
    pending_order['id'] = oid

    # Hapus dari session
    session.pop('pending_order', None)

    movie_id = pending_order['movie_id']
    movie = next((m for m in movies if m['id'] == movie_id), None)
    
    if not movie:
        return redirect(url_for('home'))
    
    # Render invoice page dengan order dan movie data
    return render_template('invoice.html', order=pending_order, movie=movie)


@app.route('/admin')
@admin_required
def admin():
    # read orders from DB
    all_orders = get_all_orders_db()
    return render_template('admin.html', orders=all_orders, movies=movies)


@app.route('/users')
@admin_required
def list_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, membership, role, created_at FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    users = [dict(r) for r in rows]
    return render_template('users.html', users=users)


@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    orders = get_orders_by_user_email(user['email'])
    return render_template('profile.html', user=user, orders=orders)


@app.route('/admin/upgrade/<int:user_id>', methods=['POST'])
@admin_required
def admin_upgrade(user_id):
    # Upgrade user membership to VIP (admin action)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET membership = 'vip' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_users'))


# ---------- AUTH ROUTES ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        membership = request.form.get('membership', 'member')

        if not name or not email or not password:
            flash('Lengkapi semua field')
            return render_template('register.html')

        existing = get_user_by_email(email)
        if existing:
            flash('Email sudah terdaftar')
            return render_template('register.html')

        user = create_user(name, email, password, membership)
        if not user:
            flash('Gagal membuat user (email mungkin sudah terpakai)')
            return render_template('register.html')

        # Auto-login setelah registrasi
        # `user` is a sqlite3.Row which doesn't implement .get(), so access safely
        role = user['role'] if user and 'role' in user.keys() else 'user'
        session['user'] = { 'id': user['id'], 'name': user['name'], 'email': user['email'], 'membership': user['membership'], 'role': role }
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        if not user:
            flash('Email tidak ditemukan')
            return render_template('login.html')

        if not check_password_hash(user['password'], password):
            flash('Password salah')
            return render_template('login.html')

        # `user` is sqlite3.Row; read role safely
        role = user['role'] if user and 'role' in user.keys() else 'user'
        session['user'] = { 'id': user['id'], 'name': user['name'], 'email': user['email'], 'membership': user['membership'], 'role': role }
        return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    # Initialize database (users table)
    init_db()
    app.run(debug=True)
