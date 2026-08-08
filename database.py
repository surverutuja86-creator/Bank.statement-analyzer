import sqlite3
import os
from decimal import Decimal
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Transactions table with Decimal stored as string/TEXT for exact monetary precision
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            txn_date TEXT NOT NULL,
            description TEXT NOT NULL,
            ref_number TEXT,
            txn_type TEXT CHECK(txn_type IN ('CREDIT', 'DEBIT')) NOT NULL,
            amount TEXT NOT NULL,  -- Stored as Decimal string e.g. "1250.50"
            balance TEXT,          -- Stored as Decimal string
            category TEXT NOT NULL DEFAULT 'Uncategorized',
            is_upi BOOLEAN DEFAULT 0,
            is_salary BOOLEAN DEFAULT 0,
            is_emi BOOLEAN DEFAULT 0,
            is_subscription BOOLEAN DEFAULT 0,
            is_duplicate BOOLEAN DEFAULT 0,
            is_spike BOOLEAN DEFAULT 0,
            upload_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (upload_id) REFERENCES upload_logs (id)
        )
    ''')

    # Upload logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS upload_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            total_records INTEGER DEFAULT 0,
            total_income TEXT DEFAULT '0.00',
            total_expense TEXT DEFAULT '0.00',
            status TEXT DEFAULT 'SUCCESS',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Custom categorization rules
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classification_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            rule_type TEXT DEFAULT 'DESCRIPTION_MATCH'
        )
    ''')

    # Insert default classification rules if empty
    cursor.execute("SELECT COUNT(*) FROM classification_rules")
    if cursor.fetchone()[0] == 0:
        default_rules = [
            ('SALARY', 'Salary', 'KEYWORD'),
            ('PAYROLL', 'Salary', 'KEYWORD'),
            ('UPI', 'UPI Transfer', 'PREFIX'),
            ('SWIGGY', 'Food & Dining', 'KEYWORD'),
            ('ZOMATO', 'Food & Dining', 'KEYWORD'),
            ('RESTAURANT', 'Food & Dining', 'KEYWORD'),
            ('CAFE', 'Food & Dining', 'KEYWORD'),
            ('DMART', 'Groceries', 'KEYWORD'),
            ('BIGBASKET', 'Groceries', 'KEYWORD'),
            ('SUPERMARKET', 'Groceries', 'KEYWORD'),
            ('AMAZON', 'Shopping', 'KEYWORD'),
            ('FLIPKART', 'Shopping', 'KEYWORD'),
            ('MYNTRA', 'Shopping', 'KEYWORD'),
            ('NETFLIX', 'Subscriptions', 'KEYWORD'),
            ('SPOTIFY', 'Subscriptions', 'KEYWORD'),
            ('PRIME VIDEO', 'Subscriptions', 'KEYWORD'),
            ('YOUTUBE PREMIUM', 'Subscriptions', 'KEYWORD'),
            ('ELECTRICITY', 'Utilities', 'KEYWORD'),
            ('BESCOM', 'Utilities', 'KEYWORD'),
            ('AIRTEL', 'Utilities', 'KEYWORD'),
            ('JIO', 'Utilities', 'KEYWORD'),
            ('WATER BOARD', 'Utilities', 'KEYWORD'),
            ('EMI', 'EMI & Loans', 'KEYWORD'),
            ('HDFC LOAN', 'EMI & Loans', 'KEYWORD'),
            ('AXIS BANK EMI', 'EMI & Loans', 'KEYWORD'),
            ('MUTUAL FUND', 'Investments', 'KEYWORD'),
            ('ZERODHA', 'Investments', 'KEYWORD'),
            ('GROWW', 'Investments', 'KEYWORD'),
            ('SIP', 'Investments', 'KEYWORD'),
            ('ATM WDL', 'Cash Withdrawal', 'KEYWORD')
        ]
        cursor.executemany("INSERT INTO classification_rules (keyword, category, rule_type) VALUES (?, ?, ?)", default_rules)

    conn.commit()
    conn.close()
