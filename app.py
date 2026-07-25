"""
Backup Buddy AI - Power AI Edition
-----------------------------------
A Streamlit app that helps households figure out whether their
UPS / inverter / battery / solar backup system can actually run the
appliances they want, for how long, and what to switch off if it can't.

Design System: Power AI Visual Language
Author: Soban
"""

import os
import json
import re
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 1. CUSTOM CSS & HTML INJECTION (Power AI Visual Language)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Backup Buddy AI", page_icon="⚡", layout="wide")

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500&family=Inter:wght@400;500&display=swap');

    :root {
        --bg:             hsl(260, 87%, 3%);
        --foreground:     hsl(40, 6%, 95%);
        --hero-sub:       hsl(40, 6%, 82%);
        --indigo-accent:  #6366f1;
        --purple-accent:  #a855f7;
        --gold-accent:    #fcd34d;
        --glass-border:   rgba(255, 255, 255, 0.15);
        --overlay-blur:   rgba(3, 7, 18, 0.9);
        --tri-gradient:   linear-gradient(to right, var(--indigo-accent), var(--purple-accent), var(--gold-accent));
        --glass-bg:       rgba(255, 255, 255, 0.03);
    }

    .stApp {
        background-color: var(--bg);
        color: var(--foreground);
        font-family: 'Geist Sans', 'Inter', sans-serif;
        font-size: 18px;
        line-height: 2rem;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: 1px solid transparent;
        mask-image: linear-gradient(to right, transparent, rgba(0,0,0,1) 20%, rgba(0,0,0,1) 80%, transparent);
        -webkit-mask-image: linear-gradient(to right, transparent, rgba(0,0,0,1) 20%, rgba(0,0,0,1) 80%, transparent);
    }

    h1, h2, h3, .st-emotion-cache-10trblm {
        font-family: 'General Sans', 'Space Grotesk', sans-serif !important;
        color: var(--foreground) !important;
        font-weight: 400 !important;
        letter-spacing: -0.024em;
    }

    p, span, div, label {
        font-family: 'Geist Sans', 'Inter', sans-serif;
        color: var(--hero-sub);
    }

    .custom-header {
        padding: 80px 0 60px;
        position: relative;
        text-align: center;
        margin-bottom: 40px;
        margin-top: -60px;
        z-index: 10;
    }

    .custom-header::before {
        content: '';
        position: absolute;
        width: 984px;
        height: 400px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        top: -100px;
        left: 50%;
        transform: translateX(-50%);
        z-index: -1;
        border-radius: 999px;
        filter: blur(40px);
    }

    .tag {
        display: inline-block;
        font-family: 'Geist Sans', 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 500;
        background: var(--tri-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 25px;
    }

    .custom-header h1 {
        font-size: clamp(60px, 8vw, 160px);
        line-height: 1.02;
        margin-bottom: 15px;
    }

    .stButton > button {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--foreground) !important;
        border-radius: 999px !important;
        padding: 24px 29px !important;
        font-size: 16px;
        transition: transform 0.2s ease-in-out, background 0.3s ease;
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.1);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: var(--purple-accent) !important;
    }

    .sensor-strip {
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 24px 32px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 24px;
        margin-bottom: 32px;
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.05);
    }

    .sensor-item { display: flex; flex-direction: column; gap: 8px; }

    .sensor-label {
        font-size: 14px;
        font-weight: 500;
        color: var(--hero-sub);
    }

    .sensor-value {
        font-family: 'General Sans', 'Space Grotesk', sans-serif;
        font-size: 32px;
        font-weight: 400;
        color: var(--foreground);
        letter-spacing: -0.024em;
    }

    .sensor-bar {
        height: 2px;
        background: rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
        border-radius: 4px;
        margin-top: 5px;
    }

    .sensor-bar-fill {
        height: 100%;
        background: var(--tri-gradient);
        transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .section-label {
        font-family: 'Geist Sans', 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: var(--purple-accent);
        margin-bottom: 8px;
        border-bottom: 1px solid;
        border-image: linear-gradient(to right, var(--glass-border), transparent) 1;
        padding-bottom: 8px;
    }

    .stTextInput > div > div > input, .stTextArea > div > textarea, .stNumberInput > div > div > input {
        background: var(--overlay-blur) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--foreground) !important;
        border-radius: 8px !important;
    }

    pre, .stMarkdown {
        background: transparent;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. HEADER INJECTION
# ---------------------------------------------------------------------------
HEADER_HTML = """
<div class="custom-header">
  <div class="tag">POWER AI SYSTEM</div>
  <h1>Backup <em>Intelligence</em></h1>
  <p style="font-size: 18px; max-width: 600px; margin: 0 auto;">Predicting runtime and optimal appliance distribution across your electrical infrastructure.</p>
</div>
"""
st.markdown(HEADER_HTML, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 3. REFERENCE WATTAGE TABLE & LOGIC
# ---------------------------------------------------------------------------
REFERENCE_APPLIANCES = {
    "Ceiling fan":            {"running_watts": 75,   "surge_watts": 150},
    "Pedestal fan":           {"running_watts": 55,   "surge_watts": 100},
    "Exhaust fan":            {"running_watts": 40,   "surge_watts": 80},
    "LED bulb":               {"running_watts": 10,   "surge_watts": 10},
    "Energy saver bulb":      {"running_watts": 20,   "surge_watts": 40},
    "LED tube light":         {"running_watts": 20,   "surge_watts": 20},
    "WiFi router":            {"running_watts": 10,   "surge_watts": 10},
    "Laptop":                 {"running_watts": 65,   "surge_watts": 90},
    "Desktop computer":       {"running_watts": 200,  "surge_watts": 300},
    "Mobile charger":         {"running_watts": 10,   "surge_watts": 10},
    "LED TV (32-43 inch)":    {"running_watts": 80,   "surge_watts": 100},
    "LED TV (50 inch+)":      {"running_watts": 150,  "surge_watts": 180},
    "Refrigerator":           {"running_watts": 150,  "surge_watts": 600},
    "Deep freezer":           {"running_watts": 200,  "surge_watts": 800},
    "Washing machine":        {"running_watts": 500,  "surge_watts": 1500},
    "Iron":                   {"running_watts": 1000, "surge_watts": 1000},
    "Microwave oven":         {"running_watts": 1200, "surge_watts": 1200},
    "Water pump (0.5 HP)":    {"running_watts": 370,  "surge_watts": 1100},
    "Water pump (1 HP)":      {"running_watts": 750,  "surge_watts": 2200},
    "Air cooler":             {"running_watts": 200,  "surge_watts": 400},
    "Split AC (1 ton inverter)":       {"running_watts": 900,  "surge_watts": 1800},
    "Split AC (1.5 ton non-inverter)": {"running_watts": 1800, "surge_watts": 3500},
    "Electric kettle":        {"running_watts": 1500, "surge_watts": 1500},
    "Toaster":                {"running_watts": 800,  "surge_watts": 800},
    "Blender / juicer":       {"running_watts": 400,  "surge_watts": 800},
    "Instant water heater / geyser": {"running_watts": 3000, "surge_watts": 3000},
    "CCTV DVR system (4 cam)": {"running_watts": 40,  "surge_watts": 40},
    "Sewing machine":         {"running_watts": 90,   "surge_watts": 180},
    "Printer":                {"running_watts": 30,   "surge_watts": 60},
}
PRIORITY_LEVELS = ["Essential", "Preferred", "Optional"]

# Typical inverters allow roughly 150-200% of their continuous rating as a
# brief surge/peak rating. 1.6x is used as the assumed default whenever a
# peak rating isn't given, in both the AI extractor and the manual form.
# This is only ever a starting guess, never a locked value; both places let
# the user override it.
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

def reduce_to_target_runtime(appliances, usable_wh, required_hours):
    working, removed = list(appliances), []
    rt = runtime_hours(usable_wh, total_continuous_load(working))

    if rt == float("inf") or rt >= required_hours: return working, removed, rt

    for level in ["Optional", "Preferred"]:
        candidates = sorted([a for a in working if a["priority"] == level], key=lambda x: x["quantity"] * x["running_watts"], reverse=True)
        for c in candidates:
            if rt >= required_hours: break
            working = [a for a in working if a is not c]
            removed.append(c)
            rt = runtime_hours(usable_wh, total_continuous_load(working))
        if rt >= required_hours: break
    return working, removed, rt

# ---------------------------------------------------------------------------
# 4. AI LOGIC
# ---------------------------------------------------------------------------
EXTRACTOR_SYSTEM_PROMPT = """You extract appliances and hardware specs from plain text.
Rules:
1. Match appliances to reference wattages where possible. Set estimated: false.
2. If unknown, estimate wattage. Set estimated: true.
3. Priority defaults to "Preferred". Use Essential/Optional based on user urgency.
4. Extract battery and inverter specs if provided. Otherwise return null.
5. If solar panel array capacity (DC watts) is specified but the inverter AC rating is missing, estimate the inverter_rating by dividing the total solar capacity by 1.20 (assuming a standard 1.15 to 1.25 Inverter Loading Ratio / DC-to-AC ratio).
6. If an inverter continuous rating is known (either stated directly, or derived from solar capacity per rule 5) but no peak/surge rating is mentioned, estimate inverter_peak_rating as the continuous rating multiplied by 1.6 (typical inverter surge headroom).
Return exactly this JSON:
{
  "appliances": [{"name": "string", "quantity": int, "running_watts": int, "surge_watts": int, "priority": "Essential|Preferred|Optional", "estimated": bool}],
  "required_hours": number,
  "system_specs": {"battery_voltage": number|null, "battery_capacity_ah": number|null, "battery_count": number|null, "inverter_rating": number|null, "inverter_peak_rating": number|null}
}"""

ADVISOR_SYSTEM_PROMPT = """You are an electrical backup planning assistant inside the Backup Buddy AI app.
You will receive calculated electrical results (continuous load, surge load, usable energy, estimated runtime, inverter status, and removed appliances).

Responsibilities:
1. Explain results in simple, plain language.
2. Flag any overload, low runtime, or surge capacity warnings.
3. Write a practical appliance usage schedule fitting calculated runtime.
4. Separate calculated facts from assumptions.
5. Never change, override, or invent calculated numeric values.
6. Explicitly state when appliance wattages were estimated.
7. Recommend consulting a qualified electrician for installation work.

Return answer in exactly these six sections using Markdown headers (##): 
## System Assessment
## Calculated Limitations
## Recommended Usage Plan
## Appliances to Reduce
## Assumptions
## Safety Notice
"""

def get_api_key():
    try: return st.secrets["GEMINI_API_KEY"]
    except: return os.environ.get("GEMINI_API_KEY", "")

def get_model():
    try: return st.secrets.get("GEMINI_MODEL", "gemini-2.0-flash")
    except: return os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

def extract_appliances_with_ai(description):
    client = genai.Client(api_key=get_api_key())
    prompt = f"Reference:\n{json.dumps(REFERENCE_APPLIANCES, indent=2)}\n\nInput:\n{description}"
    response = client.models.generate_content(
        model=get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=EXTRACTOR_SYSTEM_PROMPT)
    )
    raw = re.sub(r"^```(json)?", "", response.text.strip())
    raw = re.sub(r"```$", "", raw.strip())
    return json.loads(raw)

def get_ai_usage_plan(context):
    client = genai.Client(api_key=get_api_key())
    prompt = "Calculated data:\n" + json.dumps(context, indent=2)
    response = client.models.generate_content(
        model=get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=ADVISOR_SYSTEM_PROMPT)
    )
    return response.text

