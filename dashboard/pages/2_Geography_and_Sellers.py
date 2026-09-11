import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils import (
    load_data, render_filters, empty_state,
    ACCENT, ACCENT_WARN, NEUTRAL, SMALL_SAMPLE_THRESHOLD,
)

st.set_page_config(page_title="Geography & Sellers", layout="wide")

df = load_data()
filtered = render_filters(df)

st.title("Geography & Sellers")
st.markdown("Where delivery problems concentrate : which states, which routes, and which seller profiles.")

if len(filtered) == 0:
    empty_state()
    st.stop()

delivered = filtered[filtered["is_delivered"] == True].copy()

MIN_ROUTE_ORDERS = 10


# Same-state vs cross-state
st.subheader("Same state vs. cross state delivery")

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough delivered orders under current filters.")
else:
    geo_compare = delivered.groupby("same_state", observed=True).agg(
        avg_days=("delivery_days", "mean"), late_rate=("is_late", "mean"), n=("order_id", "count")
    )
    geo_compare.index = geo_compare.index.map({True: "Same state", False: "Cross state"})

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Bar(
            x=geo_compare.index, 
            y=geo_compare["avg_days"],
            marker_color=[ACCENT, NEUTRAL],
            text=[f"{v:.1f}d" for v in geo_compare["avg_days"]], 
            textposition="outside")
        )

        fig.update_layout(
            height=350, 
            margin=dict(t=30, b=30), 
            yaxis_title="Avg delivery days", 
            title="Delivery time"
        )

        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = go.Figure(go.Bar(
            x=geo_compare.index, 
            y=geo_compare["late_rate"] * 100,
            marker_color=[ACCENT, NEUTRAL],
            text=[f"{v:.1f}%" for v in geo_compare["late_rate"] * 100], 
            textposition="outside")
        )

        fig.update_layout(height=350, margin=dict(t=30, b=30), yaxis_title="Late rate (%)", title="Late rate")

        st.plotly_chart(fig, width="stretch")

st.divider()



# Route risk heatmap

st.subheader("Route risk: seller state to customer state")

routes = (delivered.dropna(subset=["seller_state", "customer_state"])
          .groupby(["seller_state", "customer_state"])
          .agg(n=("order_id", "count"), late_rate=("is_late", "mean"))
          .reset_index())
routes_confident = routes[routes["n"] >= MIN_ROUTE_ORDERS]

if len(routes_confident) == 0:
    empty_state(f"No routes with at least {MIN_ROUTE_ORDERS} orders under current filters.")
