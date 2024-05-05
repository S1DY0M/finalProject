from flask import Flask, render_template, request, session, redirect, url_for, jsonify
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

    def __repr__(self):
        return f"Reservation {self.id}: {self.passengerName} - Seat: ({self.seatRow}, {self.seatColumn})"



@app.route('/')
def main_menu():
    return render_template('main_menu.html')


@app.route('/reserve_seat', methods=['GET','POST'])
def reserve_seat():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        seat_row = request.form['seat_row']
        seat_column = request.form['seat_column']

        # Generate eTicketNumber (random alphanumeric string)
        e_ticket_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # Create new reservation record in the database
        new_reservation = Reservations(
            passengerName=f"{first_name} {last_name}",
            seatRow=int(seat_row),
            seatColumn=int(seat_column),
            eTicketNumber=e_ticket_number
        )
        db.session.add(new_reservation)
        db.session.commit()

        return render_template('reservation_success.html', e_ticket_number=e_ticket_number, is_seat_reserved=is_seat_reserved)

    return render_template('reservation_form.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Replace this with your actual authentication logic
        if username == 'username' and password == 'password' :
            session['admin_logged_in'] = True
            return redirect(url_for('admin_portal'))  # Correct endpoint
        else:
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
    print("Reserved Seats:", reserved_seats)
    for seat_row, seat_column in reserved_seats:
        try:
            # Convert to 0-based index for accessing cost_matrix
            row_index = seat_row - 1
            col_index = seat_column - 1
            seat_price = cost_matrix[row_index][col_index]
            print(f"Seat ({seat_row}, {seat_column}): Price = {seat_price}")
            total_sales += seat_price
        except IndexError:
            print(f"Invalid seat index ({seat_row}, {seat_column})")
            # Handle invalid seat data gracefully
            pass
    print("Total Sales:", total_sales)
    return total_sales


def get_reserved_seats():
    reserved_seats = Reservations.query.filter_by(seatStatus='reserved').with_entities(Reservations.seatRow, Reservations.seatColumn).all()
    return {(seat.seatRow, seat.seatColumn) for seat in reserved_seats}

def is_seat_reserved(seat_row, seat_column):
    reserved_seats = get_reserved_seats()
    return (seat_row, seat_column) in reserved_seats

@app.context_processor
def utility_processor():
    def is_seat_reserved(row, column):
        # Query the database to check if a seat at the given row and column is reserved
        reservation = Reservations.query.filter_by(seatRow=row, seatColumn=column).first()
        return reservation is not None

    return dict(is_seat_reserved=is_seat_reserved)


if __name__ == '__main__':
    # Create all database tables before running the app
    with app.app_context():
        db.create_all()
    app.run(debug=True)

