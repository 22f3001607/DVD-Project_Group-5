import streamlit as st
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import load_data, render_filters, empty_state, ACCENT, ACCENT_WARN, SMALL_SAMPLE_THRESHOLD

st.set_page_config(page_title="Acquisition Funnel", layout="wide")

df = load_data()
filtered = render_filters(df)

st.title("Acquisition Funnel")
st.markdown("Marketing funnel conversion, the growth vs quality counter narrative, and whether declared seller attributes predict real performance.")


@st.cache_data
def load_funnel_data():
    mql = pd.read_csv("marketing_qualified_leads_dataset.csv")
    deals = pd.read_csv("closed_deals_dataset.csv")
    mql["first_contact_date"] = pd.to_datetime(mql["first_contact_date"])
    return mql, deals


mql, deals = load_funnel_data()
sellers_global = df.dropna(subset=["seller_id"]).drop_duplicates(subset=["seller_id"]).set_index("seller_id")


leads_with_outcome = mql.merge(deals[["mql_id"]], on="mql_id", how="left", indicator=True)
leads_with_outcome["won"] = leads_with_outcome["_merge"] == "both"



# Conversion by channel

st.subheader("Conversion rate by acquisition channel")
st.caption("Marketplace wide : not affected by sidebar filters.")

by_origin = (leads_with_outcome.dropna(subset=["origin"])
             .groupby("origin")["won"].agg(conversion_rate="mean", n="count")
             .sort_values("conversion_rate", ascending=False))

by_origin["conversion_rate"] = by_origin["conversion_rate"] * 100

colors = [ACCENT_WARN if o in ["email", "other"] else ACCENT for o in by_origin.index]

fig = go.Figure(go.Bar(
    x=by_origin["conversion_rate"], 
    y=by_origin.index, 
    orientation="h", 
    marker_color=colors,
    customdata=by_origin["n"],
    hovertemplate="%{y}<br>Conversion: %{x:.1f}%<br>n=%{customdata:,} leads<extra></extra>",
))

fig.update_layout(
    height=420, 
    margin=dict(t=10, b=10), 
    xaxis_title="Conversion rate (%)"
)

st.plotly_chart(fig, width="stretch")

st.divider()




# Funnel efficiency over time

st.subheader("Funnel efficiency over time")
st.caption("Marketplace wide : not affected by sidebar filters. Data runs only through May 2018.")

mql_time = mql.copy()
mql_time["month"] = mql_time["first_contact_date"].dt.to_period("M").astype(str)

monthly_leads = mql_time.merge(deals[["mql_id"]], on="mql_id", how="left", indicator=True)
monthly_leads["won"] = monthly_leads["_merge"] == "both"
monthly_funnel = (monthly_leads[monthly_leads["month"] != "2017-06"]  # single-digit-lead month, excluded per notebook 05
                   .groupby("month").agg(n_leads=("mql_id", "count"), conversion_rate=("won", "mean")).reset_index())
monthly_funnel["conversion_rate"] = monthly_funnel["conversion_rate"] * 100

fig = make_subplots(
    rows=2, 
    cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.2,
    subplot_titles=("Leads per month", "Conversion rate (%)")
)

fig.add_trace(go.Scatter(
    x=monthly_funnel["month"], 
    y=monthly_funnel["n_leads"], 
    mode="lines+markers",
    line=dict(color=ACCENT, width=2), 
    name="Leads", 
    showlegend=False), 
    row=1, 
    col=1
)

fig.add_trace(go.Scatter(
    x=monthly_funnel["month"], 
    y=monthly_funnel["conversion_rate"], 
    mode="lines+markers",
    line=dict(color=ACCENT, width=2), 
    name="Conversion Rate (%)",
    showlegend=False), 
    row=2, 
    col=1
)

fig.update_layout(
    height=500, 
    margin=dict(t=40, b=10), 
    hovermode="x unified"
)

fig.update_xaxes(tickangle=45)

fig.update_yaxes(rangemode="tozero")

st.plotly_chart(fig, width="stretch")

st.caption("The last point (May 2018) likely understates the true rate since deals can take up to a year to close, so very recent leads haven't had time to convert yet.")

st.divider()




# Seller overlap

st.subheader("How much of the marketplace does the funnel actually explain?")

active_sellers = df.dropna(subset=["seller_id"])["seller_id"].unique()
overlap_sellers = deals[deals["seller_id"].isin(active_sellers)]["seller_id"].unique()

col1, col2 = st.columns(2)

with col1:
    st.metric("Won deals that became an active seller", f"{len(overlap_sellers)/len(deals)*100:.1f}%")
    st.caption(f"{len(overlap_sellers):,} of {len(deals):,} won deals")

with col2:
    st.metric("Active sellers with any funnel record", f"{len(overlap_sellers)/len(active_sellers)*100:.1f}%")
    st.caption(f"{len(overlap_sellers):,} of {len(active_sellers):,} active sellers")

st.info("Only 12% of active sellers have a funnel record at all so every finding below applies specifically to this overlap, not the marketplace as a whole.")

st.divider()




# Closing the loop -- responds to filters

