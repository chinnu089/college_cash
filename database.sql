-- ============================================
-- College Cash: UPI Transaction Facilitation
-- Database Schema + Sample Data
-- ============================================

CREATE DATABASE IF NOT EXISTS college_cash;
USE college_cash;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    phone       VARCHAR(15) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    cash_balance  DECIMAL(10,2) DEFAULT 500.00,
    upi_balance   DECIMAL(10,2) DEFAULT 500.00,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exchange Requests Table
CREATE TABLE IF NOT EXISTS exchange_requests (
    request_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    request_type  ENUM('need_cash','need_upi') NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    latitude      DECIMAL(10,7),
    longitude     DECIMAL(10,7),
    status        ENUM('open','matched','cancelled') DEFAULT 'open',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    user1_id         INT NOT NULL,
    user2_id         INT NOT NULL,
    amount           DECIMAL(10,2) NOT NULL,
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status           ENUM('completed','failed') DEFAULT 'completed',
    FOREIGN KEY (user1_id) REFERENCES users(user_id),
    FOREIGN KEY (user2_id) REFERENCES users(user_id)
);

-- ============================================
-- Sample Data
-- ============================================

INSERT INTO users (name, phone, password, cash_balance, upi_balance) VALUES
('Arjun Sharma',   '9876543210', 'pass123', 1200.00, 800.00),
('Priya Nair',     '9876543211', 'pass123',  300.00, 1500.00),
('Rahul Verma',    '9876543212', 'pass123',  900.00,  600.00),
('Sneha Reddy',    '9876543213', 'pass123',  150.00, 2000.00),
('Vikram Patel',   '9876543214', 'pass123', 2000.00,  200.00);

INSERT INTO exchange_requests (user_id, request_type, amount, latitude, longitude, status) VALUES
(1, 'need_upi',  500.00, 12.9716, 77.5946, 'open'),
(2, 'need_cash', 300.00, 12.9720, 77.5950, 'open'),
(3, 'need_upi',  200.00, 12.9710, 77.5940, 'open'),
(4, 'need_cash', 700.00, 12.9730, 77.5960, 'open'),
(5, 'need_upi',  400.00, 12.9715, 77.5945, 'matched');

INSERT INTO transactions (user1_id, user2_id, amount, status) VALUES
(1, 2, 300.00, 'completed'),
(3, 4, 200.00, 'completed'),
(5, 1, 150.00, 'completed');
