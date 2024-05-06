from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configure SQLAlchemy to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define Reservation model corresponding to the reservations table
class Reservations(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    passengerName = db.Column(db.Text, nullable=False)
    seatRow = db.Column(db.Integer, nullable=False)
    seatColumn = db.Column(db.Integer, nullable=False)
    eTicketNumber = db.Column(db.Text, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())


# Define Admins model corresponding to the admins table
class Admins(db.Model):
    username = db.Column(db.Text, primary_key=True)
    password = db.Column(db.Text, nullable=False)


@app.route('/')
def main_menu():
    return render_template('main_menu.html')


@app.route('/reserve_seat', methods=['GET', 'POST'])
def reserve_seat():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        seat_row_user = int(request.form['seat_row'])
        seat_column_user = int(request.form['seat_column'])

        #Convert user selection to zero based index
        seat_row_db = seat_row_user - 1
        seat_column_db = seat_column_user - 1

        # Check if the seat is already reserved
        if is_seat_reserved(int(seat_row_db), int(seat_column_db)):
            print(f"Seat {seat_row_db}-{seat_column_db} is reserved")
            error=f"Seat {seat_row_db}-{seat_column_db} already reserved. Please choose new seat."
            return render_template('reservation_form.html', error=error)
            

        # Generate eTicketNumber (random alphanumeric string)
        e_ticket_number = generate_e_ticket_number(first_name)

        # Create new reservation record in the database
        new_reservation = Reservations(
            passengerName=f"{first_name} {last_name}",
            seatRow=int(seat_row_db),
            seatColumn=int(seat_column_db),
            eTicketNumber=e_ticket_number
        )
        db.session.add(new_reservation)
        db.session.commit()

        return render_template('reservation_success.html', e_ticket_number=e_ticket_number)

    return render_template('reservation_form.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check admin credentials against the database
        admin_user = Admins.query.filter_by(username=username).first()
        if admin_user and admin_user.password == password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_portal'))

        error = "Invalid username or password. Please try again."
        return render_template('admin_login.html', error=error)

    return render_template('admin_login.html')


@app.route('/admin/portal')
def admin_portal():
    if session.get('admin_logged_in'):
        # Fetch all reservations from the database
        reservations = Reservations.query.all()

        # Get reserved seats
        reserved_seats = {(r.seatRow, r.seatColumn) for r in reservations}

        # Calculate total sales using cost matrix
        cost_matrix = get_cost_matrix()
        total_sales = calculate_total_sales(reserved_seats, cost_matrix)

        return render_template('admin_portal.html', reservations=reservations, total_sales=total_sales)
    else:
        return redirect(url_for('admin_login'))


def get_cost_matrix():
    cost_matrix = [[100, 75, 50, 100] for _ in range(12)]  # Example cost matrix
    return cost_matrix


def calculate_total_sales(reserved_seats, cost_matrix):
    total_sales = 0
    for seat_row, seat_column in reserved_seats:
        try:
            seat_price = cost_matrix[seat_row - 1][seat_column - 1]
            total_sales += seat_price
        except IndexError:
            pass
    return total_sales


def get_reserved_seats():
    reserved_seats = Reservations.query.with_entities(Reservations.seatRow, Reservations.seatColumn).all()
    return {(seat.seatRow, seat.seatColumn) for seat in reserved_seats}


def is_seat_reserved(seat_row, seat_column):
    reserved_seats = get_reserved_seats()
    return (seat_row, seat_column) in reserved_seats

# Make is_seat_reserved available to all templates globally
app.jinja_env.globals['is_seat_reserved'] = is_seat_reserved


def generate_e_ticket_number(first_name):
    alternating_string = "INFOTC4320"
    max_length = min(len(first_name), len(alternating_string))
    e_ticket_number = []

    for i in range(max_length):
        e_ticket_number.append(first_name[i])
        e_ticket_number.append(alternating_string[i])

    if len(first_name) < len(alternating_string):
        e_ticket_number.append(alternating_string[len(first_name):])

    return ''.join(e_ticket_number)


if __name__ == '__main__':
    # Create all database tables before running the app
    with app.app_context():
        db.create_all()

    # Run the Flask application on port 5008
    app.run(host='0.0.0.0', port=5008, debug=True)