# ---------------------------------------------------------------------------
# 5. UI LAYOUT
# ---------------------------------------------------------------------------
if "appliances" not in st.session_state: st.session_state.appliances = []


def _sync_peak_default():
    """
    Runs when the Inverter Rating (continuous) field changes.
    If the user has not manually typed their own peak rating, keep the
    peak field following the continuous field at the default ratio.
    """
    if not st.session_state.get("ip_touched", False):
        st.session_state.ip = st.session_state.get("ir", 0) * INVERTER_PEAK_RATIO_DEFAULT


def _mark_peak_touched():
    """Runs when the Peak Rating field itself changes: stop auto-filling it."""
    st.session_state.ip_touched = True


col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.markdown('<div class="section-label">Configuration Panel</div>', unsafe_allow_html=True)
    st.markdown("<h2>Input Parameters</h2>", unsafe_allow_html=True)

    desc = st.text_area("Describe your load and hardware...", placeholder="E.g., 3 fans and a fridge for 4 hours. I have a 12V 200Ah battery and a 1200W solar array.", height=100)

    if st.button("Initialize Deep Parse"):
        if desc.strip():
            with st.spinner("Processing natural language..."):
                try:
                    res = extract_appliances_with_ai(desc)
                except Exception as e:
                    st.error(f"Could not process that description: {e}")
                    res = None

                if res is not None:
                    st.session_state.appliances = res.get("appliances", [])
                    st.session_state.required_hours = res.get("required_hours", 4.0)
                    specs = res.get("system_specs", {}) or {}

                    st.session_state.bv = specs.get("battery_voltage") if specs.get("battery_voltage") is not None else 0.0
                    st.session_state.bc = specs.get("battery_capacity_ah") if specs.get("battery_capacity_ah") is not None else 0.0
                    st.session_state.count = specs.get("battery_count") if specs.get("battery_count") is not None else 0
                    st.session_state.ir = specs.get("inverter_rating") if specs.get("inverter_rating") is not None else 0.0
                    st.session_state.ip = specs.get("inverter_peak_rating") if specs.get("inverter_peak_rating") is not None else 0.0
                    # If the AI returned a peak rating (stated or its own 1.6x
                    # estimate), treat it as set so a later continuous-rating
                    # edit in the form doesn't silently overwrite it.
                    st.session_state.ip_touched = specs.get("inverter_peak_rating") is not None

                    if st.session_state.count == 0 or st.session_state.bc == 0 or st.session_state.ir == 0:
                        st.session_state.missing_hardware = True
                    else:
                        st.session_state.missing_hardware = False

                    st.session_state.show_results = False
                    st.rerun()

    if st.session_state.appliances:
        edited = st.data_editor(
            st.session_state.appliances,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={"priority": st.column_config.SelectboxColumn(options=PRIORITY_LEVELS)},
            key="appliance_editor",
        )
        # data_editor returns a fresh list/DataFrame; without writing it back,
        # any edits the user makes are discarded and calculations always run
        # on the original, un-edited list.
        st.session_state.appliances = (
            edited.to_dict("records") if hasattr(edited, "to_dict") else edited
        )

    st.markdown('<br><div class="section-label">Hardware Specifications</div>', unsafe_allow_html=True)

    if st.session_state.get("missing_hardware"):
        st.warning("Hardware specifications incomplete. Manual entry required.")

    c1, c2 = st.columns(2)
    bv = c1.number_input("Battery Volts", value=float(st.session_state.get("bv", 0)))
    bc = c2.number_input("Battery Ah", value=float(st.session_state.get("bc", 0)))
    count = c1.number_input("Battery Count", value=int(st.session_state.get("count", 0)))
    req_h = c2.number_input("Target Hours", min_value=0.1, value=max(0.1, float(st.session_state.get("required_hours", 4.0))))
    ir = c1.number_input("Inverter Rating (W)", value=float(st.session_state.get("ir", 0)), key="ir", on_change=_sync_peak_default)
    ip = c2.number_input("Peak Rating (W)", value=float(st.session_state.get("ip", 0)), key="ip", on_change=_mark_peak_touched)
    c2.caption(f"Auto-fills at {INVERTER_PEAK_RATIO_DEFAULT}x continuous rating until you edit it. Overwrite with your inverter's real datasheet value if you have it.")
    # Safe discharge depth and inverter efficiency directly affect usable
    # energy, so these must be user-adjustable, not fixed constants.
    discharge_limit_pct = c1.slider("Safe discharge (%)", 10, 100, int(st.session_state.get("discharge_limit_pct", 80)))
    inverter_efficiency_pct = c2.slider("Inverter efficiency (%)", 50, 100, int(st.session_state.get("inverter_efficiency_pct", 85)))

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Execute Simulation"):
        st.session_state.show_results = True
        st.session_state.pop("ai_plan_text", None)


