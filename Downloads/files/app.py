"""
FUSION - Multi-Source Intelligence Dashboard
Built for CyberJoar AI OC Assignment — Problem Statement 1
Author: [Your Name]

Logic Summary:
- Ingests OSINT (MongoDB/S3/manual), HUMINT (CSV/JSON/Excel), IMINT (JPG/JPEG images)
- Normalizes all sources into a unified GeoDataFrame
- Renders interactive Leaflet map via Folium with type-coded markers
- Hover/click popups show metadata + embedded IMINT imagery
- Streamlit session state acts as lightweight in-memory fusion layer
"""

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium
import json
import io
import base64
from PIL import Image
import datetime
import uuid
import os

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FUSION | Intelligence Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Import fonts */
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;700;900&display=swap');

  /* Dark military theme */
  .stApp { background-color: #0d1117; color: #c9d1d9; }
  .stApp header { background-color: #161b22 !important; }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #21293a;
  }
  section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stFileUploader label { color: #8b9ab0 !important; font-size: 11px; letter-spacing: 2px; }

  /* Metric cards */
  div[data-testid="metric-container"] {
    background-color: #161b22;
    border: 1px solid #21293a;
    border-radius: 4px;
    padding: 14px 18px;
  }
  div[data-testid="metric-container"] label { color: #4a5568 !important; font-size: 10px; letter-spacing: 3px; }
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #00e5a0 !important;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 32px;
    font-weight: 900;
  }

  /* Main dashboard header */
  .fusion-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21293a;
    border-left: 3px solid #00e5a0;
    padding: 18px 24px;
    margin-bottom: 20px;
    border-radius: 4px;
  }
  .fusion-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 36px;
    font-weight: 900;
    letter-spacing: 10px;
    color: #00e5a0;
    margin: 0;
  }
  .fusion-subtitle {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: #4a5568;
    margin-top: 4px;
  }
  .status-pill {
    display: inline-block;
    background: rgba(0,229,160,0.1);
    border: 1px solid #00e5a0;
    color: #00e5a0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    padding: 3px 12px;
    border-radius: 2px;
    margin-top: 8px;
  }

  /* Intel type badges */
  .badge-osint  { background:#00e5a022; color:#00e5a0; border:1px solid #00e5a0; padding:2px 8px; border-radius:2px; font-size:10px; letter-spacing:2px; font-family:'Share Tech Mono',monospace; }
  .badge-humint { background:#38bdf822; color:#38bdf8; border:1px solid #38bdf8; padding:2px 8px; border-radius:2px; font-size:10px; letter-spacing:2px; font-family:'Share Tech Mono',monospace; }
  .badge-imint  { background:#f59e0b22; color:#f59e0b; border:1px solid #f59e0b; padding:2px 8px; border-radius:2px; font-size:10px; letter-spacing:2px; font-family:'Share Tech Mono',monospace; }

  /* Section headers */
  .sec-header {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px;
    letter-spacing: 4px;
    color: #00e5a0;
    border-bottom: 1px solid #21293a;
    padding-bottom: 8px;
    margin-bottom: 14px;
    opacity: 0.8;
  }

  /* Feed table */
  .feed-row {
    background: #161b22;
    border: 1px solid #21293a;
    border-radius: 3px;
    padding: 10px 14px;
    margin-bottom: 6px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  /* Buttons */
  .stButton button {
    background: transparent !important;
    border: 1px solid #00e5a0 !important;
    color: #00e5a0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 3px !important;
    border-radius: 2px !important;
    font-size: 12px !important;
  }
  .stButton button:hover {
    background: #00e5a0 !important;
    color: #000 !important;
  }

  /* File uploader */
  .stFileUploader {
    background: #161b22 !important;
    border: 1px dashed #21293a !important;
    border-radius: 3px !important;
  }

  /* Dataframe */
  .stDataFrame { border: 1px solid #21293a; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] { background-color: #161b22 !important; border-bottom: 1px solid #21293a; }
  .stTabs [data-baseweb="tab"] { color: #4a5568 !important; font-family: 'Share Tech Mono', monospace; font-size: 10px; letter-spacing: 2px; }
  .stTabs [aria-selected="true"] { color: #00e5a0 !important; border-bottom: 2px solid #00e5a0 !important; }

  /* Expander */
  .streamlit-expanderHeader {
    background: #161b22 !important;
    border: 1px solid #21293a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    color: #8b9ab0 !important;
  }

  /* Input fields */
  input, textarea, .stSelectbox select {
    background-color: #0d1117 !important;
    border-color: #21293a !important;
    color: #c9d1d9 !important;
    font-family: 'Share Tech Mono', monospace !important;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: #0d1117; }
  ::-webkit-scrollbar-thumb { background: #21293a; }

  /* Success/warning */
  .stSuccess { background: rgba(0,229,160,0.08) !important; border: 1px solid #00e5a0 !important; color: #00e5a0 !important; }
  .stWarning { background: rgba(245,158,11,0.08) !important; border: 1px solid #f59e0b !important; }
  .stError   { background: rgba(239,68,68,0.08)  !important; border: 1px solid #ef4444 !important; }
  .stInfo    { background: rgba(56,189,248,0.08) !important; border: 1px solid #38bdf8 !important; color: #38bdf8 !important; }

  /* Hide Streamlit branding */
  #MainMenu, footer { visibility: hidden; }
  .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
if "entries" not in st.session_state:
    st.session_state.entries = []
    # Seed some demo data so the map isn't empty on first load
    st.session_state.entries = [
        {
            "id": "DEMO-001", "lat": 28.6139, "lon": 77.2090,
            "desc": "Unusual movement pattern detected near Parliament Street corridor.",
            "intel_type": "HUMINT", "source": "Field Agent ALPHA", "priority": "HIGH",
            "timestamp": "2025-04-19 08:32", "image_b64": None, "image_name": None
        },
        {
            "id": "DEMO-002", "lat": 19.0760, "lon": 72.8777,
            "desc": "Open-source reporting on maritime vessel cluster — 3 unidentified ships.",
            "intel_type": "OSINT", "source": "Twitter Feed / Vessel Finder", "priority": "MED",
            "timestamp": "2025-04-19 09:15", "image_b64": None, "image_name": None
        },
        {
            "id": "DEMO-003", "lat": 12.9716, "lon": 77.5946,
            "desc": "Satellite imagery confirms infrastructure expansion at identified site.",
            "intel_type": "IMINT", "source": "Commercial SAT-7B", "priority": "CRITICAL",
            "timestamp": "2025-04-19 10:05", "image_b64": None, "image_name": None
        },
        {
            "id": "DEMO-004", "lat": 17.3850, "lon": 78.4867,
            "desc": "Social media analysis: coordinated bot activity around key topics.",
            "intel_type": "OSINT", "source": "SOCMINT Module", "priority": "LOW",
            "timestamp": "2025-04-19 11:22", "image_b64": None, "image_name": None
        },
        {
            "id": "DEMO-005", "lat": 22.5726, "lon": 88.3639,
            "desc": "HUMINT source confirms meeting at Port facility — 4 individuals.",
            "intel_type": "HUMINT", "source": "Field Agent BRAVO", "priority": "HIGH",
            "timestamp": "2025-04-19 12:44", "image_b64": None, "image_name": None
        },
    ]

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None


# ─── HELPERS ─────────────────────────────────────────────────────────────────
TYPE_COLOR = {"OSINT": "#00e5a0", "HUMINT": "#38bdf8", "IMINT": "#f59e0b"}
PRIO_COLOR = {"LOW": "#4ade80", "MED": "#f59e0b", "HIGH": "#f97316", "CRITICAL": "#ef4444"}

def make_uid():
    return uuid.uuid4().hex[:6].upper()

def img_to_b64(img_bytes):
    return base64.b64encode(img_bytes).decode("utf-8")

def now_ts():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def marker_color(intel_type):
    return {"OSINT": "green", "HUMINT": "blue", "IMINT": "orange"}.get(intel_type, "gray")

def priority_icon(priority):
    return {"LOW": "info-sign", "MED": "warning-sign", "HIGH": "fire", "CRITICAL": "remove"}.get(priority, "info-sign")


# ─── BUILD MAP ────────────────────────────────────────────────────────────────
def build_map(entries, filter_type="ALL"):
    m = folium.Map(
        location=[22.0, 78.5],
        zoom_start=5,
        tiles=None
    )

    # Dark terrain tile
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© OpenStreetMap, © CARTO",
        name="Dark Terrain",
        max_zoom=19
    ).add_to(m)

    # Satellite option
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri",
        name="Satellite",
        max_zoom=19
    ).add_to(m)

    folium.LayerControl().add_to(m)
    MiniMap(toggle_display=True, tile_layer="CartoDB.DarkMatter").add_to(m)

    filtered = entries if filter_type == "ALL" else [e for e in entries if e["intel_type"] == filter_type]

    for entry in filtered:
        color = marker_color(entry["intel_type"])
        icon  = priority_icon(entry["priority"])
        tc    = TYPE_COLOR.get(entry["intel_type"], "#00e5a0")
        pc    = PRIO_COLOR.get(entry["priority"], "#f59e0b")

        # Build popup HTML
        img_html = ""
        if entry.get("image_b64"):
            img_html = f'<img src="data:image/jpeg;base64,{entry["image_b64"]}" style="width:100%;border-radius:3px;margin-top:8px;border:1px solid #333;"/>'

        popup_html = f"""
        <div style="
          min-width:220px; max-width:260px;
          background:#161b22; color:#c9d1d9;
          font-family:'Courier New',monospace; font-size:12px;
          padding:14px; border-radius:4px;
          border:1px solid #21293a;
        ">
          <div style="font-size:9px;letter-spacing:3px;color:{tc};margin-bottom:4px;">{entry['intel_type']}</div>
          <div style="font-size:10px;letter-spacing:2px;color:#4a5568;margin-bottom:8px;">ID: #{entry['id']}</div>
          <div style="line-height:1.6;margin-bottom:8px;font-size:12px;">{entry['desc']}</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">
            <span style="background:{tc}22;color:{tc};border:1px solid {tc};padding:2px 7px;border-radius:2px;font-size:9px;letter-spacing:1px;">{entry['intel_type']}</span>
            <span style="background:{pc}22;color:{pc};border:1px solid {pc};padding:2px 7px;border-radius:2px;font-size:9px;letter-spacing:1px;">{entry['priority']}</span>
          </div>
          <div style="color:#4a5568;font-size:10px;">SRC: {entry.get('source','—')}</div>
          <div style="color:#4a5568;font-size:10px;margin-top:2px;">⏱ {entry['timestamp']}</div>
          <div style="color:#4a5568;font-size:10px;margin-top:2px;">📍 {entry['lat']:.4f}, {entry['lon']:.4f}</div>
          {img_html}
        </div>
        """

        tooltip_html = f"<b style='font-family:monospace;color:{tc}'>{entry['intel_type']}</b> · {entry['desc'][:40]}..."

        folium.Marker(
            location=[entry["lat"], entry["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=tooltip_html,
            icon=folium.Icon(color=color, icon=icon, prefix="glyphicon")
        ).add_to(m)

    return m


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family:"Barlow Condensed",sans-serif;font-size:26px;font-weight:900;letter-spacing:8px;color:#00e5a0;margin-bottom:2px;'>⬡ FUSION</div>
    <div style='font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:3px;color:#4a5568;margin-bottom:20px;'>INTELLIGENCE PLATFORM v1.0</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── MANUAL ENTRY ──
    st.markdown("<div class='sec-header'>// LOG NEW INTEL</div>", unsafe_allow_html=True)

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("LAT", value=28.6139, format="%.4f", step=0.0001)
    with col_lon:
        lon = st.number_input("LON", value=77.2090, format="%.4f", step=0.0001)

    desc     = st.text_area("DESCRIPTION", placeholder="What did you observe?", height=80)
    itype    = st.selectbox("INTEL TYPE", ["OSINT", "HUMINT", "IMINT"])
    source   = st.text_input("SOURCE", placeholder="Agent / Platform / Feed")
    priority = st.selectbox("PRIORITY", ["LOW", "MED", "HIGH", "CRITICAL"])

    img_file = st.file_uploader("ATTACH IMINT IMAGE (JPG/JPEG/PNG)", type=["jpg","jpeg","png"])

    if st.button("▶  TRANSMIT INTEL", use_container_width=True):
        if not desc.strip():
            st.error("DESCRIPTION REQUIRED")
        else:
            img_b64 = None
            img_name = None
            if img_file:
                img_b64  = img_to_b64(img_file.read())
                img_name = img_file.name

            entry = {
                "id": make_uid(),
                "lat": lat, "lon": lon,
                "desc": desc.strip(),
                "intel_type": itype,
                "source": source or "Manual Entry",
                "priority": priority,
                "timestamp": now_ts(),
                "image_b64": img_b64,
                "image_name": img_name
            }
            st.session_state.entries.append(entry)
            st.success(f"✓ LOGGED  —  ID: {entry['id']}")
            st.rerun()

    st.markdown("---")

    # ── BULK INGEST ──
    st.markdown("<div class='sec-header'>// BULK INGEST</div>", unsafe_allow_html=True)

    with st.expander("UPLOAD CSV / JSON / EXCEL"):
        bulk_file = st.file_uploader("DROP FILE", type=["csv","json","xlsx","xls"], key="bulk")
        if bulk_file:
            try:
                ext = bulk_file.name.split(".")[-1].lower()
                if ext == "csv":
                    df = pd.read_csv(bulk_file)
                elif ext == "json":
                    df = pd.read_json(bulk_file)
                elif ext in ["xlsx","xls"]:
                    df = pd.read_excel(bulk_file)

                required = {"lat","lon","desc"}
                if not required.issubset(set(df.columns.str.lower())):
                    st.error(f"FILE MUST HAVE: lat, lon, desc  columns")
                else:
                    df.columns = df.columns.str.lower()
                    count = 0
                    for _, row in df.iterrows():
                        e = {
                            "id": make_uid(),
                            "lat": float(row.get("lat", 0)),
                            "lon": float(row.get("lon", 0)),
                            "desc": str(row.get("desc","—")),
                            "intel_type": str(row.get("intel_type", row.get("type","OSINT"))).upper(),
                            "source": str(row.get("source","Bulk Import")),
                            "priority": str(row.get("priority","MED")).upper(),
                            "timestamp": str(row.get("timestamp", now_ts())),
                            "image_b64": None, "image_name": None
                        }
                        st.session_state.entries.append(e)
                        count += 1
                    st.success(f"✓ {count} ENTRIES INGESTED")
                    st.rerun()
            except Exception as ex:
                st.error(f"PARSE ERROR: {ex}")

    st.markdown("---")

    # ── FILTER ──
    st.markdown("<div class='sec-header'>// FILTER</div>", unsafe_allow_html=True)
    filter_type = st.radio("TYPE", ["ALL","OSINT","HUMINT","IMINT"], horizontal=True)

    st.markdown("---")

    # ── CLEAR ──
    if st.button("✕  CLEAR ALL ENTRIES", use_container_width=True):
        st.session_state.entries = []
        st.rerun()

    st.markdown("""
    <div style='margin-top:20px;font-family:"Share Tech Mono",monospace;font-size:8px;letter-spacing:2px;color:#21293a;text-align:center;'>
    CYBERJOAR · PS-01 · 2025
    </div>""", unsafe_allow_html=True)


# ─── MAIN PANEL ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="fusion-header">
  <div class="fusion-title">FUSION</div>
  <div class="fusion-subtitle">MULTI-SOURCE INTELLIGENCE FUSION DASHBOARD  ·  CYBERJOAR AI OC.41335.2026</div>
  <div class="status-pill">● SYSTEM ONLINE  ·  {now_ts()} UTC+5:30</div>
</div>
""", unsafe_allow_html=True)

entries = st.session_state.entries

# ── STATS ROW ──
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("TOTAL ENTRIES",   len(entries))
with c2: st.metric("OSINT",  len([e for e in entries if e["intel_type"]=="OSINT"]))
with c3: st.metric("HUMINT", len([e for e in entries if e["intel_type"]=="HUMINT"]))
with c4: st.metric("IMINT",  len([e for e in entries if e["intel_type"]=="IMINT"]))
with c5: st.metric("CRITICAL", len([e for e in entries if e["priority"]=="CRITICAL"]))

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──
tab_map, tab_feed, tab_export = st.tabs(["🗺  MAP VIEW", "📋  INTEL FEED", "📤  EXPORT"])

with tab_map:
    st.markdown("<div class='sec-header'>// GEOSPATIAL INTELLIGENCE OVERLAY</div>", unsafe_allow_html=True)

    if not entries:
        st.info("NO ENTRIES LOGGED — use the sidebar to add intel or upload a file.")
    else:
        m = build_map(entries, filter_type)
        result = st_folium(m, width="100%", height=560, returned_objects=["last_object_clicked"])

    # Legend
    st.markdown("""
    <div style='display:flex;gap:20px;margin-top:12px;font-family:"Share Tech Mono",monospace;font-size:10px;'>
      <span style='color:#00e5a0'>● OSINT — Open Source</span>
      <span style='color:#38bdf8'>● HUMINT — Human Intel</span>
      <span style='color:#f59e0b'>● IMINT — Imagery Intel</span>
      <span style='color:#ef4444'>● CRITICAL PRIORITY</span>
    </div>
    <div style='margin-top:6px;font-family:"Share Tech Mono",monospace;font-size:9px;color:#4a5568;'>
      💡 HOVER over markers for quick preview  ·  CLICK for full intel popup with imagery
    </div>
    """, unsafe_allow_html=True)

with tab_feed:
    st.markdown("<div class='sec-header'>// LIVE INTEL FEED</div>", unsafe_allow_html=True)

    if not entries:
        st.info("NO ENTRIES IN SYSTEM")
    else:
        # Search
        search = st.text_input("🔍 SEARCH", placeholder="Filter by description, source, type...", label_visibility="collapsed")
        filtered_entries = [
            e for e in reversed(entries)
            if search.lower() in e["desc"].lower()
            or search.lower() in e.get("source","").lower()
            or search.lower() in e["intel_type"].lower()
        ] if search else list(reversed(entries))

        st.markdown(f"<div style='font-family:\"Share Tech Mono\",monospace;font-size:9px;color:#4a5568;margin-bottom:10px;'>{len(filtered_entries)} ENTRIES DISPLAYED</div>", unsafe_allow_html=True)

        for e in filtered_entries:
            tc  = TYPE_COLOR.get(e["intel_type"],"#00e5a0")
            pc  = PRIO_COLOR.get(e["priority"],"#f59e0b")
            img_badge = " 🖼" if e.get("image_b64") else ""

            with st.expander(f"#{e['id']}  ·  {e['intel_type']}  ·  {e['desc'][:55]}...{img_badge}  [{e['priority']}]"):
                col_a, col_b = st.columns([2,1])
                with col_a:
                    st.markdown(f"""
                    <div style='font-family:"Share Tech Mono",monospace;font-size:12px;line-height:2;'>
                      <div><span style='color:#4a5568'>TYPE &nbsp;&nbsp;→</span> <span style='color:{tc}'>{e['intel_type']}</span></div>
                      <div><span style='color:#4a5568'>PRIO &nbsp;&nbsp;→</span> <span style='color:{pc}'>{e['priority']}</span></div>
                      <div><span style='color:#4a5568'>SOURCE →</span> {e.get('source','—')}</div>
                      <div><span style='color:#4a5568'>TIME &nbsp;&nbsp;→</span> {e['timestamp']}</div>
                      <div><span style='color:#4a5568'>COORDS →</span> {e['lat']:.4f}, {e['lon']:.4f}</div>
                    </div>
                    <div style='margin-top:10px;padding:10px;background:#0d1117;border:1px solid #21293a;border-radius:3px;font-size:12px;line-height:1.7;'>
                      {e['desc']}
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    if e.get("image_b64"):
                        st.image(
                            f"data:image/jpeg;base64,{e['image_b64']}",
                            caption=f"IMINT: {e.get('image_name','')}",
                            use_container_width=True
                        )
                    else:
                        st.markdown("""
                        <div style='height:100px;border:1px dashed #21293a;border-radius:3px;display:flex;align-items:center;justify-content:center;font-family:"Share Tech Mono",monospace;font-size:9px;letter-spacing:2px;color:#4a5568;'>
                          NO IMAGE
                        </div>""", unsafe_allow_html=True)

with tab_export:
    st.markdown("<div class='sec-header'>// EXPORT FUSED INTELLIGENCE</div>", unsafe_allow_html=True)

    if not entries:
        st.info("NO DATA TO EXPORT")
    else:
        export_df = pd.DataFrame([
            {
                "ID": e["id"],
                "Timestamp": e["timestamp"],
                "Intel Type": e["intel_type"],
                "Priority": e["priority"],
                "Latitude": e["lat"],
                "Longitude": e["lon"],
                "Description": e["desc"],
                "Source": e.get("source",""),
                "Has Image": "YES" if e.get("image_b64") else "NO"
            }
            for e in entries
        ])

        st.dataframe(export_df, use_container_width=True, height=320)

        col_csv, col_json = st.columns(2)
        with col_csv:
            csv_data = export_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇  DOWNLOAD CSV", csv_data, "fusion_intel_export.csv", "text/csv", use_container_width=True)
        with col_json:
            json_data = export_df.to_json(orient="records", indent=2).encode("utf-8")
            st.download_button("⬇  DOWNLOAD JSON", json_data, "fusion_intel_export.json", "application/json", use_container_width=True)
