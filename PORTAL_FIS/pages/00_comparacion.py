"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/00_comparacion.py  — Comparación Detallada (Index)
AUTOR: Ing. Fredy Alejandro Sarmiento Torres
DESCRIPCIÓN:
    Página de comparación ampliada con gráficos radar/barras y tabla
    de KPIs de los tres flujos. Disponible desde el menú lateral.
=============================================================================
"""

import streamlit as st
import os
import json

st.set_page_config(page_title="Comparación Flujos | Portal FIS", layout="wide", page_icon="📊")

# =============================================================================
# CSS INSTITUCIONAL (compartido)
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.header-box {
    background: linear-gradient(135deg, #8B0000, #5a0000);
    padding: 16px 30px; border-radius: 10px; color: white;
    text-align: center; margin-bottom: 24px;
    box-shadow: 0 4px 15px rgba(139,0,0,0.3);
}
.header-box h2 { margin: 0; font-weight: 700; }
.kpi-card {
    background: #fff; border: 1px solid #e8e8e8;
    border-top: 4px solid #8B0000; border-radius: 8px;
    padding: 18px; text-align: center;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
}
.kpi-card .val { font-size: 1.8rem; font-weight: 700; color: #8B0000; }
.kpi-card .lbl { font-size: 0.82rem; color: #666; margin-top: 4px; }
.telemetria { background:#1e1e1e; color:#00FF41; padding:10px; border-radius:5px;
              font-family:monospace; font-size:0.82em; text-align:center; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #eee !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO COMPARTIDO
# =============================================================================
cinta_datos: dict = st.session_state.get("cinta_datos", {})

# =============================================================================
# ENCABEZADO
# =============================================================================
st.markdown("""
<div class="header-box">
    <h2>📊 Comparación Detallada de los 3 Flujos</h2>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# KPIs POR FLUJO
# =============================================================================
st.subheader("📌 KPIs Clave por Flujo")
c1, c2, c3 = st.columns(3)
flujos = [
    ("🙋 Flujo 1", "Humano", "flujo1_costo_total", "flujo1_precision", "flujo1_tiempo_hrs"),
    ("🤖 Flujo 2", "Agentes IA", "flujo2_costo_total", "flujo2_precision", "flujo2_tiempo_hrs"),
    ("🧬 Flujo 3", "FIS Simbiomemésico", "flujo3_costo_total", "flujo3_precision", "flujo3_tiempo_hrs"),
]
for col, (icono, nombre, k_costo, k_prec, k_tiempo) in zip([c1, c2, c3], flujos):
    costo  = cinta_datos.get(k_costo, 0.0)
    prec   = cinta_datos.get(k_prec,  "—")
    tiempo = cinta_datos.get(k_tiempo, "—")
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:2rem;">{icono}</div>
            <b>{nombre}</b><br><br>
            <div class="val">${costo:,.0f}</div>
            <div class="lbl">Costo Total ABC</div><br>
            <div class="val" style="font-size:1.2rem;">{prec}</div>
            <div class="lbl">Precisión relativa (%)</div><br>
            <div class="val" style="font-size:1.2rem;">{tiempo}</div>
            <div class="lbl">Tiempo de ejecución (hrs)</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# GRÁFICO DE BARRAS COMPARATIVO (nativo Streamlit)
# =============================================================================
try:
    import pandas as pd

    st.subheader("📊 Gráfico Comparativo — Costo Total ABC")
    df_bar = pd.DataFrame({
        "Flujo": ["Flujo 1 (Humano)", "Flujo 2 (Agentes IA)", "Flujo 3 (FIS)"],
        "Costo Total ($)": [
            cinta_datos.get("flujo1_costo_total", 0.0),
            cinta_datos.get("flujo2_costo_total", 0.0),
            cinta_datos.get("flujo3_costo_total", 0.0),
        ],
    }).set_index("Flujo")
    st.bar_chart(df_bar, width="stretch", color="#8B0000")
except Exception as e:
    st.warning(f"Gráfico no disponible: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# TABLA DETALLADA DE DIMENSIONES
# =============================================================================
st.subheader("🔬 Análisis Dimensional Completo")

try:
    import pandas as pd
    dimensiones = {
        "Dimensión": [
            "Método de costeo", "Rol del humano", "Automatización",
            "Trazabilidad", "Memoria semántica", "Ecuación U",
            "Convergencia sistémica", "Resultado principal"
        ],
        "🙋 Flujo 1: Humano": [
            "Manual (experto)", "Ejecutor 100 %", "❌ Ninguna",
            "Registro manual", "❌", "❌ No aplica",
            "Depende del auditor", "Excel / CSV"
        ],
        "🤖 Flujo 2: Agentes IA": [
            "Automático (enjambre)", "Supervisor", "✅ Alta",
            "Logs de agentes", "Parcial (Pinecone)", "Calculada post-proceso",
            "Estocástica", "Reporte automático"
        ],
        "🧬 Flujo 3: FIS": [
            "Híbrido (coevolución)", "Coautor simbiótico", "🔄 Adaptativa",
            "Cinta Estigmérgica Inmutable", "✅ RAG completo (3072 dims)", "✅ Tiempo real",
            "Guiada por gradiente Δ", "Escalar U + Diagnóstico IA"
        ],
    }
    df_dim = pd.DataFrame(dimensiones)
    st.dataframe(df_dim, width="stretch", hide_index=True)
except Exception as e:
    st.error(f"Error cargando tabla: {e}")

# =============================================================================
# SIDEBAR NAVEGACIÓN
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding-bottom:12px; border-bottom:2px solid #8B0000; margin-bottom:16px;">
        <h2 style="margin:0; color:#ff6b6b;">🏛️ URosario</h2>
        <span style="font-size:11px; color:#aaa;">Portal FIS v8.1 · Menú</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("portal_fis.py",                label="🏠  Inicio — Comparación",       icon="🏠")
    st.page_link("pages/00_comparacion.py",       label="📊  Comparación Detallada",       icon="📊")
    st.page_link("pages/01_flujo_humano.py",      label="🙋  Flujo 1: Humano",             icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py",  label="🤖  Flujo 2: Agentes IA",         icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",         label="🧬  Flujo 3: FIS Simbiomemésico", icon="3️⃣")
    st.page_link("pages/04_simulador_fis.py",     label="📊  Simulador Diferencial",        icon="📊")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""<div class="telemetria">📡 <b>COMPARACIÓN ACTIVA</b> | Vectores Forenses: 3072 dims | Simbiomémesis v8.1</div>""", unsafe_allow_html=True)
