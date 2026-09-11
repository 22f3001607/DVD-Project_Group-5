import streamlit as st
import plotly.graph_objects as go

from utils import (
    load_data, render_filters, kpi_metric, empty_state,
    ACCENT, ACCENT_WARN, DELAY_LABELS, SMALL_SAMPLE_THRESHOLD,
)

st.set_page_config(page_title="Marketplace Satisfaction & Risk", layout="wide")

df = load_data()
filtered = render_filters(df)

st.title("A Visual Study of E-Commerce Orders, Delivery & Customer Satisfaction")
st.markdown(
    "Explore what drives customer satisfaction and where the marketplace is genuinely at "
    "risk. Filter by category, region, and delivery performance using the sidebar, "
    "every page in this dashboard updates together."
)

if len(filtered) == 0:
    empty_state()
    st.stop()

delivered = filtered[filtered["is_delivered"] == True]
reviewed = filtered[filtered["review_score"].notna()]

# Title row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Orders (filtered)", f"{len(filtered):,}")
    st.caption(f"of {len(df):,} total")
with col2:
    late_rate = delivered["is_late"].mean() * 100 if len(delivered) else float("nan")
    kpi_metric("Late delivery rate", f"{late_rate:.1f}%", len(delivered))
with col3:
    avg_review = reviewed["review_score"].mean() if len(reviewed) else float("nan")
    kpi_metric("Avg review score", f"{avg_review:.2f} / 5", len(reviewed))
with col4:
    cancel_rate = filtered["is_canceled"].mean() * 100
    kpi_metric("Cancellation rate", f"{cancel_rate:.2f}%", len(filtered))

st.divider()

# Story summary
st.subheader("The core story, in three parts")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        "**1. The mechanism and its paradox**\n\n"
        "Delay predicts review score and transport time (carrier side) matters more "
        "than processing time (seller side) per order, though processing time better "
        "identifies which sellers are reliably good. See **Delivery Performance.**"
    )
with c2:
    st.markdown(
        "**2. Growth vs. quality is measurable**\n\n"
        "Delivery quality dipped at real points as volume grew, while acquisition "
        "efficiency improved over the same period. See **Delivery Performance** and "
        "**Acquisition Funnel**."
    )
with c3:
    st.markdown(
        "**3. Some interesting stories**\n\n"
        "Stories with smaller supporting data but some interesting patterns like holiday tolerance, an early delivery "
        "ceiling effect, and more. See **Customer Behavior**."
    )

st.divider()

# The main chart: delay -> review score
st.subheader("The anchor relationship: delivery delay vs. review score")

if len(delivered) == 0:
    empty_state("No delivered orders match the current filters.")
else:
    agg = (
        delivered.groupby("delay_bucket", observed=True)
        .agg(mean_score=("review_score", "mean"), n=("review_score", "count"))
        .reindex(DELAY_LABELS)
        .dropna(subset=["mean_score"])
    )

    if agg.empty:
        empty_state("No reviewed, delivered orders match the current filters.")
    else:
        colors = [ACCENT_WARN if n < SMALL_SAMPLE_THRESHOLD else ACCENT for n in agg["n"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=agg.index, y=agg["mean_score"], mode="lines+markers",
            line=dict(color=ACCENT, width=3),
            marker=dict(size=12, color=colors, line=dict(width=1, color="white")),
            customdata=agg["n"],
            hovertemplate="<b>%{x}</b><br>Avg review score: %{y:.2f}<br>n=%{customdata:,} orders<extra></extra>",
        ))
        fig.update_layout(
            yaxis=dict(range=[1, 5], title="Mean review score"),
            xaxis_title="Delivery delay bucket",
            height=450,
            margin=dict(t=20, b=20), 
            hovermode="x unified",
        )
        st.plotly_chart(fig, width='stretch')
        small_n_buckets = agg[agg["n"] < SMALL_SAMPLE_THRESHOLD]
        if len(small_n_buckets) > 0:
            st.caption(
                f"Marker(s) in red have fewer than {SMALL_SAMPLE_THRESHOLD} orders under "
                "the current filters so interpret the finding with that in mind."
            )

st.divider()
st.markdown(
    "Use the pages in the left sidebar for delivery performance, geography & sellers, "
    "categories & economics, customer behavior, and the acquisition funnel in more depth."
)
