# 🔌 AI Cable Design Validator (IEC 60502-1)

An **AI-assisted validation system** for **low-voltage power cable designs** based on **IEC 60502-1**, combining **LLM-based extraction** with **deterministic engineering rules** to produce reliable **PASS / WARN / FAIL** decisions.

---

## 📌 Overview

This project validates cable design specifications provided in **free-text form**, such as:

- Datasheets  
- Engineering notes  
- User-entered specifications  

The system:
- Extracts key cable parameters using a **lightweight Hugging Face LLM**
- Applies **hard safety rules** derived from IEC 60502-1
- Produces **explainable, deterministic validation outcomes**

⚠️ This is a **decision-support prototype**, not a certified compliance tool.

---

## 🎯 Key Features

- ✅ Single LLM call (fast and cost-efficient)
- ✅ Deterministic fallback logic (no silent failures)
- ✅ PASS / WARN / FAIL classification
- ✅ Confidence score with justification
- ✅ Handles messy real-world input
- ✅ Google Colab & local Python compatible

---

## 🧠 Why Hybrid AI + Rules?

Small language models:
- ❌ Do not reliably remember IEC tables
- ❌ Can hallucinate values
- ❌ Are unsafe for strict engineering limits

**Solution:**  
> Use AI for extraction, deterministic rules for safety.

This mirrors how **real industrial validation systems** are designed.

---

## 📥 Example Input

IEC 60502-1, 0.6/1 kV, Cu Class 2, 10 sqmm, PVC insulation, 1 mm


---
