# ============================================================
# AI-DRIVEN CABLE DESIGN VALIDATOR - STREAMLIT
# IEC 60502-1 & IEC 60228 | InnoVites | LLM + Safety Net
# ============================================================

import json
import re
import streamlit as st
from transformers import pipeline
import pandas as pd

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="InnoVites AI Cable Design Validator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS Styling
# ============================================================
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 2rem;
    }
    
    /* Headers */
    h1 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    h2, h3 {
        color: white;
        font-weight: 600;
    }
    
    /* Status badges */
    .status-pass {
        background-color: #10b981;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .status-warn {
        background-color: #f59e0b;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .status-fail {
        background-color: #ef4444;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    /* Card styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Confidence meter */
    .confidence-high {
        color: #10b981;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .confidence-medium {
        color: #f59e0b;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .confidence-low {
        color: #ef4444;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    /* InnoVites branding */
    .innovites-brand {
        background: white;
        color: #1e3a8a;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Load LLM (with caching)
# ============================================================
@st.cache_resource
def load_model():
    with st.spinner("🚀 Loading AI model (Qwen 2.5)..."):
        llm = pipeline(
            "text-generation",
            model="Qwen/Qwen2.5-1.5B-Instruct",
            device=-1
        )
    return llm

# ============================================================
# Enhanced Prompt Builder for IEC 60502-1 & IEC 60228
# ============================================================
def build_prompt(user_input: str) -> str:
    return f"""You are an expert electrical engineer validating cable designs against IEC standards.

Standards: IEC 60502-1 (Low Voltage ≤ 1 kV) and IEC 60228 (Conductor specifications)

VALIDATION RULES:
1. IEC 60502-1 applies ONLY to cables rated ≤ 1 kV
2. Conductor class must comply with IEC 60228 (Class 1, 2, 5, or 6)
3. Insulation thickness must meet minimum requirements for the voltage rating
4. Cross-sectional area (CSA) must match standard values
5. Material specifications must be clear (Cu/Al for conductor, PVC/XLPE for insulation)

OUTPUT REQUIREMENTS:
- Provide ONLY valid JSON
- Use null for missing values (do NOT invent data)
- Status must be: "PASS", "WARN", or "FAIL"
- FAIL only for clear violations of IEC standards
- WARN for missing or ambiguous information
- Include detailed reasoning for engineering review

JSON STRUCTURE:
{{
  "fields": {{
    "standard": null,
    "voltage_kv": null,
    "conductor_material": null,
    "conductor_class": null,
    "csa_mm2": null,
    "insulation_material": null,
    "insulation_thickness_mm": null
  }},
  "validation": [
    {{
      "field": "field_name",
      "status": "PASS/WARN/FAIL",
      "expected": "expected_value",
      "provided": "provided_value",
      "comment": "detailed engineering explanation"
    }}
  ],
  "reasoning": "overall validation reasoning",
  "confidence": {{
    "overall": 0.0,
    "justification": "explanation of confidence level"
  }}
}}

CABLE DESIGN INPUT:
{user_input}

VALIDATION OUTPUT (JSON only):
"""

# ============================================================
# Safe JSON Extraction
# ============================================================
def extract_json(text: str):
    """Extract JSON from LLM response"""
    text = text.replace("```json", "").replace("```", "")
    # Find all JSON-like blocks
    blocks = re.findall(r"\{[\s\S]*?\}", text)
    
    # Try parsing from last to first (most complete)
    for b in reversed(blocks):
        try:
            parsed = json.loads(b)
            # Validate it has expected structure
            if "fields" in parsed or "validation" in parsed:
                return parsed
        except:
            continue
    return None

# ============================================================
# Enhanced Fallback Extraction
# ============================================================
def fallback_extract(text: str):
    """Deterministic pattern-based extraction as safety net"""
    t = text.lower()
    fields = {
        "standard": None,
        "voltage_kv": None,
        "conductor_material": None,
        "conductor_class": None,
        "csa_mm2": None,
        "insulation_material": None,
        "insulation_thickness_mm": None
    }

    # Standard detection
    if "iec 60502-1" in t or "iec60502-1" in t:
        fields["standard"] = "IEC 60502-1"
    elif "iec 60502" in t:
        fields["standard"] = "IEC 60502 (ambiguous - specify part)"

    # Voltage (0.6/1 kV format or single value)
    m = re.search(r"(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*kv", t)
    if m:
        fields["voltage_kv"] = float(m.group(2))
    else:
        m = re.search(r"(\d+\.?\d*)\s*kv", t)
        if m:
            fields["voltage_kv"] = float(m.group(1))

    # Cross-sectional area
    m = re.search(r"(\d+\.?\d*)\s*(sqmm|mm2|mm²)", t)
    if m:
        fields["csa_mm2"] = float(m.group(1))

    # Insulation thickness
    m = re.search(r"(?:insulation|tᵢ|ti).*?(\d+\.?\d*)\s*mm", t)
    if m:
        fields["insulation_thickness_mm"] = float(m.group(1))
    else:
        # Try general mm pattern if not found with insulation keyword
        matches = re.findall(r"(\d+\.?\d*)\s*mm", t)
        if matches and len(matches) == 1:
            fields["insulation_thickness_mm"] = float(matches[0])

    # Conductor material
    if "copper" in t or " cu" in t or "cu," in t:
        fields["conductor_material"] = "Cu"
    elif "aluminium" in t or "aluminum" in t or " al" in t or "al," in t:
        fields["conductor_material"] = "Al"

    # Conductor class (IEC 60228)
    m = re.search(r"class\s*(\d+)", t)
    if m:
        fields["conductor_class"] = f"Class {m.group(1)}"

    # Insulation material
    if "pvc" in t:
        fields["insulation_material"] = "PVC"
    elif "xlpe" in t or "cross-linked" in t:
        fields["insulation_material"] = "XLPE"
    elif "epr" in t:
        fields["insulation_material"] = "EPR"

    return fields

# ============================================================
# Enhanced IEC Validation Rules
# ============================================================
def apply_iec_rules(fields):
    """Apply deterministic IEC 60502-1 and IEC 60228 validation rules"""
    validation = []

    # Rule 1: Standard specification
    if fields["standard"] != "IEC 60502-1":
        validation.append({
            "field": "standard",
            "status": "FAIL",
            "expected": "IEC 60502-1",
            "provided": fields["standard"],
            "comment": "IEC 60502-1 must be explicitly specified for LV cable designs."
        })

    # Rule 2: Voltage rating
    if fields["voltage_kv"] is None:
        validation.append({
            "field": "voltage_kv",
            "status": "WARN",
            "expected": "≤ 1 kV",
            "provided": "Not specified",
            "comment": "Voltage rating must be specified. IEC 60502-1 covers up to 1 kV."
        })
    elif fields["voltage_kv"] > 1.0:
        validation.append({
            "field": "voltage_kv",
            "status": "FAIL",
            "expected": "≤ 1 kV",
            "provided": f"{fields['voltage_kv']} kV",
            "comment": "IEC 60502-1 is valid only for low voltage (≤ 1 kV). Use IEC 60502-2 for medium voltage."
        })

    # Rule 3: Conductor material
    if fields["conductor_material"] is None:
        validation.append({
            "field": "conductor_material",
            "status": "WARN",
            "expected": "Cu or Al",
            "provided": "Not specified",
            "comment": "Conductor material (Cu or Al) must be specified."
        })

    # Rule 4: Conductor class (IEC 60228)
    if fields["conductor_class"] is None:
        validation.append({
            "field": "conductor_class",
            "status": "WARN",
            "expected": "Class 1, 2, 5, or 6 per IEC 60228",
            "provided": "Not specified",
            "comment": "Conductor class must conform to IEC 60228 (Class 1=solid, 2=stranded, 5/6=flexible)."
        })

    # Rule 5: Cross-sectional area
    if fields["csa_mm2"] is None:
        validation.append({
            "field": "csa_mm2",
            "status": "WARN",
            "expected": "Standard nominal size",
            "provided": "Not specified",
            "comment": "Cross-sectional area (CSA) in mm² must be specified."
        })

    # Rule 6: Insulation material
    if fields["insulation_material"] is None:
        validation.append({
            "field": "insulation_material",
            "status": "WARN",
            "expected": "PVC, XLPE, or EPR",
            "provided": "Not specified",
            "comment": "Insulation material must be specified (typically PVC or XLPE for LV)."
        })

    # Rule 7: Insulation thickness (simplified check)
    if fields["insulation_thickness_mm"] is None:
        validation.append({
            "field": "insulation_thickness_mm",
            "status": "WARN",
            "expected": "Per IEC 60502-1 Table 4",
            "provided": "Not specified",
            "comment": "Insulation thickness must be specified and meet IEC 60502-1 minimum requirements."
        })
    else:
        # Basic sanity check (detailed tables should be in AI reasoning)
        if fields["insulation_thickness_mm"] < 0.6:
            validation.append({
                "field": "insulation_thickness_mm",
                "status": "FAIL",
                "expected": "≥ 0.6 mm (typical minimum)",
                "provided": f"{fields['insulation_thickness_mm']} mm",
                "comment": "Insulation thickness appears too low for IEC 60502-1 compliance."
            })

    # Determine overall status
    if any(v["status"] == "FAIL" for v in validation):
        overall = "FAIL"
    elif any(v["status"] == "WARN" for v in validation):
        overall = "WARN"
    else:
        overall = "PASS"

    # Calculate confidence score
    confidence = 1.0
    for v in validation:
        if v["status"] == "FAIL":
            confidence -= 0.35
        elif v["status"] == "WARN":
            confidence -= 0.15
    
    confidence = round(max(confidence, 0.0), 2)

    return validation, overall, confidence

# ============================================================
# Core Validation Logic
# ============================================================
def validate_cable_design(user_input: str, llm):
    """Main validation function combining AI and deterministic rules"""
    
    # Step 1: Get AI response
    prompt = build_prompt(user_input)
    raw_response = llm(prompt, max_new_tokens=800, do_sample=False)[0]["generated_text"]
    
    # Step 2: Extract JSON from AI response
    ai_parsed = extract_json(raw_response)
    
    # Step 3: Use AI extraction or fallback to pattern matching
    if ai_parsed and "fields" in ai_parsed:
        fields = ai_parsed["fields"]
        ai_validation = ai_parsed.get("validation", [])
        ai_reasoning = ai_parsed.get("reasoning", "AI reasoning not provided")
        ai_confidence = ai_parsed.get("confidence", {})
    else:
        fields = fallback_extract(user_input)
        ai_validation = []
        ai_reasoning = "Fallback extraction used (AI response could not be parsed)"
        ai_confidence = {"overall": 0.5, "justification": "Pattern matching only"}
    
    # Step 4: Apply deterministic IEC rules as safety net
    rule_validation, overall_status, rule_confidence = apply_iec_rules(fields)
    
    # Step 5: Combine AI and rule-based validation
    combined_validation = ai_validation if ai_validation else rule_validation
    
    # Step 6: Use more conservative confidence
    final_confidence = min(
        ai_confidence.get("overall", 0.5),
        rule_confidence
    )
    
    return {
        "fields": fields,
        "validation": combined_validation,
        "overall_status": overall_status,
        "ai_reasoning": ai_reasoning,
        "confidence": {
            "overall": final_confidence,
            "ai_confidence": ai_confidence.get("overall", 0.5),
            "rule_confidence": rule_confidence,
            "justification": "Combined AI extraction with deterministic IEC rule validation"
        }
    }

# ============================================================
# Streamlit UI
# ============================================================

# Header with InnoVites branding
col_brand, col_title = st.columns([1, 3])
with col_brand:
    st.markdown('<div class="innovites-brand">InnoVites</div>', unsafe_allow_html=True)
with col_title:
    st.markdown("<h1>⚡ AI Cable Design Validator</h1>", unsafe_allow_html=True)

st.markdown("<h3>IEC 60502-1 & IEC 60228 Compliance Validation</h3>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🏢 About InnoVites")
    st.info("""
    **InnoVites** - Leading provider of software solutions for cable and wire manufacturing.
    
    Transforming cable factories into smart factories worldwide.
    """)
    
    st.markdown("### 📋 Standards Coverage")
    st.success("""
    ✅ **IEC 60502-1**: Low voltage power cables (≤ 1 kV)
    
    ✅ **IEC 60228**: Conductors of insulated cables
    """)
    
    st.markdown("### 🤖 AI + Engineering")
    st.warning("""
    This system combines:
    - AI reasoning (Qwen 2.5 LLM)
    - Deterministic IEC rules
    - Pattern matching fallbacks
    
    **Note**: AI assists validation but does not replace engineering review.
    """)
    
    st.markdown("### 📝 Example Input")
    st.code("""IEC 60502-1, 0.6/1 kV, Cu, Class 2, 10 mm², PVC, tᵢ = 1.0 mm""", language="text")
    
    st.markdown("### 🎨 Status Legend")
    st.markdown('<span class="status-pass">PASS</span> Compliant', unsafe_allow_html=True)
    st.markdown('<span class="status-warn">WARN</span> Incomplete data', unsafe_allow_html=True)
    st.markdown('<span class="status-fail">FAIL</span> Non-compliant', unsafe_allow_html=True)

# Main content area
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.markdown("### 📝 Cable Design Input")
    
    input_mode = st.radio(
        "Input Mode",
        ["Free Text", "Structured JSON"],
        horizontal=True,
        help="Choose how you want to input the cable design"
    )
    
    if input_mode == "Free Text":
        user_input = st.text_area(
            "Cable Design Specification",
            placeholder='Example:\nIEC 60502-1, 0.6/1 kV, Cu, Class 2, 10 mm², PVC, insulation 1.0 mm',
            height=200,
            key="cable_input",
            label_visibility="collapsed"
        )
    else:
        user_input = st.text_area(
            "JSON Design Specification",
            placeholder='''{
  "standard": "IEC 60502-1",
  "voltage": "0.6/1 kV",
  "conductor_material": "Cu",
  "conductor_class": "Class 2",
  "csa": 10,
  "insulation_material": "PVC",
  "insulation_thickness": 1.0
}''',
            height=250,
            key="cable_json",
            label_visibility="collapsed"
        )
    
    validate_btn = st.button("🔍 Validate Design", type="primary", use_container_width=True)
    
    if validate_btn and user_input:
        st.success("✅ Input received - processing...")

with col2:
    st.markdown("### 📊 Validation Results")
    
    if validate_btn and user_input:
        # Load model and validate
        llm = load_model()
        
        with st.spinner("🔄 AI analyzing design against IEC standards..."):
            result = validate_cable_design(user_input, llm)
        
        # Overall Status Banner
        status = result["overall_status"]
        if status == "PASS":
            st.success(f"✅ **VALIDATION STATUS: {status}**")
        elif status == "WARN":
            st.warning(f"⚠️ **VALIDATION STATUS: {status}**")
        else:
            st.error(f"❌ **VALIDATION STATUS: {status}**")
        
        # Confidence Metrics
        col_conf1, col_conf2, col_conf3 = st.columns(3)
        
        conf_overall = result["confidence"]["overall"]
        conf_class = "confidence-high" if conf_overall >= 0.75 else "confidence-medium" if conf_overall >= 0.5 else "confidence-low"
        
        with col_conf1:
            st.metric("Overall Confidence", f"{conf_overall * 100:.0f}%")
        with col_conf2:
            st.metric("AI Confidence", f"{result['confidence']['ai_confidence'] * 100:.0f}%")
        with col_conf3:
            st.metric("Rule Confidence", f"{result['confidence']['rule_confidence'] * 100:.0f}%")
        
        # Extracted Fields Table
        st.markdown("#### 🔧 Extracted Design Parameters")
        fields_data = []
        for key, value in result["fields"].items():
            fields_data.append({
                "Attribute": key.replace("_", " ").title(),
                "Value": str(value) if value is not None else "❌ Not specified"
            })
        
        fields_df = pd.DataFrame(fields_data)
        st.dataframe(fields_df, use_container_width=True, hide_index=True)
        
        # Validation Results Table
        if result["validation"]:
            st.markdown("#### ⚙️ Detailed Validation Results")
            
            validation_data = []
            for item in result["validation"]:
                status_badge = {
                    "PASS": "✅ PASS",
                    "WARN": "⚠️ WARN",
                    "FAIL": "❌ FAIL"
                }.get(item["status"], item["status"])
                
                validation_data.append({
                    "Field": item["field"].replace("_", " ").title(),
                    "Status": status_badge,
                    "Expected": item.get("expected", "N/A"),
                    "Provided": item.get("provided", "N/A"),
                    "Comment": item.get("comment", item.get("reason", ""))
                })
            
            val_df = pd.DataFrame(validation_data)
            st.dataframe(val_df, use_container_width=True, hide_index=True)
        
        # AI Reasoning Expandable Section
        with st.expander("🧠 AI Reasoning & Confidence Justification", expanded=False):
            st.markdown("**AI Reasoning:**")
            st.write(result["ai_reasoning"])
            st.markdown("**Confidence Justification:**")
            st.write(result["confidence"]["justification"])
        
        # Full JSON Output
        with st.expander("📄 Complete JSON Response", expanded=False):
            st.json(result)
    
    elif validate_btn and not user_input:
        st.warning("⚠️ Please enter a cable design specification to validate.")
    else:
        st.info("👈 Enter cable design details and click **Validate Design** to begin")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: white;'>"
    "Built with ❤️ by <strong>InnoVites</strong> | AI-Driven Engineering Validation | "
    "IEC 60502-1 & IEC 60228 Compliance"
    "</p>",
    unsafe_allow_html=True
)

# ============================================================
# Run using: streamlit run app.py
# ============================================================
