
import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import time

# ==========================================
# 1. PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Riyadh Solar Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. STATE & LANGUAGE LOGIC
# ==========================================
if "points" not in st.session_state: st.session_state.points = []
if "area" not in st.session_state: st.session_state.area = 0
if "map_center" not in st.session_state: st.session_state.map_center = [24.7136, 46.6753]
if "map_zoom" not in st.session_state: st.session_state.map_zoom = 18
if "lang" not in st.session_state: st.session_state.lang = "en"
if "time_view" not in st.session_state: st.session_state.time_view = "Annual"

if "show_audit" not in st.session_state: st.session_state.show_audit = False
if "show_service" not in st.session_state: st.session_state.show_service = False
if "svc_stage" not in st.session_state: st.session_state.svc_stage = "idle"
if "show_alert" not in st.session_state: st.session_state.show_alert = False
if "selected_contractor" not in st.session_state: st.session_state.selected_contractor = ""

def toggle_language(): st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
def toggle_time(): st.session_state.time_view = "Monthly" if st.session_state.time_view == "Annual" else "Annual"

def toggle_audit():
    if st.session_state.area > 0:
        st.session_state.show_audit = not st.session_state.show_audit; st.session_state.show_service = False; st.session_state.show_alert = False
    else: st.session_state.show_alert = True; st.session_state.show_service = False

def open_service():
    if st.session_state.area > 0:
        st.session_state.show_service = True; st.session_state.show_audit = False; st.session_state.show_alert = False
        if st.session_state.svc_stage == "idle": st.session_state.svc_stage = "scanning"
    else: st.session_state.show_alert = True; st.session_state.show_audit = False

def close_all_popups():
    st.session_state.show_audit = False; st.session_state.show_service = False; st.session_state.svc_stage = "idle"

def reset_view():
    close_all_popups(); st.session_state.show_alert = False; st.session_state.points = []; st.session_state.area = 0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1)/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1)/2.0)**2
    return R * (2 * np.arcsin(np.sqrt(a)))

t = {
    "en": {
        "btn_lang": "تغيير اللغة", "title_top": "RIYADH", "title_bot": "SOLAR AI", "load": "Building Scale Profile",
        "maint": "Maintenance Strategy", "tech": "Solar Panel Tech (W)", "reset": "RESET MAP BOUNDARY", "area": "Rooftop Area",
        "units": "Panel Units", "opt_loads": ["Small Villa", "Standard Villa", "Large Estate", "Palace"], "opt_maint": ["Weekly (Elite)", "Monthly (Standard)", "Lazy Owner"],
        "annual": "Annual", "monthly": "Monthly", "overview": "Overview", "audit": "Investment Audit", "service": "Book Service",
        "alert": "⚠️ Please select a roof area on the map first!", "audit_title": "FINANCIAL AUDIT", "cost": "Estimated Install Cost",
        "payback": "Payback Period", "years": "Years", "direct_a": "Annual Direct Savings", "direct_m": "Monthly Direct Savings",
        "export_a": "Annual Export Credits", "export_m": "Monthly Export Credits", "total_a": "Total Annual Benefit", "total_m": "Total Monthly Benefit",
        "service_title": "SERVICE DISPATCH", "scanning": "Pinging Local Grid...", "request": "SEND REQUEST",
        "receipt_title": "PROJECT SUMMARY", "confirm": "Confirm & Submit", "cancel": "Cancel", "selected": "Selected Contractor",
        "success": "DISPATCH SUCCESSFUL", "success_sub": "A technician from your selected contractor will contact you shortly."
    },
    "ar": {
        "btn_lang": "English", "title_top": "الرياض", "title_bot": "للذكاء الشمسي", "load": "حجم المبنى", "maint": "استراتيجية الصيانة",
        "tech": "قدرة اللوح الشمسي (واط)", "reset": "إعادة تعيين الخريطة", "area": "مساحة السطح", "units": "عدد الألواح",
        "opt_loads": ["فيلا صغيرة", "فيلا قياسية", "قصر صغير", "قصر كبير"], "opt_maint": ["أسبوعي (ممتاز)", "شهري (قياسي)", "بدون صيانة"],
        "annual": "سنوي", "monthly": "شهري", "overview": "المخطط العام", "audit": "التدقيق الاستثماري", "service": "حجز الخدمة",
        "alert": "⚠️ الرجاء تحديد مساحة السطح على الخريطة أولاً!", "audit_title": "التقرير المالي", "cost": "التكلفة التقديرية للتركيب",
        "payback": "فترة الاسترداد", "years": "سنوات", "direct_a": "التوفير المباشر السنوي", "direct_m": "التوفير المباشر الشهري",
        "export_a": "أرباح التصدير السنوية", "export_m": "أرباح التصدير الشهرية", "total_a": "إجمالي العائد السنوي", "total_m": "إجمالي العائد الشهري",
        "service_title": "مركز الخدمة", "scanning": "جاري البحث عن مقاولين...", "request": "إرسال طلب",
        "receipt_title": "ملخص المشروع", "confirm": "تأكيد وإرسال الطلب", "cancel": "إلغاء", "selected": "المقاول المختار",
        "success": "تم إرسال الطلب بنجاح", "success_sub": "سيتواصل معك فني متخصص قريباً."
    }
}
loc = t[st.session_state.lang]

