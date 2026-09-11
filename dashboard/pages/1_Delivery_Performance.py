import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import (
    load_data, render_filters, empty_state,
    ACCENT, ACCENT_WARN, ACCENT_LIGHT, NEUTRAL, SMALL_SAMPLE_THRESHOLD,
)

st.set_page_config(page_title="Delivery Performance", layout="wide")

df = load_data()
filtered = render_filters(df)

st.title("Delivery Performance")
st.markdown(
    "The central mechanism: delivery delay predicts satisfaction, transport time drives "
    "the order level effect, and growth has not ensured good quality throughout."
)

if len(filtered) == 0:
    empty_state()
    st.stop()

delivered = filtered[filtered["is_delivered"] == True].copy()


# Order journey
st.subheader("The order journey")

funnel_stages = pd.Series({
    "Orders placed": len(filtered),
    "Payment approved": filtered["approved_ts"].notna().sum(),
    "Handed to carrier": filtered["carrier_ts"].notna().sum(),
    "Delivered": filtered["is_delivered"].sum(),
    "Delivered + reviewed": ((filtered["is_delivered"] == True) & (filtered["review_score"].notna())).sum(),
})

fig = go.Figure(go.Bar(
    x=funnel_stages.values, y=funnel_stages.index, orientation="h",
    marker_color=ACCENT,
    text=[f"{v:,} ({v/funnel_stages.iloc[0]*100:.1f}%)" for v in funnel_stages.values],
    textposition="outside",
    hovertemplate="%{y}: %{x:,}<extra></extra>",
))

fig.update_layout(
    height=320, 
    margin=dict(t=10, b=10), 
    xaxis_title="Number of orders",
    yaxis=dict(autorange="reversed")
)

st.plotly_chart(fig, width="stretch")

st.divider()


# Driver ranking
st.subheader("What actually predicts review score?")

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state(f"Only {len(delivered)} delivered orders match your filters which is too few to compute reliable correlations.")
else:
    driver_cols = ["transport_days", "delivery_delay_days", "processing_days", "n_items",
                   "freight_value", "distance_km", "order_item_value", "freight_ratio"]
    available_cols = [c for c in driver_cols if delivered[c].notna().sum() >= SMALL_SAMPLE_THRESHOLD]

    driver_corr = delivered[available_cols + ["review_score"]].corr()["review_score"].drop("review_score")
    driver_corr = driver_corr.dropna().reindex(driver_corr.abs().sort_values(ascending=False).index)

    colors = [ACCENT_WARN if abs(v) == driver_corr.abs().max() else ACCENT for v in driver_corr.values]

    fig = go.Figure(go.Bar(
        x=driver_corr.values, y=driver_corr.index, orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}" for v in driver_corr.values], textposition="outside",
        hovertemplate="%{y}<br>correlation: %{x:.3f}<extra></extra>",
    ))

    fig.update_layout(
        height=420, 
        margin=dict(t=10, b=10), 
        xaxis_title="Correlation with review score",
        yaxis=dict(autorange="reversed")
    )

    fig.add_vline(x=0, line_color="black", line_width=1)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Computed on {len(delivered):,} delivered orders matching current filters.")

st.divider()


# Processing vs transport time and the paradox
st.subheader("Decomposing delay: processing time vs. transport time")

col1, col2 = st.columns([1, 2])

with col1:
    if len(delivered) > 0:
        means = delivered[["processing_days", "transport_days"]].mean()

        fig = go.Figure(go.Bar(
            x=["Processing<br>(seller side)", "Transport<br>(carrier side)"], y=means.values,
            marker_color=[ACCENT, ACCENT_WARN],
            text=[f"{v:.1f} days" for v in means.values], textposition="outside",
        ))

        fig.update_layout(
            height=380, 
            margin=dict(t=10, b=10), 
            yaxis_title="Mean days"
        )

        st.plotly_chart(fig, width="stretch")

with col2:

    sellers_global = df.dropna(subset=["seller_id"]).drop_duplicates(subset=["seller_id"]).set_index("seller_id")
    seller_avg_review_global = df.dropna(subset=["seller_id"]).groupby("seller_id")["review_score"].mean()
    sellers_global = sellers_global.join(seller_avg_review_global.rename("seller_avg_review_score"))

    sellers_in_filter = filtered["seller_id"].dropna().unique()
    seller_confident = sellers_global[
        (sellers_global["seller_low_confidence"] == False) & (sellers_global.index.isin(sellers_in_filter))
    ]

    if len(delivered) < SMALL_SAMPLE_THRESHOLD or len(seller_confident) < SMALL_SAMPLE_THRESHOLD:
        empty_state("Not enough data under current filters to compute the order level vs. seller level comparison.")
    else:
        labels = ["Processing time", "Transport time"]

        order_vals = [
            delivered["processing_days"].corr(delivered["review_score"]),
            delivered["transport_days"].corr(delivered["review_score"]),
        ]
        seller_vals = [
            seller_confident["seller_avg_processing_days"].corr(seller_confident["seller_avg_review_score"]),
            seller_confident["seller_avg_transport_days"].corr(seller_confident["seller_avg_review_score"]),
        ]

        fig = make_subplots(rows=1, cols=2, subplot_titles=(
            "Order level", f"Seller level (n >= 5 global orders, {len(seller_confident)} sellers)"
        ))

        fig.add_trace(go.Bar(
            x=labels, 
            y=order_vals,
            marker_color=[ACCENT, ACCENT_WARN], 
            showlegend=False, 
            hovertemplate="<b>%{x}</b><br>Correlation: %{y:.3f}<extra></extra>"), 
            row=1, 
            col=1
        )

        fig.add_trace(go.Bar(
            x=labels, 
            y=seller_vals,
            marker_color=[ACCENT, ACCENT_WARN], 
            showlegend=False, 
            hovertemplate="<b>%{x}</b><br>Correlation: %{y:.3f}<extra></extra>"), 
            row=1, 
            col=2
        )

        fig.update_layout(
            height=380, 
            margin=dict(t=40, b=10),
            yaxis_title="Correlation with review score"
        )

        st.plotly_chart(fig, width="stretch")

