import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional, List

import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------
LOGO_PATH = "logo_gnews_mcp.png"  # light/white logo recommended


def load_logo() -> Any:
    """Load a logo image if available, otherwise fall back to an emoji."""
    if os.path.exists(LOGO_PATH):
        return Image.open(LOGO_PATH)
    return "📰"


st.set_page_config(
    page_title="Enterprise GNews MCP Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# Global styling
# ---------------------------------------------------------------------
def load_css(path: str = "style.css") -> None:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# Hide default Streamlit UI chrome
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# MCP client integration
# ---------------------------------------------------------------------
async def call_gnews_mcp(
    query: str,
    lang: str,
    country: str,
    max_results: int,
) -> Optional[Dict[str, Any]]:
    """Invoke the GNews MCP server and return the JSON payload."""
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        raise RuntimeError("Environment variable GNEWS_API_KEY is not set.")

    server_path = os.path.join(os.path.dirname(__file__), "main.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        env={"GNEWS_API_KEY": api_key},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_news",
                arguments={
                    "q": query,
                    "lang": lang,
                    "country": country,
                    "max": max_results,
                },
            )

            payloads: List[Dict[str, Any]] = []
            for item in result.content:
                if item.type == "text":
                    try:
                        payloads.append(json.loads(item.text))
                    except json.JSONDecodeError:
                        st.error("Unable to parse response from MCP server.")
                        return None

            return payloads[0] if payloads else None


# ---------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------
def render_header(logo: Any) -> None:
    """Render the top header with branding."""
    with st.container():
        col_logo, col_title, col_meta = st.columns([0.12, 0.63, 0.25])
        with col_logo:
            if isinstance(logo, Image.Image):
                st.image(logo, use_column_width=True)
            else:
                st.markdown(
                    '<div class="logo-pill">📰</div>',
                    unsafe_allow_html=True,
                )
        with col_title:
            st.markdown(
                """
                <div class="hero-block">
                    <h1 class="main-title">Enterprise News Intelligence</h1>
                    <p class="subtitle">
                        GNews MCP Server · Real-time global coverage for AI & executive insights
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_meta:
            st.markdown(
                """
                <div class="context-pill">
                    <div class="pill-label">Session Context</div>
                    <div class="pill-value">MCP · GNews API</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_sidebar() -> Dict[str, Any]:
    """Render sidebar controls and return selected parameters."""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Search Controls</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sidebar-subtitle">Define your news slice and trigger a focused query.</p>',
            unsafe_allow_html=True,
        )

        query = st.text_input(
            "Search query",
            value="artificial intelligence",
            help="Enter keywords for news search. Use quotes for exact phrases.",
        )

        col_lang, col_country = st.columns(2)
        with col_lang:
            lang = st.selectbox(
                "Language",
                options=["en", "hi", "mr", "es", "de", "fr", "ja"],
                index=0,
            )
        with col_country:
            country = st.selectbox(
                "Country",
                options=["us", "in", "gb", "jp", "de", "fr"],
                index=1,
            )

        max_results = st.slider(
            "Max results",
            min_value=5,
            max_value=20,
            value=10,
            step=5,
        )

        st.markdown('<div class="sidebar-section-label">Execution</div>', unsafe_allow_html=True)
        search_triggered = st.button(
            "Run Search",
            type="primary",
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown(
            """
            <div class="sidebar-footer">
                <div class="sidebar-footer-title">Enterprise Features</div>
                <ul class="sidebar-list">
                    <li>Session-aware queries</li>
                    <li>Executive KPI overview</li>
                    <li>Collapsible article insights</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "query": query,
        "lang": lang,
        "country": country,
        "max_results": max_results,
        "search_triggered": search_triggered,
    }


def render_metrics(
    total_articles: int,
    query: str,
    lang: str,
    country: str,
) -> None:
    """Render top-level KPIs."""
    st.markdown('<h3 class="section-title">Search Overview</h3>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles", f"{total_articles}")
    with col2:
        st.metric("Active Query", query if len(query) <= 28 else query[:25] + "…")
    with col3:
        st.metric("Language", lang.upper())
    with col4:
        st.metric("Country", country.upper())


def render_articles(articles: List[Dict[str, Any]]) -> None:
    """Render article list as card-style expanders."""
    st.markdown('<h3 class="section-title">Articles</h3>', unsafe_allow_html=True)

    if not articles:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-title">No articles found</div>
                <div class="empty-subtitle">
                    Try refining your query, expanding language/country, or increasing the result limit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for index, article in enumerate(articles, start=1):
        title = article.get("title", "Untitled article")
        description = article.get("description", "No description available.")
        source = article.get("source", {}).get("name", "Unknown source")
        published_at = article.get("publishedAt", "N/A")
        url = article.get("url")
        img_url = article.get("image")

        with st.expander(f"{index}. {title}", expanded=(index == 1)):
            card_cols = st.columns([0.8, 0.2])

            with card_cols[0]:
                st.markdown(
                    f"""
                    <div class="article-meta">
                        <div class="article-source">{source}</div>
                        <div class="article-date">{published_at}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f'<p class="article-description">{description}</p>', unsafe_allow_html=True)
                if url:
                    st.markdown(
                        f'<a href="{url}" target="_blank" class="article-link">Open full article ↗</a>',
                        unsafe_allow_html=True,
                    )
            with card_cols[1]:
                if img_url:
                    st.markdown(
                        f"""
                        <div class="article-image-container">
                            <img src="{img_url}" class="article-image" />
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ---------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------
def main() -> None:
    # Initialize session state
    if "search_clicked" not in st.session_state:
        st.session_state.search_clicked = False
    if "articles" not in st.session_state:
        st.session_state.articles = []
    if "last_params" not in st.session_state:
        st.session_state.last_params = {}

    logo = load_logo()
    render_header(logo)

    st.markdown(
        """
        <div class="page-intro">
            Track critical narratives across regions in real time.
            Configure your filters on the left and inspect structured article cards below.
        </div>
        """,
        unsafe_allow_html=True,
    )

    params = render_sidebar()
    query = params["query"].strip()

    # Handle initial state
    if params["search_triggered"]:
        st.session_state.search_clicked = True
        st.session_state.last_params = {
            "query": query,
            "lang": params["lang"],
            "country": params["country"],
            "max_results": params["max_results"],
        }

    if not st.session_state.search_clicked or not query:
        st.markdown(
            """
            <div class="empty-state empty-state-initial">
                <div class="empty-title">Ready when you are</div>
                <div class="empty-subtitle">
                    Set your search parameters in the sidebar and click <strong>Run Search</strong> to retrieve the latest coverage.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Use last committed params for consistency across reruns
    active_params = st.session_state.last_params

    with st.spinner("Fetching latest news from GNews via MCP..."):
        try:
            result = asyncio.run(
                call_gnews_mcp(
                    query=active_params["query"],
                    lang=active_params["lang"],
                    country=active_params["country"],
                    max_results=active_params["max_results"],
                )
            )
        except Exception as exc:
            st.error(
                f"Enterprise alert: {exc} · Please contact the platform administrator if this persists."
            )
            st.session_state.search_clicked = False
            return

    if not result:
        st.warning(
            "No results received from the GNews MCP server. "
            "Verify your API key, network connectivity, and MCP server status."
        )
        return

    st.session_state.articles = result.get("articles", [])
    total_articles = result.get("totalArticles", len(st.session_state.articles))

    render_metrics(
        total_articles=total_articles,
        query=active_params["query"],
        lang=active_params["lang"],
        country=active_params["country"],
    )

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    render_articles(st.session_state.articles)


if __name__ == "__main__":
    main()
