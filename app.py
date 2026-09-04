import streamlit as st
import pandas as pd
import plotly.express as px
import cv2

from db import connect, seed_demo

st.set_page_config(
    page_title="RetailEdge",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

seed_demo()


# ---------------------------------------------------------
# BASIC STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.25);
        padding: 12px;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATABASE READER
# ---------------------------------------------------------

def read(query):
    with connect() as con:
        return pd.read_sql_query(query, con)


def status_icon(status):

    icons = {
        "CRITICAL": "🔴",
        "LOW": "🟡",
        "HEALTHY": "🟢",
        "CONGESTED": "🔴",
        "BUSY": "🟡",
        "NORMAL": "🟢",
    }

    return icons.get(status, "⚪")


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.title("🛒 RetailEdge")
st.sidebar.caption("Smart Retail Intelligence")

role = st.sidebar.radio(
    "Access Level",
    ["Manager", "Staff"],
)

page_options = [
    "🏠 Overview",
    "📦 Inventory",
    "🧍 Queues",
    "🚨 Alerts",
]

if role == "Manager":

    page_options += [
        "👥 Shopper Analytics",
        "🗺 Store Map",
        "🛒 Scan & Go",
        "📹 Camera Feeds",
    ]


page = st.sidebar.radio(
    "Page",
    page_options,
)


st.sidebar.divider()

st.sidebar.caption("Local edge dashboard")
st.sidebar.caption("Database: SQLite")
st.sidebar.caption("Cloud dependency: None")
st.sidebar.caption("Auto-refresh: 2 seconds")


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🛒 RetailEdge — Store Operations")

st.caption(
    f"{role} view • Local / on-premise"
)


# =========================================================
# OVERVIEW
# =========================================================

@st.fragment(run_every="2s")
def overview():

    metrics = read(
        "SELECT * FROM metrics WHERE id=1"
    )

    inv = read(
        "SELECT * FROM inventory ORDER BY stock_percent ASC"
    )

    queues = read(
        "SELECT * FROM queues ORDER BY people DESC"
    )

    alerts = read(
        "SELECT * FROM alerts ORDER BY id DESC LIMIT 50"
    )

    # Remove duplicate alerts
    if not alerts.empty:

        alerts = (
            alerts
            .drop_duplicates(
                subset=["category", "location"],
                keep="first"
            )
            .head(4)
        )

    pred = read(
        "SELECT * FROM predictions WHERE id=1"
    )


    # -----------------------------------------------------
    # KPI VALUES
    # -----------------------------------------------------

    footfall = (
        int(metrics.iloc[0]["footfall"])
        if not metrics.empty
        else 0
    )

    inside = (
        int(metrics.iloc[0]["customers_inside"])
        if not metrics.empty
        else 0
    )

    low = (
        int((inv["stock_percent"] <= 40).sum())
        if not inv.empty
        else 0
    )

    qmax = (
        int(queues["people"].max())
        if not queues.empty
        else 0
    )


    # -----------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "👥 Today's Footfall",
        footfall
    )

    c2.metric(
        "🏪 Customers Inside",
        inside
    )

    c3.metric(
        "📦 Low-stock Shelves",
        low
    )

    c4.metric(
        "🧍 Largest Queue",
        qmax
    )


    st.divider()


    # -----------------------------------------------------
    # ALERTS + FORECAST
    # -----------------------------------------------------

    left, right = st.columns([1.1, 1])


    # PRIORITY ALERTS
    with left:

        st.subheader("🚨 Priority Alerts")

        if alerts.empty:

            st.success(
                "No active alerts"
            )

        else:

            for _, a in alerts.iterrows():

                title = (
                    a["location"]
                    if a["location"]
                    else a["category"]
                )

                message = (
                    f"**{title}**\n\n"
                    f"{a['message']}"
                )

                if a["severity"] == "critical":

                    st.error(message)

                elif a["severity"] == "warning":

                    st.warning(message)

                else:

                    st.info(message)


    # CROWD FORECAST
    with right:

        st.subheader("📈 Crowd Forecast")

        if not pred.empty:

            p = pred.iloc[0]

            st.metric(
                "Predicted Peak Time",
                p["peak_window"]
            )

            c1, c2 = st.columns(2)

            c1.metric(
                "Expected Footfall",
                int(p["expected_footfall"])
            )

            c2.metric(
                "Crowd Level",
                p["crowd_level"]
            )


        st.subheader(
            "🧾 Queue Recommendation"
        )

        if not queues.empty:

            worst = queues.iloc[0]

            people = int(
                worst["people"]
            )

            if people >= 6:

                st.error(
                    f"**{worst['counter']}** has "
                    f"{people} people.\n\n"
                    "Recommended action: "
                    "Open or redirect customers "
                    "to another counter."
                )

            elif people >= 4:

                st.warning(
                    f"{worst['counter']} "
                    "is getting busy."
                )

            else:

                st.success(
                    "All checkout queues "
                    "are currently manageable."
                )


    # -----------------------------------------------------
    # LIVE STORE STATUS
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "⚡ Live Store Status"
    )

    inventory_col, queue_col = st.columns(2)


    # INVENTORY STATUS
    with inventory_col:

        st.markdown(
            "### 📦 Inventory"
        )

        if inv.empty:

            st.info(
                "No inventory data"
            )

        else:

            for _, item in inv.head(4).iterrows():

                stock = float(
                    item["stock_percent"]
                )

                if stock <= 20:

                    icon = "🔴"

                elif stock <= 40:

                    icon = "🟡"

                else:

                    icon = "🟢"

                st.write(
                    f"{icon} "
                    f"**{item['product']}** "
                    f"— {stock:.0f}%"
                )


    # QUEUE STATUS
    with queue_col:

        st.markdown(
            "### 🧍 Checkout Queues"
        )

        if queues.empty:

            st.info(
                "No queue data"
            )

        else:

            for _, q in queues.iterrows():

                people = int(
                    q["people"]
                )

                if people >= 6:

                    icon = "🔴"

                elif people >= 4:

                    icon = "🟡"

                else:

                    icon = "🟢"

                st.write(
                    f"{icon} "
                    f"**{q['counter']}** "
                    f"— {people} people"
                )


