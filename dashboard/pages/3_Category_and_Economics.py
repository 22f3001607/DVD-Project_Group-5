import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import (
    load_data, render_filters, empty_state,
    ACCENT, ACCENT_WARN, NEUTRAL, SMALL_SAMPLE_THRESHOLD,
)

st.set_page_config(page_title="Category & Economics", layout="wide")

df = load_data()
filtered = render_filters(df)

st.title("Category & Economics")
st.markdown("Category level risk, freight economics, and where growth isn't reaching evenly.")

if len(filtered) == 0:
    empty_state()
    st.stop()

delivered = filtered[filtered["is_delivered"] == True].copy()

TOP_N = 15
top_categories = filtered["primary_category"].value_counts().head(TOP_N).index.tolist()
st.caption(f"Category charts below use the top {TOP_N} categories **within your current filter selection**.")

EXCLUDE_MONTHS = ["2016-09", "2016-12", "2018-09", "2018-10"]




# Category review-score distribution (small multiples)

st.subheader("Review score distribution by category")

cat_reviewed = delivered[delivered["primary_category"].isin(top_categories)]

if len(cat_reviewed) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough reviewed orders under current filters.")
else:
    star_dist = (cat_reviewed.groupby("primary_category")["review_score"]
                 .value_counts(normalize=True).unstack().reindex(columns=[1, 2, 3, 4, 5]) * 100)

    cat_order = cat_reviewed.groupby("primary_category")["review_score"].mean().sort_values().index

    star_dist = star_dist.reindex(cat_order).dropna(how="all")

    n_cols = 5
    n_rows = int(np.ceil(len(star_dist) / n_cols))

    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=star_dist.index.tolist())

    for i, cat in enumerate(star_dist.index):
        row, col = i // n_cols + 1, i % n_cols + 1
        row_data = star_dist.loc[cat]
        colors = [ACCENT_WARN if s <= 2 else NEUTRAL if s == 3 else ACCENT for s in [1, 2, 3, 4, 5]]
        fig.add_trace(go.Bar(
            x=[1, 2, 3, 4, 5], 
            y=row_data.values, 
            marker_color=colors, 
            showlegend=False,
            hovertemplate="%{x} star: %{y:.1f}%<extra></extra>"), 
            row=row, 
            col=col
        )

    fig.update_layout(height=220 * n_rows, margin=dict(t=40, b=10))

    fig.update_xaxes(type="category")

    st.plotly_chart(fig, width="stretch")

st.divider()




# Cancellation by category

st.subheader("Cancellation rate by category")

cat_all = filtered[filtered["primary_category"].isin(top_categories)]

if len(cat_all) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough orders under current filters.")
else:
    cat_cancel = cat_all.groupby("primary_category")["is_canceled"].agg(rate="mean", n="count").sort_values("rate")
    fig = go.Figure(go.Bar(
        x=cat_cancel["rate"] * 100, 
        y=cat_cancel.index, 
        orientation="h", 
        marker_color=ACCENT,
        customdata=cat_cancel["n"],
        hovertemplate="%{y}<br>Cancellation: %{x:.2f}%<br>n=%{customdata:,}<extra></extra>",
    ))

    fig.update_layout(
        height=400, 
        margin=dict(t=10, b=10), 
        xaxis_title="Cancellation rate (%)"
    )
    
    st.plotly_chart(fig, width="stretch")

st.divider()




# Category rank slopegraph

st.subheader("How category rank shifted, pre 2018 vs. 2018+")

d_rank = filtered[~filtered["purchase_month"].isin(EXCLUDE_MONTHS) & filtered["primary_category"].isin(top_categories)].copy()
d_rank["period"] = np.where(d_rank["purchase_month"] < "2018-01", "pre-2018", "2018+")

n_months_pre = d_rank[d_rank["period"] == "pre-2018"]["purchase_month"].nunique()
n_months_post = d_rank[d_rank["period"] == "2018+"]["purchase_month"].nunique()

if n_months_pre < 2 or n_months_post < 2 or len(d_rank) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough months of data on both sides of 2018 under current filters for a rank comparison.")
else:
    avg_monthly = d_rank.groupby(["primary_category", "period"]).size().unstack(fill_value=0)

    avg_monthly["pre-2018"] = avg_monthly["pre-2018"] / n_months_pre
    avg_monthly["2018+"] = avg_monthly["2018+"] / n_months_post

    avg_monthly["rank_pre"] = avg_monthly["pre-2018"].rank(ascending=False)
    avg_monthly["rank_post"] = avg_monthly["2018+"].rank(ascending=False)
    avg_monthly["rank_change"] = avg_monthly["rank_pre"] - avg_monthly["rank_post"]

    fig = go.Figure()
    for cat, row in avg_monthly.iterrows():
        is_decliner = row["rank_change"] <= -3
        color = ACCENT_WARN if is_decliner else "#999999"
        width = 3 if is_decliner else 1
        opacity = 1.0 if is_decliner else 0.35
        fig.add_trace(go.Scatter(
            x=["Pre 2018", "2018+"], 
            y=[row["rank_pre"], row["rank_post"]],
            mode="lines+markers+text", 
            line=dict(color=color, width=width),
            text=[cat, cat], 
            textposition=["middle left", "middle right"], 
            textfont=dict(size=9, color=ACCENT_WARN if is_decliner else "#555555"),
            showlegend=False,
            hovertemplate=f"{cat}<br>" + "Rank: %{y}<extra></extra>",
        ))

    fig.update_layout(
        height=550, 
        margin=dict(t=10, b=10, l=100, r=100),
        xaxis=dict(range=[-0.5, 1.5]),
        yaxis=dict(autorange="reversed", 
        title="Rank (1 = highest volume)", 
        dtick=1)
    )

    st.plotly_chart(fig, width="stretch")

    st.caption("Categories in red dropped 3+ rank positions, you can hover any point for its category name and exact rank.")