else:
    top_seller_states = delivered["seller_state"].value_counts().head(12).index
    top_customer_states = delivered["customer_state"].value_counts().head(12).index

    matrix_data = routes[routes["seller_state"].isin(top_seller_states) & routes["customer_state"].isin(top_customer_states)]

    matrix_data = matrix_data.copy()
    matrix_data.loc[matrix_data["n"] < MIN_ROUTE_ORDERS, "late_rate"] = np.nan

    pivot = matrix_data.pivot(index="seller_state", columns="customer_state", values="late_rate") * 100
    n_pivot = matrix_data.pivot(index="seller_state", columns="customer_state", values="n")

    pivot = pivot.reindex(index=top_seller_states, columns=top_customer_states)
    n_pivot = n_pivot.reindex(index=top_seller_states, columns=top_customer_states)

    hover_text = [[
        f"{seller_state} -> {customer_state}<br>Insufficient Data (n={0 if pd.isna(n_pivot.loc[seller_state, customer_state]) else int(n_pivot.loc[seller_state, customer_state])})"
        if pd.isna(pivot.loc[seller_state, customer_state])
        else f"{seller_state} -> {customer_state}<br>Late Rate: {pivot.loc[seller_state, customer_state]:.1f}%<br>n = {int(n_pivot.loc[seller_state, customer_state]):,}"
        for customer_state in pivot.columns
    ] for seller_state in pivot.index]

    fig = go.Figure(go.Heatmap(
        z=pivot.values, 
        x=pivot.columns, 
        y=pivot.index, 
        colorscale="Reds",
        zmin = 0,
        zmax = 40,
        # customdata=n_pivot.values,
        # hovertemplate="%{y} -> %{x}<br>Late rate: %{z:.1f}%<br>n=%{customdata}<extra></extra>",
        hoverinfo="text",
        text=hover_text,
        colorbar=dict(title="Late %"),
    ))
    fig.update_layout(
        height=500, 
        margin=dict(t=10, b=10),
        xaxis_title="Customer state (destination)", 
        yaxis_title="Seller state (origin)"
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(f"Restricted to the top 12 states by volume on each axis; blank cells have fewer than {MIN_ROUTE_ORDERS} orders.")

    st.markdown("**Worst individual routes (any state, minimum {} orders):**".format(MIN_ROUTE_ORDERS))

    worst = routes_confident.sort_values("late_rate", ascending=False).head(10).copy()

    worst["route"] = worst["seller_state"] + " -> " + worst["customer_state"]

    fig2 = go.Figure(go.Bar(
        x=worst["late_rate"] * 100, 
        y=worst["route"], 
        orientation="h", 
        marker_color=ACCENT_WARN,
        text=[f"{v:.0f}% (n={n})" for v, n in zip(worst["late_rate"] * 100, worst["n"])], 
        textposition="outside",
    ))

    fig2.update_layout(
        height=400, 
        margin=dict(t=10, b=10), 
        xaxis_title="Late rate (%)",
        yaxis=dict(autorange="reversed")
    )

    st.plotly_chart(fig2, width="stretch")

st.divider()



# Seller quadrant

st.subheader("Seller performance: speed vs. reliability")

seller_perf = (df.dropna(subset=["seller_id"])
               .drop_duplicates(subset=["seller_id"])
               .set_index("seller_id")[["seller_avg_delivery_days", "seller_pct_late", "seller_low_confidence"]])

sellers_in_filter = delivered["seller_id"].dropna().unique()

seller_n = delivered.dropna(subset=["seller_id"]).groupby("seller_id")["order_id"].count().rename("n")

seller_confident = seller_perf[
    (seller_perf["seller_low_confidence"] == False) & (seller_perf.index.isin(sellers_in_filter))
].copy()

seller_confident["n"] = seller_n

if len(seller_confident) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough sellers with 5+ orders under current filters for a meaningful quadrant view.")
else:
    fig = go.Figure(go.Scattergl(
        x=seller_confident["seller_avg_delivery_days"], y=seller_confident["seller_pct_late"] * 100,
        mode="markers",
        marker=dict(
            size=np.clip(seller_confident["n"] / 3, 4, 40), 
            color=ACCENT, opacity=0.5,
            line=dict(width=0.5, 
            color="white")
        ),
        customdata=np.stack([seller_confident.index, seller_confident["n"]], axis=-1),
        hovertemplate="Seller %{customdata[0]}<br>Avg delivery: %{x:.1f}d<br>Late rate: %{y:.1f}%<br>n=%{customdata[1]}<extra></extra>",
    ))

    fig.add_hline(
        y=seller_confident["seller_pct_late"].median() * 100, 
        line_dash="dash", 
        line_color=NEUTRAL
    )

    fig.add_vline(
        x=seller_confident["seller_avg_delivery_days"].median(), 
        line_dash="dash", 
        line_color=NEUTRAL
    )

    fig.update_layout(
        height=550, 
        margin=dict(t=10, b=10),
        xaxis_title="Average delivery time (days) or speed",
        yaxis_title="Late rate (%) or reliability"
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(
        f"{len(seller_confident):,} sellers with 5+ orders under current filters. "
        "Hover any point for the exact seller ID and numbers so unlike a static chart, "
        "you can identify a specific outlier here rather than just see the overall shape."
    )

st.divider()



# State map (interactive hover replaces the need for always-visible labels)

st.subheader("Order volume and late rate by customer state")

state_geo = (delivered.dropna(subset=["customer_lat", "customer_lng"])
             .groupby("customer_state")
             .agg(lat=("customer_lat", "mean"), lng=("customer_lng", "mean"),
                  n_orders=("order_id", "count"), late_rate=("is_late", "mean")))

if len(state_geo) == 0:
    empty_state("No geolocated orders under current filters.")
else:
    orders = state_geo["n_orders"]

    if len(orders) == 1 or orders.max() == orders.min():
        marker_sizes = np.full(len(orders), 35.0)
    else:
        scaled_sizes = (np.sqrt(orders) - np.sqrt(orders.min())) / (np.sqrt(orders.max()) - np.sqrt(orders.min()))
        marker_sizes = scaled_sizes * 45 + 8

    fig = go.Figure(go.Scatter(
        x=state_geo["lng"], 
        y=state_geo["lat"], 
        mode="markers+text",
        text=state_geo.index, 
        textposition="top center", 
        textfont=dict(size=9),
        marker=dict(
            size=marker_sizes,
            color=state_geo["late_rate"] * 100, colorscale="Reds", showscale=True,
            colorbar=dict(title="Late %"), line=dict(width=1, color="black"),
        ),
        customdata=np.stack([state_geo["n_orders"], state_geo["late_rate"] * 100], axis=-1),
        hovertemplate="<b>%{text}</b><br>Orders: %{customdata[0]:,}<br>Late rate: %{customdata[1]:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        height=650, 
        margin=dict(t=10, b=10), 
        xaxis_title="Longitude", 
        yaxis_title="Latitude"
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(
        "Real coordinates, not a choropleth "
        "which also solves the choropleth area bias problem directly. Hover for exact figures "
        "instead of needing every label visible at once."
    )

st.divider()




# Weekday processing pattern

st.subheader("Processing time by day of week")

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough delivered orders under current filters.")
else:
    weekday_processing = delivered.groupby("purchase_weekday", observed=True)["processing_days"].mean().reindex(WEEKDAY_ORDER)

    fig = go.Figure(go.Bar(
        x=weekday_processing.index, 
        y=weekday_processing.values, 
        marker_color=ACCENT,
        text=[f"{v:.1f}" for v in weekday_processing.values], 
        textposition="outside")
    )

    fig.update_layout(
        height=380, 
        margin=dict(t=10, b=10), 
        yaxis_title="Mean processing days"
    )

    st.plotly_chart(fig, width="stretch")

st.divider()




# Distance vs outcome

st.subheader("Distance vs. delivery outcome")

dist_data = delivered.dropna(subset=["distance_km"])
n_unique_dist = dist_data["distance_km"].nunique()

if len(dist_data) < SMALL_SAMPLE_THRESHOLD or n_unique_dist < 2:
    empty_state("Not enough distance tagged orders under current filters.")
else:
    n_bins = min(6, n_unique_dist)
    try:
        dist_data = dist_data.copy()
        dist_data["distance_bucket"] = pd.qcut(dist_data["distance_km"], q=n_bins, duplicates="drop")

        distance_outcome = dist_data.groupby("distance_bucket", observed=True)["is_late"].agg(late_rate="mean", n="count")

        labels = [f"{int(iv.left)}-{int(iv.right)}" for iv in distance_outcome.index]

        fig = go.Figure(go.Scatter(
            x=labels, 
            y=distance_outcome["late_rate"] * 100, 
            mode="lines+markers",
            line=dict(color=ACCENT_WARN, width=2),
            customdata=distance_outcome["n"],
            hovertemplate="%{x} km<br>Late rate: %{y:.1f}%<br>n=%{customdata}<extra></extra>",
        ))

        fig.update_layout(
            height=400, 
            margin=dict(t=10, b=10), 
            xaxis_title="Distance (km), equal sized bins",
            yaxis_title="Late rate (%)"
        )

        st.plotly_chart(fig, width="stretch")

    except ValueError:
        empty_state("Distance values under current filters are too uniform to bin meaningfully.")
