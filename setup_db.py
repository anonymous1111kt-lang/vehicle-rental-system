#!/usr/bin/env python3
"""
Database setup script for Vehicle Rental System.
Usage:
    python setup_db.py [--no-seed]
"""
import sys
from config import Config
from database import init_db
from seed_data import seed_sample_data

def main():
    print("=" * 60)
    print("  Vehicle Rental System - Database Setup & Initialization")
    print("=" * 60)
    print(f"Target Database: {Config.DB_NAME} on {Config.DB_HOST}:{Config.DB_PORT}")
    
    # 1. Initialize schema
    print("\n[1/2] Creating database and tables if not already present...")
    ok, msg = init_db()
    if not ok:
        print(f"❌ Failed to initialize database: {msg}")
        print("\nPlease check your credentials in `.env` and make sure MySQL is running.")
        sys.exit(1)
    print(f"✅ {msg}")

    # 2. Seed data
    if '--no-seed' in sys.argv:
        print("\n[2/2] Skipping seed data (--no-seed flag supplied).")
    else:
        print("\n[2/2] Checking and inserting sample data (vehicles, users, bookings)...")
        if seed_sample_data():
            print("✅ Sample data verified/inserted successfully!")
        else:
            print("⚠️  Could not insert sample data (check logs).")

    print("\n" + "=" * 60)
    print("🚀 Setup complete! You can now start the web app with:")
    print("    python app.py")
    print("=" * 60)

if __name__ == '__main__':
    main()
