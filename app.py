"""
Backup Buddy AI - Power AI Edition
-----------------------------------
A Streamlit app that helps households figure out whether their
UPS / inverter / battery / solar backup system can actually run the
appliances they want, for how long, and what to switch off if it can't.

Author: Soban
"""

import os
import json
import re
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

# ---------------------------------------------------------------------------
# 1. PAGE CONFIGURATION (mobile‑first meta)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Backup Buddy AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Backup Buddy AI · Power AI Edition"}
)

# ---------------------------------------------------------------------------
# 2. RESPONSIVE CSS WITH MOBILE TWEAKS
# ---------------------------------------------------------------------------
SAFE_CSS_AND_BG = """
<div class="aurora-bg"></div>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

    :root {
        --bg:             #05010f;
        --foreground:     #ffffff;
        --hero-sub:       rgba(255,255,255,0.7);
        --indigo:         #6366f1;
        --purple:         #a855f7;
        --gold:           #fcd34d;
        --red:            #ef4444;
        --glass-bg:       rgba(255, 255, 255, 0.03);
        --glass-border:   rgba(255, 255, 255, 0.08);
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--bg);
        background-image: 
            radial-gradient(circle at 20% 20%, rgba(99,102,241,.18), transparent 35%),
            radial-gradient(circle at 80% 10%, rgba(168,85,247,.12), transparent 35%),
            radial-gradient(circle at 50% 90%, rgba(252,211,77,.08), transparent 45%);
        color: var(--foreground);
        font-family: 'Inter', sans-serif;
    }

    .aurora-bg {
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        z-index: 0;
        background: conic-gradient(
            from 180deg,
            rgba(99,102,241,.15),
            rgba(168,85,247,.10),
            rgba(252,211,77,.05),
            rgba(99,102,241,.15)
        );
        filter: blur(90px);
        animation: aurora 30s linear infinite;
        pointer-events: none;
    }

    @keyframes aurora {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .block-container {
        position: relative;
        z-index: 10; 
        padding-top: 2rem !important;
        animation: fadeIn 0.8s ease forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: none; }
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 15;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--foreground) !important;
        font-weight: 600 !important;
        letter-spacing: -1px;
    }

    p, span, label, .stMarkdown {
        color: var(--hero-sub) !important;
    }

    .custom-header {
        text-align: center;
        margin-bottom: 32px;
    }

    .tag {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: var(--purple);
        margin-bottom: 12px;
    }

    .custom-header h1 {
        font-size: clamp(36px, 8vw, 64px);
        line-height: 1.1;
        margin-bottom: 8px;
        color: var(--foreground) !important;
    }

    /* Primary Button – larger touch target */
    .stButton button[data-testid="baseButton-primary"] {
        height: 56px;
        font-size: 17px;
        font-weight: 600;
        min-width: 240px;
        background: linear-gradient(135deg, var(--indigo), var(--purple)) !important;
        box-shadow: 0 0 25px rgba(99,102,241,.45);
        border: none !important;
        color: white !important;
        border-radius: 14px;
        transition: all 0.3s ease;
        margin: 24px auto 48px auto;
        display: block;
    }

    .stButton button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 0 1px rgba(255,255,255,.12), 0 15px 40px rgba(99,102,241,.35);
    }

    /* Secondary Buttons */
    .stButton button[data-testid="baseButton-secondary"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(8px);
        border: 1px solid var(--glass-border) !important;
        color: var(--foreground) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
        font-size: 14px;
    }
    
    .stButton button[data-testid="baseButton-secondary"]:hover {
        border-color: var(--indigo) !important;
        background: rgba(255,255,255,0.08) !important;
    }

    /* Glass Cards */
    .glass-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        backdrop-filter: blur(18px);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* Telemetry Grid */
    .sensor-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }

    .sensor-item {
        display: flex;
        flex-direction: column;
    }

    .sensor-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 32px !important;
        font-weight: 600;
        letter-spacing: -2px;
        color: var(--foreground) !important;
        line-height: 1.2;
    }

    .sensor-label {
        font-size: 12px;
        font-weight: 500;
        color: var(--hero-sub) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .section-label {
        font-size: 15px;
        font-weight: 500;
        color: var(--foreground) !important;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--glass-border);
    }

    .stTextInput > div > div > input, 
    .stTextArea > div > textarea, 
    .stNumberInput > div > div > input {
        background: rgba(0,0,0,0.4) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--foreground) !important;
        border-radius: 8px !important;
        padding: 12px 14px !important;
        font-size: 15px !important;
    }

    section[data-testid="stSidebar"] {
        background: rgba(5, 1, 15, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,.08) !important;
    }

    /* Mobile adjustments */
    @media (max-width: 640px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        .custom-header h1 {
            font-size: 36px !important;
        }
        .sensor-value {
            font-size: 28px !important;
        }
        .glass-card {
            padding: 16px;
        }
        .sensor-grid {
            grid-template-columns: 1fr;
        }
        .stButton button[data-testid="baseButton-primary"] {
            height: 50px;
            font-size: 16px;
            min-width: 200px;
        }
    }
</style>
"""
st.markdown(SAFE_CSS_AND_BG, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------------------------
st.markdown("""
<div class="custom-header">
  <div class="tag">Power Backup Planner</div>
  <h1>Backup Buddy AI</h1>
  <p style="font-size: 16px; max-width: 600px; margin: 0 auto;">Describe your power system to predict runtime and optimal appliance distribution.</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# REFERENCE & LOGIC
# ---------------------------------------------------------------------------
REFERENCE_APPLIANCES = {
    "Ceiling fan": {"running_watts": 75, "surge_watts": 150},
    "Refrigerator": {"running_watts": 150, "surge_watts": 600},
    "LED TV (32-43 inch)": {"running_watts": 80, "surge_watts": 100},
    "Split AC (1 ton inverter)": {"running_watts": 900, "surge_watts": 1800},
    "Water pump (0.5 HP)": {"running_watts": 370, "surge_watts": 1100},
    "LED bulb": {"running_watts": 10, "surge_watts": 10},
    "WiFi router": {"running_watts": 10, "surge_watts": 10},
    "Laptop": {"running_watts": 65, "surge_watts": 90},
    "Iron": {"running_watts": 1000, "surge_watts": 1000},
    "Microwave oven": {"running_watts": 1200, "surge_watts": 1200},
    
    "Window AC (1.5 ton)": {"running_watts": 1500, "surge_watts": 3300},
    "Space heater": {"running_watts": 1500, "surge_watts": 1500},
    "Electric geyser (water heater)": {"running_watts": 2000, "surge_watts": 2000},
    "Air cooler": {"running_watts": 200, "surge_watts": 400},
    "Exhaust fan": {"running_watts": 40, "surge_watts": 60},

    "Deep freezer": {"running_watts": 300, "surge_watts": 1000},
    "Electric kettle": {"running_watts": 1500, "surge_watts": 1500},
    "Toaster": {"running_watts": 800, "surge_watts": 800},
    "Coffee maker": {"running_watts": 1000, "surge_watts": 1000},
    "Blender/Mixer": {"running_watts": 400, "surge_watts": 850},
    "Air fryer": {"running_watts": 1500, "surge_watts": 1500},
    "Dishwasher": {"running_watts": 1200, "surge_watts": 1200},

    "Washing machine (top load)": {"running_watts": 500, "surge_watts": 1000},
    "Washing machine (front load with heater)": {"running_watts": 2000, "surge_watts": 2000},
    "Vacuum cleaner": {"running_watts": 1200, "surge_watts": 1200},

    "Hair dryer": {"running_watts": 1500, "surge_watts": 1500},
    
    "Desktop computer (with monitor)": {"running_watts": 500, "surge_watts": 650},
    "Gaming console (PS5/Xbox)": {"running_watts": 200, "surge_watts": 200},
    "Security camera system (DVR + 4 Cams)": {"running_watts": 50, "surge_watts": 50},
    "Inkjet printer": {"running_watts": 20, "surge_watts": 30},
    "Laser printer": {"running_watts": 400, "surge_watts": 1000}
}
PRIORITY_LEVELS = ["Essential", "Preferred", "Optional"]
INVERTER_PEAK_RATIO_DEFAULT = 1.6

def usable_energy_wh(v, ah, count, limit, eff):
    return (v * ah * count * (limit / 100.0) * (eff / 100.0))

def total_continuous_load(appliances):
    return sum(a["quantity"] * a["running_watts"] for a in appliances)

def total_surge_load(appliances):
    if not appliances: return 0
    return total_continuous_load(appliances) + max((a["surge_watts"] - a["running_watts"] for a in appliances), default=0)

def runtime_hours(usable_wh, load_watts):
    return float("inf") if load_watts <= 0 else usable_wh / load_watts

def inverter_status(cont, surge, rating, peak):
    c_pct = (cont / rating * 100) if rating > 0 else (float('inf') if cont > 0 else 0)
    s_pct = (surge / peak * 100) if peak > 0 else (float('inf') if surge > 0 else 0)
    w_pct = max(c_pct, s_pct)
    if w_pct > 100: return "Overloaded", c_pct, s_pct
    elif w_pct > 85: return "Marginal", c_pct, s_pct
    return "Optimal", c_pct, s_pct

def compute_load_shed_plan(appliances, target_runtime_h, usable_wh):
    priority_rank = {"Optional": 0, "Preferred": 1, "Essential": 2}

    shed_candidates = sorted(
        appliances,
        key=lambda a: (
            priority_rank.get(a.get("priority", "Preferred"), 1),
            -(a.get("quantity", 1) * a.get("running_watts", 0)),
        ),
    )

    kept = list(appliances)
    shed = []

    for candidate in shed_candidates:
        current_load = total_continuous_load(kept)
        current_runtime = runtime_hours(usable_wh, current_load)
        if current_runtime >= target_runtime_h:
            break
        kept = [a for a in kept if a is not candidate]
        shed.append(candidate)

    final_load = total_continuous_load(kept)
    final_runtime = runtime_hours(usable_wh, final_load)

    return {
        "kept": kept,
        "shed": shed,
        "achieved_runtime_hours": final_runtime,
        "target_met": final_runtime >= target_runtime_h,
    }


# ---------------------------------------------------------------------------
# AI HELPERS (Groq)
# ---------------------------------------------------------------------------
def get_api_key():
    try: return st.secrets["GROQ_API_KEY"]
    except: return os.environ.get("GROQ_API_KEY", "")

@st.cache_data(show_spinner=False)
def extract_appliances_with_ai(description):
    client = OpenAI(
        api_key=get_api_key(),
        base_url="https://api.groq.com/openai/v1"
    )
    system_instruction = (
        "You extract appliances and hardware specs from plain text. "
        "Return ONLY valid JSON with the following structure:\n"
        "{\n"
        "  \"appliances\": [{\n"
        "    \"name\": \"string\",\n"
        "    \"quantity\": int,\n"
        "    \"running_watts\": float,\n"
        "    \"surge_watts\": float,\n"
        "    \"priority\": \"Essential\"|\"Preferred\"|\"Optional\",\n"
        "    \"estimated\": true/false\n"
        "  }],\n"
        "  \"required_hours\": float,\n"
        "  \"system_specs\": {\n"
        "    \"battery_voltage\": float,\n"
        "    \"battery_capacity_ah\": float,\n"
        "    \"battery_count\": int,\n"
        "    \"inverter_rating\": float,\n"
        "    \"inverter_peak_rating\": float\n"
        "  }\n"
        "}\n"
        "Rules:\n"
        "- Use the reference table for typical wattages if the user doesn't provide exact values.\n"
        "- If the user mentions a solar panel with a wattage, treat it as the inverter rating and calculate peak as rating * 1.6.\n"
        "- Always set the 'estimated' flag to true if you used reference data.\n"
        "- If a number is missing, leave it as 0.\n"
        "- Return nothing but the JSON."
    )
    prompt = f"Reference:\n{json.dumps(REFERENCE_APPLIANCES, indent=2)}\n\nInput:\n{description}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(json)?", "", raw)
    raw = re.sub(r"```$", "", raw.strip())
    return json.loads(raw)

@st.cache_data(show_spinner=False)
def get_ai_usage_plan(context):
    client = OpenAI(
        api_key=get_api_key(),
        base_url="https://api.groq.com/openai/v1"
    )
    system_instruction = (
        "You are an electrical backup planning assistant inside the Backup Buddy AI app. "
        "Provide an actionable plan with exactly six sections, each marked as a heading.\n\n"
        "## 1. System Assessment\n"
        "Explain inverter status and battery health in plain language.\n\n"
        "## 2. Runtime Analysis\n"
        "Compare estimated runtime with required runtime. If short, say by how many hours.\n\n"
        "## 3. Recommended Load Shedding\n"
        "The 'load_shed_plan' field in the context below is already decided by a deterministic "
        "calculation, not by you. Do not choose different appliances. Simply explain, in plain "
        "language, why those specific appliances in 'turn_off' were chosen over the ones in "
        "'keep_running', referencing priority levels and wattage. If 'target_met_by_shedding' is "
        "false, say clearly that shedding alone was not enough and the household needs more "
        "battery capacity or fewer Essential appliances.\n\n"
        "## 4. Optimisation Tips\n"
        "Practical advice to extend runtime without turning off more devices.\n\n"
        "## 5. Safety Warning\n"
        "If any appliance wattage was estimated, remind them to check the actual label. "
        "If inverter is overloaded or marginal, recommend consulting an electrician.\n\n"
        "## 6. Energy Savings Estimate\n"
        "Approximate daily cost saved by using battery vs grid, assuming local tariff of Rs. 30/kWh.\n\n"
        "Use markdown formatting. Be friendly and specific."
    )
    prompt = "System context:\n" + json.dumps(context, indent=2)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# STATE MANAGEMENT & SIDEBAR (mobile‑friendly)
# ---------------------------------------------------------------------------
if "appliances" not in st.session_state:
    st.session_state.appliances = []

DEMO_SCENARIO = {
    "appliances": [
        {"name": "Ceiling fan", "quantity": 3, "running_watts": 75, "surge_watts": 150, "priority": "Essential", "estimated": False},
        {"name": "Refrigerator", "quantity": 1, "running_watts": 150, "surge_watts": 600, "priority": "Preferred", "estimated": False},
        {"name": "Laptop", "quantity": 1, "running_watts": 65, "surge_watts": 90, "priority": "Preferred", "estimated": False},
    ],
    "required_hours": 4.0, "bv": 12.0, "bc": 200.0, "count": 1, "ir": 1200.0, "ip": 1920.0,
}

with st.sidebar:
    st.markdown("### Quick Start")
    st.caption("Load a working example instantly.")
    if st.button("Load Demo"):
        st.session_state.appliances = [dict(a) for a in DEMO_SCENARIO["appliances"]]
        st.session_state.required_hours = DEMO_SCENARIO["required_hours"]
        st.session_state.bv = DEMO_SCENARIO["bv"]
        st.session_state.bc = DEMO_SCENARIO["bc"]
        st.session_state.count = DEMO_SCENARIO["count"]
        st.session_state.ir = DEMO_SCENARIO["ir"]
        st.session_state.ip = DEMO_SCENARIO["ip"]
        st.session_state.show_results = True
        st.toast("Demo loaded! Scroll down to see results.")
        st.rerun()

    if st.button("Clear All"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def _sync_peak_default():
    if not st.session_state.get("ip_touched", False):
        st.session_state.ip = st.session_state.get("ir", 0) * INVERTER_PEAK_RATIO_DEFAULT

def _mark_peak_touched():
    st.session_state.ip_touched = True


# ---------------------------------------------------------------------------
# PRIMARY INPUT (Center Stage)
# ---------------------------------------------------------------------------
desc = st.text_area(
    "System Description",
    placeholder="E.g., 3 fans and a fridge for 4 hours. I have a 12V 200Ah battery and a 1200W inverter.",
    height=100,
    label_visibility="collapsed"
)

if st.button("Analyse my system", type="primary"):
    if desc.strip():
        with st.status("Analysing your backup system...", expanded=True) as status:
            st.write("Extracting appliances and hardware specs...")
            try:
                res = extract_appliances_with_ai(desc)
                if res:
                    st.session_state.appliances = res.get("appliances", [])
                    st.session_state.required_hours = res.get("required_hours", 4.0)
                    specs = res.get("system_specs", {}) or {}

                    st.session_state.bv = specs.get("battery_voltage", 0.0)
                    st.session_state.bc = specs.get("battery_capacity_ah", 0.0)
                    st.session_state.count = specs.get("battery_count", 0)
                    st.session_state.ir = specs.get("inverter_rating", 0.0)
                    st.session_state.ip = specs.get("inverter_peak_rating", st.session_state.ir * INVERTER_PEAK_RATIO_DEFAULT)
                    st.session_state.ip_touched = specs.get("inverter_peak_rating") is not None
                    st.session_state.show_results = True

                    st.write("Calculating load and runtime...")
                    import time; time.sleep(0.3)
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                    st.toast("System analysed! Review your configuration below.")
                else:
                    status.update(label="No data found in description.", state="error")
                    st.error("The AI couldn't extract any appliances. Please try a more detailed description.")
            except Exception as e:
                status.update(label="Analysis failed", state="error")
                st.error(f"Could not process description: {e}")
                st.toast("Analysis failed. Check your API key or internet connection.")
    else:
        st.warning("Please enter a description of your backup system.")


# ---------------------------------------------------------------------------
# MAIN LAYOUT (TWO COLUMNS)
# ---------------------------------------------------------------------------
col_config, col_results = st.columns([1.1, 1], gap="large")

with col_config:
    # ---------------------------------------------------------------------------
    # HARDWARE & APPLIANCE CONFIGURATION
    # ---------------------------------------------------------------------------
    st.markdown("### System Configuration")

    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Hardware Specifications</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        bv = c1.number_input("Battery (V)", value=float(st.session_state.get("bv", 12.0)))
        bc = c2.number_input("Capacity (Ah)", value=float(st.session_state.get("bc", 200.0)))

        c3, c4 = st.columns(2)
        count = c3.number_input("Battery Count", value=int(st.session_state.get("count", 1)))
        req_h = c4.number_input("Target (Hrs)", min_value=0.1, value=max(0.1, float(st.session_state.get("required_hours", 4.0))))
        
        c5, c6 = st.columns(2)
        ir = c5.number_input("Inverter (W)", value=float(st.session_state.get("ir", 1200.0)), key="ir", on_change=_sync_peak_default)
        ip = c6.number_input("Peak (W)", value=float(st.session_state.get("ip", 1920.0)), key="ip", on_change=_mark_peak_touched)
        
        c7, c8 = st.columns(2)
        discharge = c7.slider("Discharge (%)", 10, 100, 80)
        efficiency = c8.slider("Efficiency (%)", 50, 100, 85)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Appliance Load Profile</div>', unsafe_allow_html=True)
        
        if st.session_state.appliances:
            edited = st.data_editor(
                st.session_state.appliances,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "priority": st.column_config.SelectboxColumn(options=PRIORITY_LEVELS),
                    "name": st.column_config.TextColumn("Appliance"),
                    "quantity": st.column_config.NumberColumn("Qty", min_value=0, step=1),
                    "running_watts": st.column_config.NumberColumn("Running (W)", min_value=0),
                    "surge_watts": st.column_config.NumberColumn("Surge (W)", min_value=0),
                    "estimated": st.column_config.CheckboxColumn("AI Estimated?"),
                },
                height=min(35 * len(st.session_state.appliances) + 38, 400)
            )
            st.session_state.appliances = edited.to_dict("records") if hasattr(edited, "to_dict") else edited
            st.caption("Tick 'AI Estimated?' off once you've confirmed a wattage against the appliance's actual label.")
        else:
            st.caption("No appliances added yet. Type your requirements above and press 'Analyse my system'.")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("Recalculate", use_container_width=True):
                st.session_state.show_results = True
                st.rerun()
        with col_btn2:
            if st.button("Clear Appliances", use_container_width=True):
                st.session_state.appliances = []
                st.session_state.show_results = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


with col_results:
    # ---------------------------------------------------------------------------
    # RESULTS & TELEMETRY
    # ---------------------------------------------------------------------------
    if st.session_state.get("show_results") and st.session_state.appliances:
        if bv <= 0 or bc <= 0 or count <= 0 or ir <= 0:
            st.error("Hardware specifications incomplete. Please enter values greater than zero.")
        else:
            st.markdown("### Your Results")
            
            wh = usable_energy_wh(bv, bc, count, discharge, efficiency)
            cont = total_continuous_load(st.session_state.appliances)
            surge = total_surge_load(st.session_state.appliances)
            rt = runtime_hours(wh, cont)
            status, cpct, spct = inverter_status(cont, surge, ir, ip)
            rt_display = "∞" if rt == float('inf') else f"{rt:.1f}"
            
            st.markdown(f"""
<div class="glass-card">
<div class="section-label">Load and Runtime (calculated from your inputs)</div>
<div class="sensor-grid">
<div class="sensor-item">
<span class="sensor-value">{cont:.0f} W</span>
<span class="sensor-label">Continuous Load</span>
</div>
<div class="sensor-item">
<span class="sensor-value" style="color:var(--hero-sub)">{surge:.0f} W</span>
<span class="sensor-label">Surge Load</span>
</div>
<div class="sensor-item">
<span class="sensor-value">{wh:.0f} Wh</span>
<span class="sensor-label">Usable Energy</span>
</div>
<div class="sensor-item">
<span class="sensor-value" style="color: {'var(--red)' if rt < req_h else 'var(--foreground)'}">{rt_display} hrs</span>
<span class="sensor-label">Est. Runtime</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)

            shed_plan = None
            if rt < req_h:
                shed_plan = compute_load_shed_plan(st.session_state.appliances, req_h, wh)

            if shed_plan:
                kept_names = ", ".join(a["name"] for a in shed_plan["kept"]) or "none"
                shed_names = ", ".join(a["name"] for a in shed_plan["shed"]) or "none"
                achieved = shed_plan["achieved_runtime_hours"]
                achieved_display = "∞" if achieved == float('inf') else f"{achieved:.1f}"
                met_line = (
                    f"Turning these off gets you to {achieved_display} hrs, meeting your {req_h:.1f} hr target."
                    if shed_plan["target_met"]
                    else f"Even after turning these off, you only reach {achieved_display} hrs. "
                         f"Your {req_h:.1f} hr target needs more battery capacity or a smaller Essential load, "
                         f"not just switching off Preferred/Optional appliances."
                )
                st.markdown(f"""
<div class="glass-card">
<div class="section-label" style="color: {'var(--red)' if not shed_plan['target_met'] else 'var(--gold)'} !important;">
Suggested Load Shedding (calculated, not AI guesswork)
</div>
<p style="margin-bottom:8px;"><strong style="color:var(--foreground) !important;">Turn off:</strong> {shed_names}</p>
<p style="margin-bottom:8px;"><strong style="color:var(--foreground) !important;">Keep running:</strong> {kept_names}</p>
<p style="font-size:13px;">{met_line}</p>
</div>
""", unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Load Distribution</div>', unsafe_allow_html=True)
            df = pd.DataFrame([{"App": a["name"], "Load": a["quantity"]*a["running_watts"]} for a in st.session_state.appliances])
            fig = px.pie(df, names="App", values="Load", hole=0.7, color_discrete_sequence=['#6366f1', '#a855f7', '#fcd34d', '#4a4d63', '#2a2b38'])
            
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, b=0, t=0),
                font_color="white",
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label" style="color: var(--purple) !important;">AI Recommendations</div>', unsafe_allow_html=True)
            
            calc_context = {
                "inverter_status": status,
                "continuous_load_w": cont,
                "usable_energy_wh": round(wh, 1),
                "estimated_runtime_hours": round(rt, 2) if rt != float('inf') else "Infinite",
                "required_runtime_hours": req_h,
                "load_shed_plan": {
                    "turn_off": [a["name"] for a in shed_plan["shed"]] if shed_plan else [],
                    "keep_running": [a["name"] for a in shed_plan["kept"]] if shed_plan else [a["name"] for a in st.session_state.appliances],
                    "target_met_by_shedding": shed_plan["target_met"] if shed_plan else True,
                },
            }
            
            if st.button("Generate Action Plan", use_container_width=True):
                with st.spinner("Synthesizing actionable load distribution plan..."):
                    try:
                        plan = get_ai_usage_plan(calc_context)
                        st.markdown(plan)
                        st.toast("Action plan ready!")
                    except Exception as e:
                        st.error(str(e))
                        st.toast("Failed to generate plan.")
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown("""
<div style="text-align: center; padding: 48px 0 24px 0;">
    <p style="font-size: 13px; font-weight: 500; letter-spacing: 1px; color: var(--hero-sub) !important;">
        Built by 
        <a href="https://sobanmujtaba.github.io/" target="_blank" style="color: var(--purple); text-decoration: none; border-bottom: 1px dotted var(--purple); transition: all 0.3s ease;">Soban Mujtaba</a>
        &nbsp; | &nbsp;
        <a href="https://github.com/sobanmujtaba/BackupBuddyAI" target="_blank" style="color: var(--gold); text-decoration: none; border-bottom: 1px dotted var(--gold); transition: all 0.3s ease;">View Source on GitHub</a>
    </p>
</div>
""", unsafe_allow_html=True)