# ==========================================
# 3. TYPOGRAPHY ENGINE (Dynamic Font Scaling)
# ==========================================
is_ar = st.session_state.lang == "ar"

css_vars = f"""
<style>
    :root {{
        --f-btn: {'1.25rem' if is_ar else '1.05rem'};
        --f-pri: {'1.3rem' if is_ar else '1.1rem'};
        --f-hud-lbl: {'0.85rem' if is_ar else '0.7rem'};
        --f-hud-val: {'1.5rem' if is_ar else '1.3rem'};
        --f-hud-val-dark: {'1.6rem' if is_ar else '1.4rem'};
    }}
</style>
"""
st.markdown(css_vars, unsafe_allow_html=True)

f_title = "1.9rem" if is_ar else "1.6rem"
f_lbl = "1.0rem" if is_ar else "0.85rem"
f_val = "1.4rem" if is_ar else "1.2rem"
f_big = "1.8rem" if is_ar else "1.6rem"
f_card_tit = "1.25rem" if is_ar else "1.1rem"
f_card_sub = "0.95rem" if is_ar else "0.8rem"
f_card_dsc = "0.85rem" if is_ar else "0.75rem"
f_succ_tit = "2.2rem" if is_ar else "1.8rem"
f_succ_sub = "1.2rem" if is_ar else "1rem"

def calculate_area(pts):
    if len(pts) < 3: return 0
    lats = np.array([p[0] for p in pts]) * 111111
    lngs = np.array([p[1] for p in pts]) * 111111 * np.cos(np.radians(24.7))
    return 0.5 * np.abs(np.dot(lats, np.roll(lngs, 1)) - np.dot(lngs, np.roll(lats, 1)))

