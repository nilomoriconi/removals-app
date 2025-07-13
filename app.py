from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import sessionmaker
import googlemaps
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from config import DevelopmentConfig, ProductionConfig
from models import db, Booking


# Load environment variables
load_dotenv()

# Create the Flask app
app = Flask(__name__, static_folder="static")
app.secret_key = 'removals_secret_key'

# Load the appropriate configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Initialize Database and Migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Google Maps Client
gmaps = googlemaps.Client(key=app.config['GOOGLE_MAPS_API_API_KEY_SERVER'])

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
    
file_handler = RotatingFileHandler('logs/removals_app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Removals App startup')

# Context processor to inject today's and tomorrow's dates into templates
@app.context_processor
def inject_dates():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    return {
        'today': today.strftime('%Y-%m-%d'),
        'tomorrow': tomorrow.strftime('%Y-%m-%d')
    }

@app.context_processor
def inject_google_maps_key():
    return {'google_maps_api_key': app.config['GOOGLE_MAPS_API_KEY_CLIENT']}

# Ensure database tables are created within an application context
with app.app_context():
    db.create_all()


############ Home Page ###########
@app.route('/')
def home():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    
    # Get today's bookings and trucks
    today_bookings = Booking.query.filter_by(date=today).all()
    trucks_assigned = list(set(booking.truck for booking in today_bookings if booking.truck))
    
    # Get tomorrow's bookings and trucks
    tomorrow_bookings = Booking.query.filter_by(date=tomorrow).all()
    tomorrow_trucks_assigned = list(set(booking.truck for booking in tomorrow_bookings if booking.truck))
    
    return render_template('home.html',
                         today_date=datetime.today(),
                         tomorrow_date=datetime.today() + timedelta(days=1),
                         today_bookings=today_bookings,
                         tomorrow_bookings=tomorrow_bookings,
                         trucks_assigned=trucks_assigned,
                         tomorrow_trucks_assigned=tomorrow_trucks_assigned)

############ View All Bookings ###########

@app.route('/view_bookings')
def view_bookings():
    sort_by = request.args.get('sort_by', 'date')
    order = request.args.get('order', 'asc')
    show_past = request.args.get('show_past', 'no')

    query = Booking.query

    # Filter out past bookings if show_past is 'no'
    if show_past == 'no':
        query = query.filter(Booking.date >= date.today())

    # Apply sorting
    if sort_by == 'date':
        if order == 'desc':
            query = query.order_by(Booking.date.desc())
        else:
            query = query.order_by(Booking.date.asc())

    bookings = query.all()

    return render_template('view_bookings.html', 
                         bookings=bookings, 
                         sort_by=sort_by, 
                         order=order,
                         show_past=show_past)



######### View DAY Bookings ###########

@app.route('/bookings/day', methods=['GET'])
def view_day_bookings():
    """Displays bookings filtered by selected date."""
    
    # Get the selected date from query parameters
    date_str = request.args.get('date')

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format! Please use YYYY-MM-DD.", "danger")
            return redirect(url_for('view_bookings'))
        
        # Fetch bookings for the selected date
        bookings = Booking.query.filter_by(date=selected_date).all()
    else:
        # Default to today's date if no date is provided
        selected_date = datetime.today().date()
        bookings = Booking.query.filter_by(date=selected_date).all()

    return render_template('view_day_bookings.html', bookings=bookings, selected_date=selected_date)

########### View Job Info ###########

@app.route('/bookings/<int:id>', methods=['GET'])
def view_job(id):
    """Displays detailed information for a single booking."""
    booking = Booking.query.get(id)

    if not booking:
        flash("Booking not found!", "danger")
        return redirect(url_for('view_bookings'))

    return render_template('view_job.html', booking=booking)


############ Add Booking ###########
@app.route('/add', methods=['GET', 'POST'])
def add_booking():
    if request.method == 'POST':
        client_name = request.form['client_name']
        date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()

        truck = request.form.get('truck')
        if truck == "Other":
            truck = request.form.get('truck_other', 'Other')

        # Handle hourly_rate safely
        hourly_rate_str = request.form.get('hourly_rate')
        hourly_rate = float(hourly_rate_str) if hourly_rate_str and hourly_rate_str.strip() else 0.0

        new_booking = Booking(
            client_name=client_name,
            date=date,
            phone=request.form.get('phone'),
            pickup_address=request.form.get('pickup_address'),
            dropoff_address=request.form.get('dropoff_address'),
            start_time=request.form.get('start_time'),
            hourly_rate=hourly_rate,  # Use the safely converted value
            truck=truck,
            men=request.form.get('men'),
            details=request.form.get('details'),
            estimated_time=request.form.get('estimated_time'),
            booking_source=request.form.get('booking_source'),
            parking_info=request.form.get('parking_info'),
            pickup_access_stairs=request.form.get('pickup_access_stairs'),
            dropoff_access_stairs=request.form.get('dropoff_access_stairs'),
            list_of_items=request.form.get('list_of_items'),
            email=request.form.get('email'),
            # New fields (initially empty until edited)
            total_time=None,
            amount_charged=None,
            payment_method=None,
            client_happy=None,
            asked_for_review=None,
        )

        db.session.add(new_booking)
        db.session.commit()

        flash("Booking added successfully!", "success")
        return redirect(url_for('view_bookings'))

    return render_template('add_booking.html')

