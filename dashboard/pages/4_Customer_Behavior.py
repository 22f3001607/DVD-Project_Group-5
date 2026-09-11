import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import (
    load_data, render_filters, empty_state,
    ACCENT, ACCENT_WARN, NEUTRAL, DELAY_LABELS, SMALL_SAMPLE_THRESHOLD,
)

st.set_page_config(page_title="Customer Behavior & Loyalty", layout="wide")

df = load_data()
filtered = render_filters(df)

st.title("Customer Behavior & Loyalty")
st.markdown(
    "Review behavior, repeat customers, the voucher mini story, and four discovery "
    "findings which are worth noting about as they might lead to some hidden patterns."
)

if len(filtered) == 0:
    empty_state()
    st.stop()

delivered = filtered[filtered["is_delivered"] == True].copy()



# Review score distribution

st.subheader("Review score distribution")

reviewed = filtered[filtered["review_score"].notna()]

if len(reviewed) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough reviewed orders under current filters.")
else:
    dist = reviewed["review_score"].value_counts(normalize=True).sort_index() * 100

    colors = [ACCENT_WARN if s <= 2 else NEUTRAL if s == 3 else ACCENT for s in dist.index]

    fig = go.Figure(go.Bar(
        x=dist.index.astype(int), 
        y=dist.values, 
        marker_color=colors,
        text=[f"{v:.1f}%" for v in dist.values], 
        textposition="outside")
    )

    fig.update_layout(
        height=380, 
        margin=dict(t=10, b=10), 
        xaxis_title="Review score (stars)",
        yaxis=dict(title="% of reviewed orders", 
        range=[0, dist.max() * 1.2])
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(f"n = {len(reviewed):,} reviewed orders under current filters.")

st.divider()



# Comment presence

st.subheader("Comment presence as a dissatisfaction signal")

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough delivered orders under current filters.")
else:
    comment_review = delivered.groupby("has_comment")["review_score"].agg(mean="mean", n="count")
    comment_review.index = comment_review.index.map({False: "No comment", True: "Has comment"})

    fig = go.Figure(go.Bar(
        x=comment_review.index, 
        y=comment_review["mean"], 
        marker_color=[ACCENT, ACCENT_WARN],
        text=[f"{v:.2f}" for v in comment_review["mean"]], 
        textposition="outside",
        customdata=comment_review["n"],
        hovertemplate="%{x}<br>Avg score: %{y:.2f}<br>n=%{customdata:,}<extra></extra>")
    )

    fig.update_layout(
        height=380, 
        margin=dict(t=10, b=10), 
        yaxis=dict(title="Mean review score", 
        range=[0, 5])
    )

    st.plotly_chart(fig, width="stretch")

st.divider()




# Repeat customers

st.subheader("Repeat customers and their first order experience")

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough delivered orders under current filters.")
else:
    repeat_delivery = delivered.groupby("is_repeat")["is_late"].agg(mean="mean", n="count")
    repeat_delivery.index = repeat_delivery.index.map({False: "One time customers", True: "Repeat customers"})

    if repeat_delivery["n"].min() < SMALL_SAMPLE_THRESHOLD:
        st.warning("One of the two groups has very few orders under current filters -- interpret the comparison cautiously.")

    fig = go.Figure(go.Bar(
        x=repeat_delivery.index, 
        y=repeat_delivery["mean"] * 100, 
        marker_color=[NEUTRAL, ACCENT],
        text=[f"{v:.1f}%" for v in repeat_delivery["mean"] * 100], 
        textposition="outside",
        customdata=repeat_delivery["n"],
        hovertemplate="%{x}<br>Late rate: %{y:.1f}%<br>n=%{customdata:,}<extra></extra>")
    )

    fig.update_layout(
        height=380, 
        margin=dict(t=10, b=10), 
        yaxis_title="Late rate (%)"
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("**How many times do repeat customers actually come back?**")
customers = filtered.dropna(subset=["customer_unique_id"]).drop_duplicates(subset="customer_unique_id")
repeat_counts = customers[customers["customer_order_count"] > 1]["customer_order_count"].value_counts().sort_index()

if len(repeat_counts) == 0:
    empty_state("No repeat customers under current filters.")
else:
    max_count = repeat_counts.max()

    use_log = max_count > 50

    fig = go.Figure(go.Bar(
        x=repeat_counts.index.astype(str), 
        y=repeat_counts.values, 
        marker_color=ACCENT,
        text=repeat_counts.values, 
        textposition="outside", 
        hovertemplate="Orders: %{x}<br>Customers: %{y:,}<extra></extra>")
    )

    fig.update_layout(
        height=380, 
        margin=dict(t=50, b=10), 
        xaxis_title="Total orders placed",
        yaxis=dict(title="Number of customers", 
        type="log" if use_log else "linear", 
        tickformat="d", 
        dtick=1 if use_log else None)
    )

    fig.update_xaxes(type="category")

    st.plotly_chart(fig, width="stretch")

st.divider()




# Voucher mini-story

st.subheader("The voucher mini story")

payment_types = filtered["payment_type_primary"].dropna()
payment_types = payment_types[payment_types != "not_defined"]

if len(payment_types) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough orders under current filters.")
else:
    valid_orders = filtered[filtered["payment_type_primary"].isin(payment_types.unique())]

    payment_summary = valid_orders.groupby("payment_type_primary").agg(
        cancel_rate=("is_canceled", "mean"), avg_order_value=("total_payment_value", "mean"), n=("order_id", "count")
    )

    payment_review = valid_orders[valid_orders["review_score"].notna()].groupby("payment_type_primary")["review_score"].mean()
    payment_summary["avg_review"] = payment_review

    methods = payment_summary.index.tolist()
    colors = [ACCENT_WARN if m == "voucher" else ACCENT for m in methods]

    col1, col2, col3 = st.columns(3)
    with col1:
        fig = go.Figure(go.Bar(
            x=methods, 
            y=payment_summary["cancel_rate"] * 100, 
            marker_color=colors,
            text=[f"{v:.2f}%" for v in payment_summary["cancel_rate"] * 100], 
            textposition="outside")
        )

        fig.update_layout(
            height=380, 
            margin=dict(t=30, b=10), 
            title="Cancellation rate"
        )

        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = go.Figure(go.Bar(
            x=methods, 
            y=payment_summary["avg_order_value"], 
            marker_color=colors,
            text=[f"{v:.0f}" for v in payment_summary["avg_order_value"]], 
            textposition="outside")
        )

        fig.update_layout(
            height=380, 
            margin=dict(t=30, b=10), 
            title="Average order value"
        )

        st.plotly_chart(fig, width="stretch")

    with col3:
        fig = go.Figure(go.Bar(
            x=methods, 
            y=payment_summary["avg_review"], 
            marker_color=colors,
            text=[f"{v:.2f}" for v in payment_summary["avg_review"]], 
            textposition="outside")
        )

        fig.update_layout(
            height=380,
            margin=dict(t=30, b=10), 
            title="Average review score", 
            yaxis=dict(range=[0, 5])
        )

        st.plotly_chart(fig, width="stretch")

st.divider()
st.header("Discovery findings")
st.caption(
    "Smaller, but interesting patterns which usually go unnoticed and carrying more "
    "uncertainty than the findings above. So it should be read with the caveat related to it, not just the headline number."
)



# Discovery 1: holiday tolerance

st.subheader("No holiday tolerance effect")

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough delivered orders under current filters.")
else:
    holiday_months = ["2017-11", "2017-12", "2018-01"]

    d = delivered.copy()
    d["is_holiday_period"] = d["purchase_month"].isin(holiday_months)

    holiday_table = d.groupby(["delay_bucket", "is_holiday_period"], observed=True)["review_score"].agg(mean="mean", n="count")

    fig = go.Figure()

    for is_holiday, name, color in [(False, "Rest of year", ACCENT), (True, "Nov 2017 - Jan 2018", ACCENT_WARN)]:
        y_vals, n_vals = [], []
        for label in DELAY_LABELS:
            try:
                y_vals.append(holiday_table.loc[(label, is_holiday), "mean"])
                n_vals.append(holiday_table.loc[(label, is_holiday), "n"])
            except KeyError:
                y_vals.append(None)
                n_vals.append(0)

        fig.add_trace(go.Bar(
            x=DELAY_LABELS, 
            y=y_vals, 
            name=name, 
            marker_color=color,
            customdata=n_vals, 
            hovertemplate="%{x}<br>Avg: %{y:.2f}<br>n=%{customdata}<extra></extra>")
        )

    fig.update_layout(
        barmode="group", 
        height=450, 
        margin=dict(t=10, b=10), 
        yaxis=dict(title="Mean review score", 
        range=[1, 5])
    )

    st.plotly_chart(fig, width="stretch")

    st.caption("Caveat: bucketed by calendar month, which is a proxy for high demand period, not real promotional calendar data.")

st.divider()



# Discovery 2: early delivery ceiling effect

st.subheader("An early delivery ceiling effect")

d2 = delivered.copy()
d2["early_days"] = -d2["delivery_delay_days"]

early_only = d2[d2["early_days"] > 0]

if len(early_only) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough early delivered orders under current filters.")
else:
    fine_bins = [0, 3, 7, 14, 21, 30, 45, 999]
    fine_labels = ["1-3d", "4-7d", "8-14d", "15-21d", "22-30d", "31-45d", "45+d"]

    early_only = early_only.copy()
    early_only["bucket"] = pd.cut(early_only["early_days"], bins=fine_bins, labels=fine_labels)

    ceiling = early_only.groupby("bucket", observed=True)["review_score"].agg(mean="mean", n="count").reindex(fine_labels).dropna()

    if len(ceiling) < 3:
        empty_state("Not enough spread in early-delivery timing under current filters to show the ceiling shape.")
    else:
        fig = go.Figure(go.Scatter(
            x=ceiling.index, 
            y=ceiling["mean"], 
            mode="lines+markers", 
            line=dict(color=ACCENT, width=2),
            customdata=ceiling["n"],
            hovertemplate="%{x} early<br>Avg: %{y:.3f}<br>n=%{customdata:,}<extra></extra>",
        ))

        fig.update_layout(
            height=420, 
            margin=dict(t=10, b=10), 
            xaxis_title="Days early", 
            yaxis_title="Mean review score"
        )

        st.plotly_chart(fig, width="stretch")

st.divider()




# Discovery 3: category delay sensitivity

st.subheader("Delay sensitivity by category")

top10_cats = delivered["primary_category"].value_counts().head(10).index
cat_sens_data = []

for cat in top10_cats:
    sub = delivered[delivered["primary_category"] == cat]

    if len(sub) >= SMALL_SAMPLE_THRESHOLD:
        cat_sens_data.append((cat, sub["delivery_delay_days"].corr(sub["review_score"]), len(sub)))

if len(cat_sens_data) < 3:
    empty_state("Not enough categories with sufficient data under current filters.")
else:
    cat_sens_df = pd.DataFrame(cat_sens_data, columns=["category", "corr", "n"]).sort_values("corr")

    fig = go.Figure(go.Bar(
        x=cat_sens_df["corr"], 
        y=cat_sens_df["category"], 
        orientation="h", 
        marker_color=ACCENT,
        customdata=cat_sens_df["n"],
        hovertemplate="%{y}<br>Correlation: %{x:.3f}<br>n=%{customdata:,}<extra></extra>",
        text=[f"{v:.3f}" for v in cat_sens_df["corr"]], 
        textposition="outside",
    ))

    fig.update_layout(
        height=400, 
        margin=dict(t=10, b=10), 
        xaxis_title="Correlation between delay and review score"
    )

    st.plotly_chart(fig, width="stretch")

st.divider()




# Discovery 4: repeat customer delay interaction

st.subheader("Loyalty buys patience for big failures, not small slips")

if len(delivered) < SMALL_SAMPLE_THRESHOLD:
    empty_state("Not enough delivered orders under current filters.")
else:
    repeat_interaction = delivered.groupby(["delay_bucket", "is_repeat"], observed=True)["review_score"].agg(mean="mean", n="count")

    fig = go.Figure()

    for is_repeat, name, color in [(False, "First time customers", ACCENT), (True, "Repeat customers", ACCENT_WARN)]:
        y_vals, n_vals = [], []
        for label in DELAY_LABELS:
            try:
                y_vals.append(repeat_interaction.loc[(label, is_repeat), "mean"])
                n_vals.append(repeat_interaction.loc[(label, is_repeat), "n"])
            except KeyError:
                y_vals.append(None)
                n_vals.append(0)

        fig.add_trace(go.Bar(
            x=DELAY_LABELS, 
            y=y_vals, 
            name=name, 
            marker_color=color,
            customdata=n_vals, 
            hovertemplate="%{x}<br>Avg: %{y:.2f}<br>n=%{customdata}<extra></extra>")
        )

    fig.update_layout(barmode="group", height=450, margin=dict(t=10, b=10), yaxis=dict(title="Mean review score", range=[0, 5]))

    st.plotly_chart(fig, width="stretch")

    st.caption("Repeat customer late buckets are often thin (check hover for n) so this is a directional evidence, not a precise estimate.")
