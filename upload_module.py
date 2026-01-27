import streamlit as st
import tempfile
from storage import insert_receipt, receipt_exists_by_raw_text
from ocr_utils import gemini_parse_receipt
from ocr_utils import (
    cv_to_rgb,
    preprocess_for_ocr,
    extract_text_from_image,
    clean_ocr_text,
    gemini_parse_receipt
)


# ---------------- VALIDATION ----------------
def is_valid_receipt(parsed):
    return (
        parsed["vendor"] not in (None, "", "UNKNOWN") and
        parsed["total"] is not None and
        len(parsed["line_items"]) > 0
    )

# ---------------- UI ----------------
def upload_receipt_ui():
    st.subheader("📤 Upload Receipt / Invoice")

    uploaded_file = st.file_uploader(
        "Upload Image or PDF",
        type=["png", "jpg", "jpeg", "pdf"]
    )

    if not uploaded_file:
        return

    suffix = "." + uploaded_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    original, processed = preprocess_for_ocr(file_path)
    st.markdown("### Image Preprocessing Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Original")
        st.image(cv_to_rgb(original), use_container_width=True)

    with col2:
        st.markdown("### Preprocessed")
        st.image(cv_to_rgb(processed), use_container_width=True)

    if st.button("⚙️ Process & Save to Vault"):
        # OCR → CLEAN → PARSE
        raw_ocr = extract_text_from_image(original)
        proc_ocr = extract_text_from_image(processed)

        combined_text = raw_ocr + "\n" + proc_ocr
        cleaned_text = clean_ocr_text(combined_text)

        # 🚫 DUPLICATE CHECK — EARLY EXIT
        if receipt_exists_by_raw_text(cleaned_text):
            st.warning("⚠️ This receipt or invoice has already been uploaded.")
            st.stop()
        try:
           parsed = gemini_parse_receipt(cleaned_text)
        except Exception as e:
            st.error(f"Gemini parsing failed: {e}")
            st.stop()

        

        # Validate before saving
        if not is_valid_receipt(parsed):
            st.warning("⚠️ Extraction uncertain. Please review the data.")
            st.markdown("### OCR Output (Debug)")
            st.text_area("", cleaned_text, height=250)


        insert_receipt(parsed, cleaned_text)
        st.success("✅ Receipt processed and saved successfully!")
