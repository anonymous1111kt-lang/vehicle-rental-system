import pymysql
from pymysql.cursors import DictCursor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection(use_db=True):
    """
    Establish a connection to MySQL server.
    If use_db=True, connects to the configured database (Config.DB_NAME).
    Otherwise, connects to the server without selecting a specific database.
    """
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME if use_db else None,
        cursorclass=DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

def test_connection():
    """
    Test connectivity to the MySQL database.
    Returns (True, "Connected successfully") or (False, error_message).
    """
    try:
        conn = get_db_connection(use_db=False)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version;")
            row = cursor.fetchone()
            version = row['version'] if row else "Unknown"
        conn.close()
        return True, f"Connected to MySQL {version} successfully."
    except Exception as e:
        return False, str(e)

def init_db():
    """
    Initializes the database and tables according to schema.
    Also ensures compatibility if tables were previously created with fewer columns.
    """
    try:
        # Step 1: Connect without database and create database if not exists
        conn = get_db_connection(use_db=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4;")
        conn.commit()
        conn.close()

        # Step 2: Connect to the specific database
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cursor:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    phone VARCHAR(15),
                    driver_license_number VARCHAR(50) UNIQUE NOT NULL,
                    role ENUM('customer', 'admin', 'staff') DEFAULT 'customer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Vehicles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
                    make VARCHAR(50) NOT NULL,
                    model VARCHAR(50) DEFAULT '',
                    year INT DEFAULT 2024,
                    license_plate VARCHAR(20) UNIQUE NOT NULL,
                    vehicle_type ENUM('car', 'bike', 'suv', 'truck') NOT NULL,
                    daily_rate DECIMAL(10,2) NOT NULL,
                    status ENUM('available', 'rented', 'maintenance', 'damaged') DEFAULT 'available',
                    image_url VARCHAR(500) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Bookings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    vehicle_id INT NOT NULL,
                    pickup_date DATETIME NOT NULL,
                    dropoff_date DATETIME NOT NULL,
                    total_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_method ENUM('credit card', 'upi', 'cash', 'net_banking') NOT NULL,
                    payment_status ENUM('pending', 'success', 'failed', 'refunded') DEFAULT 'pending',
                    booking_status ENUM('pending', 'confirmed', 'active', 'completed', 'cancelled') DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Schema compatibility checks (in case tables were created manually without optional columns)
            _ensure_column_exists(cursor, 'vehicles', 'model', "VARCHAR(50) DEFAULT ''")
            _ensure_column_exists(cursor, 'vehicles', 'year', "INT DEFAULT 2024")
            _ensure_column_exists(cursor, 'vehicles', 'image_url', "VARCHAR(500) DEFAULT ''")
            _ensure_column_exists(cursor, 'bookings', 'total_cost', "DECIMAL(10,2) NOT NULL DEFAULT 0.00")
            _ensure_column_exists(cursor, 'bookings', 'booking_status', "ENUM('pending','confirmed','active','completed','cancelled') DEFAULT 'confirmed'")

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
        return True, "Database and tables verified successfully."
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False, str(e)

def _ensure_column_exists(cursor, table_name, column_name, column_definition):
    """Adds a column if it doesn't already exist in the specified table."""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) AS cnt 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{Config.DB_NAME}' 
              AND TABLE_NAME = '{table_name}' 
              AND COLUMN_NAME = '{column_name}';
        """)
        res = cursor.fetchone()
        if res and res['cnt'] == 0:
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition};")
            logger.info(f"Added column {column_name} to {table_name}")
    except Exception as e:
        logger.warning(f"Could not verify/add column {column_name} on {table_name}: {e}")
