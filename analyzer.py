import re
from decimal import Decimal, ROUND_HALF_UP

class StatementAnalyzer:
    def __init__(self, classification_rules=None):
        self.rules = classification_rules or []
        
    @staticmethod
    def to_decimal(val):
        """Converts currency string/float to exact Decimal with 2 decimal places."""
        if val is None or val == '':
            return Decimal('0.00')
        if isinstance(val, (int, float)):
            val = str(val)
        # Clean currency characters
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        if not cleaned or cleaned == '-':
            return Decimal('0.00')
        return Decimal(cleaned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def analyze_transaction(self, txn_date, description, amount_dec, txn_type):
        """
        Analyzes a single transaction and returns categorization & tag flags.
        """
        desc_upper = description.upper()
        
        is_upi = False
        is_salary = False
        is_emi = False
        is_subscription = False
        category = 'Miscellaneous'
        
        # 1. UPI Detection
        if 'UPI/' in desc_upper or '@' in desc_upper or 'UPI-' in desc_upper or desc_upper.startswith('UPI'):
            is_upi = True
            category = 'UPI Transfer'

        # 2. Salary Detection (Credits only)
        if txn_type == 'CREDIT':
            salary_patterns = ['SALARY', 'PAYROLL', 'DIRECT DEP', 'ACH CREDIT', 'EMPLOYER', 'CORP CREDIT']
            if any(pat in desc_upper for pat in salary_patterns) or (is_upi and 'SALARY' in desc_upper):
                is_salary = True
                category = 'Salary'

        # 3. EMI Detection (Debits only)
        if txn_type == 'DEBIT':
            emi_patterns = ['EMI', 'LOAN', 'MORTGAGE', 'AUTO DEBIT EMI', 'HDFC LOAN', 'AXIS EMI', 'CREDIT CARD EMI']
            if any(pat in desc_upper for pat in emi_patterns):
                is_emi = True
                category = 'EMI & Loans'

        # 4. Subscription Detection
        subscription_keywords = ['NETFLIX', 'SPOTIFY', 'PRIME VIDEO', 'YOUTUBE PREMIUM', 'AWS', 'CHATGPT', 'GITHUB', 'ADOBE', 'APPLE.COM/BILL']
        if any(sub in desc_upper for sub in subscription_keywords):
            is_subscription = True
            category = 'Subscriptions'

        # 5. Fallback rule-based matching if category is still generic
        if category in ('Miscellaneous', 'UPI Transfer'):
            for keyword, rule_cat, rtype in self.rules:
                if keyword in desc_upper:
                    category = rule_cat
                    break

        # Specific pattern overrides
        if 'SWIGGY' in desc_upper or 'ZOMATO' in desc_upper or 'RESTAURANT' in desc_upper:
            category = 'Food & Dining'
        elif 'AMAZON' in desc_upper or 'FLIPKART' in desc_upper or 'MYNTRA' in desc_upper:
            category = 'Shopping'
        elif 'DMART' in desc_upper or 'BIGBASKET' in desc_upper or 'GROCERY' in desc_upper:
            category = 'Groceries'
        elif 'ELECTRICITY' in desc_upper or 'BESCOM' in desc_upper or 'AIRTEL' in desc_upper or 'JIO' in desc_upper:
            category = 'Utilities'
        elif 'ZERODHA' in desc_upper or 'GROWW' in desc_upper or 'MUTUAL FUND' in desc_upper or 'SIP' in desc_upper:
            category = 'Investments'
        elif 'ATM' in desc_upper and 'WDL' in desc_upper:
            category = 'Cash Withdrawal'

        return {
            'category': category,
            'is_upi': is_upi,
            'is_salary': is_salary,
            'is_emi': is_emi,
            'is_subscription': is_subscription
        }

    def detect_anomalies(self, transactions):
        """
        Runs batch anomaly detection:
        - Duplicate Debits (identical debit amount within 48h or adjacent)
        - Spending Spikes (> 2.5x average debit size)
        """
        if not transactions:
            return transactions

        # Calculate average debit amount using exact Decimal
        debit_amounts = [self.to_decimal(t['amount']) for t in transactions if t['txn_type'] == 'DEBIT']
        avg_debit = (sum(debit_amounts) / Decimal(len(debit_amounts))) if debit_amounts else Decimal('0.00')
        spike_threshold = avg_debit * Decimal('2.5')

        processed = []
        seen_debits = {}  # key: amount_str, val: txn index

        for idx, t in enumerate(transactions):
            t_copy = dict(t)
            amt_dec = self.to_decimal(t_copy['amount'])
            t_type = t_copy['txn_type']
            
            # Check spending spike
            if t_type == 'DEBIT' and avg_debit > 0 and amt_dec >= spike_threshold and amt_dec > Decimal('5000.00'):
                t_copy['is_spike'] = True
            else:
                t_copy['is_spike'] = False

            # Check duplicate debits
            amt_key = str(amt_dec)
            if t_type == 'DEBIT':
                if amt_key in seen_debits:
                    prev_idx = seen_debits[amt_key]
                    # Flag both current and previous as duplicate
                    t_copy['is_duplicate'] = True
                    processed[prev_idx]['is_duplicate'] = True
                else:
                    t_copy['is_duplicate'] = False
                    seen_debits[amt_key] = idx
            else:
                t_copy['is_duplicate'] = False

            processed.append(t_copy)

        return processed