# =========================================================
# INVENTORY
# =========================================================

@st.fragment(run_every="2s")
def inventory_page():

    inv = read(
        "SELECT * FROM inventory "
        "ORDER BY stock_percent ASC"
    )

    st.subheader(
        "📦 Shelf Inventory Monitoring"
    )

    st.caption(
        "Real-time shelf availability "
        "and replenishment recommendations"
    )


    if inv.empty:

        st.info(
            "No inventory data available."
        )

        return


    for _, r in inv.iterrows():

        icon = status_icon(
            r["status"]
        )

        a, b, c = st.columns(
            [3, 1, 1]
        )

        a.write(
            f"**{icon} {r['product']}**"
        )

        b.write(
            f"Shelf **{r['shelf']}**"
        )

        c.write(
            f"**{r['stock_percent']:.0f}%**"
        )

        stock = int(
            max(
                0,
                min(
                    100,
                    r["stock_percent"]
                )
            )
        )

        st.progress(stock)


        if r["status"] == "CRITICAL":

            st.error(
                f"Refill {r['product']} "
                f"on Shelf {r['shelf']} now"
            )

        elif r["status"] == "LOW":

            st.warning(
                f"{r['product']} "
                "is running low"
            )


# =========================================================
# QUEUES
# =========================================================

@st.fragment(run_every="2s")
def queue_page():

    q = read(
        "SELECT * FROM queues "
        "ORDER BY counter"
    )

    st.subheader(
        "🧍 Checkout Queue Intelligence"
    )

    st.caption(
        "Live queue status, estimated "
        "waiting time and counter recommendations"
    )


    if q.empty:

        st.info(
            "No queue data available."
        )

        return


    for _, r in q.iterrows():

        icon = status_icon(
            r["status"]
        )

        a, b, c, d = st.columns(
            [2, 1, 1, 2]
        )

        a.write(
            f"**{icon} {r['counter']}**"
        )

        b.metric(
            "People",
            int(r["people"])
        )

        c.metric(
            "Est. wait",
            f"{r['wait_min']:.1f} min"
        )


        if r["status"] == "CONGESTED":

            d.error(
                "Open / redirect "
                "to another counter"
            )

        elif r["status"] == "BUSY":

            d.warning(
                "Monitor closely"
            )

        else:

            d.success(
                "Normal"
            )


# =========================================================
# ALERTS
# =========================================================