with col2:
    st.markdown('<div class="section-label">Telemetry & Diagnostics</div>', unsafe_allow_html=True)
    st.markdown("<h2>Simulation Output</h2>", unsafe_allow_html=True)

    if st.session_state.get("show_results") and st.session_state.appliances:
        wh = usable_energy_wh(bv, bc, count, discharge_limit_pct, inverter_efficiency_pct)
        cont = total_continuous_load(st.session_state.appliances)
        surge = total_surge_load(st.session_state.appliances)
        rt = runtime_hours(wh, cont)
        status, cpct, spct = inverter_status(cont, surge, ir, ip)

        remaining, removed, new_rt = (st.session_state.appliances, [], rt)
        if rt < req_h and rt != float('inf'):
            remaining, removed, new_rt = reduce_to_target_runtime(st.session_state.appliances, wh, req_h)

        bar_width = min(100, (rt / req_h) * 100) if (req_h > 0 and rt != float('inf')) else 100
        rt_display = "∞" if rt == float('inf') else f"{rt:.1f}"

        strip_html = f"""
        <div class="sensor-strip">
            <div class="sensor-item">
                <div class="sensor-label">Cont. Load</div>
                <div class="sensor-value">{cont:.0f} W</div>
                <div class="sensor-bar"><div class="sensor-bar-fill" style="width:{min(100, cpct)}%;"></div></div>
            </div>
            <div class="sensor-item">
                <div class="sensor-label">Surge Load</div>
                <div class="sensor-value" style="color:var(--hero-sub)">{surge:.0f} W</div>
                <div class="sensor-bar"><div class="sensor-bar-fill" style="width:{min(100, spct)}%;"></div></div>
            </div>
            <div class="sensor-item">
                <div class="sensor-label">Usable Energy</div>
                <div class="sensor-value">{wh:.0f} Wh</div>
                <div class="sensor-bar"><div class="sensor-bar-fill" style="width:100%;"></div></div>
            </div>
            <div class="sensor-item">
                <div class="sensor-label">Est. Runtime</div>
                <div class="sensor-value">{rt_display} hrs</div>
                <div class="sensor-bar"><div class="sensor-bar-fill" style="width:{bar_width}%;"></div></div>
            </div>
        </div>
        """
        st.markdown(strip_html, unsafe_allow_html=True)

        fig_c1, fig_c2 = st.columns(2)
        with fig_c1:
            df = pd.DataFrame([{"App": a["name"], "Load": a["quantity"]*a["running_watts"]} for a in st.session_state.appliances])
            fig1 = px.pie(df, names="App", values="Load", hole=0.6, color_discrete_sequence=['#6366f1', '#a855f7', '#fcd34d', '#4a4d63', '#2a2b38'])
            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f2f2f2', family='Geist Sans'),
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig1, use_container_width=True)

        with fig_c2:
            st.markdown('<div class="section-label" style="margin-top:20px;">System Status</div>', unsafe_allow_html=True)
            if status == "Overloaded":
                st.markdown(f'<span style="color:#ef4444"><strong>Inverter Status: Overloaded</strong></span>', unsafe_allow_html=True)
            else:
                st.write(f"**Inverter Status:** {status}")
            st.write(f"> Continuous draw: {cpct:.1f}%")
            st.write(f"> Surge draw: {spct:.1f}%")

            if rt < req_h and rt != float('inf'):
                st.markdown(f'<br><span style="color:#fcd34d">Anomaly Detected: Runtime shortfall. Requires load shedding to hit {req_h} hr target.</span>', unsafe_allow_html=True)

        if removed:
            st.markdown('<br><div class="section-label">Suggested Appliances to Turn Off</div>', unsafe_allow_html=True)
            st.write(f"To reach the {req_h:.1f} hour target, removing these appliances (largest load first, Optional before Preferred, Essential never removed) brings estimated runtime to **{new_rt:.2f} hrs**.")
            st.dataframe(pd.DataFrame(removed)[["name", "quantity", "running_watts", "priority"]], use_container_width=True, hide_index=True)
            if new_rt < req_h:
                st.error("Even after removing every non-essential appliance, the target is not reached. The battery bank or inverter needs to be upsized.")

        st.markdown("<hr style='border: 1px solid var(--glass-border); mask-image: linear-gradient(to right, transparent, black, transparent);'>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">AI Action Plan</div>', unsafe_allow_html=True)

        if st.button("Synthesize Strategy"):
            calc_context = {
                "appliances": st.session_state.appliances,
                "removed_appliances": removed,
                "inverter_status": status,
                "continuous_load_w": cont,
                "surge_load_w": surge,
                "usable_energy_wh": round(wh, 1),
                "estimated_runtime_hours": round(rt, 2) if rt != float('inf') else "Infinite",
                "required_runtime_hours": req_h,
                "runtime_after_removals": round(new_rt, 2) if removed else None
            }
            with st.spinner("Synthesizing actionable load distribution plan..."):
                try:
                    plan = get_ai_usage_plan(calc_context)
                    st.session_state.ai_plan_text = plan
                except Exception as e:
                    st.error(str(e))

        if "ai_plan_text" in st.session_state:
            st.markdown(st.session_state.ai_plan_text)

    else:
        st.markdown('<div class="sensor-strip" style="text-align:center; display:block;"><p style="margin-top: 15px;">Configure your hardware stack and execute the simulation.</p></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 6. FOOTER
# ---------------------------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
footer_html = """
<div style="text-align: center; padding: 40px 0; border-top: 1px solid transparent; border-image: linear-gradient(to right, transparent, var(--glass-border), transparent) 1; margin-top: 40px;">
    <p style="color: var(--hero-sub); font-size: 14px;">
        Built by <a href="https://sobanmujtaba.github.io/" target="_blank" style="color: var(--purple-accent); text-decoration: none; border-bottom: 1px dotted var(--purple-accent);">Soban Mujtaba</a>
        &nbsp; | &nbsp;
        <a href="https://github.com/sobanmujtaba/BackupBuddyAI" target="_blank" style="color: var(--gold-accent); text-decoration: none; border-bottom: 1px dotted var(--gold-accent);">View Source on GitHub</a>
    </p>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
