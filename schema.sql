-- =======================================================
-- Vehicle Rental System Database Schema
-- Database: project
-- =======================================================

CREATE DATABASE IF NOT EXISTS project;
USE project;

-- 1. Users Table
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

-- 2. Vehicles Table
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

-- 3. Bookings & Payments Table
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    pickup_date DATETIME NOT NULL,
    dropoff_date DATETIME NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('credit card', 'upi', 'cash', 'net_banking') NOT NULL,
    payment_status ENUM('pending', 'success', 'failed', 'refunded') DEFAULT 'pending',
    booking_status ENUM('pending', 'confirmed', 'active', 'completed', 'cancelled') DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