# ==========================================
# 4. GLOBAL BASE CSS
# ==========================================
st.markdown("""
<style>
    /* BASE THEME & MAP */
    :root { color-scheme: dark; }
    body, .stApp, [data-testid="stAppViewContainer"] { background-color: #0A0A0A !important; color: white !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; overflow: hidden; }
    iframe { position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important; z-index: 0 !important; border: none !important; }
    div[data-testid="stTooltipContent"] { display: none !important; opacity: 0 !important; }

    /* GLOBAL BUTTON OUTLINE FIX */
    .stButton > button { outline: none !important; }
    .stButton > button:focus { outline: none !important; box-shadow: none !important; color: inherit !important; }

    /* HEADER & LOGO */
    .solid-header { position: fixed; top: 0; left: 0; right: 0; height: 90px; background-color: #0A0A0A !important; border-bottom: 2px solid #D4AF37; z-index: 999; display: flex; justify-content: flex-end; align-items: center; padding-right: 40px; box-shadow: 0px 4px 15px rgba(0,0,0,0.9); pointer-events: none; }
    .logo-container { pointer-events: auto; text-align: right; }
    .logo-top { color: #D4AF37 !important; font-family: 'Times New Roman', serif !important; font-weight: 300 !important; letter-spacing: 6px !important; font-size: 2.2rem !important; margin: 0 0 -4px 0 !important; line-height: 1 !important; }
    .logo-bottom { color: #FFFFFF !important; font-family: 'Times New Roman', serif !important; font-weight: 300 !important; letter-spacing: 4px !important; font-size: 1.4rem !important; margin: 0 !important; line-height: 1 !important; }

    /* =========================================================
       1. HEADER NAV SHIELD (Locked perfectly)
       ========================================================= */
       
    div[data-testid="stHorizontalBlock"]:has(span#header-nav-id) {
        position: fixed !important;
        top: 22px !important;
        left: 30px !important;
        right: 0px !important;
        padding-right: 320px !important;
        z-index: 99999 !important;
        pointer-events: none !important;
    }
   
    span#header-nav-id { display: none !important; }
    div[data-testid="stHorizontalBlock"]:has(span#header-nav-id) button { pointer-events: auto !important; }
   
    div[data-testid="stHorizontalBlock"]:has(span#header-nav-id) button[kind="secondary"] {
        background: transparent !important; color: white !important; border: none !important; box-shadow: none !important; font-weight: bold !important; font-size: var(--f-btn) !important; height: 45px !important; margin: 0 !important; padding: 0 25px !important; width: 100% !important; transition: 0.2s !important; display: flex !important; align-items: center !important; justify-content: center !important; outline: none !important; white-space: nowrap !important; min-width: max-content !important;
    }
    div[data-testid="stHorizontalBlock"]:has(span#header-nav-id) button[kind="secondary"] p { margin: 0 !important; line-height: 1 !important; color: white !important; white-space: nowrap !important; }
    div[data-testid="stHorizontalBlock"]:has(span#header-nav-id) button[kind="secondary"]:hover { color: #D4AF37 !important; text-shadow: 0 0 10px rgba(212,175,55,0.6); transform: translateY(-2px); }
   
    div[data-testid="stHorizontalBlock"]:has(span#header-nav-id) div[data-testid="column"]:nth-child(1) button[kind="secondary"] {
        background: rgba(10,10,10,0.5) !important; color: #D4AF37 !important; border: 2px solid #D4AF37 !important; border-radius: 12px !important; padding: 0 25px !important; width: 100% !important;
    }

    /* =========================================================
       2. FLOATING BUBBLES CSS
       ========================================================= */
    [data-testid="stSidebar"], [data-testid="collapsedControl"], header[data-testid="stHeader"] { display: none !important; }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) {
        position: fixed !important; top: 110px !important; left: 30px !important; width: 280px !important; z-index: 99999 !important; background: transparent !important; padding: 0 !important; pointer-events: none !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) .stSelectbox,
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) button {
        pointer-events: auto !important;
    }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) .stSelectbox {
        background-color: rgba(15, 15, 15, 0.9) !important; border: 2px solid #D4AF37 !important; border-radius: 18px !important; padding: 8px 15px !important; margin-bottom: 12px !important; box-shadow: 0px 8px 20px rgba(0,0,0,0.8) !important; backdrop-filter: blur(5px);
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) label { color: #D4AF37 !important; font-weight: bold; text-shadow: 1px 1px 3px black !important; margin-bottom: 5px !important; font-size: var(--f-hud-lbl) !important; }
    div[data-baseweb="select"] > div { background-color: #111 !important; border: 1px solid #333 !important; border-radius: 8px !important; color: white !important; font-size: var(--f-btn) !important; }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) button[kind="primary"] {
        background: rgba(15, 15, 15, 0.9) !important; color: #D4AF37 !important; border: 2px solid #D4AF37 !important; border-radius: 18px !important; width: 100% !important; height: 60px !important; box-shadow: 0px 8px 20px rgba(0,0,0,0.8) !important; transition: 0.2s !important; display: flex !important; align-items: center !important; justify-content: center !important; outline: none !important; backdrop-filter: blur(5px); margin-top: 5px !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) button[kind="primary"] p { font-size: var(--f-pri) !important; font-weight: bold !important; margin: 0 !important; color: inherit !important; }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) button[kind="primary"]:hover { background: #D4AF37 !important; color: #0A0A0A !important; box-shadow: 0 0 20px rgba(212, 175, 55, 0.8) !important; transform: translateY(-2px); border-color: #D4AF37 !important; }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#floating-controls) button[kind="primary"]:active { transform: scale(0.95) !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.5) !important; }

    /* SMART ALERTS & HUD */
    .smart-alert { position: fixed; top: 110px; left: 50%; transform: translateX(-50%); background: rgba(200, 50, 50, 0.95); border: 1px solid #ff4b4b; color: white; padding: 12px 25px; border-radius: 8px; text-align: center; font-weight: bold; z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .results-hud { position: fixed; bottom: 25px; left: 55%; transform: translateX(-50%); z-index: 9999; display: flex; gap: 15px; flex-wrap: nowrap; }
    .hud-card { background-color: rgba(10, 10, 10, 0.85); border: 1px solid rgba(212, 175, 55, 0.5); border-radius: 18px; min-width: 140px; height: 100px; box-shadow: 0px 5px 15px rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0 10px; }
    .highlight-card { background-color: #D4AF37; border: 2px solid #FFFFFF; box-shadow: 0px 5px 20px rgba(212, 175, 55, 0.5); min-width: 180px !important; }
    .hud-label { color: #D4AF37; font-size: var(--f-hud-lbl); font-weight: bold; text-transform: uppercase; margin-bottom: 5px; text-align: center; }
    .hud-value { color: white; font-size: var(--f-hud-val); font-weight: bold; text-align: center; white-space: nowrap; }
    .hud-label-dark { color: black; font-size: var(--f-hud-lbl); font-weight: 900; text-transform: uppercase; margin-bottom: 2px; text-align: center; line-height: 1.1; }
    .hud-value-dark { color: black; font-size: var(--f-hud-val-dark); font-weight: 900; text-align: center; white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. PAGE ARCHITECTURE
# ==========================================

# A. Header Navigation
nav_cols = st.columns([1.2, 1.2, 4.5, 1.3, 1.3, 1.2])
nav_cols[0].markdown("<span id='header-nav-id'></span>", unsafe_allow_html=True)
nav_cols[0].button(loc["btn_lang"], on_click=toggle_language, type="secondary", use_container_width=True)
view_label = loc['monthly'] if st.session_state.time_view == 'Annual' else loc['annual']
nav_cols[1].button(f"🔄 {view_label}", on_click=toggle_time, type="secondary", use_container_width=True)
nav_cols[3].button(f"🛠️ {loc['service']}", on_click=open_service, type="secondary", use_container_width=True)
nav_cols[4].button(f"📊 {loc['audit']}", on_click=toggle_audit, type="secondary", use_container_width=True)
nav_cols[5].button(f"🏠 {loc['overview']}", on_click=reset_view, type="secondary", use_container_width=True)

# B. Floating Bubbles Configuration
with st.container():
    st.markdown("<div id='floating-controls'></div>", unsafe_allow_html=True)
    load_choice = st.selectbox(loc["load"], loc["opt_loads"])
    maint_val = st.selectbox(loc["maint"], loc["opt_maint"])
    m_multiplier = {"Weekly (Elite)": 0.95, "Monthly (Standard)": 0.75, "Lazy Owner": 0.60, "أسبوعي (ممتاز)": 0.95, "شهري (قياسي)": 0.75, "بدون صيانة": 0.60}[maint_val]
    panel_w = st.selectbox(loc["tech"], [350, 450, 550, 650], index=1)
    st.button(loc["reset"], on_click=reset_view, type="primary", use_container_width=True)

st.markdown(f'<div class="solid-header"><div class="logo-container"><div class="logo-top">{loc["title_top"]}</div><div class="logo-bottom">{loc["title_bot"]}</div></div></div>', unsafe_allow_html=True)

if st.session_state.show_alert:
    st.markdown(f'<div class="smart-alert">{loc["alert"]}</div>', unsafe_allow_html=True)

# ==========================================
# 6. THE MAP ENGINE & MATH HUD (RESTORED THE 5TH BUBBLE)
# ==========================================
m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', zoom_control=True, max_zoom=22)

if st.session_state.points:
    for p in st.session_state.points: folium.CircleMarker(p, radius=5, color='#D4AF37', fill=True, fill_color='white').add_to(m)
    if len(st.session_state.points) >= 3: folium.Polygon(st.session_state.points, color="#D4AF37", fill=True, fill_opacity=0.3, weight=3).add_to(m)

map_data = st_folium(m, height=1000, width="100%", key="main_map", returned_objects=["last_clicked", "center", "zoom"])

if map_data:
    if map_data.get("zoom"): st.session_state.map_zoom = map_data["zoom"]
    if map_data.get("center"): st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
    if map_data.get("last_clicked"):
        new_p = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
        if not st.session_state.points or new_p != st.session_state.points[-1]:
            st.session_state.points.append(new_p)
            st.session_state.area = calculate_area(st.session_state.points)
            st.rerun()

if st.session_state.area > 0:
    area = st.session_state.area
    units = int(area / 2.3)
    kwp = (units * panel_w) / 1000.0
    consumption_map = {"Small Villa": 45000, "فيلا صغيرة": 45000, "Standard Villa": 75000, "فيلا قياسية": 75000, "Large Estate": 120000, "قصر صغير": 120000, "Palace": 200000, "قصر كبير": 200000}
    annual_consumption = consumption_map[load_choice]
    annual_generation = kwp * 2200 * m_multiplier
   
    # THE MATH RESTORE: Separating direct vs exported
    direct_kwh = min(annual_generation, annual_consumption)
    export_kwh = max(0, annual_generation - annual_consumption)
   
    direct_savings_ann = direct_kwh * 0.18
    export_credits_ann = export_kwh * 0.07
    total_benefit_ann = direct_savings_ann + export_credits_ann
   
    install_cost = 35000 + (kwp * 2100)
    payback = install_cost / total_benefit_ann if total_benefit_ann > 0 else 0
    divider = 1 if st.session_state.time_view == "Annual" else 12

    # Dynamic labels based on time view
    lbl_dir = loc["direct_a"] if st.session_state.time_view == "Annual" else loc["direct_m"]
    lbl_exp = loc["export_a"] if st.session_state.time_view == "Annual" else loc["export_m"]
    lbl_tot = loc["total_a"] if st.session_state.time_view == "Annual" else loc["total_m"]

    # THE BUBBLE RESTORE: 5 distinct bubbles rendering flawlessly!
    st.markdown(f"""
    <div class="results-hud">
        <div class="hud-card"><div class="hud-label">{loc["area"]}</div><div class="hud-value">{area:.1f} m²</div></div>
        <div class="hud-card"><div class="hud-label">{loc["units"]}</div><div class="hud-value">{units}</div></div>
        <div class="hud-card"><div class="hud-label">{lbl_dir}</div><div class="hud-value">{(direct_savings_ann/divider):,.0f} SAR</div></div>
        <div class="hud-card"><div class="hud-label">{lbl_exp}</div><div class="hud-value">{(export_credits_ann/divider):,.0f} SAR</div></div>
        <div class="hud-card highlight-card"><div class="hud-label-dark">{lbl_tot}</div><div class="hud-value-dark">{(total_benefit_ann/divider):,.0f} SAR</div></div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 7. MODAL ENGINE CSS (Locked and Untouched)
# ==========================================
modal_css = """
<style>
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) {
        position: fixed !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important;
        width: 480px !important; max-width: 90vw !important; background: rgba(15, 15, 15, 0.98) !important; border: 2px solid #D4AF37 !important;
        border-radius: 20px !important; padding: 40px 30px !important; z-index: 9999999 !important; box-shadow: 0px 20px 50px rgba(0,0,0,0.9) !important; max-height: 85vh !important; overflow-y: auto !important;
    }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) {
        position: absolute !important; top: 15px !important; right: 20px !important; width: auto !important; z-index: 999999 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) button[kind="secondary"] {
        background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; height: auto !important; outline: none !important; color: #D4AF37 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) button[kind="secondary"] p {
        font-size: 2.2rem !important; font-weight: 300 !important; line-height: 1 !important; margin: 0 !important; color: inherit !important; transition: 0.2s !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) button[kind="secondary"]:hover p {
        color: white !important; transform: scale(1.1); text-shadow: 0 0 10px rgba(212,175,55,0.6);
    }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="tertiary"] {
        background: transparent !important; color: transparent !important; border: none !important; box-shadow: none !important;
        height: 95px !important; width: 100% !important; margin-top: -110px !important; margin-bottom: 15px !important; position: relative !important; z-index: 9999 !important; cursor: pointer !important; display: block !important; outline: none !important; color: transparent !important;
    }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type {
        display: flex !important;
        flex-wrap: nowrap !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 20px !important;
        margin-top: 30px !important;
        margin-bottom: 10px !important;
        width: 100% !important;
        z-index: 999999 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type > div[data-testid="column"] {
        width: 45% !important;
        flex: 1 1 45% !important;
        min-width: 0 !important;
        display: block !important;
    }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button[kind="secondary"] {
        background: #222 !important; color: white !important; font-weight: bold !important; font-size: var(--f-pri) !important; border: 1px solid rgba(212,175,55,0.4) !important; border-radius: 12px !important; height: 50px !important; width: 100% !important; transition: 0.2s !important; margin: 0 !important; display: flex !important; align-items: center !important; justify-content: center !important; outline: none !important; opacity: 1 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button[kind="secondary"] p { color: inherit !important; margin: 0 !important; font-weight: inherit !important; }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button[kind="secondary"]:hover { background: #333 !important; border-color: #D4AF37 !important; box-shadow: 0 4px 15px rgba(212,175,55,0.4) !important; transform: translateY(-2px); }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button[kind="secondary"]:active { transform: scale(0.95) !important; box-shadow: none !important; }

    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"] {
        background-color: #D4AF37 !important; color: #0A0A0A !important; font-weight: bold !important; font-size: var(--f-pri) !important; border: none !important; border-radius: 12px !important; height: 50px !important; width: 100% !important; box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important; transition: 0.2s !important; display: flex !important; align-items: center !important; justify-content: center !important; outline: none !important; margin: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"] p { color: inherit !important; margin: 0 !important; font-weight: inherit !important; }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"]:hover { background-color: #FFFFFF !important; box-shadow: 0 4px 20px rgba(212,175,55,0.8) !important; transform: translateY(-2px); }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"]:active { transform: scale(0.95) !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.5) !important; }
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"]:disabled { background-color: #333 !important; color: #777 !important; cursor: not-allowed !important; border: 1px solid #444 !important; box-shadow: none !important; transform: none !important; }

    .scanner-ring { width: 100px; height: 100px; border: 4px solid #D4AF37; border-radius: 50%; margin: 60px auto 40px auto; animation: pulse 1.5s infinite; opacity: 0; }
    @keyframes pulse { 0% { transform: scale(0.6); opacity: 0; } 50% { opacity: 1; } 100% { transform: scale(1.2); opacity: 0; } }
    .checkmark-circle { width: 100px; height: 100px; border: 4px solid #D4AF37; border-radius: 50%; margin: 40px auto 20px auto; display: flex; align-items: center; justify-content: center; animation: scale-in 0.5s ease-out; }
    @keyframes scale-in { 0% { transform: scale(0); } 100% { transform: scale(1); } }
</style>
"""

# ==========================================
# 8. POPUP MODAL GENERATION
# ==========================================

if st.session_state.show_audit and st.session_state.area > 0:
    st.markdown(modal_css, unsafe_allow_html=True)
    with st.container():
        st.markdown("<div id='modal-marker'></div>", unsafe_allow_html=True)
        st.button("✖", key="aud_x", type="secondary", on_click=close_all_popups)
           
        st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); margin-top: -10px; padding-right: 40px;'>{loc['audit_title']}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #D4AF37; opacity: 0.3; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between; margin-top: 10px; padding: 0 10px;'><div><div style='color:#aaa; font-size:{f_lbl};'>{loc['cost']}</div><div style='color:white; font-size:{f_big}; font-weight:bold;'>{install_cost:,.0f} SAR</div></div><div><div style='color:#aaa; font-size:{f_lbl};'>{loc['payback']}</div><div style='color:white; font-size:{f_big}; font-weight:bold;'>{payback:.1f} {loc['years']}</div></div></div>", unsafe_allow_html=True)

