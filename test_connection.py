#!/usr/bin/env python3
"""
Test connection script for Vehicle Rental System MySQL database.
Usage:
    python test_connection.py
"""
import sys
from config import Config
from database import test_connection, get_db_connection

def main():
    print("=" * 60)
    print("  Vehicle Rental System - Database Connection Diagnostic")
    print("=" * 60)
    print(f"Host:     {Config.DB_HOST}")
    print(f"Port:     {Config.DB_PORT}")
    print(f"User:     {Config.DB_USER}")
    print(f"Password: {'*' * len(Config.DB_PASSWORD) if Config.DB_PASSWORD else '(empty)'}")
    print(f"Database: {Config.DB_NAME}")
    print("-" * 60)

    # 1. Test Server Connectivity
    print("[1/3] Testing MySQL Server connectivity...")
    success, msg = test_connection()
    if not success:
        print(f"❌ Failed to connect to MySQL server: {msg}")
        print("\nTroubleshooting tips:")
        print("  1. Ensure MySQL server is running: `sudo systemctl status mysql`")
        print("  2. Verify your password in `.env` file (DB_PASSWORD=...)")
        print("  3. Verify username in `.env` (default is root)")
        sys.exit(1)
    else:
        print(f"✅ {msg}")

    # 2. Check Database existence
    print(f"\n[2/3] Checking if database '{Config.DB_NAME}' exists...")
    try:
        conn = get_db_connection(use_db=False)
        with conn.cursor() as cur:
            cur.execute("SHOW DATABASES;")
            dbs = [row['Database'] for row in cur.fetchall()]
        conn.close()

        if Config.DB_NAME in dbs:
            print(f"✅ Database '{Config.DB_NAME}' exists.")
        else:
            print(f"⚠️  Database '{Config.DB_NAME}' does not exist yet. Run `python setup_db.py` to create it.")
    except Exception as e:
        print(f"❌ Error listing databases: {e}")
        sys.exit(1)

    # 3. Check Tables
    print("\n[3/3] Checking tables inside database...")
    try:
        conn = get_db_connection(use_db=True)
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cur.fetchall()]
            print(f"Found tables: {tables}")
            
            for t in ['users', 'vehicles', 'bookings']:
                if t in tables:
                    cur.execute(f"SELECT COUNT(*) AS c FROM `{t}`;")
                    cnt = cur.fetchone()['c']
                    print(f"  • {t}: {cnt} rows")
                else:
                    print(f"  • {t}: MISSING")
        conn.close()
        print("\n🎉 Connection test completed successfully!")
    except Exception as e:
        print(f"⚠️  Could not connect to database '{Config.DB_NAME}': {e}")
        print("Run `python setup_db.py` to create database and tables.")

if __name__ == '__main__':
    main()
