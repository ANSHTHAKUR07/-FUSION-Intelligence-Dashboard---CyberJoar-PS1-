# FUSION — Multi-Source Intelligence Fusion Dashboard
### CyberJoar AI OC.41335.2026 · Problem Statement 1

---

## What This Does

A centralized web-based dashboard that ingests and visualizes **OSINT**, **HUMINT**, and **IMINT** data on a unified geospatial map. Built with Streamlit for rapid deployment.

---

## Features

| Feature | Implementation |
|---|---|
| Multi-source ingestion | Manual form + CSV/JSON/Excel bulk upload |
| Interactive map | Folium + CartoDB Dark terrain tiles |
| Hover tooltips | Quick intel preview on cursor hover |
| Click popups | Full metadata + embedded IMINT imagery |
| Color-coded markers | Green=OSINT, Blue=HUMINT, Orange=IMINT |
| Priority indicators | Icon changes by LOW/MED/HIGH/CRITICAL |
| Layer switching | Dark terrain + Satellite toggle |
| Export | CSV + JSON download |
| Live feed | Searchable intel feed with image preview |

---

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy to Streamlit Community Cloud (Free)

1. Push this folder to a **GitHub repository** (public or private)
2. Go to → https://share.streamlit.io
3. Click **"New app"**
4. Select your repo, branch `main`, file `app.py`
5. Click **Deploy** — live link in ~2 minutes

**That's your shareable link for the email.**

---

## Logic Notes (for email to Sashrik@cyberjoar.com)

Include these points in your email:

> **Ingestion Layer**: The system supports three parallel ingestion channels. OSINT/HUMINT data arrives via manual form entry or bulk CSV/JSON/Excel upload. IMINT imagery (JPG/JPEG) is accepted as binary file upload, immediately base64-encoded and stored in session state alongside its geospatial coordinates — eliminating the need for a separate image server.

> **Fusion Logic**: All ingested records — regardless of source type — are normalized into a unified Python dictionary schema with fields: `id, lat, lon, desc, intel_type, source, priority, timestamp, image_b64`. This acts as the in-memory fusion layer that feeds the map renderer and intel feed simultaneously.

> **Geospatial Visualization**: Folium renders an interactive Leaflet map with CartoDB Dark Matter tiles (terrain-accurate). Each entry becomes a positioned marker with `intel_type`-coded color and `priority`-coded icon. Hover tooltips provide instant context without clicking; click events open full popup windows displaying all metadata and embedded IMINT imagery.

> **Scalability Path**: Session state can be replaced with MongoDB Atlas (pymongo) for persistent OSINT storage and AWS S3 (boto3) for IMINT imagery, matching the production architecture described in the problem statement — the fusion schema remains unchanged.

---

## Folder Structure

```
fusion-streamlit/
├── app.py              ← Main Streamlit application
├── requirements.txt    ← Python dependencies
├── sample_data.csv     ← Test data for bulk ingest demo
└── README.md
```
