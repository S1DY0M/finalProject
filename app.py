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

        # Check if the seat is already reserved
        if is_seat_reserved(seat_row, seat_column):
            return render_template('reservation_failure.html', message="Seat is already reserved.")

        # Create new reservation record in the database
        new_reservation = Reservations(
            passengerName=f"{first_name} {last_name}",
            seatRow=int(seat_row),
            seatColumn=int(seat_column),
            eTicketNumber=e_ticket_number
        )
        db.session.add(new_reservation)
        db.session.commit()

        return render_template('reservation_success.html', e_ticket_number=e_ticket_number)

    return render_template('reservation_form.html')


def is_seat_reserved(seat_row, seat_column):
    # Query the database to check if a seat at the given row and column is reserved
    reservation = Reservations.query.filter_by(seatRow=seat_row, seatColumn=seat_column).first()
    return reservation is not None


if __name__ == '__main__':
    # Create all database tables before running the app
    with app.app_context():
        db.create_all()
    app.run(debug=True)
