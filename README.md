# Smart Bank Statement Analyzer 🚀

> **"Smart Financial Analysis for Every Bank Statement"**

A high-performance, privacy-focused bank statement parsing, categorization, and anomaly detection engine built with **Python**, **Flask**, **SQLite**, and **Chart.js**.

---

## 🌟 Key Features

1. **CSV & Excel Upload**: Universal ingest engine supporting HDFC, ICICI, SBI, Axis, and international bank CSV/Excel statements.
2. **Automatic Transaction Categorization**: Pattern-matching classifier categorizing Groceries, Food & Dining, Utilities, Shopping, Investments, and Loans.
3. **UPI Detection**: Regex parsing for VPA handles (`@okaxis`, `@ybl`, `@paytm`) to distinguish P2P transfers from P2M merchant expenses.
4. **Salary Detection**: Auto-identifies recurring monthly payroll credits (`ACH CREDIT`, `PAYROLL`, employer credits).
5. **EMI Detection**: Pinpoints monthly loan repayments, tenure tracking, and credit card EMIs.
6. **Subscription Detection**: Flags recurring SaaS, streaming, and membership debits (Netflix, Spotify, AWS, Prime).
7. **Duplicate Debit Detection**: Flags identical charge amounts executed within short 48-hour time windows.
8. **Spending Spike Detection**: Outlier detection engine flagging sudden surge debits > 2.5x the rolling 30-day average.
9. **Monthly Expense Analysis**: Categorical breakdowns, cash flow momentum metrics, and month-over-month burn rate.
10. **SQLite Database Storage**: Relational schema storing normalized transaction entries, upload logs, and classification rules.
11. **Decimal Precision for Money**: Native Python `Decimal` data types preventing IEEE-754 binary floating-point rounding errors.
12. **Rule-Based Classification**: Configurable priority keyword rules engine for custom tags and merchant mapping.

---

## 🏗️ Project Structure

```
bank-statement-analyzer/
├── app.py                      # Flask REST API server & web routes
├── run.py                      # Application entrypoint script
├── config.py                   # Flask & database configuration
├── database.py                 # SQLite database schema initialization
├── analyzer.py                 # Core analysis engine (categorization & anomaly detection)
├── sample_data_generator.py    # Seeds realistic bank statement demo dataset
├── sample_statement.csv        # Pre-formatted sample statement for testing
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment configuration (Gunicorn WSGI)
├── templates/
│   └── index.html              # Main single-page web app with 8 semantic sections
└── static/
    ├── css/
    │   └── styles.css          # Modern FinTech glassmorphism styling
    ├── js/
    │   └── app.js              # Client script (Chart.js init, table filters, animated counters)
    └── images/
        └── hero-illustration.jpg
```

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask, Werkzeug, Pandas, Openpyxl
- **Database**: SQLite3 (native relational database with `Decimal` string serialization)
- **Financial Precision**: Python `decimal.Decimal` module
- **Frontend**: HTML5, CSS3 (Glassmorphism, Flexbox, Grid), JavaScript ES6+
- **Visualizations**: Chart.js (Interactive Doughnut & Bar charts)
- **Icons & Fonts**: FontAwesome 6, Google Fonts (*Plus Jakarta Sans* & *Outfit*)

---

## ⚡ Quickstart Guide

### 1. Clone & Navigate to Project
```bash
cd C:\Users\tsurv\.gemini\antigravity\scratch\bank-statement-analyzer
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run Application
```bash
python run.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/upload` | `POST` | Upload & parse a CSV/Excel statement file |
| `GET /api/transactions` | `GET` | Query transactions with search, category, and flag filters |
| `GET /api/analytics/summary` | `GET` | Fetch Total Income, Total Expenses, Net Savings, and Savings Rate |
| `GET /api/analytics/categories` | `GET` | Fetch category distribution for Doughnut Chart |
| `GET /api/analytics/monthly` | `GET` | Fetch 6-month income vs expense trend for Bar Chart |
| `POST /api/seed-demo` | `POST` | Reset demo dataset in SQLite |

---

## 🗄️ SQLite Database Schema

### `transactions` Table
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id`: INTEGER NOT NULL
- `txn_date`: TEXT (Format: YYYY-MM-DD)
- `description`: TEXT NOT NULL
- `ref_number`: TEXT
- `txn_type`: TEXT ('CREDIT' or 'DEBIT')
- `amount`: TEXT (Stored as Decimal string e.g. "125000.00")
- `balance`: TEXT (Stored as Decimal string)
- `category`: TEXT NOT NULL
- `is_upi`: BOOLEAN (0 or 1)
- `is_salary`: BOOLEAN (0 or 1)
- `is_emi`: BOOLEAN (0 or 1)
- `is_subscription`: BOOLEAN (0 or 1)
- `is_duplicate`: BOOLEAN (0 or 1)
- `is_spike`: BOOLEAN (0 or 1)

---

## 💡 How to Test Uploads

1. Navigate to the **Dashboard** section on `http://127.0.0.1:5000#dashboard`.
2. Drag and drop the included `sample_statement.csv` file into the upload dropzone.
3. The server will parse the file using `StatementAnalyzer`, detect categories, flag duplicate debits and spending spikes, store the entries in SQLite with exact `Decimal` precision, and automatically update the Chart.js visualizations and transaction table!

---

## 📜 License & Copyright

© 2026 Smart Bank Statement Analyzer. Made with ❤️ using Python & SQLite.