st.caption(
    "**The paradox:** transport time tends to dominate at the order level, while processing "
    "time tends to be the stronger signal for which sellers are reliably good. Can try filtering "
    "to a single category or state to see whether this flip holds within that slice too."
)

st.divider()


# Growth vs quality tension
st.subheader("Growth vs. quality over time")

EXCLUDE_MONTHS = ["2016-09", "2016-12", "2018-09", "2018-10"]

monthly = (filtered[~filtered["purchase_month"].isin(EXCLUDE_MONTHS)]
           .groupby("purchase_month")
           .agg(orders=("order_id", "count"), late_rate=("is_late", "mean"))
           .reset_index())

if len(monthly) < 3:
    empty_state("Too few months remain under current filters to show a meaningful trend.")
else:
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08,
        subplot_titles=("Order volume", "Late delivery rate (%)")
    )

    fig.add_trace(go.Scatter(
        x=monthly["purchase_month"], 
        y=monthly["orders"],
        mode="lines", 
        line=dict(color=ACCENT, width=2), 
        name="Orders", 
        showlegend=False), 
        row=1, 
        col=1
    )

    fig.add_trace(go.Scatter(
        x=monthly["purchase_month"], 
        y=monthly["late_rate"] * 100,
        mode="lines", 
        line=dict(color=ACCENT_WARN, width=2),  
        name="Late Rate (%)", showlegend=False), 
        row=2, 
        col=1
    )

    fig.update_layout(height=500, margin=dict(t=40, b=10), hovermode="x unified")

    fig.update_xaxes(tickangle=45)

    st.plotly_chart(fig, width="stretch")

    st.caption(
        "2016-09, 2016-12 (single digit order months) and 2018-09/10 (dataset extraction tail) "
        "are excluded since both have issues (documented in visualizations), not real signal."
    )

st.divider()



# Monthly review-score composition

st.subheader("Monthly review score composition")
st.markdown("Which end of the scale actually moves in a given month : more 1 stars, or fewer 5 stars?")

monthly_delivered = delivered[~delivered["purchase_month"].isin(EXCLUDE_MONTHS)]
if len(monthly_delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough reviewed orders under current filters for a monthly breakdown.")
else:
    monthly_dist = monthly_delivered.groupby(["purchase_month", "review_score"]).size().unstack(fill_value=0)
    monthly_pct = monthly_dist.div(monthly_dist.sum(axis=1), axis=0) * 100

    star_colors = {1.0: ACCENT_WARN, 2.0: "#E67E60", 3.0: NEUTRAL, 4.0: ACCENT_LIGHT, 5.0: ACCENT}
    fig = go.Figure()
    for score in [1.0, 2.0, 3.0, 4.0, 5.0]:
        if score in monthly_pct.columns:
            fig.add_trace(go.Bar(
                x=monthly_pct.index, y=monthly_pct[score], name=f"{int(score)} star",
                marker_color=star_colors[score],
                hovertemplate=f"{int(score)} star: " + "%{y:.1f}%<extra></extra>",
            ))
    fig.update_layout(barmode="stack", height=450, margin=dict(t=10, b=10),
                       yaxis_title="% of reviewed orders", hovermode="x unified")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, width="stretch")

    st.caption(
        "There is no bar for November 2016 since there were zero orders of any type in that month in the dataset."
        "December 2016 is also excluded as it has only 1 order."
    )

st.divider()



# Seller concentration

st.subheader("Where to invest: seller order concentration")

seller_volume = (filtered.dropna(subset=["seller_id"])
                  .groupby("seller_id").size()
                  .sort_values(ascending=False))

if len(seller_volume) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Too few sellers under current filters to show a meaningful concentration curve.")
else:
    cum_pct_orders = seller_volume.cumsum() / seller_volume.sum() * 100
    cum_pct_sellers = np.arange(1, len(seller_volume) + 1) / len(seller_volume) * 100

    top10_idx = int(len(seller_volume) * 0.10)
    top10_share = cum_pct_orders.iloc[top10_idx] if top10_idx < len(cum_pct_orders) else cum_pct_orders.iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cum_pct_sellers, 
        y=cum_pct_orders.values, 
        mode="lines",
        line=dict(color=ACCENT, width=3),
        hovertemplate="Top %{x:.1f}% of sellers<br>= %{y:.1f}%% of orders<extra></extra>")
    )

    fig.add_trace(go.Scatter(
        x=[0, 100], y=[0, 100], 
        mode="lines",
        line=dict(color=NEUTRAL, dash="dash"), 
        name="equal distribution",
        hoverinfo="skip")
    )

    fig.add_trace(go.Scatter(
        x=[10], 
        y=[top10_share], 
        mode="markers",
        marker=dict(size=12, color=ACCENT_WARN),
        hovertemplate=f"Top 10% of sellers = {top10_share:.1f}% of orders<extra></extra>")
    )

    fig.update_layout(
        height=450, 
        margin=dict(t=10, b=10),
        xaxis_title="Sellers, ranked by volume (cumulative %)",
        yaxis_title="Orders (cumulative %)", 
        showlegend=False
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(f"Top 10% of sellers ({top10_idx:,} of {len(seller_volume):,}) account for {top10_share:.1f}% of filtered orders.")
