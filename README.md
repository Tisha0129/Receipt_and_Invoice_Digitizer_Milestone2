📌 Milestone 2: Field Extraction & Validation
📖 Overview

Milestone 2 focuses on converting raw OCR output into accurate, validated, and structured data. This milestone bridges the gap between noisy text extraction and reliable data storage by combining NLP-based parsing, regex-driven refinement, validation checks, and duplicate detection.

The outcome of this milestone is a robust pipeline that ensures only correct and meaningful receipt/invoice data is stored in the database.

🎯 Objective

The primary objective of Milestone 2 is to:

Extract key fields from receipts and invoices using a hybrid AI + rule-based approach

Validate financial and structural consistency of extracted data

Detect and prevent duplicate receipt uploads

Store only verified, structured records in persistent storage

🧩 Key Features Implemented
1️⃣ Field Extraction using Regex + NLP

Google Gemini (LLM) is used for semantic understanding of receipt text.

Regex patterns are applied to:

Correct numeric fields (amounts, tax, quantities)

Normalize dates

Handle OCR inconsistencies

Extracted fields include:

Vendor name

Date

Line items

Subtotal, tax, and total

2️⃣ Validation & Duplicate Detection

Total Validation
Ensures Subtotal + Tax ≈ Total with tolerance handling.

Tax Validation
Confirms tax presence and correctness.

Date Validation
Distinguishes between valid date formats, invalid formats, and missing dates.

Required Field Validation
Checks for mandatory fields before storage.

Duplicate Detection
Prevents re-uploading the same receipt by comparing cleaned OCR text against existing records in the database.

3️⃣ Structured Data Storage

Validated data is stored in an SQLite relational database.

Database design ensures:

Clear separation between receipt metadata and line items

Data integrity and consistency

Only validated records are persisted, improving reliability for downstream analysis.

🏗️ Technologies Used
Component	Technology
OCR Engine	Tesseract OCR
NLP Parsing	Google Gemini (LLM)
Pattern Matching	Python Regex
Validation Logic	Python (Math, Datetime)
Duplicate Detection	Text normalization & comparison
Database	SQLite
Frontend	Streamlit
🔄 Workflow Summary

OCR extracts raw text from receipt images.

Text is cleaned and normalized.

Duplicate detection is performed.

Gemini LLM extracts structured fields.

Regex refines and corrects extracted values.

Validation checks ensure correctness.

Verified data is stored in the database.

✅ Outcome of Milestone 2

Improved accuracy of extracted receipt data

Reduced OCR and parsing errors

Prevention of duplicate data entries

Reliable structured data ready for analytics and visualization

🧠 Conclusion

Milestone 2 transforms unstructured OCR text into validated, trustworthy, and structured data. By combining AI-driven understanding with deterministic validation logic, the system achieves high accuracy and robustness, forming a strong foundation for analytics and future system enhancements.
