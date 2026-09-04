"""
Examples showing what your teammates' modules need to send.

They can either:
A) import db.py directly if their script runs on the same Raspberry Pi, OR
B) publish the same data as JSON over MQTT if it runs on another local device.
"""

from db import (
    update_footfall, upsert_inventory, upsert_queue,
    upsert_trolley, add_heatmap_point, add_alert
)

# IR entry/exit logic output
update_footfall(401, 55)

# YOLO / shelf analysis output
upsert_inventory("Coke 500 ml", "A1", 18)

# IR queue sensors or camera queue output
upsert_queue("Counter 2", 7, 4.6)

# QR/RFID scan-and-go trolley output
upsert_trolley("T01", 9, 720, "Counter 3")

# YOLO + ByteTrack + OpenCV movement coordinate
add_heatmap_point(0.46, 0.39, "Snacks")

# SSIM / planogram anomaly
add_alert(
    "warning",
    "planogram",
    "Shelf B1",
    "Product placement differs from reference planogram"
)

print("Example data written to local database.")
