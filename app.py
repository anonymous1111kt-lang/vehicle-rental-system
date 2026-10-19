import os
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

from config import Config
from database import get_db_connection, test_connection, init_db
from seed_data import seed_sample_data

app = Flask(__name__)
app.config.from_object(Config)

# Make config available in all Jinja templates
@app.context_processor
def inject_config():
    return {'config': Config}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in with staff or administrative credentials.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') not in ['admin', 'staff']:
            flash("Access restricted to administrative and operations staff.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------
# Customer & Fleet Browsing Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    selected_type = request.args.get('type', '').strip().lower()
    selected_status = request.args.get('status', '').strip().lower()
    search = request.args.get('search', '').strip()

    vehicles = []
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            query = "SELECT * FROM vehicles WHERE 1=1"
            params = []

            if selected_type:
                query += " AND vehicle_type = %s"
                params.append(selected_type)
            if selected_status:
                query += " AND status = %s"
                params.append(selected_status)
            if search:
                query += " AND (make LIKE %s OR model LIKE %s OR license_plate LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term, term])

            query += " ORDER BY vehicle_id DESC;"
            cursor.execute(query, params)
            vehicles = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Database connection issue: {e}. You can configure credentials in the DB Status tab.", "warning")
        return redirect(url_for('db_status'))

    return render_template('index.html', vehicles=vehicles, selected_type=selected_type, selected_status=selected_status, search=search)

@app.route('/book/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def book_vehicle(vehicle_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Fetch vehicle details
            cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s;", (vehicle_id,))
            vehicle = cursor.fetchone()

            # Fetch user details
            cursor.execute("SELECT * FROM users WHERE user_id = %s;", (session['user_id'],))
            user = cursor.fetchone()
        conn.close()
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('index'))

    if not vehicle:
        flash("Requested vehicle was not found.", "danger")
        return redirect(url_for('index'))

    if vehicle['status'] != 'available' and request.method == 'GET':
        flash("This vehicle is currently unavailable for rent.", "warning")
        return redirect(url_for('index'))

    if request.method == 'POST':
        pickup_str = request.form.get('pickup_date')
        dropoff_str = request.form.get('dropoff_date')
        payment_method = request.form.get('payment_method', 'credit card')
        payment_status = request.form.get('payment_status', 'success')

        try:
            pickup_dt = datetime.datetime.fromisoformat(pickup_str)
            dropoff_dt = datetime.datetime.fromisoformat(dropoff_str)
        except (ValueError, TypeError):
            flash("Invalid date format selected.", "danger")
            return render_template('book.html', vehicle=vehicle, user=user)

        if dropoff_dt <= pickup_dt:
            flash("Dropoff date must be after pickup date.", "danger")
            return render_template('book.html', vehicle=vehicle, user=user)

        # Calculate rental days
        diff_days = (dropoff_dt - pickup_dt).total_seconds() / (24 * 3600)
        days = max(1, int(round(diff_days)))
        total_cost = float(vehicle['daily_rate']) * days
        amount = total_cost

        # Insert booking into MySQL
        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                insert_sql = """
                    INSERT INTO bookings (
                        user_id, vehicle_id, pickup_date, dropoff_date,
                        total_cost, amount, payment_method, payment_status, booking_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'confirmed');
                """
                cursor.execute(insert_sql, (
                    session['user_id'], vehicle_id, pickup_dt, dropoff_dt,
                    total_cost, amount, payment_method, payment_status
                ))

                # Update vehicle status to rented
                cursor.execute("UPDATE vehicles SET status = 'rented' WHERE vehicle_id = %s;", (vehicle_id,))
            conn.commit()
            conn.close()

            flash(f"Reservation confirmed for {vehicle['make']} {vehicle['model']}! Total: ${total_cost:.2f}", "success")
            return redirect(url_for('my_bookings'))
        except Exception as e:
            flash(f"Failed to process booking: {e}", "danger")

    return render_template('book.html', vehicle=vehicle, user=user)

@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = []
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            query = """
                SELECT b.*, v.make, v.model, v.license_plate, v.vehicle_type, v.image_url
                FROM bookings b
                JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                WHERE b.user_id = %s
                ORDER BY b.booking_id DESC;
            """
            cursor.execute(query, (session['user_id'],))
            bookings = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Database query error: {e}", "danger")

    return render_template('my_bookings.html', bookings=bookings)

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Check booking ownership (or admin privilege)
            cursor.execute("SELECT * FROM bookings WHERE booking_id = %s;", (booking_id,))
            booking = cursor.fetchone()

            if not booking:
                flash("Booking not found.", "danger")
            elif booking['user_id'] != session['user_id'] and session.get('role') not in ['admin', 'staff']:
                flash("Unauthorized to cancel this booking.", "danger")
            else:
                cursor.execute("""
                    UPDATE bookings 
                    SET booking_status = 'cancelled', payment_status = 'refunded' 
                    WHERE booking_id = %s;
                """, (booking_id,))

                # Set vehicle back to available
                cursor.execute("UPDATE vehicles SET status = 'available' WHERE vehicle_id = %s;", (booking['vehicle_id'],))
                conn.commit()
                flash("Booking cancelled and refunded successfully.", "success")
        conn.close()
    except Exception as e:
        flash(f"Error cancelling booking: {e}", "danger")

    return redirect(url_for('my_bookings'))

# -------------------------------------------------------------
# User Authentication Routes
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
                user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['name'] = f"{user['first_name']} {user['last_name']}"
                session['email'] = user['email']
                session['role'] = user['role']
                flash(f"Welcome back, {session['name']}!", "success")
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            flash(f"Database connection error: {e}", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        driver_license = request.form.get('driver_license_number', '').strip().upper()
        password = request.form.get('password', '')
        role = request.form.get('role', 'customer')

        if not (first_name and last_name and email and driver_license and password):
            flash("Please complete all required fields.", "warning")
            return render_template('register.html')

        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                # Check duplicate email or license
                cursor.execute("SELECT user_id FROM users WHERE email = %s OR driver_license_number = %s;", (email, driver_license))
                existing = cursor.fetchone()
                if existing:
                    flash("An account with this email or driver license number already exists.", "danger")
                    conn.close()
                    return render_template('register.html')

                cursor.execute("""
                    INSERT INTO users (first_name, last_name, email, password_hash, phone, driver_license_number, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (first_name, last_name, email, password_hash, phone, driver_license, role))
                user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            session['user_id'] = user_id
            session['name'] = f"{first_name} {last_name}"
            session['email'] = email
            session['role'] = role
            flash("Registration successful! Welcome to AutoRent.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('index'))

# -------------------------------------------------------------
# Admin & Staff Operations Routes
# -------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    vehicles = []
    bookings = []
    stats = {
        'total_vehicles': 0,
        'available_vehicles': 0,
        'active_rentals': 0,
        'total_revenue': 0.00
    }

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Vehicles list
            cursor.execute("SELECT * FROM vehicles ORDER BY vehicle_id DESC;")
            vehicles = cursor.fetchall()

            # Bookings list with multilateral joins
            cursor.execute("""
                SELECT b.*, u.first_name, u.last_name, u.email, v.make, v.model, v.license_plate
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                JOIN vehicles v ON b.vehicle_id = v.vehicle_id
                ORDER BY b.booking_id DESC;
            """)
            bookings = cursor.fetchall()

            # Aggregated stats
            stats['total_vehicles'] = len(vehicles)
            stats['available_vehicles'] = sum(1 for v in vehicles if v['status'] == 'available')
            stats['active_rentals'] = sum(1 for b in bookings if b['booking_status'] in ['active', 'confirmed'])
            stats['total_revenue'] = sum(float(b['amount']) for b in bookings if b['payment_status'] == 'success')
        conn.close()
    except Exception as e:
        flash(f"Error fetching administrative metrics: {e}", "danger")

    return render_template('admin.html', vehicles=vehicles, bookings=bookings, stats=stats)

@app.route('/admin/vehicles/add', methods=['GET', 'POST'])
@admin_required
def admin_add_vehicle():
    if request.method == 'POST':
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        year = int(request.form.get('year', 2024))
        license_plate = request.form.get('license_plate', '').strip().upper()
        vehicle_type = request.form.get('vehicle_type', 'car')
        daily_rate = float(request.form.get('daily_rate', 50.0))
        status = request.form.get('status', 'available')
        image_url = request.form.get('image_url', '').strip()

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO vehicles (make, model, year, license_plate, vehicle_type, daily_rate, status, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (make, model, year, license_plate, vehicle_type, daily_rate, status, image_url))
            conn.commit()
            conn.close()
            flash(f"Vehicle '{make} {model}' added to inventory.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Failed to add vehicle: {e}", "danger")

    return render_template('admin_vehicle_form.html', vehicle=None)

@app.route('/admin/vehicles/edit/<int:vehicle_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_vehicle(vehicle_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s;", (vehicle_id,))
            vehicle = cursor.fetchone()
        conn.close()
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('admin_dashboard'))

    if not vehicle:
        flash("Vehicle not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        year = int(request.form.get('year', 2024))
        license_plate = request.form.get('license_plate', '').strip().upper()
        vehicle_type = request.form.get('vehicle_type', 'car')
        daily_rate = float(request.form.get('daily_rate', 50.0))
        status = request.form.get('status', 'available')
        image_url = request.form.get('image_url', '').strip()

        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE vehicles 
                    SET make = %s, model = %s, year = %s, license_plate = %s,
                        vehicle_type = %s, daily_rate = %s, status = %s, image_url = %s
                    WHERE vehicle_id = %s;
                """, (make, model, year, license_plate, vehicle_type, daily_rate, status, image_url, vehicle_id))
            conn.commit()
            conn.close()
            flash(f"Vehicle '{make} {model}' updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Failed to update vehicle: {e}", "danger")

    return render_template('admin_vehicle_form.html', vehicle=vehicle)

@app.route('/admin/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@admin_required
def admin_delete_vehicle(vehicle_id):
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM vehicles WHERE vehicle_id = %s;", (vehicle_id,))
        conn.commit()
        conn.close()
        flash("Vehicle deleted from fleet inventory.", "info")
    except Exception as e:
        flash(f"Failed to delete vehicle: {e}", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/vehicles/status/<int:vehicle_id>', methods=['POST'])
@admin_required
def admin_update_vehicle_status(vehicle_id):
    new_status = request.form.get('status')
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("UPDATE vehicles SET status = %s WHERE vehicle_id = %s;", (new_status, vehicle_id))
        conn.commit()
        conn.close()
        flash("Vehicle status updated.", "success")
    except Exception as e:
        flash(f"Failed to update status: {e}", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/bookings/status/<int:booking_id>', methods=['POST'])
@admin_required
def admin_update_booking_status(booking_id):
    booking_status = request.form.get('booking_status')
    payment_status = request.form.get('payment_status')

    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE bookings 
                SET booking_status = %s, payment_status = %s 
                WHERE booking_id = %s;
            """, (booking_status, payment_status, booking_id))

            # If marked completed or cancelled, make vehicle available
            if booking_status in ['completed', 'cancelled']:
                cursor.execute("""
                    UPDATE vehicles v
                    JOIN bookings b ON v.vehicle_id = b.vehicle_id
                    SET v.status = 'available'
                    WHERE b.booking_id = %s;
                """, (booking_id,))
        conn.commit()
        conn.close()
        flash(f"Booking #{booking_id} status updated.", "success")
    except Exception as e:
        flash(f"Failed to update booking: {e}", "danger")

    return redirect(url_for('admin_dashboard'))

# -------------------------------------------------------------
# Database Diagnostics & Live Credential Configuration
# -------------------------------------------------------------
@app.route('/db-status')
def db_status():
    connected, db_msg = test_connection()
    table_stats = {
        'users': {'exists': False, 'count': 0},
        'vehicles': {'exists': False, 'count': 0},
        'bookings': {'exists': False, 'count': 0}
    }

    if connected:
        try:
            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                tables = [list(row.values())[0] for row in cursor.fetchall()]
                for t in table_stats.keys():
                    if t in tables:
                        table_stats[t]['exists'] = True
                        cursor.execute(f"SELECT COUNT(*) AS c FROM `{t}`;")
                        table_stats[t]['count'] = cursor.fetchone()['c']
            conn.close()
        except Exception as e:
            db_msg += f" (Note: Database '{Config.DB_NAME}' error: {e})"

    return render_template('db_status.html', connected=connected, db_msg=db_msg, table_stats=table_stats)

@app.route('/update-db-credentials', methods=['POST'])
def update_db_credentials():
    db_host = request.form.get('db_host', '127.0.0.1').strip()
    db_user = request.form.get('db_user', 'root').strip()
    db_password = request.form.get('db_password', '')
    db_name = request.form.get('db_name', 'project').strip()

    # Update in-memory config
    Config.DB_HOST = db_host
    Config.DB_USER = db_user
    Config.DB_PASSWORD = db_password
    Config.DB_NAME = db_name

    # Write to .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        with open(env_path, 'w') as f:
            f.write(f"DB_HOST={db_host}\n")
            f.write(f"DB_PORT=3306\n")
            f.write(f"DB_USER={db_user}\n")
            f.write(f"DB_PASSWORD={db_password}\n")
            f.write(f"DB_NAME={db_name}\n")
            f.write(f"SECRET_KEY={Config.SECRET_KEY}\n")
            f.write(f"FLASK_DEBUG=True\n")
            f.write(f"PORT=5000\n")
    except Exception as e:
        flash(f"Warning: Could not save to .env: {e}", "warning")

    # Test connection with new credentials
    ok, msg = test_connection()
    if ok:
        flash("MySQL credentials updated and connection established successfully!", "success")
        # Try initializing database if not exists
        init_db()
    else:
        flash(f"Credentials updated, but MySQL test returned: {msg}", "danger")

    return redirect(url_for('db_status'))

@app.route('/reseed-db', methods=['POST'])
def reseed_db():
    if seed_sample_data():
        flash("Sample data successfully inserted into MySQL!", "success")
    else:
        flash("Failed to seed sample data. Check database logs.", "danger")
    return redirect(url_for('db_status'))

if __name__ == '__main__':
    # Initialize DB on startup if possible
    try:
        init_db()
        seed_sample_data()
    except Exception as e:
        print(f"Startup DB check note: {e}")

    print(f"\n🚗 AutoRent Vehicle Rental System is running!")
    print(f"👉 Access Web Interface at: http://127.0.0.1:{Config.PORT}\n")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.FLASK_DEBUG)
