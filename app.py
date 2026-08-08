import os
import csv
import io
from functools import wraps
from decimal import Decimal, ROUND_HALF_UP
from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from database import init_db, get_db_connection
from analyzer import StatementAnalyzer

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database schema
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required. Please login.'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    return session.get('user_id', 1)

# -------------------------------------------------------------------
# PRODUCTION PAGE ROUTES
# -------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = 'default_user'
        session['full_name'] = 'Account Workspace'
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('register.html')

@app.route('/download-sample-csv')
def download_sample_csv():
    file_path = os.path.join(Config.BASE_DIR, 'sample_statement.csv')
    return send_file(file_path, as_attachment=True, download_name='sample_bank_statement.csv', mimetype='text/csv')

# -------------------------------------------------------------------
# USER AUTHENTICATION API
# -------------------------------------------------------------------
@app.route('/api/auth/register', methods=['POST'])
def register_api():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()

    if not username or not email or not password:
        return jsonify({'error': 'Please fill in all required fields.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        pw_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
            (username, email, pw_hash, full_name or username)
        )
        conn.commit()
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        session['full_name'] = full_name or username
        
        return jsonify({'message': f'Welcome {full_name or username}! Account created successfully.', 'redirect': '/dashboard'})
    except Exception:
        conn.rollback()
        return jsonify({'error': 'Username or Email already registered.'}), 400
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login_api():
    data = request.get_json() or {}
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username_or_email or not password:
        return jsonify({'error': 'Please enter username/email and password.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        return jsonify({'message': f'Welcome back, {user["full_name"]}!', 'redirect': '/dashboard'})
    
    return jsonify({'error': 'Invalid username/email or password.'}), 401

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def logout_api():
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False, 'user': {'id': 1, 'username': 'default_user', 'full_name': 'Account Workspace'}})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({'logged_in': True, 'user': dict(user)})
    return jsonify({'logged_in': False, 'user': {'id': 1, 'username': 'default_user', 'full_name': 'Account Workspace'}})

# -------------------------------------------------------------------
# PRODUCTION STATEMENT PARSING & UPLOAD API
# -------------------------------------------------------------------
@app.route('/api/upload', methods=['POST'])
def upload_statement():
    user_id = get_current_user_id()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported file format .{ext}. Upload a CSV or Excel (.xlsx) file.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT keyword, category, rule_type FROM classification_rules")
    rules = cursor.fetchall()
    analyzer = StatementAnalyzer(rules)

    raw_txns = []

    try:
        if ext == 'csv':
            stream = io.StringIO(file.stream.read().decode("utf-8", errors="ignore"))
            reader = csv.DictReader(stream)
            
            for row in reader:
                r_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k}
                txn_date = r_clean.get('date') or r_clean.get('txn_date') or r_clean.get('value date') or '2026-07-01'
                desc = r_clean.get('description') or r_clean.get('narration') or r_clean.get('particulars') or r_clean.get('details') or 'Transaction'
                ref = r_clean.get('ref_number') or r_clean.get('chq/ref no') or r_clean.get('reference') or ''
                
                credit_val = r_clean.get('credit') or r_clean.get('deposit') or '0'
                debit_val = r_clean.get('debit') or r_clean.get('withdrawal') or '0'
                amt_raw = r_clean.get('amount')
                
                cr_dec = StatementAnalyzer.to_decimal(credit_val)
                db_dec = StatementAnalyzer.to_decimal(debit_val)
                
                if cr_dec > Decimal('0.00'):
                    txn_type = 'CREDIT'
                    amt_dec = cr_dec
                elif db_dec > Decimal('0.00'):
                    txn_type = 'DEBIT'
                    amt_dec = db_dec
                elif amt_raw:
                    amt_dec = StatementAnalyzer.to_decimal(amt_raw)
                    type_raw = (r_clean.get('type') or r_clean.get('txn_type') or '').upper()
                    txn_type = 'CREDIT' if 'CR' in type_raw or amt_dec > 0 else 'DEBIT'
                    amt_dec = abs(amt_dec)
                else:
                    continue

                analysis = analyzer.analyze_transaction(txn_date, desc, amt_dec, txn_type)
                raw_txns.append({
                    'txn_date': txn_date,
                    'description': desc,
                    'ref_number': ref,
                    'txn_type': txn_type,
                    'amount': str(amt_dec),
                    'balance': '0.00',
                    'category': analysis['category'],
                    'is_upi': 1 if analysis['is_upi'] else 0,
                    'is_salary': 1 if analysis['is_salary'] else 0,
                    'is_emi': 1 if analysis['is_emi'] else 0,
                    'is_subscription': 1 if analysis['is_subscription'] else 0
                })
        else:
            try:
                import pandas as pd
                df = pd.read_excel(file)
                for _, row in df.iterrows():
                    r_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    txn_date = r_clean.get('date', '2026-07-01')
                    desc = r_clean.get('description', 'Excel Transaction')
                    amt_dec = StatementAnalyzer.to_decimal(r_clean.get('amount', '0'))
                    txn_type = 'CREDIT' if 'CR' in r_clean.get('type', '').upper() else 'DEBIT'
                    analysis = analyzer.analyze_transaction(txn_date, desc, amt_dec, txn_type)
                    raw_txns.append({
                        'txn_date': txn_date,
                        'description': desc,
                        'ref_number': '',
                        'txn_type': txn_type,
                        'amount': str(amt_dec),
                        'balance': '0.00',
                        'category': analysis['category'],
                        'is_upi': 1 if analysis['is_upi'] else 0,
                        'is_salary': 1 if analysis['is_salary'] else 0,
                        'is_emi': 1 if analysis['is_emi'] else 0,
                        'is_subscription': 1 if analysis['is_subscription'] else 0
                    })
            except ImportError:
                return jsonify({'error': 'Excel parser requires pandas library. Please upload CSV format.'}), 400

        final_txns = analyzer.detect_anomalies(raw_txns)
        
        tot_inc = Decimal('0.00')
        tot_exp = Decimal('0.00')

        for t in final_txns:
            amt = StatementAnalyzer.to_decimal(t['amount'])
            if t['txn_type'] == 'CREDIT':
                tot_inc += amt
            else:
                tot_exp += amt

        cursor.execute(
            "INSERT INTO upload_logs (user_id, filename, file_size, total_records, total_income, total_expense) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, filename, 5120, len(final_txns), str(tot_inc), str(tot_exp))
        )
        upload_id = cursor.lastrowid

        for t in final_txns:
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
        return jsonify({
            'message': f'Statement "{filename}" parsed and saved successfully!',
            'filename': filename,
            'records_processed': len(final_txns),
            'total_income': f"₹{tot_inc:,.2f}",
            'total_expense': f"₹{tot_exp:,.2f}"
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500
    finally:
        conn.close()

# -------------------------------------------------------------------
# CLEAR TRANSACTIONS API
# -------------------------------------------------------------------
@app.route('/api/transactions/clear', methods=['POST'])
def clear_transactions():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM upload_logs WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Transaction history cleared from SQLite database!'})

# -------------------------------------------------------------------
# FINANCIAL ANALYTICS & DASHBOARD API
# -------------------------------------------------------------------
@app.route('/api/analytics/summary', methods=['GET'])
def get_summary():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT txn_type, amount FROM transactions WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    tot_income = Decimal('0.00')
    tot_expense = Decimal('0.00')

    for r in rows:
        amt = StatementAnalyzer.to_decimal(r['amount'])
        if r['txn_type'] == 'CREDIT':
            tot_income += amt
        else:
            tot_expense += amt

    net_savings = tot_income - tot_expense
    savings_rate = (net_savings / tot_income * Decimal('100.00')).quantize(Decimal('0.1')) if tot_income > Decimal('0.00') else Decimal('0.0')

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND is_duplicate = 1", (user_id,))
    dup_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND is_spike = 1", (user_id,))
    spike_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND is_subscription = 1", (user_id,))
    sub_count = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        'total_income': f"₹{tot_income:,.2f}",
        'total_expense': f"₹{tot_expense:,.2f}",
        'net_savings': f"₹{net_savings:,.2f}",
        'savings_rate': float(savings_rate),
        'anomalies_count': dup_count + spike_count,
        'duplicate_debits': dup_count,
        'spending_spikes': spike_count,
        'subscriptions_count': sub_count
    })