st.subheader("Do declared signup attributes predict real performance?")
st.caption("**Responds to the sidebar filters** : seller performance is computed live from the currently filtered orders.")

if len(filtered) == 0:
    empty_state()
else:
    sellers_global = df.dropna(subset=["seller_id"]).drop_duplicates(subset=["seller_id"]).set_index("seller_id")
    sellers_in_filter = filtered["seller_id"].dropna().unique()
    seller_perf_confident = sellers_global[sellers_global.index.isin(sellers_in_filter)][["seller_pct_late"]].rename(columns={"seller_pct_late": "late_rate"}) 

    funnel_perf = deals.merge(seller_perf_confident.reset_index(), on="seller_id", how="inner")

    if len(funnel_perf) < SMALL_SAMPLE_THRESHOLD:
        empty_state("Not enough overlapping sellers under current filters to compare declared attributes against real performance.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            lead_type_perf = funnel_perf.groupby("lead_type")["late_rate"].agg(mean="mean", n="count").sort_values("mean")
            fig = go.Figure(go.Bar(
                x=lead_type_perf["mean"] * 100, 
                y=lead_type_perf.index, 
                orientation="h", 
                marker_color=ACCENT,
                customdata=lead_type_perf["n"],
                hovertemplate="%{y}<br>Late rate: %{x:.1f}%<br>n=%{customdata}<extra></extra>",
            ))

            fig.update_layout(
                height=400, 
                margin=dict(t=30, b=10), 
                xaxis_title="Late rate (%)", 
                title="By lead type"
            )

            st.plotly_chart(fig, width="stretch")

        with col2:
            bt_perf = funnel_perf.groupby("business_type")["late_rate"].agg(mean="mean", n="count")

            fig = go.Figure(go.Bar(
                x=bt_perf.index, 
                y=bt_perf["mean"] * 100, 
                marker_color=[ACCENT, ACCENT_WARN],
                customdata=bt_perf["n"],
                hovertemplate="%{x}<br>Late rate: %{y:.1f}%<br>n=%{customdata}<extra></extra>",
                text=[f"{v:.1f}%" for v in bt_perf["mean"] * 100], 
                textposition="outside",
            ))

            fig.update_layout(
                height=400, 
                margin=dict(t=30, b=10), 
                yaxis_title="Late rate (%)", 
                title="By business type"
            )

            st.plotly_chart(fig, width="stretch")

        st.caption(f"n = {len(funnel_perf)} sellers in this comparison, under current filters (confident sellers, 5+ orders, only).")

st.divider()




# lead_behaviour_profile discovery

st.subheader("Discovery finding: an unlabeled tag that predicts real outcomes")

st.caption("Responds to the sidebar filters, same live recompute approach as above.")

if len(filtered) == 0:
    empty_state()
else:
    sellers_in_filter2 = filtered["seller_id"].dropna().unique()
    seller_perf_confident2 = sellers_global[sellers_global.index.isin(sellers_in_filter2)][["seller_pct_late"]].rename(columns={"seller_pct_late": "late_rate"}).reset_index()

    profile_perf = deals.merge(seller_perf_confident2, on="seller_id", how="inner")
    profile_summary = profile_perf.groupby("lead_behaviour_profile")["late_rate"].agg(mean="mean", n="count")
    profile_summary = profile_summary[profile_summary["n"] >= 10].sort_values("mean")

    if len(profile_summary) < 2:
        empty_state("Not enough overlapping sellers under current filters for this comparison.")
    else:
        fig = go.Figure(go.Bar(
            x=profile_summary.index, y=profile_summary["mean"] * 100, marker_color=ACCENT,
            customdata=profile_summary["n"],
            hovertemplate="%{x}<br>Late rate: %{y:.1f}%<br>n=%{customdata}<extra></extra>",
            text=[f"{v:.1f}%" for v in profile_summary["mean"] * 100], textposition="outside",
        ))
        fig.update_layout(height=400, margin=dict(t=10, b=10), yaxis_title="Late rate (%)")
        st.plotly_chart(fig, width="stretch")
        st.caption("What these labels actually represent is not documented anywhere in this dataset. So the pattern is real, but the mechanism is unknown.")

st.divider()

# ============================================================
# Sales rep concentration
# ============================================================
st.subheader("Sales rep concentration")
st.caption("Marketplace wide : not affected by sidebar filters.")

rep_counts = deals["sr_id"].value_counts()
fig = go.Figure(go.Bar(x=list(range(1, len(rep_counts) + 1)), y=rep_counts.values, marker_color=ACCENT,
                        hovertemplate="Rep rank %{x}<br>Deals closed: %{y}<extra></extra>"))
fig.update_layout(height=380, margin=dict(t=10, b=10), xaxis_title=f"Sales reps (closers), ranked by deals closed (n = {len(rep_counts)})",
                   yaxis_title="Deals closed", xaxis=dict(showticklabels=False))
st.plotly_chart(fig, width="stretch")
st.caption(f"Top rep alone closed {rep_counts.iloc[0]} deals ({rep_counts.iloc[0]/len(deals)*100:.1f}% of all {len(deals)} won deals).")
