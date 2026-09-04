import random
import time
from db import (
    seed_demo, connect, now, upsert_inventory, upsert_queue,
    upsert_trolley, update_footfall, add_heatmap_point, add_alert
)

seed_demo()

footfall = 327
inside = 42
stocks = {
    "Coke 500 ml": ["A1", 20],
    "Lays Classic": ["A2", 72],
    "Maggi": ["B1", 38],
    "Pepsi 500 ml": ["B2", 86],
}
last_stock_alert = {}
last_queue_alert = {}

print("Simulator running. Keep this terminal open. Ctrl+C to stop.")

while True:
    # Footfall
    if random.random() < 0.45:
        footfall += 1
        inside += random.choice([0, 1])
    if random.random() < 0.25 and inside > 0:
        inside -= 1
    update_footfall(footfall, inside)

    # Inventory drift
    product = random.choice(list(stocks.keys()))
    shelf, stock = stocks[product]
    stock += random.choice([-3, -2, -1, 0, 1])
    stock = max(0, min(100, stock))
    stocks[product][1] = stock
    upsert_inventory(product, shelf, stock)

    if stock <= 20 and last_stock_alert.get(product) != "critical":
        add_alert("critical", "inventory", f"Shelf {shelf}",
                  f"{product} at {stock}% — refill now")
        last_stock_alert[product] = "critical"
    elif stock > 25:
        last_stock_alert[product] = "ok"

    # Queues
    for counter in ["Counter 1", "Counter 2", "Counter 3"]:
        people = random.randint(1, 8)
        wait = round(people * random.uniform(0.45, 0.8), 1)
        upsert_queue(counter, people, wait)
        if people >= 6 and last_queue_alert.get(counter) != "high":
            add_alert("warning", "queue", counter,
                      f"{people} people detected — open/redirect to another counter")
            last_queue_alert[counter] = "high"
        elif people < 5:
            last_queue_alert[counter] = "ok"

    # Trolleys
    upsert_trolley("T01", random.randint(3, 15), random.randrange(150, 1200, 10),
                   random.choice(["Counter 1","Counter 2","Counter 3"]))
    upsert_trolley("T02", random.randint(2, 20), random.randrange(100, 1600, 10),
                   random.choice(["Counter 1","Counter 2","Counter 3"]))

    # Heatmap points
    center = random.choice([(0.18,0.22,"Entrance"), (0.50,0.42,"Snacks"), (0.79,0.75,"Checkout")])
    x = max(0, min(1, random.gauss(center[0], 0.05)))
    y = max(0, min(1, random.gauss(center[1], 0.05)))
    add_heatmap_point(x, y, center[2])

    # Keep heatmap table small
    with connect() as con:
        con.execute("""
            DELETE FROM heatmap_points
            WHERE id NOT IN (
                SELECT id FROM heatmap_points ORDER BY id DESC LIMIT 1000
            )
        """)

    time.sleep(2)
