import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import duckdb

from database import DB_PATH

st.set_page_config(page_title="Stock Market Data", layout="wide")

# Paleta de cores Design
BG = "#0B1220"
SURFACE = "#121B2E"
BORDER = "#22304A"
TEXT = "#E7EAF0"
TEXT_MUTED = "#8B96A8"
ACCENT = "#D4A017"
POSITIVE = "#34D399"
NEGATIVE = "#F87171"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

header[data-testid="stHeader"] {{
    background-color: transparent;
}}

.ticker-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: {ACCENT};
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
    margin-bottom: 18px;
}}
.ticker-badge .dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: {ACCENT};
}}

h1 {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 28px;
    letter-spacing: -0.02em;
    margin-bottom: 4px;
}}
.subtitle {{
    color: {TEXT_MUTED};
    font-size: 14px;
    margin-bottom: 16px;
}}

.project-desc {{
    color: {TEXT_MUTED};
    font-size: 13.5px;
    line-height: 1.6;
    max-width: 720px;
    padding: 12px 16px;
    background-color: {SURFACE};
    border-left: 2px solid {ACCENT};
    border-radius: 4px;
    margin-bottom: 24px;
}}

.metric-card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
}}
.metric-label {{
    font-size: 12px;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}}
.metric-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 600;
    color: {TEXT};
}}

[data-testid="stSelectbox"] label {{
    color: {TEXT_MUTED};
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dados

@st.cache_resource
def get_conn():
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=600)
def load_table(table_name: str) -> pd.DataFrame:
    conn = get_conn()
    return conn.sql(f"SELECT * FROM {table_name}").df()


asset_info = load_table("asset_info")
daily = load_table("daily_data")
daily["Data"] = pd.to_datetime(daily["Data"])
estatisticas = load_table("estatisticas_mensais")


# ---------------------------------------------------------------------------
# Header (explicacao breve)

st.markdown("<h1>Explorador de Ativos</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>Pipeline de dados diários — AMEX · NASDAQ · NYSE</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class='project-desc'>
        Pipeline próprio de ETL que ingere dados históricos de ações da AMEX, NASDAQ e NYSE,
        calcula retornos logarítmicos diários e mensais, estatísticas descritivas e matriz de
        correlação entre ativos — armazenados em DuckDB. Este dashboard consulta o warehouse
        diretamente para exploração interativa dos resultados.
    </div>
    """,
    unsafe_allow_html=True,
)

col_filter1, col_filter2 = st.columns(2)

with col_filter1:
    exchanges = ["Todas"] + sorted(asset_info["Exchange"].unique().tolist())
    exchange_filter = st.selectbox("Exchange", exchanges)

tickers_pool = (
    asset_info if exchange_filter == "Todas"
    else asset_info[asset_info["Exchange"] == exchange_filter]
)

with col_filter2:
    ticker = st.selectbox("Ticker", sorted(tickers_pool["Ticker"].tolist()))

ticker_exchange = asset_info.loc[asset_info["Ticker"] == ticker, "Exchange"].iloc[0]

st.markdown(
    f"""
    <div class="ticker-badge">
        <span class="dot"></span>
        {ticker_exchange} · {ticker}
    </div>
    """,
    unsafe_allow_html=True,
)


# Gráfico de crescimento acumulado

serie = daily[["Data", ticker]].dropna().copy()
serie["Crescimento"] = np.exp(serie[ticker].cumsum())

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=serie["Data"], y=serie["Crescimento"],
    mode="lines",
    line=dict(color=ACCENT, width=2),
    fill="tozeroy",
    fillcolor="rgba(212, 160, 23, 0.08)",
))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="IBM Plex Mono", color=TEXT_MUTED, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    height=380,
    xaxis=dict(showgrid=False, title=None),
    yaxis=dict(showgrid=True, gridcolor=BORDER, title="Crescimento (base 1.0)"),
)

st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Estatísticas mensais

if ticker in estatisticas.columns:
    stats_ticker = estatisticas.set_index("Metrica")[ticker]

    media = stats_ticker.get("Media", float("nan"))
    media_color = POSITIVE if media >= 0 else NEGATIVE

    metrics = [
        ("Retorno médio mensal", f"{media:.2%}", media_color),
        ("Desvio padrão mensal", f"{stats_ticker.get('Devio Padrão', float('nan')):.2%}", TEXT),
        ("Assimetria", f"{stats_ticker.get('Assimetria', float('nan')):.2f}", TEXT),
        ("Curtose", f"{stats_ticker.get('Kurtose', float('nan')):.2f}", TEXT),
    ]

    cols = st.columns(4)
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value" style="color:{color}">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.warning("Sem estatísticas disponíveis para este ticker.")