@st.fragment(run_every="2s")
def alerts_page():

    a = read(
        "SELECT * FROM alerts "
        "ORDER BY id DESC LIMIT 100"
    )


    st.subheader(
        "🚨 Operational Alerts"
    )

    st.caption(
        "Latest queue, shelf and "
        "store-operation notifications"
    )


    if a.empty:

        st.success(
            "No alerts"
        )

        return


    # STAFF ONLY SEES OPERATIONAL ALERTS
    if role == "Staff":

        a = a[
            a["category"].isin(
                [
                    "inventory",
                    "queue",
                    "planogram"
                ]
            )
        ]


    # REMOVE DUPLICATES
    a = a.drop_duplicates(
        subset=[
            "category",
            "location",
            "message"
        ],
        keep="first"
    )


    st.dataframe(
        a[
            [
                "created_at",
                "severity",
                "category",
                "location",
                "message"
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# SHOPPER ANALYTICS
# =========================================================

@st.fragment(run_every="3s")
def shopper_page():

    heat = read(
        """
        SELECT x, y, zone
        FROM heatmap_points
        ORDER BY id DESC
        LIMIT 1000
        """
    )

    hist = read(
        """
        SELECT time_label, count
        FROM footfall_history
        ORDER BY id
        """
    )


    st.subheader(
        "👥 Shopper Analytics"
    )

    st.caption(
        "Anonymous movement analytics "
        "generated through local processing"
    )


    left, right = st.columns(2)


    # FOOTFALL GRAPH
    with left:

        st.markdown(
            "### 📈 Footfall Trend"
        )

        if not hist.empty:

            st.line_chart(
                hist.set_index(
                    "time_label"
                )["count"]
            )

        else:

            st.info(
                "Waiting for footfall data."
            )


    # HEATMAP
    with right:

        st.markdown(
            "### 🔥 Store Heatmap"
        )

        if len(heat) >= 2:

            fig = px.density_heatmap(
                heat,
                x="x",
                y="y",
                nbinsx=20,
                nbinsy=20,
                hover_data=["zone"]
            )

            fig.update_layout(
                height=360,
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Waiting for shopper "
                "movement data."
            )


# =========================================================
# SCAN & GO
# =========================================================

@st.fragment(run_every="2s")
def scan_go_page():

    t = read(
        """
        SELECT *
        FROM trolleys
        ORDER BY trolley_id
        """
    )

    q = read(
        """
        SELECT *
        FROM queues
        ORDER BY wait_min ASC
        """
    )


    st.subheader(
        "🛒 Scan & Go Billing"
    )

    st.caption(
        "Cart status, bill value "
        "and recommended checkout counter"
    )


    if t.empty:

        st.info(
            "No active carts."
        )

        return


    best_counter = (
        q.iloc[0]["counter"]
        if not q.empty
        else "N/A"
    )


    for _, r in t.iterrows():

        a, b, c, d = st.columns(
            [1.2, 1, 1.2, 2]
        )

        a.write(
            f"**{r['trolley_id']}**"
        )

        b.metric(
            "Items",
            int(r["items"])
        )

        c.metric(
            "Total",
            f"₹{r['total']:.0f}"
        )


        recommendation = (
            r["recommendation"]
            or best_counter
        )


        d.success(
            f"Recommended: "
            f"{recommendation}"
        )


# =========================================================
# STORE MAP
# =========================================================

def store_map_page():

    st.subheader(
        "🗺️ Store Anomaly Map"
    )

    st.caption(
        "Location of important store "
        "zones and operational anomalies"
    )


    zones = pd.DataFrame(
        [
            {
                "zone": "Entrance",
                "x": 10,
                "y": 50
            },
            {
                "zone": "Shelf A",
                "x": 35,
                "y": 75
            },
            {
                "zone": "Shelf B",
                "x": 60,
                "y": 75
            },
            {
                "zone": "Snacks",
                "x": 45,
                "y": 40
            },
            {
                "zone": "Checkout",
                "x": 80,
                "y": 20
            },
        ]
    )


    alerts = read(
        """
        SELECT
            location,
            category,
            severity,
            message
        FROM alerts
        ORDER BY id DESC
        LIMIT 10
        """
    )


    fig = px.scatter(
        zones,
        x="x",
        y="y",
        text="zone",
        range_x=[0, 100],
        range_y=[0, 100],
        title="Store Layout"
    )


    fig.update_traces(
        marker_size=22,
        textposition="top center"
    )


    fig.update_layout(
        height=520
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.markdown(
        "### 🚨 Current Anomaly Locations"
    )


    if alerts.empty:

        st.success(
            "No anomalies detected."
        )

    else:

        st.dataframe(
            alerts,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# CAMERA FEEDS
# =========================================================

@st.cache_resource
def get_capture(source):

    src = (
        int(source)
        if str(source).isdigit()
        else source
    )

    return cv2.VideoCapture(src)


def camera_page():

    st.subheader(
        "📹 Camera Feeds"
    )

    st.caption(
        "Manager-only local camera access"
    )


    source = st.text_input(
        "Camera Source",
        value="0",
        help=(
            "Use 0 for laptop/USB webcam "
            "or enter an RTSP URL."
        )
    )


    enabled = st.toggle(
        "Enable Camera Preview",
        value=False
    )


    @st.fragment(run_every="0.5s")
    def camera_preview():

        if not enabled:

            st.info(
                "Enable preview "
                "to view camera."
            )

            return


        cap = get_capture(
            source
        )


        ok, frame = cap.read()


        if not ok:

            st.error(
                "Could not read camera. "
                "Check camera index or RTSP URL."
            )

            return


        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        st.image(
            frame,
            channels="RGB",
            use_container_width=True
        )


    camera_preview()


# =========================================================
# PAGE ROUTING
# =========================================================

if "Overview" in page:

    overview()


elif "Inventory" in page:

    inventory_page()


elif "Queues" in page:

    queue_page()


elif "Alerts" in page:

    alerts_page()


elif "Shopper Analytics" in page:

    shopper_page()


elif "Store Map" in page:

    store_map_page()


elif "Scan & Go" in page:

    scan_go_page()


elif "Camera Feeds" in page:

    camera_page()