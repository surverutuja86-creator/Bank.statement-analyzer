import os
from decimal import Decimal

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'finpulse-secret-key-super-secure-2026')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'bank_analyzer.db')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Financial precision default context
    CURRENCY_SYMBOL = '₹'
    DEFAULT_TAX_RATE = Decimal('0.00')
