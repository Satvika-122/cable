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

## 📤 Example Output

```json
{
  "fields": {
    "standard": "IEC 60502-1",
    "voltage_kv": 1.0,
    "conductor_material": "Cu",
    "conductor_class": "Class 2",
    "csa_mm2": 10.0,
    "insulation_material": "PVC",
    "insulation_thickness_mm": 1.0
  },
  "validation": [],
  "overall_status": "PASS",
  "confidence": {
    "overall": 1.0,
    "justification": "All checks satisfied."
  }
}
## ⚙️ Validation Logic (IEC 60502-1)

The validator applies deterministic rules based on widely known IEC 60502-1 constraints.

| Condition | Result |
|---------|--------|
| Voltage > 1 kV | FAIL |
| Missing voltage | WARN |
| Missing CSA | WARN |
| Missing insulation thickness | WARN |
| Missing IEC standard | FAIL |

Voltage limits are enforced **deterministically**, even if the AI model fails to extract values correctly.

---

## 🧪 Test Scenarios

| Case | Description | Result |
|----|----|----|
| PASS | Complete low-voltage cable specification | PASS |
| WARN | Missing safety-related parameters | WARN |
| FAIL | High-voltage cable (> 1 kV) | FAIL |
| FAIL | Unknown or missing standard | FAIL |

---

## 🏗 System Architecture

User Input
↓
LLM-Based Extraction (Qwen 2.5 – 1.5B)
↓
Safe JSON Parsing
↓
Regex-Based Deterministic Fallback
↓
IEC 60502-1 Rule Enforcement
↓
PASS / WARN / FAIL + Confidence Score


---

## 🧩 Technologies Used

- Python 3.9+
- Hugging Face Transformers
- Qwen/Qwen2.5-1.5B-Instruct
- Regex-based deterministic fallback logic
- Google Colab compatible

---