############ Edit Booking ###########
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_booking(id):
    booking = Booking.query.get(id)
    if not booking:
        flash("Booking not found!", "danger")
        return redirect(url_for('view_bookings'))
            
    if request.method == 'POST':
        booking.date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        booking.client_name = request.form['client_name']
        booking.phone = request.form.get('phone')
        booking.pickup_address = request.form.get('pickup_address')
        booking.dropoff_address = request.form.get('dropoff_address')
        booking.start_time = request.form.get('start_time')
        booking.hourly_rate = float(request.form.get('hourly_rate', 0))
        # Handle truck logic
        truck = request.form.get('truck')
        if truck == "Other":
            truck = request.form.get('truck_other', 'Other')
        booking.truck = truck
        booking.men = request.form.get('men')
        booking.details = request.form.get('details')
        booking.estimated_time = request.form.get('estimated_time')
        booking.booking_source = request.form.get('booking_source')
        booking.parking_info = request.form.get('parking_info')
        booking.pickup_access_stairs = request.form.get('pickup_access_stairs')
        booking.dropoff_access_stairs = request.form.get('dropoff_access_stairs')
        booking.list_of_items = request.form.get('list_of_items')
        booking.email = request.form.get('email')
        amount_charged_str = request.form.get('amount_charged')
        booking.amount_charged = float(amount_charged_str) if amount_charged_str and amount_charged_str.strip() else None
        booking.payment_method = request.form.get('payment_method')
        booking.client_happy = request.form.get('client_happy')
        booking.asked_for_review = request.form.get('asked_for_review')

        db.session.commit()
        flash("Booking updated successfully!", "success")
        # Check if a date parameter was passed in the query string
        selected_date = request.args.get('date')
        if selected_date:
            return redirect(url_for('view_day_bookings', date=selected_date))
        else:
            return redirect(url_for('view_bookings'))        


    return render_template('edit_booking.html', booking=booking)

############ Delete Booking ###########
@app.route('/delete/<int:id>', methods=['POST'])
def delete_booking(id):
    booking = Booking.query.get(id)
    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash("Booking deleted successfully!", "success")
    else:
        flash("Booking not found!", "danger")

    return redirect(url_for('view_bookings'))

############# FULL CALENDAR ##############
@app.route('/api/bookings')
def api_bookings():
    bookings = Booking.query.all()
    events = []
    for booking in bookings:
        # Combine the date and start_time into an ISO datetime string.
        start_datetime = f"{booking.date.isoformat()}T{booking.start_time}:00"

        # Safely get each field (adjust defaults as necessary)
        client_name = booking.client_name if booking.client_name else "No Name"
        truck = booking.truck if booking.truck else "No Truck"
        men = booking.men if booking.men else "0"
        estimated_time = booking.estimated_time if booking.estimated_time else "0"

        # Build the title string as "Name - Truck - Men - EstimatedTime hs EST"
        title_str = f"{client_name} - {truck} - {men} - {estimated_time} hs estimate"

        events.append({
            'title': title_str,
            'start': start_datetime,
        })
    return jsonify(events)    




##GOOGLE MAPS

import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/calculate_route', methods=['POST'])
def calculate_route():
    pickup_address = request.form['pickup_address']
    dropoff_address = request.form['dropoff_address']
    
    try:
        logger.debug(f"Geocoding pickup: {pickup_address}")
        pickup_geocode = gmaps.geocode(pickup_address + ', QLD, Australia')[0]['geometry']['location']
        logger.debug(f"Geocoding dropoff: {dropoff_address}")
        dropoff_geocode = gmaps.geocode(dropoff_address + ', QLD, Australia')[0]['geometry']['location']
        
        logger.debug(f"Pickup Geocode: {pickup_geocode}")
        logger.debug(f"Dropoff Geocode: {dropoff_geocode}")
        
        now = datetime.now()
        
        base_address = "Palm Beach, QLD, Australia"
        base_geocode = gmaps.geocode(base_address)[0]['geometry']['location']
        logger.debug(f"Base Geocode (Palm Beach): {base_geocode}")
        
        to_pickup = gmaps.directions(
            origin=(base_geocode['lat'], base_geocode['lng']),
            destination=(pickup_geocode['lat'], pickup_geocode['lng']),
            mode="driving",
            departure_time=now,
            traffic_model="best_guess"
        )
        pickup_to_dropoff = gmaps.directions(
            origin=(pickup_geocode['lat'], pickup_geocode['lng']),
            destination=(dropoff_geocode['lat'], dropoff_geocode['lng']),
            mode="driving",
            departure_time=now,
            traffic_model="best_guess"
        )
        dropoff_to_base = gmaps.directions(
            origin=(dropoff_geocode['lat'], dropoff_geocode['lng']),
            destination=(base_geocode['lat'], base_geocode['lng']),
            mode="driving",
            departure_time=now,
            traffic_model="best_guess"
        )

        to_pickup_eta = to_pickup[0]['legs'][0]['duration_in_traffic']['text']
        pickup_to_dropoff_eta = pickup_to_dropoff[0]['legs'][0]['duration_in_traffic']['text']
        dropoff_to_base_eta = dropoff_to_base[0]['legs'][0]['duration_in_traffic']['text']

        return jsonify({
            'to_pickup': to_pickup_eta,
            'pickup_to_dropoff': pickup_to_dropoff_eta,
            'dropoff_to_base': dropoff_to_base_eta,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error in calculate_route: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400


@app.route('/get_booking_count/<date>')
def get_booking_count(date):
    count = Booking.query.filter(Booking.date == date).count()
    return jsonify({'count': count})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Google Maps
    gmaps = googlemaps.Client(key=app.config['GOOGLE_MAPS_API_KEY_SERVER'])
    
    return app

# Use in development
app = create_app()

if __name__ == '__main__':
    app.run()
