from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    truck = db.Column(db.String(50), nullable=True)
    men = db.Column(db.Integer, nullable=True)
    start_time = db.Column(db.String(50), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pickup_address = db.Column(db.String(255), nullable=False)
    dropoff_address = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.String(50), nullable=True)
    hourly_rate = db.Column(db.Float, nullable=True)
    booking_source = db.Column(db.String(50), nullable=True)
    parking_info = db.Column(db.String(255), nullable=True)
    pickup_access_stairs = db.Column(db.String(255), nullable=True)
    dropoff_access_stairs = db.Column(db.String(255), nullable=True)
    list_of_items = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(100), nullable=True)
    total_time = db.Column(db.String(50), nullable=True)
    amount_charged = db.Column(db.Float, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    client_happy = db.Column(db.String(20), nullable=True)
    asked_for_review = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f'<Booking {self.id}: {self.client_name} on {self.date}>'
