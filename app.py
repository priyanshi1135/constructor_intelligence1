import json
import re
import urllib.parse

import streamlit as st
from PIL import Image

st.set_page_config(page_title="Construction Intelligence Platform", page_icon="🏗️", layout="wide")

st.markdown(
    """
<style>
.pill{display:inline-block;padding:4px 14px;border-radius:999px;font-weight:600;color:#fff}
.ok{background:#16a34a}.warn{background:#d97706}.bad{background:#dc2626}
.card{border:1px solid #e5e7eb;border-radius:12px;padding:14px;margin-bottom:8px}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- AI helpers
def get_model(api_key, model_name):
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Could not initialise Gemini: {e}. Using demo mode.")
        return None


def parse_json(text):
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)


def ask_json(model, prompt, image, demo):
    """Call the multimodal model and return a dict; fall back to demo data."""
    if model is None:
        return demo, True
    try:
        resp = model.generate_content([prompt + "\nReturn ONLY valid JSON, no markdown.", image])
        return parse_json(resp.text), False
    except Exception as e:  # noqa: BLE001
        st.error(f"AI call failed ({e}). Showing demo output instead.")
        return demo, True


SAFETY_PROMPT = """You are a construction safety auditor (OSHA and IS 456 aware). Analyse this site photo.
JSON schema: {"safety_score": int 0-100, "overall_status": "Safe|Needs Attention|Unsafe",
"ppe_detection": {"helmet": bool, "high_vis_vest": bool, "safety_boots": bool, "safety_harness": bool},
"hazards": [{"hazard": str, "severity": "Low|Medium|High|Critical", "remedy": str}]}"""

CRACK_PROMPT = """You are a structural engineer. Analyse this concrete/wall surface photo.
JSON schema: {"defect_type": "Hairline|Settlement|Structural Shear|Thermal Expansion|Spalling",
"estimated_width_mm": float, "severity_score": int 0-100, "root_causes": [str],
"recommended_repairs": [str], "urgency": "Low|Medium|High|Immediate"}"""

DEMO_SAFETY = {
    "safety_score": 62,
    "overall_status": "Needs Attention",
    "ppe_detection": {"helmet": True, "high_vis_vest": True, "safety_boots": False, "safety_harness": False},
    "hazards": [
        {"hazard": "Worker at height without harness", "severity": "Critical", "remedy": "Stop work; provide full-body harness and anchor points."},
        {"hazard": "Loose material near edge", "severity": "Medium", "remedy": "Install toe boards and secure materials."},
    ],
}
DEMO_CRACK = {
    "defect_type": "Settlement",
    "estimated_width_mm": 2.5,
    "severity_score": 58,
    "root_causes": ["Differential foundation settlement", "Poor soil compaction"],
    "recommended_repairs": ["Epoxy injection", "Structural re-grouting", "Monitor with crack gauges for 3 months"],
    "urgency": "Medium",
}

SEV_CLASS = {"Low": "ok", "Medium": "warn", "High": "bad", "Critical": "bad", "Immediate": "bad"}


def pill(text, cls):
    return f'<span class="pill {cls}">{text}</span>'


def inr(v):
    if v >= 1e7:
        return f"₹{v / 1e7:.2f} Cr"
    return f"₹{v / 1e5:.2f} Lakh"


# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.title("🏗️ Control Panel")
    api_key = st.text_input("Google Gemini API key", type="password", help="Leave empty for demo mode")
    model_name = st.text_input("Model name", value="gemini-1.5-flash")
    model = get_model(api_key, model_name) if api_key else None
    st.success("Live AI mode" if model else "Demo mode (no API key)")
    st.markdown("---")
    st.caption(
        "**Architecture**\n\nImage upload → multimodal LLM prompt → strict JSON contract → "
        "Streamlit UI. Planning module uses deterministic INR cost models."
    )

st.title("Multimodal Construction Intelligence Platform")
tabs = st.tabs(["🦺 Safety & PPE", "🧱 Crack Diagnostics", "📐 Planning & Valuation", "🌦️ Site Assistant"])

# ---------------------------------------------------------------- Tab 1
with tabs[0]:
    up = st.file_uploader("Upload site photo", type=["jpg", "jpeg", "png"], key="safety")
    if up:
        img = Image.open(up)
        st.image(img, use_container_width=True)
        if st.button("Run safety audit", key="run_safety"):
            with st.spinner("Analysing..."):
                data, demo = ask_json(model, SAFETY_PROMPT, img, DEMO_SAFETY)
            if demo:
                st.info("Demo output shown.")
            try:
                score = int(data["safety_score"])
                c1, c2 = st.columns(2)
                c1.metric("Safety score", f"{score}/100")
                cls = "ok" if score >= 80 else "warn" if score >= 50 else "bad"
                c2.markdown("**Status**<br>" + pill(data["overall_status"], cls), unsafe_allow_html=True)
                st.subheader("PPE checklist")
                cols = st.columns(4)
                for col, (k, v) in zip(cols, data["ppe_detection"].items()):
                    col.metric(k.replace("_", " ").title(), "✅ Yes" if v else "❌ No")
                st.subheader("Hazards")
                for h in data["hazards"]:
                    st.markdown(
                        f'<div class="card">{pill(h["severity"], SEV_CLASS.get(h["severity"], "warn"))} '
                        f'<b>{h["hazard"]}</b><br>Remedy: {h["remedy"]}</div>',
                        unsafe_allow_html=True,
                    )
                st.download_button("Download JSON report", json.dumps(data, indent=2), "safety_report.json", "application/json")
            except (KeyError, TypeError, ValueError) as e:
                st.error(f"Unexpected AI response format: {e}")

# ---------------------------------------------------------------- Tab 2
with tabs[1]:
    up2 = st.file_uploader("Upload concrete / wall surface photo", type=["jpg", "jpeg", "png"], key="crack")
    if up2:
        img2 = Image.open(up2)
        st.image(img2, use_container_width=True)
        if st.button("Diagnose crack", key="run_crack"):
            with st.spinner("Analysing..."):
                d, demo = ask_json(model, CRACK_PROMPT, img2, DEMO_CRACK)
            if demo:
                st.info("Demo output shown.")
            try:
                c1, c2, c3 = st.columns(3)
                c1.metric("Defect type", d["defect_type"])
                c2.metric("Est. width", f'{d["estimated_width_mm"]} mm')
                c3.metric("Severity", f'{d["severity_score"]}/100')
                st.markdown("**Urgency:** " + pill(d["urgency"], SEV_CLASS.get(d["urgency"], "warn")), unsafe_allow_html=True)
                st.subheader("Root causes")
                for r in d["root_causes"]:
                    st.write("•", r)
                st.subheader("Recommended repairs")
                for r in d["recommended_repairs"]:
                    st.write("•", r)
                st.download_button("Download JSON", json.dumps(d, indent=2), "crack_report.json", "application/json")
            except (KeyError, TypeError) as e:
                st.error(f"Unexpected AI response format: {e}")

# ---------------------------------------------------------------- Tab 3
with tabs[2]:
    c1, c2 = st.columns(2)
    structure = c1.selectbox("Structure type", ["Residential", "Commercial", "Industrial"])
    tier = c2.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
    sqft = c1.number_input("Built-up area (sqft)", 200, 500000, 2000, step=100)
    pct = c2.slider("Completion %", 0, 100, 40)

    base_cost = {"Residential": 1800, "Commercial": 2400, "Industrial": 1500}[structure]
    tier_cost = {"Tier 1": 1.25, "Tier 2": 1.0, "Tier 3": 0.85}[tier]
    base_val = {"Residential": 1.0, "Commercial": 1.4, "Industrial": 0.7}[structure]
    tier_val = {"Tier 1": 12000, "Tier 2": 6500, "Tier 3": 3500}[tier]

    budget = sqft * base_cost * tier_cost
    capex = budget * pct / 100
    full_value = sqft * tier_val * base_val
    current_value = full_value * (0.25 + 0.75 * pct / 100)  # land/shell value + progress
    steel_kg = sqft * 4
    cement_bags = sqft * 0.4

    m1, m2, m3 = st.columns(3)
    m1.metric("Total project budget", inr(budget))
    m2.metric("Capex incurred", inr(capex))
    m3.metric("Current market valuation", inr(current_value))
    m4, m5 = st.columns(2)
    m4.metric("Steel required", f"{steel_kg / 1000:.1f} tonnes")
    m5.metric("Cement required", f"{cement_bags:,.0f} bags")
    st.progress(pct / 100, text=f"Milestone progress: {pct}%")
    st.caption("Heuristic estimates for planning only; get a quantity surveyor's estimate for real decisions.")

    st.subheader("Conceptual 3D render")
    desc = st.text_input("Describe the building", f"modern {structure.lower()} building, architectural 3D render, daylight")
    if st.button("Generate concept image"):
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(desc)
        st.image(url, caption="Generated via Pollinations AI")

# ---------------------------------------------------------------- Tab 4
with tabs[3]:
    weather = st.selectbox("Weather condition", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
    alerts = {
        "Normal": ("ok", "Normal operations. Continue routine toolbox talks and PPE checks."),
        "High Wind": ("bad", "Suspend crane operations and work at height. Secure scaffolding sheets and loose materials."),
        "Heavy Rain": ("bad", "Electrical hazard: isolate temporary power. Protect fresh concrete and follow the curing protocol. Watch for slippery surfaces and trench collapse."),
        "Extreme Heat": ("warn", "Enforce hydration breaks, shift heavy work to early hours, increase curing water frequency to prevent plastic shrinkage cracks."),
    }
    cls, msg = alerts[weather]
    st.markdown(pill(weather, cls) + f"  {msg}", unsafe_allow_html=True)

    st.subheader("Construction engineering assistant")
    if "chat" not in st.session_state:
        st.session_state.chat = [{"role": "assistant", "content": "Hi! Ask me about concrete, safety, scheduling or costs."}]
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])
    q = st.chat_input("Ask a site question...")
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        reply = None
        if model is not None:
            try:
                history = "\n".join(f'{m["role"]}: {m["content"]}' for m in st.session_state.chat[-8:])
                reply = model.generate_content(
                    f"You are a concise senior construction engineer. Current weather: {weather}.\n{history}\nassistant:"
                ).text
            except Exception as e:  # noqa: BLE001
                reply = f"AI error: {e}"
        if reply is None:
            reply = (
                "(Demo mode) General guidance: follow IS 456 for concrete work, cure for at least 7 days, "
                "keep PPE compliance at 100%, and confirm any structural decision with a licensed engineer."
            )
        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.rerun()
