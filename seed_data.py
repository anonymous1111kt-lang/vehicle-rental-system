import datetime
from werkzeug.security import generate_password_hash
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

def seed_sample_data():
    """Seeds sample data into the database if tables are empty."""
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Check users
            cursor.execute("SELECT COUNT(*) AS count FROM users;")
            user_count = cursor.fetchone()['count']
            
            if user_count == 0:
                logger.info("Seeding initial users...")
                users = [
                    (
                        "Admin", "Officer", "admin@rental.com",
                        generate_password_hash("admin123"), "555-0100",
                        "DL-ADMIN-001", "admin"
                    ),
                    (
                        "Alex", "Staff", "staff@rental.com",
                        generate_password_hash("staff123"), "555-0101",
                        "DL-STAFF-002", "staff"
                    ),
                    (
                        "John", "Doe", "john.doe@example.com",
                        generate_password_hash("customer123"), "555-0199",
                        "DL-CUSTOMER-003", "customer"
                    ),
                    (
                        "Sarah", "Connor", "sarah@example.com",
                        generate_password_hash("customer123"), "555-0188",
                        "DL-CUSTOMER-004", "customer"
                    )
                ]
                cursor.executemany("""
                    INSERT INTO users (first_name, last_name, email, password_hash, phone, driver_license_number, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, users)

            # Check vehicles
            cursor.execute("SELECT COUNT(*) AS count FROM vehicles;")
            vehicle_count = cursor.fetchone()['count']

            if vehicle_count == 0:
                logger.info("Seeding initial vehicles...")
                vehicles = [
                    (
                        "Tesla", "Model 3", 2024, "CA-TSLA-24", "car",
                        85.00, "available",
                        "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Honda", "Civic Touring", 2023, "NY-HND-99", "car",
                        45.00, "available",
                        "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "BMW", "M4 Competition", 2024, "FL-BMW-44", "car",
                        140.00, "available",
                        "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Toyota", "RAV4 Hybrid", 2023, "TX-TYT-88", "suv",
                        65.00, "available",
                        "https://images.unsplash.com/photo-1581540222194-0def2dda95b8?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Jeep", "Wrangler Rubicon", 2024, "CO-JEP-07", "suv",
                        110.00, "rented",
                        "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Ford", "F-150 Lightning", 2023, "WA-FRD-15", "truck",
                        95.00, "available",
                        "https://images.unsplash.com/photo-1559416523-140ddc3d238c?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Chevrolet", "Silverado 1500", 2022, "AZ-CHV-50", "truck",
                        90.00, "maintenance",
                        "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Ducati", "Monster 937", 2023, "NV-DCT-93", "bike",
                        75.00, "available",
                        "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=800&q=80"
                    ),
                    (
                        "Kawasaki", "Ninja 650", 2024, "OR-KWK-65", "bike",
                        55.00, "available",
                        "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=800&q=80"
                    )
                ]
                cursor.executemany("""
                    INSERT INTO vehicles (make, model, year, license_plate, vehicle_type, daily_rate, status, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, vehicles)

            # Check bookings
            cursor.execute("SELECT COUNT(*) AS count FROM bookings;")
            booking_count = cursor.fetchone()['count']

            if booking_count == 0:
                logger.info("Seeding initial bookings...")
                now = datetime.datetime.now()
                # Find customer user_id and vehicle_id
                cursor.execute("SELECT user_id FROM users WHERE email = 'john.doe@example.com' LIMIT 1;")
                john = cursor.fetchone()
                cursor.execute("SELECT vehicle_id FROM vehicles WHERE license_plate = 'CO-JEP-07' LIMIT 1;")
                jeep = cursor.fetchone()
                cursor.execute("SELECT vehicle_id FROM vehicles WHERE license_plate = 'CA-TSLA-24' LIMIT 1;")
                tesla = cursor.fetchone()

                if john and jeep and tesla:
                    bookings = [
                        (
                            john['user_id'], jeep['vehicle_id'],
                            now - datetime.timedelta(days=1),
                            now + datetime.timedelta(days=2),
                            330.00,
                            now - datetime.timedelta(days=1),
                            330.00,
                            "credit card", "success", "active"
                        ),
                        (
                            john['user_id'], tesla['vehicle_id'],
                            now - datetime.timedelta(days=7),
                            now - datetime.timedelta(days=4),
                            255.00,
                            now - datetime.timedelta(days=7),
                            255.00,
                            "upi", "success", "completed"
                        )
                    ]
                    cursor.executemany("""
                        INSERT INTO bookings (user_id, vehicle_id, pickup_date, dropoff_date, total_cost, payment_date, amount, payment_method, payment_status, booking_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, bookings)

        conn.commit()
        conn.close()
        logger.info("Sample data seeding finished.")
        return True
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        return False

if __name__ == '__main__':
    seed_sample_data()
