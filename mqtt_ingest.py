"""
OPTIONAL hardware-integration bridge.

Run a local Mosquitto broker on the Raspberry Pi, then:
    python mqtt_ingest.py

Expected topics / JSON payloads:

store/footfall
{"footfall": 329, "customers_inside": 44}

store/inventory
{"product":"Coke 500 ml","shelf":"A1","stock_percent":18}

store/queue
{"counter":"Counter 2","people":7,"wait_min":4.4}

store/trolley
{"trolley_id":"T01","items":8,"total":620,"recommendation":"Counter 3"}

store/heatmap
{"x":0.52,"y":0.41,"zone":"Snacks"}

store/alert
{"severity":"warning","category":"planogram","location":"Shelf B1",
 "message":"Possible product misalignment detected"}
"""

import json
import paho.mqtt.client as mqtt
from db import (
    seed_demo, update_footfall, upsert_inventory, upsert_queue,
    upsert_trolley, add_heatmap_point, add_alert
)

BROKER = "127.0.0.1"
PORT = 1883

seed_demo()

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected:", reason_code)
    client.subscribe("store/#")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        topic = msg.topic

        if topic == "store/footfall":
            update_footfall(data["footfall"], data["customers_inside"])

        elif topic == "store/inventory":
            upsert_inventory(data["product"], data["shelf"], data["stock_percent"])

        elif topic == "store/queue":
            upsert_queue(data["counter"], data["people"], data.get("wait_min"))

        elif topic == "store/trolley":
            upsert_trolley(
                data["trolley_id"], data["items"], data["total"],
                data.get("recommendation", "")
            )

        elif topic == "store/heatmap":
            add_heatmap_point(data["x"], data["y"], data.get("zone", ""))

        elif topic == "store/alert":
            add_alert(
                data.get("severity", "warning"),
                data.get("category", "general"),
                data.get("location", ""),
                data["message"],
            )

        print(topic, data)

    except Exception as e:
        print("Bad MQTT message:", msg.topic, e)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
print("MQTT bridge running on", f"{BROKER}:{PORT}")
client.loop_forever()