st.divider()




# Freight vs review by category

st.subheader("Freight ratio vs. review score, by category")

cat_freight_data = delivered[delivered["primary_category"].isin(top_categories)].dropna(subset=["freight_ratio"])

if len(cat_freight_data) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough data under current filters.")
else:
    cat_freight = cat_freight_data.groupby("primary_category").agg(
        avg_freight_ratio=("freight_ratio", "mean"), avg_review=("review_score", "mean"), n=("order_id", "count")
    )
    fig = go.Figure(go.Scatter(
        x=cat_freight["avg_freight_ratio"], 
        y=cat_freight["avg_review"], 
        mode="markers+text",
        text=cat_freight.index, 
        textposition="top center", 
        textfont=dict(size=9),
        marker=dict(size=np.clip(cat_freight["n"] / cat_freight["n"].max() * 50, 10, 50), color=ACCENT, opacity=0.7),
        customdata=cat_freight["n"],
        hovertemplate="<b>%{text}</b><br>Freight ratio: %{x:.2f}<br>Avg review: %{y:.2f}<br>n=%{customdata:,}<extra></extra>",
    ))

    fig.update_layout(
        height=550, 
        margin=dict(t=10, b=10),
        xaxis_title="Average freight ratio", 
        yaxis_title="Average review score"
    )
    
    st.plotly_chart(fig, width="stretch")

st.divider()




# Freight ratio x price tier interaction

st.subheader("Discovery finding: freight ratio matters more for expensive orders")

fr_data = delivered.dropna(subset=["order_item_value", "freight_ratio"])

if len(fr_data) < 200:
    empty_state("Not enough data under current filters for a price-tier breakdown (needs a reasonable spread of order values).")
else:
    try:
        fr = fr_data.copy()
        fr["price_tier"] = pd.qcut(fr["order_item_value"], 4, labels=["Q1 (cheapest)", "Q2", "Q3", "Q4 (priciest)"], duplicates="drop")
        fr["freight_bucket"] = pd.qcut(fr["freight_ratio"], 4, labels=["Lowest", "Low-mid", "High-mid", "Highest"], duplicates="drop")

        interaction = fr.groupby(["price_tier", "freight_bucket"], observed=True).agg(mean=("review_score", "mean"), n=("review_score", "count"))

        price_tiers = fr["price_tier"].cat.categories.tolist()

        fig = make_subplots(rows=1, cols=len(price_tiers), subplot_titles=price_tiers, shared_yaxes=True)

        for i, tier in enumerate(price_tiers):

            if tier not in interaction.index.get_level_values(0):
                continue

            sub = interaction.loc[tier]

            colors = [ACCENT_WARN if n < 30 else ACCENT for n in sub["n"]]

            fig.add_trace(go.Bar(
                x=sub.index.astype(str), 
                y=sub["mean"], 
                marker_color=colors, 
                showlegend=False,
                customdata=sub["n"],
                hovertemplate="%{x}<br>Avg score: %{y:.2f}<br>n=%{customdata}<extra></extra>"),
                row=1, 
                col=i + 1
            )
        fig.update_layout(
            height=420, 
            margin=dict(t=40, b=10)
        )

        fig.update_yaxes(
            title_text="Mean review score", 
            row=1, 
            col=1
        )

        st.plotly_chart(fig, width="stretch")

        st.caption("Red bars rest on fewer than 30 orders (read with caution).")

    except (ValueError, IndexError):
        empty_state("Order values under current filters are too uniform to split into price tiers.")

st.divider()




# Zero-freight orders

st.subheader("Zero freight orders")

zero_freight = filtered[filtered["freight_value"] == 0].dropna(subset=["seller_id"])

if len(zero_freight) == 0:
    empty_state("No zero freight orders under current filters.")
else:
    by_seller = zero_freight["seller_id"].value_counts().head(10)

    fig = go.Figure(go.Bar(
        x=[s[:8] + "..." for s in by_seller.index], 
        y=by_seller.values, 
        marker_color=ACCENT,
        text=by_seller.values, 
        textposition="outside")
    )

    fig.update_layout(height=380, margin=dict(t=10, b=10), yaxis_title="Number of zero freight orders")

    st.plotly_chart(fig, width="stretch")

    st.caption(f"{len(zero_freight)} zero freight orders under current filters, traced to {zero_freight['seller_id'].nunique()} seller(s).")
