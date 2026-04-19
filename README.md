# -FUSION-Intelligence-Dashboard---CyberJoar-PS1-
a intellegence system


Hey guys just made a proj named FUSION-Intelligence-Dashboard

Logic & Architecture:
The core challenge in PS-1 is fragmentation — OSINT, HUMINT, IMINT, and SIGINT arriving from different sources with no common interface. My solution addresses this with a unified ingestion and fusion layer.
All incoming data — whether typed manually, uploaded as CSV/JSON/Excel, or attached as imagery — is normalised into a single schema: {id, lat, lon, desc, intel_type, source, priority, timestamp, image_b64, confidence}. This schema is the fusion layer. Every downstream component — the map, the feed, the export — reads from this one unified structure regardless of where the data came from.
I built a Confidence Scoring Engine that auto-calculates a 0–99 reliability score per entry based on field completeness (description length, source provided, coordinates present), intel type (IMINT and SIGINT score higher due to technical collection overhead), and priority. This gives analysts an immediate sense of data quality without reading every entry.
A Threat Level Engine reads the full entry set in real time and outputs NOMINAL / ELEVATED / HIGH / CRITICAL based on the distribution of priority flags — this aggregated situational awareness is displayed in the dashboard header and updates the moment a new entry is logged.
The map uses Folium with CartoDB Dark terrain tiles. Hover over any marker triggers an instant tooltip popup (satisfying the PS-1 'hover-activated pop-up' requirement) showing type, description, priority, confidence, and timestamp. A full click popup adds the source, coordinates, and any attached IMINT imagery rendered inline.
MongoDB Atlas and AWS S3 connector stubs are built into the sidebar Data Sources panel and are ready to be wired with credentials — the fusion schema requires no changes to support live cloud ingestion.


made this proj using vibcoding ... hope u all will this my prj out and enjoy and learn like me 


proj live link - https://anshthakurintelligencedashboard.streamlit.app/


Thnkyou 
if someone is looking at this please i wana get job please give me one as ml /ai eng ......  😃, 😊, 😄
