import random
from decimal import Decimal
from database import get_db_connection
from analyzer import StatementAnalyzer

def generate_sample_dataset(user_id=1):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if sample data already exists for user
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Ensure user 1 exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, username, email, password_hash, full_name) VALUES (?, ?, ?, ?, ?)",
            (1, 'demo_user', 'demo@bankflow.ai', 'pbkdf2:sha256:dummyhash', 'Alex Morgan')
        )

    # Fetch classification rules
    cursor.execute("SELECT keyword, category, rule_type FROM classification_rules")
    rules = cursor.fetchall()
    analyzer = StatementAnalyzer(rules)

    sample_txns = [
        # Date, Description, Ref, Type, Amount
        ('2026-06-01', 'ACH CREDIT - TECHCORP PVT LTD SALARY MAY 2026', 'SAL20260601001', 'CREDIT', '125000.00'),
        ('2026-06-02', 'UPI/SWIGGY/swiggy@paytm/Order #84920', 'UPI602001', 'DEBIT', '480.50'),
        ('2026-06-03', 'ACH DEBIT HDFC HOME LOAN EMI 481920', 'EMI20260603', 'DEBIT', '32500.00'),
        ('2026-06-04', 'UPI/DMART/dmart@icici/Groceries Ref 19283', 'UPI604002', 'DEBIT', '4250.00'),
        ('2026-06-05', 'NETFLIX DIGITAL RECURRING SUBSCRIPTION', 'SUB92019', 'DEBIT', '649.00'),
        ('2026-06-06', 'UPI/ZOMATO/zomato@axis/Dinner Delivery', 'UPI606003', 'DEBIT', '890.00'),
        ('2026-06-07', 'ACH DEBIT MUTUAL FUND SIP ZERODHA', 'INV607001', 'DEBIT', '15000.00'),
        ('2026-06-08', 'UPI/ELECTRICITY BOARD/bescom@sbi/Bill Payment', 'UPI608004', 'DEBIT', '2150.00'),
        ('2026-06-09', 'ATM WDL - HDFC BANK KORAMANGALA BR', 'ATM609001', 'DEBIT', '5000.00'),
        ('2026-06-10', 'POS/AMAZON INDIA/ELECTRONICS PURCHASE', 'POS610001', 'DEBIT', '48500.00'), # SPENDING SPIKE!
        ('2026-06-11', 'UPI/SPOTIFY/spotify@paytm/Music Monthly', 'UPI611005', 'DEBIT', '119.00'),
        ('2026-06-12', 'UPI/SWIGGY/swiggy@paytm/Lunch Combo', 'UPI612006', 'DEBIT', '350.00'),
        ('2026-06-13', 'POS/MYNTRA/FASHION APPAREL', 'POS613002', 'DEBIT', '3499.00'),
        ('2026-06-14', 'UPI/FREELANCE PAYMENT/client@okicici', 'UPI614007', 'CREDIT', '20000.00'),
        ('2026-06-15', 'UPI/AIRTEL BILL/airtel@paytm/Fiber Broadband', 'UPI615008', 'DEBIT', '1179.00'),
        ('2026-06-16', 'UPI/AIRTEL BILL/airtel@paytm/Fiber Broadband', 'UPI615008', 'DEBIT', '1179.00'), # DUPLICATE DEBIT!
        ('2026-06-18', 'UPI/BIGBASKET/bigbasket@hdfc/Weekly Groceries', 'UPI618009', 'DEBIT', '2840.00'),
        ('2026-06-20', 'UPI/UBER RIDES/uber@paytm/Commute to Office', 'UPI620010', 'DEBIT', '420.00'),
        ('2026-06-22', 'DIVIDEND CREDIT - TATA MOTORS LTD', 'DIV20260622', 'CREDIT', '4500.00'),
        ('2026-06-25', 'UPI/SWIGGY/swiggy@paytm/Dinner Party', 'UPI625011', 'DEBIT', '1450.00'),
        ('2026-06-28', 'POS/FUEL STATION/HPCL PETROL', 'POS628003', 'DEBIT', '3000.00'),
        ('2026-07-01', 'ACH CREDIT - TECHCORP PVT LTD SALARY JUN 2026', 'SAL20260701001', 'CREDIT', '125000.00'),
        ('2026-07-03', 'ACH DEBIT HDFC HOME LOAN EMI 481921', 'EMI20260703', 'DEBIT', '32500.00'),
        ('2026-07-05', 'NETFLIX DIGITAL RECURRING SUBSCRIPTION', 'SUB92020', 'DEBIT', '649.00'),
        ('2026-07-07', 'ACH DEBIT MUTUAL FUND SIP ZERODHA', 'INV607002', 'DEBIT', '15000.00'),
        ('2026-07-10', 'UPI/FLIPKART/flipkart@icici/Home Appliances', 'UPI710001', 'DEBIT', '12999.00')
    ]

    # Process transactions through analyzer
    parsed_list = []
    total_inc = Decimal('0.00')
    total_exp = Decimal('0.00')

    for t_date, desc, ref, t_type, amt_str in sample_txns:
        amt_dec = StatementAnalyzer.to_decimal(amt_str)
        if t_type == 'CREDIT':
            total_inc += amt_dec
        else:
            total_exp += amt_dec

        analysis = analyzer.analyze_transaction(t_date, desc, amt_dec, t_type)
        parsed_list.append({
            'txn_date': t_date,
            'description': desc,
            'ref_number': ref,
            'txn_type': t_type,
            'amount': str(amt_dec),
            'balance': '185000.00',
            'category': analysis['category'],
            'is_upi': 1 if analysis['is_upi'] else 0,
            'is_salary': 1 if analysis['is_salary'] else 0,
            'is_emi': 1 if analysis['is_emi'] else 0,
            'is_subscription': 1 if analysis['is_subscription'] else 0
        })

    # Run anomaly detection
    parsed_list = analyzer.detect_anomalies(parsed_list)

    # Insert upload log entry
    cursor.execute(
        "INSERT INTO upload_logs (user_id, filename, file_size, total_records, total_income, total_expense) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, 'HDFC_Statement_JuneJuly_2026.csv', 4820, len(parsed_list), str(total_inc), str(total_exp))
    )
    upload_id = cursor.lastrowid

    # Insert transactions
    for t in parsed_list:
        cursor.execute('''
            INSERT INTO transactions (
                user_id, txn_date, description, ref_number, txn_type, amount, balance,
                category, is_upi, is_salary, is_emi, is_subscription, is_duplicate, is_spike, upload_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, t['txn_date'], t['description'], t['ref_number'], t['txn_type'],
            t['amount'], t['balance'], t['category'], t['is_upi'], t['is_salary'],
            t['is_emi'], t['is_subscription'], 1 if t.get('is_duplicate') else 0,
            1 if t.get('is_spike') else 0, upload_id
        ))

    conn.commit()
    conn.close()
