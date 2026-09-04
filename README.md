# SIH RetailEdge Dashboard

A local Streamlit dashboard for the SIH retail analytics prototype.

## Architecture

Sensors / CCTV / YOLO / ByteTrack / SSIM / QR-RFID
        |
        | local Wi-Fi / local Python
        v
Raspberry Pi 5
        |
        +-- SQLite database
        +-- optional Mosquitto MQTT broker
        +-- Streamlit dashboard
        |
Manager / Staff devices on same local Wi-Fi

No cloud is required.

## Quick start (Windows laptop)

1. Open terminal in this folder.
2. Create a virtual environment:

   py -m venv .venv

3. Activate it:

   .venv\Scripts\activate

4. Install packages:

   pip install -r requirements.txt

5. Terminal 1 — start fake live data:

   python simulator.py

6. Terminal 2 — start dashboard:

   streamlit run app.py

7. Open the local URL Streamlit prints, normally:

   http://localhost:8501

## On Raspberry Pi 5

Recommended: Raspberry Pi OS 64-bit.

    sudo apt update
    sudo apt install python3-venv python3-pip libgl1 -y

Then inside the project folder:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python simulator.py

In another terminal:

    source .venv/bin/activate
    streamlit run app.py --server.address 0.0.0.0

Other phones/tablets on the same local Wi-Fi can open:

    http://<RASPBERRY_PI_IP>:8501

Find the Pi IP with:

    hostname -I

## Connecting real hardware

### Same Raspberry Pi
If the hardware/AI script runs on the Pi, import functions from db.py.

Example:

    from db import upsert_queue
    upsert_queue("Counter 1", people=7, wait_min=4.5)

### Another local device
Use MQTT.

Install Mosquitto on the Pi:

    sudo apt install mosquitto mosquitto-clients -y
    sudo systemctl enable --now mosquitto

Then run:

    python mqtt_ingest.py

Publish JSON to topics:
- store/footfall
- store/inventory
- store/queue
- store/trolley
- store/heatmap
- store/alert

## Team output contract

Shopper analytics:
- footfall
- customers_inside
- heatmap x/y
- zone / dwell-time analytics

Inventory:
- product
- shelf
- stock_percent
- planogram anomaly alert

Queue:
- counter
- people
- wait_min

Scan-and-go:
- trolley_id
- items
- total
- recommended counter

The dashboard should not run YOLO itself. AI/sensor modules calculate values, then write/publish them to the local data layer.

## Important demo note

The Manager/Staff selector is a UI demonstration of access tiers, not production-grade authentication.
Use proper authentication and device/network access controls in a real deployment.