if st.session_state.show_service:
    st.markdown(modal_css, unsafe_allow_html=True)
    with st.container():
        st.markdown("<div id='modal-marker'></div>", unsafe_allow_html=True)

        if st.session_state.svc_stage == "scanning":
            st.button("✖", key="scn_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div class='scanner-ring'></div><div style='text-align:center; color:#D4AF37; font-weight:bold; font-size:{f_val}; margin-top:40px;'>{loc['scanning']}</div>", unsafe_allow_html=True)
            time.sleep(2); st.session_state.svc_stage = "list"; st.rerun()
           
        elif st.session_state.svc_stage == "list":
            st.button("✖", key="list_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); margin-top: -10px; margin-bottom: 20px; padding-right: 40px;'>{loc['service_title']}</div>", unsafe_allow_html=True)

            my_lat, my_lon = st.session_state.map_center
            d_acwa = haversine(my_lat, my_lon, 24.72, 46.70)
            d_desert = haversine(my_lat, my_lon, 24.68, 46.65)
            d_alfanar = haversine(my_lat, my_lon, 24.75, 46.75)

            contractors = [
                ("ACWA Power Solar", "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=150&h=150&fit=crop", "⭐⭐⭐⭐⭐ 4.9", "🏆 Tier 1 Govt Partner", d_acwa),
                ("Desert Technologies", "https://images.unsplash.com/photo-1521618755572-156ae0cdd74d?w=150&h=150&fit=crop", "⭐⭐⭐⭐⭐ 4.8", "🇸🇦 Saudi Made Panels", d_desert),
                ("Alfanar Energy", "https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=150&h=150&fit=crop", "⭐⭐⭐⭐✨ 4.7", "⚡ Smart Grid Integration", d_alfanar)
            ]
           
            for name, img, stars, desc, dist in contractors:
                is_sel = (st.session_state.selected_contractor == name)
                bg = "rgba(45,45,45,0.95)" if is_sel else "rgba(30,30,30,0.6)"
                border = "2px solid #D4AF37" if is_sel else "1px solid rgba(255,255,255,0.2)"
                shadow = "0 4px 15px rgba(212,175,55,0.4)" if is_sel else "none"
               
                card = f"""
                <div style='min-height: 95px; background: {bg}; border: {border}; box-shadow: {shadow}; border-radius: 12px; padding: 15px; display: flex; align-items: center; box-sizing: border-box; transition: 0.2s;'>
                    <img src='{img}' style='width: 60px; height: 60px; border-radius: 8px; object-fit: cover; margin-right: 15px; border: 1px solid #D4AF37;'>
                    <div style='flex-grow: 1; line-height: 1.3;'>
                        <div style='color: white; font-weight: bold; font-size: {f_card_tit};'>{name}</div>
                        <div style='color: #D4AF37; font-size: {f_card_sub};'>{stars}</div>
                        <div style='color: #aaa; font-size: {f_card_dsc}; margin-top: 2px;'>{desc}</div>
                    </div>
                    <div style='color: white; font-weight: bold; font-size: {f_card_tit};'>{dist:.1f} km</div>
                </div>
                """
                st.markdown(card, unsafe_allow_html=True)
               
                if st.button(" ", key=f"btn_{name}", type="tertiary", use_container_width=True):
                    st.session_state.selected_contractor = name
                    st.rerun()

            st.write("")
            req_disabled = (st.session_state.selected_contractor == "")
            if st.button(loc['request'], type="primary", disabled=req_disabled, use_container_width=True):
                st.session_state.svc_stage = "receipt"
                st.rerun()

        elif st.session_state.svc_stage == "receipt":
            st.button("✖", key="rec_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); text-align: center; margin-top: -10px; margin-bottom: 20px; padding-right: 40px;'>{loc['receipt_title']}</div>", unsafe_allow_html=True)
           
            rec = f"<div style='background: rgba(255,255,255,0.05); border-radius: 12px; padding: 25px; text-align: left; margin-bottom: 50px; border-left: 4px solid #D4AF37;'><div style='color:#aaa; font-size:{f_lbl};'>{loc['selected']}</div><div style='color:#D4AF37; font-weight:bold; font-size: {f_val}; margin-bottom:15px;'>{st.session_state.selected_contractor}</div><div style='color:#aaa; font-size:{f_lbl};'>{loc['area']}</div><div style='color:white; font-weight:bold; font-size: {f_val}; margin-bottom:10px;'>{area:.1f} m²</div><div style='color:#aaa; font-size:{f_lbl};'>{loc['units']}</div><div style='color:white; font-weight:bold; font-size: {f_val}; margin-bottom:10px;'>{units} ({panel_w}W)</div><div style='color:#aaa; font-size:{f_lbl};'>{loc['cost']}</div><div style='color:#D4AF37; font-size:{f_big}; font-weight:bold;'>{install_cost:,.0f} SAR</div></div>"
            st.markdown(rec, unsafe_allow_html=True)
           
            b1, b2 = st.columns(2)
            with b1:
                if st.button(loc['cancel'], type="secondary", use_container_width=True):
                    st.session_state.svc_stage = "list"
                    st.rerun()
            with b2:
                if st.button(loc['confirm'], type="primary", use_container_width=True):
                    st.session_state.svc_stage = "submitting"
                    st.rerun()

        elif st.session_state.svc_stage == "submitting":
            st.button("✖", key="sub_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div class='scanner-ring'></div><div style='text-align:center; color:#D4AF37; font-size:{f_val}; font-weight:bold; margin-top:40px;'>Finalizing Dispatch...</div>", unsafe_allow_html=True)
            time.sleep(1.5); st.session_state.svc_stage = "success"; st.rerun()

        elif st.session_state.svc_stage == "success":
            st.button("✖", key="suc_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div class='checkmark-circle'><div style='color:#D4AF37; font-size:4rem; font-weight:bold;'>✔</div></div><div style='text-align:center; color:#D4AF37; font-size:{f_succ_tit}; font-weight:bold; margin-top: 20px;'>{loc['success']}</div><div style='text-align:center; color:white; font-size:{f_succ_sub}; margin-top:15px; line-height: 1.6; margin-bottom: 20px;'>{loc['success_sub']}<br><span style='color:#aaa; font-size: {f_lbl};'>Tracking ID: #RYD-{int(time.time() % 10000)}</span></div>", unsafe_allow_html=True)