import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import importlib
import bcs_client
import screener_engine
from config import INITIAL_PORTFOLIO_SYMBOLS, POPULAR_CHILEAN_STOCKS

importlib.reload(bcs_client)
importlib.reload(screener_engine)

# Page configuration
st.set_page_config(
    page_title="Screener Bolsa de Santiago | ZestyFinance",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Fintech / Institutional Terminal Style)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #181d26 0%, #202735 100%);
        padding: 16px 18px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8e99aa;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
    }
    .metric-sub {
        font-size: 0.82rem;
        font-weight: 500;
    }
    .positive { color: #00d084; }
    .negative { color: #ff4d4f; }
    .warning { color: #ffa726; }
    .neutral { color: #29b6f6; }
    
    .badge-bcs-official {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: rgba(41, 182, 246, 0.15);
        color: #29b6f6;
        border: 1px solid rgba(41, 182, 246, 0.35);
    }
    .badge-archetype {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: rgba(255, 167, 38, 0.15);
        color: #ffa726;
        border: 1px solid rgba(255, 167, 38, 0.35);
    }
    .badge-tax {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: rgba(0, 208, 132, 0.15);
        color: #00d084;
        border: 1px solid rgba(0, 208, 132, 0.35);
    }
    .concept-card {
        background: #1b202a;
        padding: 18px 22px;
        border-radius: 10px;
        border-left: 4px solid #29b6f6;
        margin-bottom: 16px;
    }
    .concept-card h4 {
        margin: 0 0 8px 0;
        color: #ffffff;
        font-size: 1.05rem;
    }
    .concept-formula {
        background: #12151b;
        padding: 6px 12px;
        border-radius: 6px;
        font-family: monospace;
        color: #00d084;
        display: inline-block;
        margin-bottom: 8px;
    }
    .concept-conclusion {
        background: rgba(0, 208, 132, 0.08);
        border: 1px solid rgba(0, 208, 132, 0.25);
        padding: 8px 14px;
        border-radius: 8px;
        margin-top: 8px;
        color: #e0f2fe;
        font-size: 0.9rem;
    }
    .checklist-card {
        background: #161b24;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .trap-box-warning {
        background: rgba(255, 77, 79, 0.08);
        border: 1px solid rgba(255, 77, 79, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }
    .trap-box-clean {
        background: rgba(0, 208, 132, 0.08);
        border: 1px solid rgba(0, 208, 132, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }
    .tax-box {
        background: rgba(41, 182, 246, 0.08);
        border: 1px solid rgba(41, 182, 246, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

def fmt_clp(val):
    if val is None or pd.isna(val):
        return "-"
    return f"${val:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")

def fmt_pct(val):
    if val is None or pd.isna(val):
        return "-"
    return f"{val:.2f}%"

# Session state initialization
if "watchlist_symbols" not in st.session_state:
    st.session_state["watchlist_symbols"] = list(INITIAL_PORTFOLIO_SYMBOLS)

if "dap_rate" not in st.session_state:
    st.session_state["dap_rate"] = 4.0

# Load full stock universe from Bolsa de Santiago
all_market_stocks = bcs_client.load_all_market_stocks()
all_nemos = sorted([s["NEMO"] for s in all_market_stocks if s.get("NEMO")])

# Sidebar Controls
st.sidebar.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=300&q=80", use_container_width=True)
st.sidebar.title("🏛️ Screener BCS")
st.sidebar.caption("Analizador Oficial de la Bolsa de Comercio de Santiago")
st.sidebar.markdown('<span class="badge-bcs-official">100% Datos Bolsa de Santiago</span>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🏦 Tasa de Referencia DAP")
sidebar_dap = st.sidebar.slider(
    "Tasa Depósito a Plazo Anual (%):",
    min_value=1.0,
    max_value=8.0,
    value=float(st.session_state["dap_rate"]),
    step=0.1,
    format="%.1f%%",
    help="Tasa anual de referencia de tu banco comercial. Afecta los spreads, el simulador y la Regla 1 del Checklist Institucional."
)
st.session_state["dap_rate"] = sidebar_dap

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Agregar Acción de la Bolsa")
selected_new_nemo = st.sidebar.selectbox(
    "Buscar entre 1.000+ acciones listadas:",
    ["-- Seleccionar Acción --"] + all_nemos,
    index=0
)

if st.sidebar.button("➕ Agregar a la Lista de Análisis", use_container_width=True):
    if selected_new_nemo and selected_new_nemo != "-- Seleccionar Acción --":
        if selected_new_nemo not in st.session_state["watchlist_symbols"]:
            st.session_state["watchlist_symbols"].append(selected_new_nemo)
            st.sidebar.success(f"{selected_new_nemo} agregado!")
            st.rerun()
        else:
            st.sidebar.info(f"{selected_new_nemo} ya está en la lista.")

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Presets Rápidos")
c_p1, c_p2 = st.sidebar.columns(2)
with c_p1:
    if st.button("💼 Mi Portafolio", use_container_width=True, help="Carga las 10 acciones iniciales de tu portafolio"):
        st.session_state["watchlist_symbols"] = list(INITIAL_PORTFOLIO_SYMBOLS)
        st.rerun()
with c_p2:
    if st.button("🏆 IPSA + Portafolio", use_container_width=True, help="Agrega principales acciones del IPSA a la lista"):
        for s in POPULAR_CHILEAN_STOCKS:
            if s not in st.session_state["watchlist_symbols"]:
                st.session_state["watchlist_symbols"].append(s)
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Sincronización en Vivo")
if st.sidebar.button("⚡ Sincronizar Cotizaciones BCS", use_container_width=True):
    with st.spinner("Descargando cotizaciones oficiales desde bolsadesantiago.com..."):
        bcs_client.sync_all_stocks_live()
        st.sidebar.success("Cotizaciones actualizadas!")
        st.rerun()

st.sidebar.caption(f"Acciones en análisis: {len(st.session_state['watchlist_symbols'])} | Tasa DAP: {st.session_state['dap_rate']:.1f}%")

# Build Screener Dataset
current_symbols = st.session_state["watchlist_symbols"]
df_screener = screener_engine.build_screener_table(current_symbols, benchmark_rf=st.session_state["dap_rate"])

# Ensure fallback columns if not present
if "Yield_Con_Credito_Pct" not in df_screener.columns:
    df_screener["Yield_Con_Credito_Pct"] = df_screener.get("Dividend_Yield_Pct", 0.0)
if "Credito_Tributario_CLP" not in df_screener.columns:
    df_screener["Credito_Tributario_CLP"] = 0.0
if "Arquetipo" not in df_screener.columns:
    df_screener["Arquetipo"] = "🐄 Vaca Lechera"
if "Indexacion" not in df_screener.columns:
    df_screener["Indexacion"] = "🇨🇱 CLP"
if "Presencia_107" not in df_screener.columns:
    df_screener["Presencia_107"] = "✅ Sí (10% Impuesto)"
if "Trap_Flags" not in df_screener.columns:
    df_screener["Trap_Flags"] = [[] for _ in range(len(df_screener))]
if "Checklist" not in df_screener.columns:
    df_screener["Checklist"] = [{"passed_count": 0, "status": "N/A", "rules": []} for _ in range(len(df_screener))]

# Header Section
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
    <div>
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">Screener & Analizador de Acciones Chilenas</h1>
        <p style="margin: 4px 0 0 0; color: #8e99aa; font-size: 0.95rem;">
            Estrategia Institucional de Dividendos, Crédito Tributario (Art. 14 A) & Valoración | Fuente oficial: <b>bolsadesantiago.com</b>
        </p>
    </div>
    <div>
        <span class="badge-bcs-official">🏛️ Oficial Bolsa de Comercio de Santiago</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top KPI Summary Cards Row
top_yield_stock = df_screener.sort_values(by="Dividend_Yield_Pct", ascending=False).iloc[0] if not df_screener.empty else None
best_score_stock = df_screener.sort_values(by="Score_Dividendo", ascending=False).iloc[0] if not df_screener.empty else None
buy_signals_count = len(df_screener[df_screener["Senal"].str.contains("COMPRA", na=False)])
avg_yield = df_screener["Dividend_Yield_Pct"].mean() if not df_screener.empty else 0.0
avg_yield_con_tax = df_screener["Yield_Con_Credito_Pct"].mean() if not df_screener.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Acciones en Seguimiento</div>
        <div class="metric-value neutral">{len(df_screener)}</div>
        <div class="metric-sub neutral">Universo: {len(all_nemos)} listadas</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Yield Promedio (TTM)</div>
        <div class="metric-value positive">{avg_yield:.2f}%</div>
        <div class="metric-sub positive">Bruto c/Crédito: <b>{avg_yield_con_tax:.2f}%</b></div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    if top_yield_stock is not None:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Mayor Dividend Yield</div>
            <div class="metric-value positive">{top_yield_stock['Dividend_Yield_Pct']:.2f}%</div>
            <div class="metric-sub neutral">{top_yield_stock['NEMO']} (${top_yield_stock['Precio_CLP']:,.0f})</div>
        </div>
        """, unsafe_allow_html=True)

with k4:
    if best_score_stock is not None:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Mejor Calificación (Score)</div>
            <div class="metric-value positive">{best_score_stock['Score_Dividendo']}/100</div>
            <div class="metric-sub positive">{best_score_stock['NEMO']} ({best_score_stock['Arquetipo']})</div>
        </div>
        """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Señales de Compra</div>
        <div class="metric-value positive">{buy_signals_count} acciones</div>
        <div class="metric-sub positive">Score Dividendo >= 72 pts</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔎 Screener Multicriterio & Ranking",
    "📊 Comparador Head-to-Head & Matriz",
    "🔍 Ficha Técnica, Diagnóstico & Glosario",
    "🎯 Simulador de Compra & Tasa DAP"
])

# ==========================================
# TAB 1: SCREENER MULTICRITERIO
# ==========================================
with tab1:
    st.subheader("🔎 Filtros Multicriterio de Acciones Chilenas")
    st.caption("Ajusta los filtros fundamentales e institucionales para descubrir las mejores oportunidades de dividendos en la Bolsa de Santiago.")

    # Filter controls - Row 1
    f_c1, f_c2, f_c3 = st.columns(3)
    with f_c1:
        min_yield = st.slider("Mínimo Dividend Yield Neto (%):", 0.0, 15.0, 0.0, 0.5)
    with f_c2:
        max_pe = st.slider("Máximo P/E (Precio / Utilidad):", 5.0, 50.0, 30.0, 1.0)
    with f_c3:
        min_roe = st.slider("Mínimo ROE (%):", 0.0, 30.0, 0.0, 1.0)

    # Filter controls - Row 2 (Archetype, Signal, Trap Toggle)
    f_c4, f_c5, f_c6 = st.columns(3)
    with f_c4:
        signal_filter = st.selectbox("Señal de Inversión:", ["Todas", "Solo Compra 🟢", "Mantener 🟡", "Precaución 🔴"])
    with f_c5:
        arquetipo_filter = st.selectbox(
            "Arquetipo Dividendero:",
            ["Todos", "🐄 Vaca Lechera", "🚀 Dividend Growth", "📦 Holding con Descuento", "⏳ Cíclica / Commodity"]
        )
    with f_c6:
        hide_traps = st.checkbox("🛡️ Ocultar Trampas de Dividendos (Payout > 100% o ROE < 4%)", value=False)

    # Apply filters
    filtered_df = df_screener.copy()
    if min_yield > 0:
        filtered_df = filtered_df[filtered_df["Dividend_Yield_Pct"] >= min_yield]
    if max_pe < 50.0:
        filtered_df = filtered_df[(filtered_df["PE_Ratio"].isna()) | (filtered_df["PE_Ratio"] <= max_pe)]
    if min_roe > 0:
        filtered_df = filtered_df[(filtered_df["ROE_Pct"].isna()) | (filtered_df["ROE_Pct"] >= min_roe)]
    if signal_filter == "Solo Compra 🟢":
        filtered_df = filtered_df[filtered_df["Senal"].str.contains("COMPRA", na=False)]
    elif signal_filter == "Mantener 🟡":
        filtered_df = filtered_df[filtered_df["Senal"].str.contains("MANTENER", na=False)]
    elif signal_filter == "Precaución 🔴":
        filtered_df = filtered_df[filtered_df["Senal"].str.contains("PRECAUCIÓN", na=False)]
    if arquetipo_filter != "Todos":
        filtered_df = filtered_df[filtered_df["Arquetipo"] == arquetipo_filter]
    if hide_traps:
        filtered_df = filtered_df[filtered_df["Trap_Flags"].apply(len) == 0]

    st.markdown(f"**Resultados:** Mostrando **{len(filtered_df)}** de **{len(df_screener)}** acciones analizadas.")

    # Helper columns for display
    filtered_df["Checklist_Fmt"] = filtered_df["Checklist"].apply(
        lambda c: f"{c.get('passed_count', 0)}/5 ({c.get('status', '')})"
    )
    filtered_df["Trampa_Fmt"] = filtered_df["Trap_Flags"].apply(
        lambda f: f"⚠️ {len(f)} Alerta(s)" if len(f) > 0 else "✅ Saludable"
    )

    display_cols = [
        "NEMO", "Nombre", "Arquetipo", "Indexacion", "Precio_CLP",
        "Dividend_Yield_Pct", "Yield_Con_Credito_Pct", "Score_Dividendo", "Senal",
        "Checklist_Fmt", "Trampa_Fmt", "PE_Ratio", "PB_Ratio", "ROE_Pct", "Payout_Ratio_Pct", "Presencia_107"
    ]
    
    df_view = filtered_df[display_cols].copy()
    df_view["Precio_CLP"] = df_view["Precio_CLP"].apply(fmt_clp)
    df_view["Dividend_Yield_Pct"] = df_view["Dividend_Yield_Pct"].apply(lambda x: f"{x:.2f}%")
    df_view["Yield_Con_Credito_Pct"] = df_view["Yield_Con_Credito_Pct"].apply(lambda x: f"{x:.2f}%")
    df_view["ROE_Pct"] = df_view["ROE_Pct"].apply(fmt_pct)
    df_view["Payout_Ratio_Pct"] = df_view["Payout_Ratio_Pct"].apply(fmt_pct)
    df_view["PE_Ratio"] = df_view["PE_Ratio"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) else "-")
    df_view["PB_Ratio"] = df_view["PB_Ratio"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "-")
    df_view["Score_Dividendo"] = df_view["Score_Dividendo"].apply(lambda x: f"{x}/100")

    rename_map = {
        "NEMO": "Acción",
        "Nombre": "Razón Social",
        "Arquetipo": "Arquetipo",
        "Indexacion": "Escudo Inflación",
        "Precio_CLP": "Precio BCS",
        "Dividend_Yield_Pct": "Yield Neto (TTM)",
        "Yield_Con_Credito_Pct": "Yield c/Crédito (14A)",
        "Score_Dividendo": "Score Calidad",
        "Senal": "Señal Dividendo",
        "Checklist_Fmt": "5 Reglas Oro",
        "Trampa_Fmt": "Semáforo Trampa",
        "PE_Ratio": "P/U",
        "PB_Ratio": "P/VL",
        "ROE_Pct": "ROE",
        "Payout_Ratio_Pct": "Payout %",
        "Presencia_107": "Art. 107 LIR"
    }

    st.dataframe(df_view.rename(columns=rename_map), use_container_width=True, hide_index=True)

    st.markdown("---")
    sc_c1, sc_c2 = st.columns([1, 1])

    with sc_c1:
        st.subheader("🎯 Mapa de Oportunidad: Dividend Yield vs Valuación (P/U)")
        st.caption("Cuadrante superior izquierdo = Alto rendimiento por dividendo y múltiplo P/U atractivo.")
        
        valid_plot_df = filtered_df[filtered_df["PE_Ratio"].notna() & (filtered_df["PE_Ratio"] > 0) & (filtered_df["PE_Ratio"] < 50)]
        if not valid_plot_df.empty:
            fig_bubble = px.scatter(
                valid_plot_df,
                x="PE_Ratio",
                y="Dividend_Yield_Pct",
                size="Score_Dividendo",
                color="Arquetipo",
                text="NEMO",
                labels={"PE_Ratio": "Múltiplo P/U (Veces)", "Dividend_Yield_Pct": "Dividend Yield (%)"},
                template="plotly_dark",
                hover_data=["Nombre", "Score_Dividendo", "Yield_Con_Credito_Pct", "Senal"]
            )
            fig_bubble.update_traces(textposition='top center')
            fig_bubble.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("No hay suficientes datos de P/U para graficar en los filtros actuales.")

    with sc_c2:
        st.subheader("🏆 Ranking de Calidad de Dividendos (Score 0-100)")
        st.caption("Puntuación algorítmica considerando Yield, cobertura de utilidades, ROE y múltiplos de precio.")
        
        fig_score = px.bar(
            filtered_df.sort_values(by="Score_Dividendo", ascending=True),
            x="Score_Dividendo",
            y="NEMO",
            orientation="h",
            color="Score_Dividendo",
            color_continuous_scale="RdYlGn",
            text="Score_Dividendo",
            template="plotly_dark"
        )
        fig_score.update_traces(texttemplate='%{text} pts', textposition='outside')
        fig_score.update_layout(margin=dict(l=20, r=20, t=30, b=20), xaxis_title="Puntos (0-100)", yaxis_title="Acción")
        st.plotly_chart(fig_score, use_container_width=True)

# ==========================================
# TAB 2: COMPARADOR HEAD-TO-HEAD & MATRIZ
# ==========================================
with tab2:
    st.subheader("📊 Comparador Head-to-Head & Matriz Institucional")
    st.caption("Compara lado a lado arquetipos, rendimiento tributario, ratios de solvencia y checklist de reglas de oro.")

    compare_selection = st.multiselect(
        "Selecciona las acciones a comparar:",
        options=current_symbols,
        default=current_symbols[:4] if len(current_symbols) >= 4 else current_symbols
    )

    if compare_selection:
        comp_df = df_screener[df_screener["NEMO"].isin(compare_selection)].copy()

        # Side-by-side bar chart
        fig_comp_bars = go.Figure()
        fig_comp_bars.add_trace(go.Bar(
            name='Dividend Yield Neto (%)',
            x=comp_df['NEMO'],
            y=comp_df['Dividend_Yield_Pct'],
            marker_color='#00d084'
        ))
        fig_comp_bars.add_trace(go.Bar(
            name='Yield c/Crédito Fiscal 14A (%)',
            x=comp_df['NEMO'],
            y=comp_df['Yield_Con_Credito_Pct'],
            marker_color='#29b6f6'
        ))
        fig_comp_bars.add_trace(go.Bar(
            name='ROE (%)',
            x=comp_df['NEMO'],
            y=comp_df['ROE_Pct'],
            marker_color='#ffa726'
        ))
        fig_comp_bars.add_trace(go.Bar(
            name='P/U (x)',
            x=comp_df['NEMO'],
            y=comp_df['PE_Ratio'],
            marker_color='#ab47bc'
        ))
        fig_comp_bars.update_layout(
            barmode='group',
            xaxis_title="Acción",
            yaxis_title="Valor de Métrica",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=35, b=20)
        )
        st.plotly_chart(fig_comp_bars, use_container_width=True)

        # Comparative Table
        st.markdown("#### 📋 Matriz Comparativa Detallada")
        metrics_rows = [
            ("Empresa / Razón Social", lambda r: r["Nombre"]),
            ("Arquetipo Dividendero", lambda r: r["Arquetipo"]),
            ("Escudo Inflacionario", lambda r: r["Indexacion"]),
            ("Presencia Bursátil (Art. 107 LIR)", lambda r: r["Presencia_107"]),
            ("Precio de Cierre (BCS)", lambda r: fmt_clp(r["Precio_CLP"])),
            ("Dividend Yield Neto (TTM)", lambda r: f"{r['Dividend_Yield_Pct']:.2f}%"),
            ("Crédito Tributario Est. / Acción", lambda r: fmt_clp(r["Credito_Tributario_CLP"])),
            ("Yield Bruto c/Crédito (Art. 14 A)", lambda r: f"{r['Yield_Con_Credito_Pct']:.2f}%"),
            ("Dividendo Líquido Anual / Acción", lambda r: fmt_clp(r["Div_TTM_CLP"])),
            ("Payout Ratio (%)", lambda r: fmt_pct(r["Payout_Ratio_Pct"])),
            ("P/U (Precio/Utilidad)", lambda r: f"{r['PE_Ratio']:.1f}x" if pd.notna(r["PE_Ratio"]) else "-"),
            ("P/VL (Bolsa/Libro)", lambda r: f"{r['PB_Ratio']:.2f}x" if pd.notna(r["PB_Ratio"]) else "-"),
            ("ROE (Rentabilidad Patrimonio)", lambda r: fmt_pct(r["ROE_Pct"])),
            ("Margen Neto (%)", lambda r: fmt_pct(r["Margen_Neto_Pct"])),
            ("Utilidad x Acción 12M (EPS)", lambda r: fmt_clp(r["EPS_12M_CLP"])),
            ("Valor Libro por Acción", lambda r: fmt_clp(r["Valor_Libro_CLP"])),
            ("Score Dividendo (0-100)", lambda r: f"{r['Score_Dividendo']} pts"),
            ("Señal de Inversión", lambda r: r["Senal"]),
            ("Checklist 5 Reglas Institucionales", lambda r: f"{r['Checklist']['passed_count']}/5 ({r['Checklist']['status']})"),
            ("Semáforo Trampa de Dividendo", lambda r: ("⚠️ " + "; ".join(r["Trap_Flags"])) if r["Trap_Flags"] else "✅ Sin alertas aparentes")
        ]

        table_dict = {"Métrica": [m[0] for m in metrics_rows]}
        for _, row in comp_df.iterrows():
            sym = row["NEMO"]
            table_dict[sym] = [m[1](row) for m in metrics_rows]

        st.dataframe(pd.DataFrame(table_dict), use_container_width=True, hide_index=True)

        # EDUCATIONAL SECTION FOR COMPARATIVE MATRIX
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📖 ¿Cómo Analizar y Concluir con esta Matriz Comparativa? (Guía del Inversionista Experto)", expanded=True):
            st.markdown("""
            A continuación se detallan las **reglas clave de decisión** para comparar las acciones de la matriz y elegir la opción más conveniente para tu estrategia:

            1. **Los 4 Arquetipos de Acciones en Chile:**
               - **🐄 Vacas Lecheras (Generadoras de Flujo):** Empresas de demanda inelástica (eléctricas como Enel Generación o Pehuenche, gas como Lipigas, AFP Habitat). Crecen poco pero entregan yield alto (> 7%) y recurrente. Ideales para vivir de rentas.
               - **🚀 Dividend Growth (Crecimiento Compuesto):** Empresas líderes que aumentan su dividendo año a año (Banco de Chile, Cencosud Shopping, Andina-A, Mallplaza). Ofrecen un yield inicial moderado (4%-6%) que en 5 años se duplica por crecimiento del negocio.
               - **📦 Holdings con Descuento:** Sociedades matrices (Quiñenco, Almendral, AAISA) que cotizan con un descuento del 20% al 40% sobre el valor liquidativo de sus filiales (NAV).
               - **⏳ Cíclicas / Commodities:** Empresas expuestas a precios internacionales (SQM litio, CAP hierro, CMPC celulosa, Vapores fletes). Pagan dividendos gigantescos en la cima del ciclo y casi cero en la parte baja. No proyectar su yield a perpetuidad.

            2. **El Crédito de Primera Categoría (Art. 14 A LIR):**
               - En Chile rige el régimen semi-integrado. Las empresas pagan un 27% de impuesto corporativo antes de pagarte el dividendo.
               - Al recibir el dividendo, tienes derecho a un **crédito imputable del 65% de ese impuesto corporativo** en tu Formulario 22 del SII.
               - Esto significa que una acción con un **Dividend Yield en pantalla de 6.5%**, en realidad te entrega un rendimiento bruto antes de impuestos de **más del 8.0%**.

            3. **Presencia Bursátil (Art. 107 LIR):**
               - Si la acción tiene presencia bursátil (como Banco de Chile, Enel Generación, Lipigas), cualquier ganancia de capital al vender tributa con una **tasa única preferencial del 10%** en lugar de sumarse a tu tasa marginal del Global Complementario (que puede llegar al 40%).

            4. **¿Quién tiene el dividendo más SEGURO y SOSTENIBLE?**
               - **Payout 30% a 70%:** Zona dorada. La empresa genera utilidades de sobra para respaldar el dividendo.
               - **Payout > 100%: ⚠️ Alerta de Trampa de Dividendo.** La empresa está pagando más dinero del que ganó en el año, descapitalizándose.

            💡 **Conclusión Institucional:** La cartera perfecta de dividendos equilibra **Vacas Lecheras** indexadas a UF para ingresos pasivos inmediatos con **Dividend Growth** para proteger el patrimonio del paso del tiempo y la inflación.
            """)
    else:
        st.info("Selecciona al menos una acción para comenzar la comparación.")

# ==========================================
# TAB 3: FICHA TÉCNICA, DIAGNÓSTICO & GLOSARIO
# ==========================================
with tab3:
    st.subheader("🔍 Ficha Técnica & Diagnóstico Fundamental")
    st.caption("Examina cualquier acción listada con su historial completo de dividendos, crédito tributario y razones financieras oficiales de la Bolsa de Santiago.")

    diag_nemo = st.selectbox("Seleccionar acción para diagnóstico detallado:", all_nemos, index=all_nemos.index("CHILE") if "CHILE" in all_nemos else 0)

    # Check if stock data is cached
    ratios_cache = bcs_client.load_cached_ratios()
    divs_cache = bcs_client.load_cached_dividends()
    has_ratios = diag_nemo in ratios_cache
    has_divs = diag_nemo in divs_cache

    col_diag_btn1, col_diag_btn2 = st.columns([1, 3])
    with col_diag_btn1:
        if st.button(f"⚡ Analizar {diag_nemo} en Vivo", use_container_width=True, help="Consulta directamente la Bolsa de Santiago en tiempo real"):
            with st.spinner(f"Consultando cotización, razones financieras y dividendos de {diag_nemo} en bolsadesantiago.com..."):
                bcs_client.fetch_live_stock_analysis([diag_nemo])
                if diag_nemo not in st.session_state["watchlist_symbols"]:
                    st.session_state["watchlist_symbols"].append(diag_nemo)
                st.success(f"¡Datos de {diag_nemo} extraídos con éxito!")
                st.rerun()

    report = screener_engine.get_detailed_stock_report(diag_nemo, benchmark_rf=st.session_state["dap_rate"])
    summary_info = report["summary"]
    parsed_ratios = report["parsed_ratios"]
    events = report["events"]
    yearly_divs = report["yearly_dividends"]
    checklist = summary_info.get("Checklist", {})
    trap_flags = summary_info.get("Trap_Flags", [])

    st.markdown("---")

    # Sub-tabs for Ficha Técnica: 1. Diagnóstico Experto, 2. Historial Dividendos, 3. Glosario Didáctico
    subtab_ficha, subtab_hist, subtab_glosario = st.tabs([
        "📊 Diagnóstico & Ratios de la Acción",
        "📜 Historial Oficial de Dividendos",
        "🎓 Glosario Didáctico: ¿Qué es y cómo se analiza cada concepto?"
    ])

    with subtab_ficha:
        # Stock Archetype & Protection Header Badges
        st.markdown(f"""
        <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap;">
            <h2 style="margin: 0;">{summary_info.get('NEMO')} - {summary_info.get('Nombre')}</h2>
            <span class="badge-archetype">{summary_info.get('Arquetipo')}</span>
            <span class="badge-tax">{summary_info.get('Indexacion')}</span>
            <span class="badge-bcs-official">{summary_info.get('Presencia_107')}</span>
        </div>
        """, unsafe_allow_html=True)

        # Metric cards for single stock
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Precio de Cierre (BCS)", fmt_clp(summary_info.get("Precio_CLP")), f"{summary_info.get('Variacion_Pct', 0):+.2f}% hoy")
            st.metric("Punta Compra (Bid)", fmt_clp(summary_info.get("Bid_CLP")))
        with d2:
            st.metric("Dividend Yield Neto", f"{summary_info.get('Dividend_Yield_Pct', 0):.2f}%")
            st.metric("Yield Bruto c/Crédito 14A", f"{summary_info.get('Yield_Con_Credito_Pct', 0):.2f}%")
        with d3:
            st.metric("P/U (Precio/Utilidad)", f"{summary_info.get('PE_Ratio', 0):.1f}x" if summary_info.get("PE_Ratio") else "-")
            st.metric("P/VL (Bolsa/Libro)", f"{summary_info.get('PB_Ratio', 0):.2f}x" if summary_info.get("PB_Ratio") else "-")
        with d4:
            st.metric("Score Calidad Dividendo", f"{summary_info.get('Score_Dividendo', 0)} / 100")
            st.metric("Señal de Inversión", summary_info.get("Senal", "-"))

        st.markdown("---")

        # CHECKLIST INSTITUCIONAL (5 REGLAS DE ORO)
        c_chk_head1, c_chk_head2 = st.columns([3, 2])
        with c_chk_head1:
            st.subheader("📋 Checklist Institucional del Inversionista Experto")
            st.caption(f"Evaluación de calidad con Tasa DAP de referencia fijada en **{st.session_state['dap_rate']:.1f}% anual**.")
        with c_chk_head2:
            tab3_dap = st.number_input(
                "🏦 Tasa DAP Seleccionable (% anual):",
                min_value=1.0,
                max_value=10.0,
                value=float(st.session_state.get("dap_rate", 4.0)),
                step=0.1,
                key="tab3_dap_selector",
                help="Ajusta aquí la tasa exacta de tu banco para recalcular de inmediato la Regla 1 del Checklist."
            )
            if tab3_dap != st.session_state["dap_rate"]:
                st.session_state["dap_rate"] = tab3_dap
                st.rerun()

        passed_rules = checklist.get("passed_count", 0)
        status_rules = checklist.get("status", "Baja Convicción")
        status_color = "#00d084" if passed_rules >= 4 else "#ffa726" if passed_rules >= 2 else "#ff4d4f"

        st.markdown(f"""
        <div class="checklist-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">Cumplimiento de Reglas de Oro: {passed_rules} de 5</span>
                <span style="font-size: 0.95rem; font-weight: 700; color: {status_color}; border: 1px solid {status_color}; padding: 3px 12px; border-radius: 12px;">{status_rules}</span>
            </div>
        """, unsafe_allow_html=True)

        for rule in checklist.get("rules", []):
            icon = "✅" if rule["cumple"] else "❌"
            rule_color = "#00d084" if rule["cumple"] else "#ff4d4f"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>{icon} <span style="font-weight: 500;">{rule['regla']}</span></div>
                <div style="color: {rule_color}; font-weight: 600; font-size: 0.85rem;">{rule['detalle']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # SEMÁFORO DE TRAMPA DE DIVIDENDOS (DIVIDEND TRAP)
        st.subheader("🚨 Semáforo de Trampa de Dividendos (Dividend Trap Alert)")
        if trap_flags:
            st.markdown(f"""
            <div class="trap-box-warning">
                <h4 style="color: #ff4d4f; margin: 0 0 6px 0;">⚠️ Alerta de Dividend Trap Detectada ({len(trap_flags)} factores de riesgo)</h4>
                <p style="margin: 0 0 8px 0; font-size: 0.9rem; color: #e0e0e0;">
                    Este rendimiento por dividendo podría ser insostenible o artificial. Presta atención a los siguientes factores:
                </p>
                <ul>
            """, unsafe_allow_html=True)
            for flag in trap_flags:
                st.markdown(f"<li style='color: #ff9999; font-weight: 500;'>{flag}</li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="trap-box-clean">
                <h4 style="color: #00d084; margin: 0 0 4px 0;">✅ Sin Alertas Aparentes de Trampa de Dividendo</h4>
                <p style="margin: 0; font-size: 0.9rem; color: #ccefe3;">
                    El Payout Ratio, el ROE y la valuación de la empresa se encuentran dentro de rangos operativos saludables.
                </p>
            </div>
            """, unsafe_allow_html=True)

        # TRATAMIENTO TRIBUTARIO CHILENO (ART. 14 A & ART. 107 LIR)
        st.subheader("🏛️ Tratamiento Tributario Chileno (SII / Ley de la Renta)")
        st.caption("Impacto real de los impuestos en tu dividendo y ganancia de capital.")

        t_c1, t_c2 = st.columns(2)
        with t_c1:
            div_ttm = summary_info.get("Div_TTM_CLP", 0.0)
            tax_credit = summary_info.get("Credito_Tributario_CLP", 0.0)
            div_bruto = div_ttm + tax_credit

            st.markdown(f"""
            <div class="tax-box">
                <h4 style="color: #29b6f6; margin: 0 0 8px 0;">🧾 Impuesto de Primera Categoría (Art. 14 A LIR)</h4>
                <p style="font-size: 0.88rem; margin-bottom: 10px;">
                    En el régimen semi-integrado, la empresa pagó 27% corporativo. En tu declaración F22 del SII recibes un <b>crédito imputable del 65%</b>:
                </p>
                <div style="font-size: 0.9rem; line-height: 1.8;">
                    • <b>Dividendo Líquido Pagado:</b> {fmt_clp(div_ttm)} / acción<br>
                    • <b>Crédito Tributario a Favor (F22):</b> <span style="color: #00d084;">+{fmt_clp(tax_credit)} / acción</span><br>
                    • <b>Dividendo Bruto Imputable:</b> <b>{fmt_clp(div_bruto)} / acción</b><br>
                    • <b>Dividend Yield Efectivo c/Crédito:</b> <span style="color: #00d084; font-weight: 700;">{summary_info.get('Yield_Con_Credito_Pct', 0):.2f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with t_c2:
            presencia_status = summary_info.get("Presencia_107")
            st.markdown(f"""
            <div class="tax-box">
                <h4 style="color: #29b6f6; margin: 0 0 8px 0;">🛡️ Presencia Bursátil (Art. 107 LIR)</h4>
                <p style="font-size: 0.88rem; margin-bottom: 10px;">
                    Beneficio tributario exclusivo para acciones con alta liquidez transaccional en la Bolsa de Santiago:
                </p>
                <div style="font-size: 0.9rem; line-height: 1.8;">
                    • <b>Estado para {diag_nemo}:</b> <b>{presencia_status}</b><br>
                    • <b>Ganancia de Capital (Venta de acciones):</b> Tributa con <b>impuesto único del 10%</b> (no se suma a tu tramo marginal de Global Complementario de hasta 40%).<br>
                    • <b>Liquidez de Salida:</b> Permite desarmar o ajustar posiciones con mínimo spread de puntas compra/venta.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Resumen de Razones Financieras Oficiales")
        r_c1, r_c2, r_c3 = st.columns(3)
        with r_c1:
            st.write(f"**ROE (Rentab. Patrimonio):** {fmt_pct(summary_info.get('ROE_Pct'))}")
            st.write(f"**Margen Neto:** {fmt_pct(summary_info.get('Margen_Neto_Pct'))}")
        with r_c2:
            st.write(f"**Utilidad por Acción (EPS 12M):** {fmt_clp(summary_info.get('EPS_12M_CLP'))}")
            st.write(f"**Valor Libro por Acción:** {fmt_clp(summary_info.get('Valor_Libro_CLP'))}")
        with r_c3:
            st.write(f"**Payout Ratio:** {fmt_pct(summary_info.get('Payout_Ratio_Pct'))}")
            st.write(f"**Deuda / Patrimonio:** {summary_info.get('Deuda_Patrimonio', '-')}")

    with subtab_hist:
        st.subheader(f"📜 Historial Oficial de Dividendos: {diag_nemo}")
        if events:
            d_c1, d_c2 = st.columns([1, 1])
            with d_c1:
                df_hist = pd.DataFrame(list(yearly_divs.items()), columns=["Año", "Dividendo_Total_CLP"])
                df_hist = df_hist[df_hist["Año"] >= 2012]
                fig_hist = px.bar(
                    df_hist,
                    x="Año",
                    y="Dividendo_Total_CLP",
                    title=f"Evolución Anual de Dividendos por Acción ($ CLP) - {diag_nemo}",
                    template="plotly_dark",
                    text="Dividendo_Total_CLP"
                )
                fig_hist.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
                fig_hist.update_layout(margin=dict(l=20, r=20, t=35, b=20), yaxis_title="Dividendo Anual ($ CLP)")
                st.plotly_chart(fig_hist, use_container_width=True)

            with d_c2:
                st.markdown("##### 📅 Eventos de Pago Recientes (Fecha de Corte y Pago)")
                ev_df = pd.DataFrame(events)[["fec_pago", "fec_lim", "val_acc", "moneda", "descrip_vc"]].copy()
                ev_df.columns = ["Fecha Pago", "Fecha Corte", "Monto/Acción", "Moneda", "Descripción / Tipo"]
                st.dataframe(ev_df.head(15), use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay dividendos registrados aún para {diag_nemo}. Haz clic en '⚡ Analizar {diag_nemo} en Vivo' para sincronizarlos directamente de la Bolsa.")

    with subtab_glosario:
        st.subheader("🎓 Guía Didáctica: ¿Qué significa cada concepto y cómo se analiza?")
        st.caption("Aprende a interpretar cada indicador como un analista profesional de renta variable chilena.")

        # ROE
        st.markdown("""
        <div class="concept-card">
            <h4>1. ROE (Return on Equity / Rentabilidad sobre el Patrimonio)</h4>
            <div class="concept-formula">Fórmula: Utilidad Neta / Patrimonio Contable × 100</div>
            <p>
                <b>¿Qué es?</b> Mide la eficiencia y capacidad del equipo directivo para generar beneficios con el dinero propio de los accionistas (sin considerar deuda).
            </p>
            <p>
                <b>¿Cómo se analiza en Chile?</b>
                <ul>
                    <li><b>> 15% (Excelente):</b> Empresas con fuertes ventajas competitivas (ej. Banco de Chile con 13.9%, Lipigas con 18.2%). Son negocios muy rentables.</li>
                    <li><b>10% a 15% (Bueno):</b> Rentabilidad sólida y saludable.</li>
                    <li><b>5% a 10% (Moderado):</b> Rentabilidad promedio en industrias intensivas en capital (centros comerciales, eléctricas).</li>
                    <li><b>< 5% o Negativo (Peligro):</b> Negocio poco rentable o en pérdidas. Cuidado si reparte dividendos, pues no se sustentan en utilidades reales.</li>
                </ul>
            </p>
            <div class="concept-conclusion">
                💡 <b>Conclusión para comprar/vender:</b> Siempre prefiere empresas con <b>ROE > 10%</b>. Un alto ROE asegura que la empresa puede seguir pagando dividendos año tras año sin descapitalizarse.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Payout Ratio
        st.markdown("""
        <div class="concept-card">
            <h4>2. Payout Ratio (Tasa de Reparto de Dividendos)</h4>
            <div class="concept-formula">Fórmula: (Dividendo Anual por Acción / Utilidad por Acción EPS) × 100</div>
            <p>
                <b>¿Qué es?</b> El porcentaje de las ganancias netas de la empresa que se devuelve en efectivo a los accionistas como dividendo.
            </p>
            <p>
                <b>¿Cómo se analiza?</b>
                <ul>
                    <li><b>Menor a 30%:</b> Muy conservador (ej. Cencosud Shopping con 36%, AAISA con 25%). La empresa retiene casi todo su dinero para reinvertir o pagar deuda. Mucho margen de seguridad.</li>
                    <li><b>30% a 70% (La Zona Dorada):</b> Rango óptimo y equilibrado (ej. Enel Generación con 67.5%). La empresa reparte un dividendo atractivo y conserva suficiente capital para operar.</li>
                    <li><b>70% a 90%:</b> Típico en empresas maduras (bancos y servicios básicos). Sostenible siempre que el negocio no tenga caídas bruscas.</li>
                    <li><b>Mayor a 100%: ⚠️ Alerta de Trampa de Dividendos (Dividend Trap):</b> La empresa está pagando más en dividendos de lo que ganó en el año (ej. Quiñenco al 100.8% o Andina). Se financia consumiendo reservas acumuladas o tomando deuda. Es un dividendo insostenible a largo plazo.</li>
                </ul>
            </p>
            <div class="concept-conclusion">
                💡 <b>Conclusión para comprar/vender:</b> Busca empresas en el rango de <b>40% a 75%</b>. Si ves un Payout > 100%, anticipa que el dividendo del próximo año podría ser recortado.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Dividend Yield
        cur_dap = float(st.session_state.get("dap_rate", 4.0))
        st.markdown(f"""
        <div class="concept-card">
            <h4>3. Dividend Yield (Rentabilidad por Dividendo)</h4>
            <div class="concept-formula">Fórmula: (Dividendo Anual por Acción TTM / Precio Actual de la Acción) × 100</div>
            <p>
                <b>¿Qué es?</b> La tasa de interés anualizada que recibes en efectivo por comprar la acción al precio de cotización de hoy.
            </p>
            <p>
                <b>¿Cómo se analiza?</b> Debe compararse siempre contra la <b>tasa de los Depósitos a Plazo (DAP)</b> y renta fija bancaria (actualmente calibrada en tu sistema en <b>{cur_dap:.1f}% anual</b>).
                <ul>
                    <li><b>Spread sobre Renta Fija:</b> Una buena acción dividendera debe pagar al menos la tasa del DAP + 1.5% adicional (ej. con DAP a {cur_dap:.1f}%, la meta institucional es rendir <b>>= {cur_dap + 1.5:.1f}%</b>).</li>
                    <li>Si una acción paga <b>7% a 8.5%</b> (como Quiñenco, Lipigas, Pehuenche o Habitat), te ofrece un flujo muy superior a un depósito a plazo tradicional.</li>
                    <li><b>⚠️ Ojo con el efecto trampa:</b> Si el precio de la acción cae estrepitosamente por problemas graves de la empresa, el Dividend Yield subirá artificialmente. Comprueba que el dividendo no esté a punto de suspenderse.</li>
                </ul>
            </p>
            <div class="concept-conclusion">
                💡 <b>Conclusión para comprar/vender:</b> Busca empresas que superen con holgura a la tasa DAP seleccionada ({cur_dap:.1f}%) manteniendo un Payout sostenible (< 75%).
            </div>
        </div>
        """, unsafe_allow_html=True)

        # P/E Ratio
        st.markdown("""
        <div class="concept-card">
            <h4>4. P/U (Relación Precio / Utilidad o P/E Ratio)</h4>
            <div class="concept-formula">Fórmula: Precio de la Acción / Utilidad por Acción en 12 Meses (EPS)</div>
            <p>
                <b>¿Qué es?</b> Indica cuántos años de ganancias de la empresa estás pagando al comprar la acción.
            </p>
            <p>
                <b>¿Cómo se analiza en el mercado chileno?</b>
                <ul>
                    <li><b>< 10x (Muy Barata):</b> Empresas que cotizan a múltiplos deprimidos (ej. AAISA con 6.1x, Enel Generación con 8.8x, Quiñenco con 9.7x). Ofrecen alto margen de seguridad.</li>
                    <li><b>10x a 15x (Valoración Justa / Razonable):</b> Típico de empresas estables en Chile (Lipigas 11.3x, Cencosud Shopping 11.4x, Banco de Chile 15.0x).</li>
                    <li><b>> 20x (Cara / Sobrevalorada):</b> Estás pagando mucho por cada peso de utilidad, a menos que la empresa tenga un crecimiento extraordinario.</li>
                </ul>
            </p>
            <div class="concept-conclusion">
                💡 <b>Conclusión para comprar/vender:</b> En una estrategia dividendera, comprar acciones con <b>P/U menor a 15x</b> te protege de caídas fuertes en el precio.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # P/B Ratio
        st.markdown("""
        <div class="concept-card">
            <h4>5. P/VL (Relación Bolsa / Valor Libro o P/B Ratio)</h4>
            <div class="concept-formula">Fórmula: Precio de Mercado / Valor Libro Contable por Acción</div>
            <p>
                <b>¿Qué es?</b> Compara el valor en bolsa de la empresa contra el valor contable de todos sus activos netos de deudas.
            </p>
            <p>
                <b>¿Cómo se analiza?</b>
                <ul>
                    <li><b>< 1.0x (Descuento Patrimonial):</b> La empresa vale en bolsa MENOS de lo que valen sus activos contables (ej. Quiñenco con 0.74x o AAISA con 0.96x). Es una compra con descuento implícito de activos.</li>
                    <li><b>1.0x a 2.5x:</b> Valoración normal para empresas con activos tangibles.</li>
                    <li><b>> 4.0x:</b> La empresa cotiza a gran premio sobre sus libros (ej. Pehuenche con 11.5x o AFP Habitat con 3.8x).</li>
                </ul>
            </p>
            <div class="concept-conclusion">
                💡 <b>Conclusión para comprar/vender:</b> Las acciones con <b>P/VL cercano o inferior a 1.0x</b> tienen un piso de valor patrimonial que las hace muy defensivas.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 6. Los 4 Arquetipos
        st.markdown("""
        <div class="concept-card">
            <h4>6. Los 4 Arquetipos de Acciones en la Bolsa de Santiago</h4>
            <div class="concept-formula">Clasificación Estratégica de Cartera</div>
            <p>
                <ul>
                    <li><b>🐄 Vacas Lecheras (Cash Cows):</b> Monopolios naturales o demanda inelástica (eléctricas, sanitarias, gas domiciliario). Poco crecimiento, pero reparten yields entre 7% y 10%. Su función es generar liquidez inmediata.</li>
                    <li><b>🚀 Dividend Growth (Compounding):</b> Negocios con expansión constante (banca líder, centros comerciales en arriendo UF). Crecen sus dividendos entre 6% y 12% anual. En 5 años su rendimiento sobre costo inicial supera con creces a cualquier bono.</li>
                    <li><b>📦 Holdings con Descuento:</b> Conglomerados familiares o financieros. Permiten comprar participaciones en grandes empresas a un descuento de hasta el 35% respecto a su valor intrínseco.</li>
                    <li><b>⏳ Cíclicas / Commodities:</b> Dependientes del ciclo global (litio, celulosa, transporte marítimo). Pagan dividendos récord en auges, pero sufren recortes drásticos en desaceleraciones. Jamás deben proyectarse con tasa fija.</li>
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 7. Crédito Tributario Art. 14 A LIR
        st.markdown("""
        <div class="concept-card">
            <h4>7. Crédito Tributario de Primera Categoría (Art. 14 A LIR)</h4>
            <div class="concept-formula">Beneficio Tributario: Imputación del 65% del Impuesto Corporativo (27%)</div>
            <p>
                <b>¿Por qué es fundamental en Chile?</b> Los dividendos no pagan impuesto directo en la fuente. La empresa ya pagó un 27% por ti. Al declarar en abril (F22), recibes un crédito tributario que puedes usar para reducir tu impuesto global complementario o incluso recibir devoluciones en efectivo si tu tasa marginal es inferior al 17,55%.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 4: SIMULADOR DE COMPRA & TASA DAP
# ==========================================
with tab4:
    st.subheader("🎯 Simulador de Inversión en Dividendos vs Depósito a Plazo (DAP)")
    st.caption("Calcula el flujo de caja anual, el crédito tributario fiscal (Art. 14 A) y compáralo con la renta fija.")

    # Context about the Chilean DAP rate
    cur_dap_sim = float(st.session_state.get("dap_rate", 4.0))
    st.info(f"""
    ℹ️ **Tasa de Depósito a Plazo (DAP) Seleccionable por el Usuario:**
    Actualmente calibrada en **{cur_dap_sim:.1f}% anual**.
    En el mercado bancario chileno (Banco de Chile, Santander, BCI, Estado, etc.), las tasas anuales de depósitos a plazo varían según la entidad, plazo y montos (habitualmente entre 3,5% y 4,5% anual).
    Puedes modificar libremente la tasa con el control deslizante a continuación, desde la ficha técnica o desde la barra lateral; el cálculo se sincroniza de inmediato en toda la aplicación.
    """)

    s_c1, s_c2 = st.columns(2)
    with s_c1:
        sim_stock = st.selectbox("Acción a simular:", current_symbols, index=0)
        sim_capital = st.number_input("Monto de inversión proyectado ($ CLP):", min_value=100000, max_value=100000000, value=2000000, step=100000)
        
        # Interactive DAP rate slider synced with session state
        dap_rate = st.slider(
            "Tasa de Referencia Depósito a Plazo / Renta Fija Anual (%):",
            min_value=1.0,
            max_value=8.0,
            value=cur_dap_sim,
            step=0.1,
            format="%.1f%%",
            key="tab4_dap_slider",
            help="Ajusta según la tasa anual efectiva que ofrezca tu banco comercial hoy."
        )
        if dap_rate != st.session_state["dap_rate"]:
            st.session_state["dap_rate"] = dap_rate
            st.rerun()

    stock_row = df_screener[df_screener["NEMO"] == sim_stock].iloc[0]
    stock_price = stock_row["Precio_CLP"]
    stock_div_ttm = stock_row["Div_TTM_CLP"]
    stock_yield = stock_row["Dividend_Yield_Pct"]
    stock_tax_credit = stock_row["Credito_Tributario_CLP"]
    stock_yield_con_tax = stock_row["Yield_Con_Credito_Pct"]

    shares_bought = int(sim_capital // stock_price) if stock_price > 0 else 0
    actual_invested = shares_bought * stock_price
    leftover = sim_capital - actual_invested
    annual_income = shares_bought * stock_div_ttm
    monthly_income = annual_income / 12.0
    annual_tax_credit = shares_bought * stock_tax_credit
    annual_gross_return = annual_income + annual_tax_credit

    # Dynamic DAP calculation
    benchmark_rf = sim_capital * (dap_rate / 100.0)
    benchmark_rf_monthly = benchmark_rf / 12.0
    spread_annual = annual_income - benchmark_rf
    spread_pct = stock_yield - dap_rate

    with s_c2:
        st.markdown(f"#### 💰 Proyección para {sim_stock} ({stock_row['Arquetipo']})")
        st.metric("Acciones que Comprarías", f"{shares_bought:,} acciones", f"Precio unitario: {fmt_clp(stock_price)}")
        st.metric("Ingreso Líquido Anual en Dividendos", fmt_clp(annual_income), f"Yield Neto: {stock_yield:.2f}%")
        st.metric("Crédito Tributario a Favor en F22 (Art. 14 A)", f"+{fmt_clp(annual_tax_credit)}", f"Yield Bruto c/Crédito: {stock_yield_con_tax:.2f}%")
        st.metric("Retorno Bruto Total Proyectado", fmt_clp(annual_gross_return))
        
        st.markdown("---")
        st.markdown(f"#### ⚖️ Comparación vs Depósito a Plazo ({dap_rate:.1f}% anual)")
        
        rf_color = "positive" if spread_annual >= 0 else "negative"
        sign_str = "+" if spread_annual >= 0 else ""
        
        st.write(f"• **Depósito a Plazo te daría:** {fmt_clp(benchmark_rf)} al año ({fmt_clp(benchmark_rf_monthly)}/mes)")
        st.write(f"• **Diferencia Líquida a favor de {sim_stock}:** **{sign_str}{fmt_clp(spread_annual)} al año** ({sign_str}{spread_pct:+.2f}% de spread)")
        st.write(f"• **Ventaja Tributaria Adicional:** En depósitos a plazo pagas impuestos sobre el interés real sin crédito alguno. En acciones recibes un crédito fiscal de **+{fmt_clp(annual_tax_credit)}**.")

        if spread_pct > 0:
            st.success(f"🎉 **{sim_stock} supera al Depósito a Plazo por {spread_pct:.2f} puntos porcentuales netos anuales.** Además, cuentas con protección inflacionaria ({stock_row['Indexacion']}) y potencial de apreciación.")
        else:
            st.warning(f"⚠️ **El Depósito a Plazo ofrece {abs(spread_pct):.2f}% más que el dividendo líquido de {sim_stock}.** Solo convendría invertir en esta acción si buscas crecimiento compuesto o esperas una fuerte plusvalía de precio.")

# Footer
st.markdown("---")
st.caption("🏛️ ZestyFinance: Analizador Oficial de Acciones Chilenas | Datos 100% fidedignos extraídos en tiempo real desde https://www.bolsadesantiago.com/")
