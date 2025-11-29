from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Diperlukan untuk menggunakan session


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
        ticket = Ticket(seat, ticket_type)
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
        name = request.form['name']
        email = request.form['email']
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

        # ====== VALIDASI SEAT SUDAH DIPESAN ======
        # Parse all booked seats for the selected showtime and ticket type
        booked_seats_set = set()
        for order in orders:
            if order['movie_id'] == movie_id and order['showtime'] == showtime and order['ticket_type'] == ticket_type:
                seats = [s.strip() for s in order['seat'].split(',')]
                booked_seats_set.update(seats)
        booked_seats = list(booked_seats_set)
        
        unavailable_seats = [seat for seat in seat_list if seat in booked_seats]

        if unavailable_seats:
            error = f"Kursi {', '.join(unavailable_seats)} sudah dipesan!"
            # Build booked_seats_by_showtime for error case
            booked_seats_by_showtime = {}
            for st in movie['showtimes']:
                booked_seats_by_showtime[st] = {"Regular": [], "VIP": []}
                for order in orders:
                    if order['movie_id'] == movie_id and order['showtime'] == st:
                        ticket_type_order = order.get('ticket_type', 'Regular')
                        seats = [s.strip() for s in order['seat'].split(',')]
                        for seat in seats:
                            if seat not in booked_seats_by_showtime[st][ticket_type_order]:
                                booked_seats_by_showtime[st][ticket_type_order].append(seat)
            return render_template("book.html", movie=movie, error=error, booked_seats_by_showtime=booked_seats_by_showtime)

        # Create customer and book tickets for each seat
        customer = Customer(name, email)
        
        # For simplicity, we'll create one order entry with all seats
        # You can modify this to create separate orders per seat if needed
        ticket = Ticket(seat_list[0], ticket_type)
        ticket_price_per_seat = ticket.calculate_price()
        admin_fee_per_seat = 5000  # Biaya admin per kursi
        ticket_price = ticket_price_per_seat * len(seat_list)  # Total harga tiket tanpa admin
        admin_fee_total = admin_fee_per_seat * len(seat_list)  # Total biaya admin
        price = ticket_price + admin_fee_total  # Total pembayaran (termasuk admin)

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
            "customer": customer.get_name(),
            "email": customer.get_email(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "payment_method": ""  # Will be set during payment
        }

        # Simpan order di session (bukan di orders list) sampai pembayaran selesai
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
    
    return render_template('book.html', movie=movie, booked_seats_by_showtime=booked_seats_by_showtime)


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
    
    # Sekarang tambahkan order ke orders list (pembayaran sudah dikonfirmasi)
    orders.append(pending_order)
    
    # Hapus dari session
    session.pop('pending_order', None)
    
    movie_id = pending_order['movie_id']
    movie = next((m for m in movies if m['id'] == movie_id), None)
    
    if not movie:
        return redirect(url_for('home'))
    
    # Render invoice page dengan order dan movie data
    return render_template('invoice.html', order=pending_order, movie=movie)


@app.route('/admin')
def admin():
    admin_user = Admin("Admin", "admin@cinema.com")
    all_orders = admin_user.view_all_orders()
    return render_template('admin.html', orders=all_orders, movies=movies)


# RUN
if __name__ == '__main__':
    app.run(debug=True)
