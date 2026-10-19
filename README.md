# AutoRent — Vehicle Rental System (Python + MySQL + Web Frontend)

A full-stack, internship-ready **Vehicle Rental Management System** powered by a **Python (Flask)** backend, modern responsive **Bootstrap 5** frontend, and a high-performance relational **MySQL** database.

---

## 🌟 Key Features

1. **Fleet Catalog & Dynamic Search**:
   - Browse complete vehicle inventory with high-resolution imagery and specs.
   - Filter by vehicle classification (`car`, `suv`, `truck`, `bike`).
   - Filter by live availability (`available`, `rented`, `maintenance`).
   - Instant search across vehicle make, model, and license plate.

2. **Customer Reservation & Settlement Flow**:
   - Interactive date picker for pickup and dropoff windows.
   - Real-time client-side rate calculator (days × daily rate).
   - Multi-modality settlement options (`credit card`, `upi`, `cash`, `net_banking`).
   - Instant vehicle status synchronization (marks vehicle `rented` upon booking).

3. **Customer Booking Hub (`My Bookings`)**:
   - Track active, upcoming, completed, and cancelled reservations.
   - Self-service cancellation with automatic status updates and refunds.

4. **Staff & Administrative Operations Portal**:
   - Real-time KPI dashboard: Total Fleet, Available Fleet, Active Rentals, Gross Revenue.
   - Full CRUD over vehicle assets: Add, Edit, Delete, Toggle Status (`available`, `rented`, `maintenance`, `damaged`).
   - Transaction & Booking log with multilateral joins and status updates.

5. **Self-Healing MySQL Connection & Diagnostic Suite**:
   - Live database status monitoring page (`/db-status`).
   - In-browser MySQL credential manager (updates `.env` on the fly).
   - One-click sample data seeder.
   - Dedicated CLI diagnostic scripts (`test_connection.py` and `setup_db.py`).

---

## 📂 Project Structure

```
vehicle_rental_system/
├── app.py                # Main Flask web application and routing
├── config.py             # Configuration loader from environment / .env
├── database.py           # MySQL connection pool, query execution, and migrations
├── seed_data.py          # Rich sample fleet, users, and booking logs
├── setup_db.py           # CLI database initialization script
├── test_connection.py    # CLI database diagnostic script
├── schema.sql            # Clean MySQL DDL schema
├── requirements.txt      # Python dependencies
├── run.sh                # Executable startup launcher
├── .env                  # MySQL host, user, password, and port settings
├── templates/            # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── book.html
│   ├── my_bookings.html
│   ├── login.html
│   ├── register.html
│   ├── admin.html
│   ├── admin_vehicle_form.html
│   └── db_status.html
└── static/
    └── css/
        └── style.css
```

---

## 🗄️ Database Architecture (MySQL)

Matches your relational blueprint:

- **`users`**:
  - `user_id` INT AUTO_INCREMENT PRIMARY KEY
  - `first_name`, `last_name`, `email` (UNIQUE), `password_hash`, `phone`
  - `driver_license_number` (UNIQUE), `role` ENUM('customer', 'admin', 'staff')
- **`vehicles`**:
  - `vehicle_id` INT AUTO_INCREMENT PRIMARY KEY
  - `make`, `model`, `year`, `license_plate` (UNIQUE)
  - `vehicle_type` ENUM('car', 'bike', 'suv', 'truck')
  - `daily_rate` DECIMAL(10,2)
  - `status` ENUM('available', 'rented', 'maintenance', 'damaged')
  - `image_url` VARCHAR(500)
- **`bookings`**:
  - `booking_id` INT AUTO_INCREMENT PRIMARY KEY
  - `user_id` FK -> `users.user_id` (CASCADE)
  - `vehicle_id` FK -> `vehicles.vehicle_id` (CASCADE)
  - `pickup_date`, `dropoff_date`, `total_cost`, `amount`
  - `payment_method` ENUM('credit card', 'upi', 'cash', 'net_banking')
  - `payment_status` ENUM('pending', 'success', 'failed', 'refunded')
  - `booking_status` ENUM('pending', 'confirmed', 'active', 'completed', 'cancelled')

---

## 🚀 Quick Start Guide

### 1. Configure MySQL Credentials

Open `/home/useer456/vehicle_rental_system/.env` and enter your MySQL root password:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=project
```

### 2. Test Connection & Initialize Database

Run the diagnostic tool:
```bash
cd /home/useer456/vehicle_rental_system
./venv/bin/python test_connection.py
```

Then initialize the schema and populate sample data:
```bash
./venv/bin/python setup_db.py
```

### 3. Launch the Web Application

Simply run:
```bash
cd /home/useer456/vehicle_rental_system
./run.sh
```
Or:
```bash
./venv/bin/python app.py
```

Open your browser at **http://localhost:5000** (or `http://127.0.0.1:5000`).

---

## 🔑 Pre-Seeded Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@rental.com` | `admin123` |
| **Customer** | `john.doe@example.com` | `customer123` |
| **Staff** | `staff@rental.com` | `staff123` |

*(Quick-login buttons are also provided directly on the sign-in page for instant testing.)*
