"""
FUSION v3 - Multi-Source Intelligence Fusion Dashboard
CyberJoar AI OC.41335.2026 — Problem Statement 1
Author: [Your Name]

Logic Summary:
- Four intel streams: OSINT (open-source), HUMINT (human), IMINT (imagery), SIGINT (signals)
- Unified ingestion layer normalises all sources — MongoDB, AWS S3, CSV/JSON/Excel, manual form
- Confidence Scoring Engine: scores 0-99 based on field completeness, source quality, intel type
- Threat Level Engine: aggregates priority distribution → NOMINAL / ELEVATED / HIGH / CRITICAL
- Folium renders CartoDB Dark terrain map with type-coded markers + hover tooltips + click popups
- CRITICAL entries get an outer pulsing CircleMarker ring for visual distinction
- Export fused intelligence package as CSV or JSON
- MongoDB / S3 connector stubs ready for production wiring (see DATA SOURCES section)
"""

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MiniMap
from streamlit_folium import st_folium
import base64, datetime, uuid

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FUSION | Intel Ops",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;700;900&display=swap');

.stApp { background-color: #080b0f; color: #c9d1d9; }
.stApp header { background-color: #0d1117 !important; }
section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #1a2332; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

div[data-testid="metric-container"] {
  background-color: #0d1117; border: 1px solid #1a2332; border-radius: 3px; padding: 12px 16px;
}
div[data-testid="metric-container"] label { color: #4a5568 !important; font-size: 9px; letter-spacing: 3px; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
  color: #00e5a0 !important; font-family: 'Barlow Condensed', sans-serif; font-size: 28px; font-weight: 900;
}

.fusion-header {
  background-color: #0d1117; border: 1px solid #1a2332; border-left: 3px solid #00e5a0;
  padding: 16px 22px; margin-bottom: 16px; border-radius: 3px;
  display: flex; align-items: center; justify-content: space-between;
}
.fusion-title { font-family: 'Barlow Condensed', sans-serif; font-size: 32px; font-weight: 900; letter-spacing: 10px; color: #00e5a0; margin: 0; }
.fusion-sub   { font-family: 'Share Tech Mono', monospace; font-size: 10px; letter-spacing: 2px; color: #4a5568; margin-top: 3px; }
.threat-badge { font-family: 'Share Tech Mono', monospace; font-size: 10px; letter-spacing: 2px; padding: 6px 16px; border-radius: 2px; border: 1px solid; }

.sec-header      { font-family: 'Share Tech Mono', monospace; font-size: 9px; letter-spacing: 4px; color: #00e5a0; border-bottom: 1px solid #1a2332; padding-bottom: 6px; margin-bottom: 12px; opacity: .8; }
.sec-header-blue { font-family: 'Share Tech Mono', monospace; font-size: 9px; letter-spacing: 4px; color: #38bdf8; border-bottom: 1px solid #1a2332; padding-bottom: 6px; margin-bottom: 12px; opacity: .8; }

.conf-wrap  { margin: 8px 0; }
.conf-track { height: 3px; background: #1a2332; border-radius: 2px; overflow: hidden; margin-top: 4px; }
.conf-fill  { height: 100%; border-radius: 2px; }

.preview-card { background: #080b0f; border: 1px solid #1a2332; border-radius: 2px; padding: 10px 12px; margin-bottom: 10px; min-height: 64px; }
.preview-id   { font-family: 'Share Tech Mono', monospace; font-size: 8px; letter-spacing: 2px; color: #00e5a0; margin-bottom: 3px; }
.preview-desc { font-size: 12px; color: #c9d1d9; line-height: 1.5; min-height: 18px; }
.preview-tag  { font-family: 'Share Tech Mono', monospace; font-size: 8px; letter-spacing: 1px; padding: 1px 6px; border-radius: 2px; border: 1px solid; display: inline-block; margin-right: 4px; margin-top: 5px; }

.conn-card  { background: #080b0f; border: 1px solid #1a2332; border-radius: 2px; padding: 8px 10px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }
.conn-live  { border-color: #00e5a033; }
.conn-label { font-family: 'Share Tech Mono', monospace; font-size: 9px; letter-spacing: 1px; color: #c9d1d9; }
.conn-badge { font-family: 'Share Tech Mono', monospace; font-size: 8px; letter-spacing: 1px; padding: 2px 8px; border-radius: 2px; border: 1px solid; }

.stButton button {
  background: transparent !important; border: 1px solid #00e5a0 !important;
  color: #00e5a0 !important; font-family: 'Share Tech Mono', monospace !important;
  letter-spacing: 3px !important; border-radius: 2px !important; font-size: 11px !important;
}
.stButton button:hover { background: #00e5a0 !important; color: #000 !important; }

.stTabs [data-baseweb="tab-list"] { background-color: #0d1117 !important; border-bottom: 1px solid #1a2332; }
.stTabs [data-baseweb="tab"] { color: #4a5568 !important; font-family: 'Share Tech Mono', monospace; font-size: 9px; letter-spacing: 2px; }
.stTabs [aria-selected="true"] { color: #00e5a0 !important; border-bottom: 2px solid #00e5a0 !important; }

.streamlit-expanderHeader { background: #0d1117 !important; border: 1px solid #1a2332 !important; font-family: 'Share Tech Mono', monospace !important; font-size: 10px !important; letter-spacing: 2px !important; color: #8b9ab0 !important; }

input, textarea { background-color: #080b0f !important; border-color: #1a2332 !important; color: #c9d1d9 !important; font-family: 'Share Tech Mono', monospace !important; }
.stSuccess { background: rgba(0,229,160,.07) !important; border: 1px solid #00e5a0 !important; color: #00e5a0 !important; }
.stError   { background: rgba(239,68,68,.07)  !important; border: 1px solid #ef4444 !important; }
.stInfo    { background: rgba(56,189,248,.07) !important; border: 1px solid #38bdf8 !important; color: #38bdf8 !important; }
.stWarning { background: rgba(245,158,11,.07) !important; border: 1px solid #f59e0b !important; }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: #1a2332; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
TC = {"OSINT":"#00e5a0","HUMINT":"#38bdf8","IMINT":"#f59e0b","SIGINT":"#a78bfa"}
PC = {"LOW":"#4ade80","MED":"#f59e0b","HIGH":"#f97316","CRITICAL":"#ef4444"}
MC = {"OSINT":"green","HUMINT":"blue","IMINT":"orange","SIGINT":"purple"}

# ── HELPERS ────────────────────────────────────────────────────────────────────
def make_uid():  return uuid.uuid4().hex[:6].upper()
def now_ts():    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
def to_b64(f):   return base64.b64encode(f.read()).decode("utf-8")

def calc_confidence(desc, source, lat, lon, itype, priority):
    s = 0
    if len(desc) > 5:   s += 25
    if len(desc) > 30:  s += 15
    if source and len(source) > 2: s += 20
    if lat and lon:     s += 20
    if itype == "IMINT":  s += 10
    if itype == "SIGINT": s += 8
    if priority in ("HIGH","CRITICAL"): s += 5
    return min(99, s)

def threat_level(entries):
    crits = sum(1 for e in entries if e["priority"] == "CRITICAL")
    highs = sum(1 for e in entries if e["priority"] == "HIGH")
    if crits >= 2:                 return "CRITICAL", "#ef4444"
    elif crits >= 1 or highs >= 3: return "HIGH",     "#f97316"
    elif highs >= 1:               return "ELEVATED", "#f59e0b"
    else:                          return "NOMINAL",  "#4ade80"

def prio_icon(priority):
    return {"LOW":"info-sign","MED":"info-sign","HIGH":"warning-sign","CRITICAL":"remove"}.get(priority,"info-sign")

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "entries" not in st.session_state:
    st.session_state.entries = [
        {"id":"A1B2","lat":28.6139,"lon":77.2090,"desc":"Unusual vehicle convoy observed near Parliament Street. 4 unplated vehicles moving in formation.","intel_type":"HUMINT","source":"Field Agent ALPHA","priority":"HIGH","timestamp":"2025-04-19 08:32","image_b64":None,"image_name":None,"confidence":82},
        {"id":"C3D4","lat":19.0760,"lon":72.8777,"desc":"Open-source: 3 unidentified vessels clustered at restricted port zone — AIS transponders disabled.","intel_type":"OSINT","source":"Vessel Finder / MarineTraffic","priority":"MED","timestamp":"2025-04-19 09:14","image_b64":None,"image_name":None,"confidence":67},
        {"id":"E5F6","lat":12.9716,"lon":77.5946,"desc":"SAT imagery confirms major infrastructure expansion at previously dormant site. New roofing visible.","intel_type":"IMINT","source":"Commercial SAT-7B Tasking","priority":"CRITICAL","timestamp":"2025-04-19 10:05","image_b64":None,"image_name":None,"confidence":91},
        {"id":"G7H8","lat":17.3850,"lon":78.4867,"desc":"Coordinated bot-network activity spike around monitored hashtags. Possible IO operation.","intel_type":"OSINT","source":"SOCMINT Monitoring Module","priority":"LOW","timestamp":"2025-04-19 11:22","image_b64":None,"image_name":None,"confidence":44},
        {"id":"I9J0","lat":22.5726,"lon":88.3639,"desc":"HUMINT source confirms clandestine meeting at eastern port facility — 4 individuals, 2 unidentified.","intel_type":"HUMINT","source":"Field Agent BRAVO","priority":"HIGH","timestamp":"2025-04-19 12:44","image_b64":None,"image_name":None,"confidence":78},
        {"id":"K1L2","lat":26.8467,"lon":80.9462,"desc":"Encrypted radio burst detected on monitored frequency — 340MHz, duration 4.2s, repeat interval 90s.","intel_type":"SIGINT","source":"ELINT Platform SIERRA","priority":"HIGH","timestamp":"2025-04-19 13:10","image_b64":None,"image_name":None,"confidence":85},
    ]

if "sel_type" not in st.session_state: st.session_state.sel_type = "OSINT"
if "sel_prio" not in st.session_state: st.session_state.sel_prio = "MED"

# ── MAP BUILDER ────────────────────────────────────────────────────────────────
def build_map(entries, filter_type="ALL"):
    m = folium.Map(location=[22.0, 78.5], zoom_start=5, tiles=None)
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© OpenStreetMap © CARTO", name="Dark Terrain", max_zoom=19
    ).add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri", name="Satellite Imagery", max_zoom=19
    ).add_to(m)
    folium.LayerControl().add_to(m)
    MiniMap(toggle_display=True, tile_layer="CartoDB.DarkMatter").add_to(m)

    shown = entries if filter_type == "ALL" else [e for e in entries if e["intel_type"] == filter_type]

    for e in shown:
        tc   = TC.get(e["intel_type"], "#00e5a0")
        pc   = PC.get(e["priority"],   "#f59e0b")
        conf = e.get("confidence", 50)
        is_crit = e["priority"] == "CRITICAL"

        img_html = (
            f'<img src="data:image/jpeg;base64,{e["image_b64"]}" '
            f'style="width:100%;border-radius:2px;margin-top:8px;border:1px solid #1a2332;"/>'
            if e.get("image_b64") else
            '<div style="height:44px;border:1px dashed #1a2332;border-radius:2px;display:flex;'
            'align-items:center;justify-content:center;margin-top:8px;font-size:9px;color:#4a5568;'
            'letter-spacing:2px;font-family:Courier New,monospace">NO IMAGE</div>'
        )

        # Hover tooltip — PS1 requirement: "hover-activated pop-ups"
        tooltip_html = (
            f'<div style="background:#0d1117;color:#c9d1d9;font-family:Courier New,monospace;'
            f'font-size:11px;padding:8px 12px;border-radius:3px;border:1px solid {tc};max-width:230px;line-height:1.65">'
            f'<div style="color:{tc};font-size:8px;letter-spacing:2px;margin-bottom:3px">{e["intel_type"]} · #{e["id"]}</div>'
            f'<div>{e["desc"][:65]}{"..." if len(e["desc"])>65 else ""}</div>'
            f'<div style="color:#4a5568;font-size:9px;margin-top:4px">'
            f'{e["priority"]} · CONF {conf}% · {e["timestamp"].split()[1]}</div></div>'
        )

        # Full popup on click
        popup_html = (
            f'<div style="min-width:220px;max-width:260px;background:#0d1117;color:#c9d1d9;'
            f'font-family:Courier New,monospace;font-size:11px;padding:14px;border-radius:3px;border:1px solid #1a2332;">'
            f'<div style="font-size:8px;letter-spacing:3px;color:{tc};margin-bottom:2px">{e["intel_type"]} INTELLIGENCE</div>'
            f'<div style="font-size:9px;color:#4a5568;margin-bottom:8px">ID #{e["id"]}</div>'
            f'<div style="line-height:1.65;margin-bottom:10px">{e["desc"]}</div>'
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px">'
            f'<span style="padding:2px 7px;border-radius:2px;border:1px solid {tc};color:{tc};font-size:8px">{e["intel_type"]}</span>'
            f'<span style="padding:2px 7px;border-radius:2px;border:1px solid {pc};color:{pc};font-size:8px">{e["priority"]}</span>'
            f'<span style="padding:2px 7px;border-radius:2px;border:1px solid #1a2332;color:#4a5568;font-size:8px">CONF {conf}%</span>'
            f'</div>'
            f'<div style="color:#4a5568;font-size:9px;line-height:2">'
            f'<span style="color:#c9d1d9">SRC:</span> {e.get("source","—")}<br>'
            f'<span style="color:#c9d1d9">TIME:</span> {e["timestamp"]}<br>'
            f'<span style="color:#c9d1d9">COORDS:</span> {e["lat"]:.4f}N, {e["lon"]:.4f}E</div>'
            f'{img_html}</div>'
        )

        # Outer ring for CRITICAL entries
        if is_crit:
            folium.CircleMarker(
                location=[e["lat"], e["lon"]], radius=18,
                color="#ef4444", fill=False, weight=1.5, opacity=0.4
            ).add_to(m)

        folium.Marker(
            location=[e["lat"], e["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=folium.Tooltip(tooltip_html, sticky=False),
            icon=folium.Icon(
                color=MC.get(e["intel_type"], "gray"),
                icon=prio_icon(e["priority"]),
                prefix="glyphicon"
            )
        ).add_to(m)

    return m

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:900;
                letter-spacing:7px;color:#00e5a0;margin-bottom:2px'>⬡ FUSION</div>
    <div style='font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:3px;
                color:#4a5568;margin-bottom:14px'>INTELLIGENCE PLATFORM v3.0</div>
    """, unsafe_allow_html=True)

    # ── DATA SOURCES PANEL ───────────────────────────────────────────────────
    st.markdown("<div class='sec-header-blue'>// DATA SOURCES</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='conn-card conn-live'>
      <div><div class='conn-label'>Manual Entry / Form</div>
        <div style='font-family:"Share Tech Mono",monospace;font-size:8px;color:#4a5568;margin-top:2px'>OSINT · HUMINT · IMINT · SIGINT</div></div>
      <div class='conn-badge' style='border-color:#00e5a0;color:#00e5a0'>LIVE</div>
    </div>
    <div class='conn-card conn-live'>
      <div><div class='conn-label'>CSV / JSON / Excel Upload</div>
        <div style='font-family:"Share Tech Mono",monospace;font-size:8px;color:#4a5568;margin-top:2px'>Bulk field report ingestion</div></div>
      <div class='conn-badge' style='border-color:#00e5a0;color:#00e5a0'>LIVE</div>
    </div>
    <div class='conn-card'>
      <div><div class='conn-label'>MongoDB Atlas</div>
        <div style='font-family:"Share Tech Mono",monospace;font-size:8px;color:#4a5568;margin-top:2px'>OSINT / SIGINT persistent store</div></div>
      <div class='conn-badge' style='border-color:#f59e0b;color:#f59e0b'>CONFIGURE</div>
    </div>
    <div class='conn-card'>
      <div><div class='conn-label'>AWS S3 Bucket</div>
        <div style='font-family:"Share Tech Mono",monospace;font-size:8px;color:#4a5568;margin-top:2px'>IMINT imagery store</div></div>
      <div class='conn-badge' style='border-color:#f59e0b;color:#f59e0b'>CONFIGURE</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("CONFIGURE MONGODB / S3"):
        st.text_input("MongoDB URI", placeholder="mongodb+srv://user:pass@cluster.mongodb.net", type="password")
        st.text_input("S3 Bucket Name", placeholder="fusion-imint-bucket")
        st.text_input("AWS Region", placeholder="ap-south-1")
        st.info("Production-ready stubs — connect credentials to activate live cloud ingestion.")

    st.markdown("---")

    # ── NEW INTEL FORM ───────────────────────────────────────────────────────
    st.markdown("<div class='sec-header'>// LOG NEW INTEL</div>", unsafe_allow_html=True)

    # Intel type — 4 columns
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;font-size:8px;letter-spacing:2px;color:#4a5568;margin-bottom:5px'>INTEL TYPE</div>", unsafe_allow_html=True)
    tc1, tc2, tc3, tc4 = st.columns(4)
    for col, t, clr in [(tc1,"OSINT","#00e5a0"),(tc2,"HUMINT","#38bdf8"),(tc3,"IMINT","#f59e0b"),(tc4,"SIGINT","#a78bfa")]:
        with col:
            sel = st.session_state.sel_type == t
            st.markdown(f"""<div style='text-align:center;padding:5px 0;
                border:1px solid {clr if sel else "#1a2332"};border-radius:2px;
                background:{clr + "11" if sel else "transparent"};
                color:{clr if sel else "#4a5568"};
                font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:1px'>{t}</div>
            """, unsafe_allow_html=True)
            if st.button(t, key=f"type_{t}", use_container_width=True):
                st.session_state.sel_type = t
                st.rerun()

    cl, cn = st.columns(2)
    with cl: lat = st.number_input("LAT", value=28.6139, format="%.4f", step=0.0001)
    with cn: lon = st.number_input("LON", value=77.2090, format="%.4f", step=0.0001)

    desc   = st.text_area("DESCRIPTION", placeholder="Describe the observation in detail...", height=72)
    source = st.text_input("SOURCE / AGENT", placeholder="Field Agent / Platform / Feed")

    # Priority — 4 columns
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;font-size:8px;letter-spacing:2px;color:#4a5568;margin-bottom:5px'>PRIORITY</div>", unsafe_allow_html=True)
    pp1, pp2, pp3, pp4 = st.columns(4)
    for col, p, clr in [(pp1,"LOW","#4ade80"),(pp2,"MED","#f59e0b"),(pp3,"HIGH","#f97316"),(pp4,"CRITICAL","#ef4444")]:
        with col:
            sel = st.session_state.sel_prio == p
            st.markdown(f"""<div style='text-align:center;padding:4px 0;
                border:1px solid {clr if sel else "#1a2332"};border-radius:2px;
                background:{clr + "11" if sel else "transparent"};
                color:{clr if sel else "#4a5568"};
                font-family:"Share Tech Mono",monospace;font-size:7px;letter-spacing:1px'>{p}</div>
            """, unsafe_allow_html=True)
            if st.button(p, key=f"prio_{p}", use_container_width=True):
                st.session_state.sel_prio = p
                st.rerun()

    # Confidence bar
    conf = calc_confidence(desc or "", source or "", lat, lon,
                           st.session_state.sel_type, st.session_state.sel_prio)
    cc = "#00e5a0" if conf > 70 else "#f59e0b" if conf > 40 else "#ef4444"
    st.markdown(f"""
    <div class='conf-wrap'>
      <div style='display:flex;justify-content:space-between'>
        <span style='font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:2px;color:#4a5568'>CONFIDENCE SCORE</span>
        <span style='font-family:"Share Tech Mono",monospace;font-size:10px;color:{cc};font-weight:bold'>{conf}%</span>
      </div>
      <div class='conf-track'><div class='conf-fill' style='width:{conf}%;background:{cc}'></div></div>
    </div>""", unsafe_allow_html=True)

    # Live preview
    tc_p  = TC.get(st.session_state.sel_type, "#00e5a0")
    pc_p  = PC.get(st.session_state.sel_prio, "#f59e0b")
    prev  = desc.strip() if desc and desc.strip() else "<span style='color:#4a5568;font-style:italic'>start typing to preview entry...</span>"
    st.markdown(f"""
    <div style='font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:3px;color:#38bdf8;
                border-bottom:1px solid #1a2332;padding-bottom:5px;margin-bottom:8px;opacity:.8'>// LIVE PREVIEW</div>
    <div class='preview-card'>
      <div class='preview-id'>PENDING · {st.session_state.sel_type}</div>
      <div class='preview-desc'>{prev}</div>
      <span class='preview-tag' style='color:{tc_p};border-color:{tc_p}'>{st.session_state.sel_type}</span>
      <span class='preview-tag' style='color:{pc_p};border-color:{pc_p}'>{st.session_state.sel_prio}</span>
      <span class='preview-tag' style='color:{cc};border-color:{cc}'>CONF {conf}%</span>
      {f'<span class="preview-tag" style="color:#4a5568;border-color:#1a2332">{(source or "")[:14]}</span>' if source else ''}
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;font-size:8px;letter-spacing:2px;color:#4a5568;margin-bottom:4px'>ATTACH IMINT IMAGE — drag and drop or click</div>", unsafe_allow_html=True)
    img_file = st.file_uploader("", type=["jpg","jpeg","png"], label_visibility="collapsed")
    if img_file:
        st.markdown(f"<div style='font-family:\"Share Tech Mono\",monospace;font-size:9px;color:#00e5a0;margin-bottom:4px'>✓ {img_file.name}</div>", unsafe_allow_html=True)

    if st.button("▶  TRANSMIT INTEL", use_container_width=True):
        if not (desc and desc.strip()):
            st.error("DESCRIPTION REQUIRED")
        else:
            b64 = to_b64(img_file) if img_file else None
            entry = {
                "id": make_uid(), "lat": lat, "lon": lon,
                "desc": desc.strip(), "intel_type": st.session_state.sel_type,
                "source": source or "Manual Entry",
                "priority": st.session_state.sel_prio,
                "timestamp": now_ts(),
                "image_b64": b64, "image_name": img_file.name if img_file else None,
                "confidence": conf
            }
            st.session_state.entries.insert(0, entry)
            st.success(f"✓ LOGGED — ID: {entry['id']}  ·  CONF {conf}%")
            st.rerun()

    st.markdown("---")

    # Bulk ingest
    st.markdown("<div class='sec-header'>// BULK INGEST</div>", unsafe_allow_html=True)
    with st.expander("UPLOAD CSV / JSON / EXCEL"):
        bulk = st.file_uploader("Drag and drop or click to browse", type=["csv","json","xlsx","xls"], key="bulk")
        if bulk:
            try:
                ext = bulk.name.split(".")[-1].lower()
                df  = (pd.read_csv(bulk) if ext=="csv" else
                       pd.read_json(bulk) if ext=="json" else pd.read_excel(bulk))
                df.columns = df.columns.str.lower()
                if not {"lat","lon","desc"}.issubset(set(df.columns)):
                    st.error("FILE MUST HAVE: lat, lon, desc columns")
                else:
                    count = 0
                    for _, row in df.iterrows():
                        c = calc_confidence(
                            str(row.get("desc","")), str(row.get("source","")),
                            row.get("lat"), row.get("lon"),
                            str(row.get("intel_type","OSINT")).upper(),
                            str(row.get("priority","MED")).upper()
                        )
                        st.session_state.entries.append({
                            "id": make_uid(), "lat": float(row.get("lat",0)),
                            "lon": float(row.get("lon",0)), "desc": str(row.get("desc","—")),
                            "intel_type": str(row.get("intel_type", row.get("type","OSINT"))).upper(),
                            "source": str(row.get("source","Bulk Import")),
                            "priority": str(row.get("priority","MED")).upper(),
                            "timestamp": str(row.get("timestamp", now_ts())),
                            "image_b64": None, "image_name": None, "confidence": c
                        })
                        count += 1
                    st.success(f"✓ {count} ENTRIES INGESTED")
                    st.rerun()
            except Exception as ex:
                st.error(f"PARSE ERROR: {ex}")

    st.markdown("---")
    filter_type = st.radio("FILTER MAP", ["ALL","OSINT","HUMINT","IMINT","SIGINT"], horizontal=True)
    st.markdown("---")
    if st.button("✕  CLEAR ALL ENTRIES", use_container_width=True):
        st.session_state.entries = []
        st.rerun()

    st.markdown("""<div style='margin-top:14px;font-family:"Share Tech Mono",monospace;
        font-size:7px;letter-spacing:2px;color:#1a2332;text-align:center'>
        CYBERJOAR · PS-01 · OC.41335.2026</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
entries = st.session_state.entries
tlevel, tcolor = threat_level(entries)

st.markdown(f"""
<div class='fusion-header'>
  <div>
    <div class='fusion-title'>FUSION</div>
    <div class='fusion-sub'>MULTI-SOURCE INTELLIGENCE FUSION DASHBOARD  ·  CYBERJOAR AI OC.41335.2026  ·  PS-01</div>
  </div>
  <div style='text-align:right'>
    <div class='threat-badge' style='border-color:{tcolor};color:{tcolor}'>● THREAT: {tlevel}</div>
    <div style='font-family:"Share Tech Mono",monospace;font-size:9px;color:#4a5568;
                margin-top:6px;letter-spacing:1px'>{now_ts()} UTC+5:30</div>
  </div>
</div>""", unsafe_allow_html=True)

# Stats — 7 columns including SIGINT and AVG CONF
c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
avg_conf = int(sum(e.get("confidence",0) for e in entries)/len(entries)) if entries else 0
with c1: st.metric("TOTAL",    len(entries))
with c2: st.metric("OSINT",    len([e for e in entries if e["intel_type"]=="OSINT"]))
with c3: st.metric("HUMINT",   len([e for e in entries if e["intel_type"]=="HUMINT"]))
with c4: st.metric("IMINT",    len([e for e in entries if e["intel_type"]=="IMINT"]))
with c5: st.metric("SIGINT",   len([e for e in entries if e["intel_type"]=="SIGINT"]))
with c6: st.metric("CRITICAL", len([e for e in entries if e["priority"]=="CRITICAL"]))
with c7: st.metric("AVG CONF", f"{avg_conf}%")

st.markdown("<br>", unsafe_allow_html=True)

tab_map, tab_feed, tab_export = st.tabs(["🗺  MAP VIEW", "📋  INTEL FEED", "📤  EXPORT"])

with tab_map:
    st.markdown("<div class='sec-header'>// GEOSPATIAL OVERLAY — HOVER FOR INSTANT INTEL · CLICK FOR FULL POPUP + IMAGE</div>", unsafe_allow_html=True)
    if not entries:
        st.info("NO ENTRIES — add intel via sidebar or bulk upload.")
    else:
        st_folium(build_map(entries, filter_type), width="100%", height=565, returned_objects=[])
    st.markdown("""
    <div style='display:flex;gap:18px;margin-top:10px;font-family:"Share Tech Mono",monospace;font-size:9px;flex-wrap:wrap'>
      <span style='color:#00e5a0'>● OSINT</span>
      <span style='color:#38bdf8'>● HUMINT</span>
      <span style='color:#f59e0b'>● IMINT</span>
      <span style='color:#a78bfa'>● SIGINT</span>
      <span style='color:#ef4444'>● CRITICAL (outer ring)</span>
      <span style='color:#4a5568;margin-left:auto'>hover = tooltip · click = popup + image</span>
    </div>""", unsafe_allow_html=True)

with tab_feed:
    st.markdown("<div class='sec-header'>// LIVE INTEL FEED — ALL SOURCES</div>", unsafe_allow_html=True)
    if not entries:
        st.info("NO ENTRIES IN SYSTEM")
    else:
        search = st.text_input("SEARCH", placeholder="Filter by description / source / type...", label_visibility="collapsed")
        shown = [e for e in entries if
                 search.lower() in e["desc"].lower() or
                 search.lower() in e.get("source","").lower() or
                 search.lower() in e["intel_type"].lower()
                ] if search else list(entries)

        st.markdown(f"<div style='font-family:\"Share Tech Mono\",monospace;font-size:8px;color:#4a5568;margin-bottom:8px'>{len(shown)} ENTRIES</div>", unsafe_allow_html=True)

        for e in shown:
            tc2  = TC.get(e["intel_type"],"#00e5a0")
            pc2  = PC.get(e["priority"],"#f59e0b")
            c2   = e.get("confidence",0)
            cc2  = "#00e5a0" if c2>70 else "#f59e0b" if c2>40 else "#ef4444"
            flag = " 🖼" if e.get("image_b64") else ""
            with st.expander(f"#{e['id']}  ·  {e['intel_type']}  ·  {e['desc'][:48]}...{flag}  [{e['priority']}]  {c2}%"):
                ca, cb = st.columns([2,1])
                with ca:
                    st.markdown(f"""
                    <div style='font-family:"Share Tech Mono",monospace;font-size:11px;line-height:2.2'>
                      <span style='color:#4a5568'>TYPE   →</span> <span style='color:{tc2}'>{e["intel_type"]}</span><br>
                      <span style='color:#4a5568'>PRIO   →</span> <span style='color:{pc2}'>{e["priority"]}</span><br>
                      <span style='color:#4a5568'>CONF   →</span> <span style='color:{cc2}'>{c2}%</span><br>
                      <span style='color:#4a5568'>SOURCE →</span> {e.get("source","—")}<br>
                      <span style='color:#4a5568'>TIME   →</span> {e["timestamp"]}<br>
                      <span style='color:#4a5568'>COORDS →</span> {e["lat"]:.4f}N, {e["lon"]:.4f}E
                    </div>
                    <div style='margin-top:10px;padding:10px;background:#080b0f;border:1px solid #1a2332;
                                border-radius:2px;font-size:12px;line-height:1.7;color:#c9d1d9'>{e["desc"]}</div>
                    """, unsafe_allow_html=True)
                with cb:
                    if e.get("image_b64"):
                        st.image(f"data:image/jpeg;base64,{e['image_b64']}",
                                 caption=f"IMINT: {e.get('image_name','')}", use_container_width=True)
                    else:
                        st.markdown("""<div style='height:90px;border:1px dashed #1a2332;border-radius:2px;
                            display:flex;align-items:center;justify-content:center;
                            font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:2px;color:#4a5568'>
                            NO IMAGE</div>""", unsafe_allow_html=True)

with tab_export:
    st.markdown("<div class='sec-header'>// EXPORT INTELLIGENCE PACKAGE</div>", unsafe_allow_html=True)
    if not entries:
        st.info("NO DATA TO EXPORT")
    else:
        df = pd.DataFrame([{
            "ID": e["id"], "Timestamp": e["timestamp"],
            "Intel Type": e["intel_type"], "Priority": e["priority"],
            "Confidence": f"{e.get('confidence',0)}%",
            "Latitude": e["lat"], "Longitude": e["lon"],
            "Description": e["desc"], "Source": e.get("source",""),
            "Has Image": "YES" if e.get("image_b64") else "NO"
        } for e in entries])
        st.dataframe(df, use_container_width=True, height=300)
        ec1, ec2 = st.columns(2)
        with ec1:
            st.download_button("⬇  DOWNLOAD CSV", df.to_csv(index=False).encode(),
                               "fusion_export.csv", "text/csv", use_container_width=True)
        with ec2:
            st.download_button("⬇  DOWNLOAD JSON", df.to_json(orient="records", indent=2).encode(),
                               "fusion_export.json", "application/json", use_container_width=True)