@app.route('/api/analytics/categories', methods=['GET'])
def get_category_breakdown():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, amount FROM transactions 
        WHERE user_id = ? AND txn_type = 'DEBIT'
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    cat_totals = {}
    for r in rows:
        cat = r['category']
        amt = StatementAnalyzer.to_decimal(r['amount'])
        cat_totals[cat] = cat_totals.get(cat, Decimal('0.00')) + amt

    labels = list(cat_totals.keys())
    values = [float(cat_totals[k]) for k in labels]

    return jsonify({'labels': labels, 'values': values})

@app.route('/api/analytics/monthly', methods=['GET'])
def get_monthly_trend():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT strftime('%Y-%m', txn_date) as month, txn_type, amount 
        FROM transactions 
        WHERE user_id = ?
        ORDER BY month ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    months = {}
    for r in rows:
        m = r['month'] or '2026-07'
        if m not in months:
            months[m] = {'income': Decimal('0.00'), 'expense': Decimal('0.00')}
        amt = StatementAnalyzer.to_decimal(r['amount'])
        if r['txn_type'] == 'CREDIT':
            months[m]['income'] += amt
        else:
            months[m]['expense'] += amt

    sorted_months = sorted(months.keys())
    labels = sorted_months
    income_vals = [float(months[m]['income']) for m in sorted_months]
    expense_vals = [float(months[m]['expense']) for m in sorted_months]

    return jsonify({'labels': labels, 'income': income_vals, 'expense': expense_vals})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    user_id = get_current_user_id()
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()
    flag = request.args.get('flag', '').strip()
    limit = int(request.args.get('limit', 100))

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if category and category != 'All':
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (description LIKE ? OR ref_number LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if flag == 'upi':
        query += " AND is_upi = 1"
    elif flag == 'salary':
        query += " AND is_salary = 1"
    elif flag == 'emi':
        query += " AND is_emi = 1"
    elif flag == 'subscription':
        query += " AND is_subscription = 1"
    elif flag == 'duplicate':
        query += " AND is_duplicate = 1"
    elif flag == 'spike':
        query += " AND is_spike = 1"

    query += " ORDER BY txn_date DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        amt = StatementAnalyzer.to_decimal(r['amount'])
        result.append({
            'id': r['id'],
            'date': r['txn_date'],
            'description': r['description'],
            'ref_number': r['ref_number'],
            'type': r['txn_type'],
            'amount_formatted': f"₹{amt:,.2f}",
            'amount_raw': float(amt),
            'category': r['category'],
            'is_upi': bool(r['is_upi']),
            'is_salary': bool(r['is_salary']),
            'is_emi': bool(r['is_emi']),
            'is_subscription': bool(r['is_subscription']),
            'is_duplicate': bool(r['is_duplicate']),
            'is_spike': bool(r['is_spike'])
        })

    return jsonify({'transactions': result, 'count': len(result)})

if __name__ == '__main__':
    print("FinPulse AI server starting at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
