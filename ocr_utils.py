# ocr_utils.py
import re
import json
import requests
import streamlit as st

from regex_patterns import (
    extract_date,
    normalize_date,
    extract_total,
    extract_tax,
    extract_invoice_id,
    fix_decimal_errors
)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"


# =========================
# JSON EXTRACTION
# =========================
def extract_json_from_text(text):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "vendor": None,
            "date": None,
            "total": None,
            "tax": None,
            "line_items": []
        }


# =========================
# PARSED DATA VALIDATION
# =========================
def validate_parsed_data(parsed):
    parsed.setdefault("vendor", None)
    parsed.setdefault("date", None)
    parsed.setdefault("total", None)
    parsed.setdefault("tax", None)
    parsed.setdefault("line_items", [])

    validated_items = []

    for item in parsed["line_items"]:
        name = item.get("name", "").strip()
        price = float(item.get("price", 0))
        quantity = item.get("quantity", 1)

        # ---- FIX LINE NUMBER MISREAD AS QUANTITY ----
        if quantity > 1 and price > 20:
            quantity = 1

        validated_items.append({
            "name": name,
            "price": round(price, 2),
            "quantity": int(quantity)
        })

    parsed["line_items"] = validated_items
    return parsed


# =========================
# GEMINI PARSER
# =========================
def gemini_parse_receipt(clean_text):
    api_key = st.session_state.get("GEMINI_API_KEY")

    prompt = f"""
You are a strict JSON generator.

Rules:
- Output ONLY valid JSON
- No markdown
- Do NOT calculate totals
- Preserve decimals exactly
- Use null if unknown

Schema:
{{
  "vendor": string | null,
  "date": string | null,
  "total": number | null,
  "tax": number | null,
  "line_items": [
    {{
      "name": string,
      "quantity": number,
      "price": number
    }}
  ]
}}

Receipt text:
{clean_text}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0}
    }

    response = requests.post(
        f"{GEMINI_URL}?key={api_key}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    raw = response.json()

    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    parsed = extract_json_from_text(text)
    result = validate_parsed_data(parsed)

    # =========================
    # REGEX FALLBACK
    # =========================
    if result["date"] is None:
        result["date"] = extract_date(clean_text)

    if result["total"] is None:
        result["total"] = extract_total(clean_text)

    result["tax"] = extract_tax(clean_text, result["total"])

    # =========================
    # NORMALIZE & FIX
    # =========================
    result["date"] = normalize_date(result["date"])
    result["total"] = fix_decimal_errors(result["total"])
    result["tax"] = fix_decimal_errors(result["tax"])

    # =========================
    # RECONCILE TOTAL USING MATH
    # =========================
    if result["line_items"]:
        subtotal = sum(i["price"] * i["quantity"] for i in result["line_items"])
        if result["tax"] is not None:
            computed_total = round(subtotal + result["tax"], 2)
            if result["total"] is None or abs(computed_total - result["total"]) > 0.5:
                result["total"] = computed_total

    return result
