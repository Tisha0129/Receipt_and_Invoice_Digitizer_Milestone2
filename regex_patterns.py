# regex_patterns.py
import re
from datetime import datetime


# =========================
# DATE REGEX
# =========================
DATE_REGEX = r"""
\b(
    \d{1,2}[/-]\d{1,2}[/-]\d{4} |
    \d{4}[/-]\d{2}[/-]\d{2}
)\b
"""


def extract_date(text):
    matches = re.findall(DATE_REGEX, text, re.I | re.VERBOSE)
    return matches[-1] if matches else None


def normalize_date(date_str):
    if not date_str:
        return None

    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# =========================
# TOTAL REGEX (LAST TOTAL WINS)
# =========================
TOTAL_REGEX = r"""
\b(total|grand\s*total|amount\s*payable)\s*[:$]?\s*(\d+\.\d{2})
"""


def extract_total(text):
    matches = re.findall(TOTAL_REGEX, text, re.I | re.VERBOSE)
    if matches:
        return float(matches[-1][1])
    return None


# =========================
# TAX REGEX (SAFE SELECTION)
# =========================
TAX_REGEX = r"""
\b(tax|gst|vat|cgst|sgst)\s*\d*\s*[:$]?\s*(\d+\.\d{2})
"""


def extract_tax(text, total=None):
    matches = re.findall(TAX_REGEX, text, re.I | re.VERBOSE)
    values = []

    for _, val in matches:
        v = float(val)
        if total is None or v < total:
            values.append(v)

    return max(values) if values else None


# =========================
# INVOICE / RECEIPT ID
# =========================
INVOICE_REGEX = r"""
\b(invoice|receipt|bill)\s*(no|#)?\s*[:\-]?\s*([A-Z0-9\-\/]+)
"""


def extract_invoice_id(text):
    match = re.search(INVOICE_REGEX, text, re.I | re.VERBOSE)
    return match.group(3) if match else None


# =========================
# DECIMAL OCR FIX
# =========================
def fix_decimal_errors(value):
    if value is None:
        return None

    if value > 100000:
        return round(value / 10, 2)

    return round(value, 2)
