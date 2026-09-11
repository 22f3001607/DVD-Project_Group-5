import pandas as pd
import streamlit as st

# Fixed colors
ACCENT = "#2E5EAA"
ACCENT_WARN = "#C0392B"
ACCENT_LIGHT = "#9FB8DE"
NEUTRAL = "#B0B0B0"

# Fixed bucket definitions
DELAY_BINS = [-200, -7, 0, 3, 7, 999]
DELAY_LABELS = ["5+ days early", "on-time/early", "1-3 days late", "4-7 days late", "8+ days late"]

SMALL_SAMPLE_THRESHOLD = 10


@st.cache_data
def load_data(path="analysis_master.csv"):

    # Loading the analysis master file and caching it for a smoother experience
    df = pd.read_csv(path, low_memory=False)
    df["purchase_ts"] = pd.to_datetime(df["purchase_ts"])
    df["delivered_ts"] = pd.to_datetime(df["delivered_ts"])
    df["delay_bucket"] = pd.cut(df["delivery_delay_days"], bins=DELAY_BINS, labels=DELAY_LABELS)
    df["is_repeat"] = df["customer_order_count"] > 1
    return df


def _reset_filters():

    # Callback for the reset button
    st.session_state["f_categories"] = []
    st.session_state["f_states"] = []
    st.session_state["f_delay"] = []
    st.session_state["f_seller_states"] = []
    st.session_state["f_seller_size"] = []
    st.query_params.clear()


def render_filters(df):

    # The sidebar filters, the filter persists across pages

    st.sidebar.header("Filters")
    st.sidebar.caption("Selections here apply across every page.")

    categories = sorted(df["primary_category"].dropna().unique().tolist())
    states = sorted(df["customer_state"].dropna().unique().tolist())

    seller_states = sorted(df["seller_state"].dropna().unique().tolist())
    size_buckets = sorted(df["seller_size_bucket"].dropna().unique().tolist())

    # Restore filters when the page is changed
    if "f_categories" not in st.session_state:
        st.session_state["f_categories"] = [v for v in st.query_params.get_all("category") if v in categories]
    if "f_states" not in st.session_state:
            st.session_state["f_states"] = [v for v in st.query_params.get_all("state") if v in states]
    if "f_delay" not in st.session_state:
            st.session_state["f_delay"] = [v for v in st.query_params.get_all("delay") if v in DELAY_LABELS]
    if "f_seller_states" not in st.session_state:
            st.session_state["f_seller_states"] = [v for v in st.query_params.get_all("seller_state") if v in seller_states]
    if "f_seller_size" not in st.session_state:
            st.session_state["f_seller_size"] = [v for v in st.query_params.get_all("seller_size") if v in size_buckets]

    selected_categories = st.sidebar.multiselect("Product category", categories, key="f_categories")
    selected_states = st.sidebar.multiselect("Customer state", states, key="f_states")
    selected_delay = st.sidebar.multiselect("Delivery performance", DELAY_LABELS, key="f_delay")
    selected_seller_states = st.sidebar.multiselect("Seller state (origin)", seller_states, key = "f_seller_states")
    selected_seller_size = st.sidebar.multiselect("Seller size", size_buckets, key = "f_seller_size")

    st.sidebar.button("Reset all filters", on_click=_reset_filters)

    # Adding the current selection into URL
    st.query_params["category"] = selected_categories
    st.query_params["state"] = selected_states
    st.query_params["delay"] = selected_delay
    st.query_params["seller_state"] = selected_seller_states
    st.query_params["seller_size"] = selected_seller_size


    filtered = df
    if selected_categories:
        filtered = filtered[filtered["primary_category"].isin(selected_categories)]
    if selected_states:
        filtered = filtered[filtered["customer_state"].isin(selected_states)]
    if selected_delay:
        filtered = filtered[filtered["delay_bucket"].isin(selected_delay)]
    if selected_seller_states:
        filtered = filtered[filtered["seller_state"].isin(selected_seller_states)]
    if selected_seller_size:
        filtered = filtered[filtered["seller_size_bucket"].isin(selected_seller_size)]

    st.sidebar.divider()
    st.sidebar.caption(f"**{len(filtered):,}** of {len(df):,} orders match current filters")

    return filtered


def small_sample_caption(n, threshold=SMALL_SAMPLE_THRESHOLD):

    # Displaying a message if the order number is too small in the selceted filter
    
    if n == 0:
        return "No orders match the current filters."
    if n < threshold:
        return f"n={n} is too small to draw conclusions from"
    return f"n={n:,}"


def kpi_metric(label, value_str, n, threshold=SMALL_SAMPLE_THRESHOLD, delta=None):

    # Showing the sample size 
    st.metric(label, value_str, delta=delta)
    st.caption(small_sample_caption(n, threshold))


def empty_state(message="No orders match the current filter combination, please try widening your selection."):
    st.info(message)