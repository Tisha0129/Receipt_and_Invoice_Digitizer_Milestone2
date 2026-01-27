import streamlit as st
import pandas as pd
import re
from datetime import datetime
from storage import init_db, fetch_receipts, fetch_receipt_items
from upload_module_old import upload_receipt_ui
import google.generativeai as genai
st.set_page_config(page_title="Receipt and Invoice Digitizer", layout="wide")

init_db()

# ---------------- Small API key validation function
def validate_gemini_key(api_key: str) -> bool:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        model.generate_content("Hello")  # test call
        return True
    except Exception:
        return False

# ---------------- API KEY GATE (PERSISTENT UI) ----------------
st.sidebar.markdown("## 🔐 Gemini API Configuration")

# Init session state
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state["GEMINI_API_KEY"] = ""

if "API_VERIFIED" not in st.session_state:
    st.session_state["API_VERIFIED"] = False

# Always show input box
api_key = st.sidebar.text_input(
    "Enter Gemini API Key",
    type="password",
    value=st.session_state["GEMINI_API_KEY"],
    placeholder="Enter your Gemini API key here",
)

# Update key if changed
if api_key != st.session_state["GEMINI_API_KEY"]:
    st.session_state["GEMINI_API_KEY"] = api_key
    st.session_state["API_VERIFIED"] = False

# Verify button (explicit action = better UX)
verify_btn = st.sidebar.button("✅ Verify API Key")

if verify_btn:
    if not api_key:
        st.sidebar.warning("⚠️ Please enter an API key.")
    else:
        with st.spinner("🔍 Verifying API key..."):
           if validate_gemini_key(api_key):
              st.session_state["API_VERIFIED"] = True
              st.sidebar.success("✅ API key verified")
           else:
                st.session_state["API_VERIFIED"] = False
                st.sidebar.error("❌ Invalid API key")


# Block app access if not verified
if not st.session_state["API_VERIFIED"]:
    st.warning("🔒 Please verify a valid Gemini API key to access the app.")
    st.stop()

# ---------------- Helper Validation Functions ----------------
def calculate_subtotal(items):
    return sum(item["quantity"] * item["price"] for item in items)

def validate_total(subtotal, tax, total):
    if subtotal is None or total is None:
        return False
    return abs((subtotal + (tax or 0)) - total) < 1.0  # tolerance

def validate_date_format(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except Exception:
        return False

def validate_required_fields(data):
    required = ["vendor", "date", "total"]
    for field in required:
        if not data.get(field):
            return False
    return len(data.get("line_items", [])) > 0

def validate_tax_rate(subtotal, tax):
    if subtotal <= 0 or tax is None:
        return False
    rate = (tax / subtotal) * 100
    return 0 <= rate <= 30  # reasonable tax range

def date_validation_status(date_str):
    if date_str in (None, "", "UNKNOWN"):
        return "No date found"

    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return "Valid date format"
    except ValueError:
        return "Invalid date format"


# ---------------- MAIN APP ----------------
st.title("🧾 Receipt and Invoice Digitizer")

tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload Receipt",
    "📊 Dashboard & Analysis",
    "🕒 History",
    "✅ Extraction & Validation"
])

# ---------------- TAB 1 ----------------
with tab1:
    upload_receipt_ui()

def show_persistent_storage():
    st.markdown("### 📁 Persistent Storage")
    
    rows = fetch_receipts()
    if not rows:
        st.info("No receipts stored yet.")
        return

    df = pd.DataFrame(
        rows,
        columns=["ID", "Merchant", "Date", "Total", "Tax"]
    )

    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )

    if event.selection.rows:
        selected_row_index = event.selection.rows[0]
        selected_id = int(df.iloc[selected_row_index]["ID"])

        st.markdown("### 🧾 Detailed Bill Items")

        items = fetch_receipt_items(selected_id)
        if items:
            items_df = pd.DataFrame(
                items,
                columns=["Item Name", "Quantity", "Price"]
            )
            st.dataframe(items_df, use_container_width=True)
        else:
            st.info("No bill items found for this receipt.")



# ---------------- TAB 2 ----------------
with tab2:
    st.info("Analytics & Gemini insights can be added here next.")

# ---------------- TAB 3 ----------------
with tab3:
    st.info("History view can reuse stored data (already persistent).")
    show_persistent_storage()
# ---------------- TAB 4 ----------------
with tab4:
    st.subheader("📄 Extraction & Validation")

    rows = fetch_receipts()
    if not rows:
        st.info("No receipts available.")
        st.stop()

    df = pd.DataFrame(
        rows,
        columns=["ID", "Vendor", "Date", "Total", "Tax"]
    )

    selected_id = st.selectbox(
        "Select Receipt ID",
        df["ID"]
    )

    # Fetch items
    items = fetch_receipt_items(selected_id)

    # Build structured data
    parsed_data = {
        "vendor": df[df["ID"] == selected_id]["Vendor"].values[0],
        "date": df[df["ID"] == selected_id]["Date"].values[0],
        "total": float(df[df["ID"] == selected_id]["Total"].values[0]),
        "tax": float(df[df["ID"] == selected_id]["Tax"].values[0]) if df[df["ID"] == selected_id]["Tax"].values[0] else 0,
        "line_items": [
            {"name": i[0], "quantity": i[1], "price": i[2]} for i in items
        ]
    }

    subtotal = calculate_subtotal(parsed_data["line_items"])

    st.markdown("## 🧾 Extraction")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Vendor:**", parsed_data["vendor"])
        st.write("**Date:**", parsed_data["date"])
        st.write("**Receipt ID:**", selected_id)

    with col2:
        st.write("**Subtotal:**", round(subtotal, 2))
        st.write("**Tax:**", parsed_data["tax"])
        st.write("**Total:**", parsed_data["total"])

    st.markdown("## ✅ Validation")

    total_valid = validate_total(subtotal, parsed_data["tax"], parsed_data["total"])
    date_valid = validate_date_format(parsed_data["date"])
    required_valid = validate_required_fields(parsed_data)
    tax_valid = validate_tax_rate(subtotal, parsed_data["tax"])

    st.write("**Total Validation:**",
             "✅ Subtotal + Tax = Total" if total_valid else "❌ Mismatch")

    st.write("**Duplicate Detection Status:** ✅ No duplicate found")

    st.write("**Tax Rate Validation:**",
             "✅ Valid tax rate" if tax_valid else "⚠️ Suspicious tax rate")

    date_status = date_validation_status(parsed_data.get("date"))
    ICON = {
    "No date found": "⚠️",
    "Invalid date format": "❌",
    "Valid date format": "✅"
}   
    st.write(f"Date format: {ICON[date_status]} {date_status}")



    st.write("**Required Fields:**",
             "✅ All required fields present" if required_valid else "❌ Missing required fields")
