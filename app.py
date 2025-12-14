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
    # movies table - untuk menyimpan data film yang dapat dikelola admin
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            duration INTEGER,
            poster TEXT,
            showtimes TEXT,
            regular_price INTEGER DEFAULT 50000,
            vip_price INTEGER DEFAULT 75000,
            available_seats INTEGER DEFAULT 50,
            created_at TEXT,
            updated_at TEXT
        )
        '''
    )
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


# ===== MOVIE MANAGEMENT FUNCTIONS =====
def get_all_movies():
    """Ambil semua film dari database"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies ORDER BY id DESC")
    movies_list = cur.fetchall()
    conn.close()
    return [dict(m) for m in movies_list]


def get_movie_by_id(movie_id):
    """Ambil film berdasarkan ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cur.fetchone()
    conn.close()
    return dict(movie) if movie else None


def add_movie(title, genre, duration, poster, showtimes_str, regular_price, vip_price):
    """Tambah film baru ke database"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        cur.execute(
            """INSERT INTO movies (title, genre, duration, poster, showtimes, regular_price, vip_price, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, genre, duration, poster, showtimes_str, regular_price, vip_price, now, now)
        )
        conn.commit()
        movie_id = cur.lastrowid
        conn.close()
        return get_movie_by_id(movie_id)
    except Exception as e:
        conn.close()
        return None


def update_movie(movie_id, title, genre, duration, poster, showtimes_str, regular_price, vip_price):
    """Update film yang sudah ada"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        cur.execute(
            """UPDATE movies SET title=?, genre=?, duration=?, poster=?, showtimes=?, regular_price=?, vip_price=?, updated_at=? 
               WHERE id=?""",
            (title, genre, duration, poster, showtimes_str, regular_price, vip_price, now, movie_id)
        )
        conn.commit()
        conn.close()
        return get_movie_by_id(movie_id)
    except Exception as e:
        conn.close()
        return None


def delete_movie(movie_id):
    """Hapus film dari database"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM movies WHERE id=?", (movie_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False


def initialize_default_movies():
    """Seed database dengan film-film default jika database kosong"""
    db_movies = get_all_movies()
    if db_movies:
        return  # Database sudah ada movies
    
    default_movies = [
        ("Avengers: Doomsday", "Action / Superhero", 165, 
         "https://posterspy.com/wp-content/uploads/2024/10/Doomsday-by-VISCOM.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Superman: Legacy", "Action / Superhero", 145,
         "https://posterspy.com/wp-content/uploads/2023/11/20231130_142631_0-glazed-intensity-10-V1.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Spider-Man: No Way Home", "Action / Sci-Fi", 135,
         "https://cdn.marvel.com/content/2x/spider-mannowayhome_lob_crd_03.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Batman: The Brave and The Bold", "Action / Crime", 150,
         "https://i.pinimg.com/736x/c4/8b/ed/c48bedde3a9cb8b745a71369627a5005.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Avatar 3", "Sci-Fi / Adventure", 170,
         "https://m.media-amazon.com/images/M/MV5BZDYxY2I1OGMtN2Y0MS00ZmU1LTgyNDAtODA0MzAyYjI0N2Y2XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("How to Train Your Dragon: Live-Action", "Adventure / Fantasy", 140,
         "https://m.media-amazon.com/images/M/MV5BODA5Y2M0NjctNWQzMy00ODRhLWE0MzUtYmE1YTAzZjYyYmQyXkEyXkFqcGc@._V1_.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Frozen 2", "Animation / Family", 120,
         "https://myhotposters.com/cdn/shop/products/mL3767_grande.jpg?v=1748534166",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Inside Out 2", "Animation / Family", 110,
         "https://upload.wikimedia.org/wikipedia/id/thumb/9/9f/Inside_Out_2_Poster_Indonesian.webp/1000px-Inside_Out_2_Poster_Indonesian.webp.png",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Mission Impossible: Reckoning Part 2", "Action / Thriller", 160,
         "https://posterspy.com/wp-content/uploads/2023/06/M.I7v4-1.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Mufasa: The Lion King", "Drama / Family", 130,
         "https://www.laughingplace.com/uploads/ddimages/2024/12/06/7-new-posters-released-for-mufasa-the-lion-king-including-imax-dolby-4dx-and-other-special-formats.jpeg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Sonic the Hedgehog 3", "Action / Comedy", 120,
         "https://i0.wp.com/mynintendonews.com/wp-content/uploads/2024/11/sonic_movie_3-poster.jpeg?resize=691%2C1024&ssl=1",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
        ("Deadpool & Wolverine", "Action / Comedy", 130,
         "https://cdn.marvel.com/content/2x/dp3_1sht_digital_srgb_ka_swords_v5_resized.jpg",
         "10:00 AM, 01:00 PM, 04:00 PM, 07:00 PM, 10:00 PM", 50000, 75000),
    ]
    
    for title, genre, duration, poster, showtimes, regular_price, vip_price in default_movies:
        add_movie(title, genre, duration, poster, showtimes, regular_price, vip_price)


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
    if not ticket_type:
        return Ticket(seat, "Regular")

    t = ticket_type.strip().lower()
    if t == "vip":
        return VIPTicket(seat, "VIP")
    return Ticket(seat, "Regular")



# ROUTES
@app.route('/')
def home():
    db_movies = get_all_movies()
    # Jika database kosong, gunakan static data untuk demo
    if not db_movies:
        db_movies = movies
    return render_template('home.html', movies=db_movies)


@app.route('/book/<int:movie_id>', methods=['GET', 'POST'])
def book(movie_id):
    # Get movie from database
    movie_data = get_movie_by_id(movie_id)
    
    if not movie_data:
        return "Film tidak ditemukan", 404
    
    # Convert database movie to format yang digunakan template
    movie = {
        'id': movie_data['id'],
        'title': movie_data['title'],
        'genre': movie_data['genre'],
        'duration': movie_data['duration'],
        'poster': movie_data['poster'],
        'showtimes': [st.strip() for st in movie_data['showtimes'].split(',')] if movie_data['showtimes'] else [],
        'regular_price': movie_data['regular_price'],
        'vip_price': movie_data['vip_price'],
        'seats': generate_seats()  # Generate available seats for this movie
    }

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
        
        # Get ticket price dari database movie
        if ticket_type.lower() == 'vip':
            ticket_price_per_seat = movie['vip_price']
        else:
            ticket_price_per_seat = movie['regular_price']
        
        # Apply membership discount via helper
        discounted_price_per_seat = apply_membership_discount(ticket_price_per_seat, membership)
        admin_fee_per_seat = 5000  # Biaya admin per kursi
        ticket_price = discounted_price_per_seat * len(seat_list)  # Total harga tiket tanpa admin
        admin_fee_total = admin_fee_per_seat * len(seat_list)  # Total biaya admin
        price = ticket_price + admin_fee_total  # Total pembayaran (termasuk admin)
        snack_included = True if membership == 'vip' else False

        # Ambil judul film dari database movie
        movie_title = movie['title']

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
    movie_data = get_movie_by_id(movie_id)
    
    if not movie_data:
        return redirect(url_for('home'))
    
    # Convert database movie to template format
    movie = {
        'id': movie_data['id'],
        'title': movie_data['title'],
        'genre': movie_data['genre'],
        'duration': movie_data['duration'],
        'poster': movie_data['poster'],
        'regular_price': movie_data['regular_price'],
        'vip_price': movie_data['vip_price']
    }
    
    # Render invoice page dengan order dan movie data
    return render_template('invoice.html', order=pending_order, movie=movie)


@app.route('/admin')
@admin_required
def admin():
    # read orders from DB
    all_orders = get_all_orders_db()
    db_movies = get_all_movies()
    return render_template('admin.html', orders=all_orders, movies=db_movies)


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


# ===== MOVIE MANAGEMENT ROUTES =====
@app.route('/admin/movies')
@admin_required
def admin_movies():
    """Tampilkan daftar semua film untuk dikelola admin"""
    db_movies = get_all_movies()
    return render_template('admin_movies.html', movies=db_movies)


@app.route('/admin/movies/add', methods=['GET', 'POST'])
@admin_required
def add_movie_route():
    """Halaman untuk menambah film baru"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        genre = request.form.get('genre', '').strip()
        duration = request.form.get('duration', '0')
        poster = request.form.get('poster', '').strip()
        showtimes_str = request.form.get('showtimes', '').strip()  # e.g., "10:00 AM, 01:00 PM, 04:00 PM"
        regular_price = request.form.get('regular_price', '50000')
        vip_price = request.form.get('vip_price', '75000')
        
        # Validasi
        if not title or not genre or not duration or not poster or not showtimes_str:
            flash('Semua field harus diisi')
            return render_template('movie_form.html', movie=None)
        
        try:
            duration = int(duration)
            regular_price = int(regular_price)
            vip_price = int(vip_price)
        except ValueError:
            flash('Duration dan harga harus berupa angka')
            return render_template('movie_form.html', movie=None)
        
        # Tambah ke database
        movie = add_movie(title, genre, duration, poster, showtimes_str, regular_price, vip_price)
        if movie:
            flash(f'Film "{title}" berhasil ditambahkan!')
            return redirect(url_for('admin_movies'))
        else:
            flash('Gagal menambahkan film')
            return render_template('movie_form.html', movie=None)
    
    return render_template('movie_form.html', movie=None)


@app.route('/admin/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def edit_movie_route(movie_id):
    """Halaman untuk mengedit film"""
    movie = get_movie_by_id(movie_id)
    if not movie:
        flash('Film tidak ditemukan')
        return redirect(url_for('admin_movies'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        genre = request.form.get('genre', '').strip()
        duration = request.form.get('duration', '0')
        poster = request.form.get('poster', '').strip()
        showtimes_str = request.form.get('showtimes', '').strip()
        regular_price = request.form.get('regular_price', '50000')
        vip_price = request.form.get('vip_price', '75000')
        
        # Validasi
        if not title or not genre or not duration or not poster or not showtimes_str:
            flash('Semua field harus diisi')
            return render_template('movie_form.html', movie=movie)
        
        try:
            duration = int(duration)
            regular_price = int(regular_price)
            vip_price = int(vip_price)
        except ValueError:
            flash('Duration dan harga harus berupa angka')
            return render_template('movie_form.html', movie=movie)
        
        # Update database
        updated_movie = update_movie(movie_id, title, genre, duration, poster, showtimes_str, regular_price, vip_price)
        if updated_movie:
            flash(f'Film "{title}" berhasil diupdate!')
            return redirect(url_for('admin_movies'))
        else:
            flash('Gagal mengupdate film')
            return render_template('movie_form.html', movie=movie)
    
    return render_template('movie_form.html', movie=movie)


@app.route('/admin/movies/delete/<int:movie_id>', methods=['POST'])
@admin_required
def delete_movie_route(movie_id):
    """Hapus film dari database"""
    movie = get_movie_by_id(movie_id)
    if not movie:
        flash('Film tidak ditemukan')
        return redirect(url_for('admin_movies'))
    
    title = movie.get('title', 'Film')
    if delete_movie(movie_id):
        flash(f'Film "{title}" berhasil dihapus!')
        return redirect(url_for('admin_movies'))
    else:
        flash('Gagal menghapus film')
        return redirect(url_for('admin_movies'))


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
    # Seed default movies if database is empty
    initialize_default_movies()
    app.run(debug=True)
