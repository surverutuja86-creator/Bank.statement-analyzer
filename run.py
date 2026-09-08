#!/usr/bin/env python3
"""
BankFlow AI / Smart Bank Statement Analyzer Launch Entrypoint
"""
import sys
import os

from app import app, init_db

if __name__ == '__main__':
    print("==================================================================")
    print("Starting Smart Bank Statement Analyzer Server...")
    print("   Tagline: Smart Financial Analysis for Every Bank Statement")
    print("   URL: http://127.0.0.1:5000")
    print("==================================================================")
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
