import os
from datetime import datetime, timedelta

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

st.set_page_config(
    page_title="Indian Financial News Aggregator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for production-quality UX
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E2E;
        border-radius: 8px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-title { font-size: 14px; font-weight: bold; color: #A0A0B0; }
    .metric-value { font-size: 28px; font-weight: bold; margin-top: 5px; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_sources():
    try:
        response = httpx.get(f"{API_BASE_URL}/sources")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch sources: {e}")
        return []

@st.cache_data(ttl=30)
def fetch_pipeline_runs():
    try:
        response = httpx.get(f"{API_BASE_URL}/pipeline-runs?limit=10")
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        st.error(f"Failed to fetch pipeline runs: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_trending():
    try:
        response = httpx.get(f"{API_BASE_URL}/analytics/trending?time_window_hours=48")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return []

def render_dashboard():
    st.title("📊 Platform Dashboard")
    
    st.subheader("Latest Pipeline Runs")
    runs = fetch_pipeline_runs()
    if runs:
        df_runs = pd.DataFrame(runs)
        # Format dates
        df_runs['started_at'] = pd.to_datetime(df_runs['started_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(
            df_runs[['status', 'started_at', 'articles_ingested', 'duplicates_detected', 'failures', 'duration_ms']],
            use_container_width=True
        )
    else:
        st.info("No pipeline runs found.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Source Health")
        sources = fetch_sources()
        if sources:
            df_sources = pd.DataFrame(sources)
            df_sources['circuit_breaker_state'] = df_sources['circuit_breaker_state'].replace({
                0: "🟢 CLOSED", 1: "🟡 HALF-OPEN", 2: "🔴 OPEN"
            })
            st.dataframe(df_sources[['name', 'source_type', 'circuit_breaker_state', 'last_success_at']], use_container_width=True)
            
    with col2:
        st.subheader("Trending Entities (48h)")
        trending = fetch_trending()
        if trending:
            df_trend = pd.DataFrame(trending)
            fig = px.bar(df_trend, x='entity', y='total_mentions', color='entity_type', title="Top Mentions")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trending data available.")

def render_explorer():
    st.title("📰 Article Explorer")
    
    with st.sidebar:
        st.header("Filters")
        search_query = st.text_input("Search (Full-Text)")
        
        sources = fetch_sources()
        source_options = {s["name"]: s["slug"] for s in sources}
        selected_source_names = st.multiselect("Sources", options=list(source_options.keys()))
        selected_sources = [source_options[k] for k in selected_source_names]
        
        keywords = st.text_input("Keywords (comma separated)")
        
        date_range = st.date_input("Date Range", value=(datetime.now() - timedelta(days=7), datetime.now()))
        
        limit = st.slider("Results Limit", 10, 100, 20)

    # Build query params
    params = {"limit": limit}
    if search_query:
        params["q"] = search_query
    if selected_sources:
        # FastAPI might expect multiple source= params
        params["source"] = selected_sources
    if keywords:
        params["keywords"] = keywords
    if len(date_range) == 2:
        params["date_from"] = date_range[0].isoformat()
        # Make date_to inclusive of the entire day
        params["date_to"] = (date_range[1] + timedelta(days=1)).isoformat()

    try:
        # Since 'source' is a list, httpx handles it nicely
        with st.spinner("Fetching articles..."):
            response = httpx.get(f"{API_BASE_URL}/articles", params=params)
            response.raise_for_status()
            data = response.json()
            articles = data.get("items", [])
            
        if articles:
            st.success(f"Loaded {len(articles)} articles.")
            
            # Export controls
            st.download_button(
                "📥 Export CSV",
                httpx.get(f"{API_BASE_URL}/articles/export/csv", params=params).content,
                file_name="articles_export.csv",
                mime="text/csv"
            )

            for art in articles:
                with st.container():
                    st.markdown(f"### [{art['title']}]({art['url']})")
                    meta_str = f"**{art['source_name']}** • {art['published_at']} • {', '.join(art.get('tags', []))}"
                    st.caption(meta_str)
                    if art.get('summary'):
                        st.markdown(art['summary'][:300] + "...")
                    st.divider()
        else:
            st.warning("No articles found matching filters.")
    except Exception as e:
        st.error(f"Error fetching articles: {e}")

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Article Explorer"])

if page == "Dashboard":
    render_dashboard()
else:
    render_explorer()
