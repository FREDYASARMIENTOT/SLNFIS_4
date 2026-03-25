"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: Portal Institucional Streamlit — Punto de Entrada (portal_fis.py)
AUTOR: Ing. Fredy Alejandro Sarmiento Torres
DESCRIPCIÓN:
    Página raíz del portal. Muestra métricas globales y la tabla comparativa
    de los tres flujos. La navegación entre flujos usa el sidebar de Streamlit
    (pages/ detectado automáticamente).
=============================================================================
"""

import streamlit as st
import os
import json

# 1. CONFIGURACIÓN DE PÁGINA (debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="Portal FIS v8.1 | URosario",
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 🎨 CSS INSTITUCIONAL
# =============================================================================
st.markdown("""
<style>
    /* ── Colores y fuentes ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Header institucional ── */
    .header-box {
        background: linear-gradient(135deg, #8B0000 0%, #5a0000 100%);
        padding: 20px 30px; border-radius: 10px;
        color: white; text-align: center; margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(139,0,0,0.3);
    }
    .header-box h1 { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: 1px; }
    .header-box h4 { margin: 4px 0 0; font-weight: 300; opacity: 0.85; }

    /* ── Métrica ── */
    .metric-box {
        background: #f8f9fa; border-left: 5px solid #8B0000;
        padding: 16px 18px; border-radius: 6px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.07);
    }
    .metric-box h3 { color: #8B0000; margin: 4px 0 0; font-size: 1.6rem; }

    /* ── Tabla comparativa ── */
    .compare-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    .compare-table th {
        background-color: #8B0000; color: white;
        padding: 10px 14px; text-align: center; font-weight: 600;
    }
    .compare-table td {
        padding: 9px 14px; border-bottom: 1px solid #e0e0e0;
        text-align: center; vertical-align: middle;
    }
    .compare-table tr:hover td { background-color: #fff5f5; }

    /* ── Footer telemetría ── */
    .telemetria {
        background-color: #1e1e1e; color: #00FF41;
        padding: 10px; border-radius: 5px;
        font-family: monospace; font-size: 0.82em; text-align: center;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] { background-color: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #eee !important; }
    [data-testid="stSidebar"] hr { border-color: #8B0000; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🧠 ESTADO DE SESIÓN — Cinta compartida entre páginas
# =============================================================================
def _init_estado():
    """Inicializa el estado mínimo necesario si no existe."""
    if "cinta_datos" not in st.session_state:
        ruta_ckpt = os.path.join(os.path.dirname(__file__), "..", "LOGS", "portal_checkpoint.json")
        datos = {}
        if os.path.exists(ruta_ckpt):
            try:
                with open(ruta_ckpt, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception:
                pass
        st.session_state["cinta_datos"] = datos

_init_estado()
cinta_datos: dict = st.session_state["cinta_datos"]

# =============================================================================
# 🏠 ENCABEZADO
# =============================================================================
st.markdown("""
<div class="header-box">
    <h1>🏛️ PORTAL FIS — SYMBIOMEMESIS V8.1</h1>
    <h4>Plataforma de Auditoría Forense y Costeo ABC · Universidad del Rosario</h4>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 📊 MÉTRICAS GLOBALES (SIEMPRE VISIBLES)
# =============================================================================
costo_f1 = cinta_datos.get("flujo1_costo_total", 0.0)
costo_f2 = cinta_datos.get("flujo2_costo_total", 0.0)
costo_f3 = cinta_datos.get("flujo3_costo_total", 0.0)
u_val    = cinta_datos.get("flujo3_valor_u",  "⏳ Pendiente")
diag     = cinta_datos.get("flujo3_diagnostico", "En espera de datos…")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"<div class='metric-box'><b>🙋 Flujo 1 — Humano</b><br><h3>${costo_f1:,.0f}</h3></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-box'><b>🤖 Flujo 2 — Agentes IA</b><br><h3>${costo_f2:,.0f}</h3></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric-box'><b>🧬 Flujo 3 — FIS (U)</b><br><h3>{u_val}</h3></div>", unsafe_allow_html=True)
with m4:
    st.markdown(f"<div class='metric-box'><b>📈 Estado Sistémico</b><br><h3 style='font-size:1rem;margin-top:6px;color:#8B0000;'>{str(diag)[:40]}</h3></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# 📋 TABLA COMPARATIVA DE LOS 3 FLUJOS (INDEX)
# =============================================================================
st.subheader("📋 Comparación de los 3 Flujos de Costeo ABC")
st.caption("Haz clic en el menú lateral para explorar cada flujo en detalle.")

st.markdown("""
<table class="compare-table">
<thead>
    <tr>
        <th>Dimensión</th>
        <th>🙋 Flujo 1: Humano</th>
        <th>🤖 Flujo 2: Agentes IA</th>
        <th>🧬 Flujo 3: FIS Simbiomemésico</th>
    </tr>
</thead>
<tbody>
    <tr><td><b>Método de costeo</b></td><td>Manual (experto)</td><td>Automático (enjambre)</td><td>Híbrido (coevolución)</td></tr>
    <tr><td><b>Rol del humano</b></td><td>Ejecutor 100 %</td><td>Supervisor</td><td>Coautor simbiótico</td></tr>
    <tr><td><b>Automatización</b></td><td>❌ Ninguna</td><td>✅ Alta</td><td>🔄 Adaptativa</td></tr>
    <tr><td><b>Trazabilidad</b></td><td>Registro manual</td><td>Logs de agentes</td><td>Cinta Estigmérgica Inmutable</td></tr>
    <tr><td><b>Memoria semántica</b></td><td>❌</td><td>Parcial (Pinecone)</td><td>✅ RAG completo (3072 dims)</td></tr>
    <tr><td><b>Ecuación U</b></td><td>❌ No aplica</td><td>Calculada post-proceso</td><td>✅ Tiempo real</td></tr>
    <tr><td><b>Convergencia</b></td><td>Depende del auditor</td><td>Estocástica</td><td>Guiada por gradiente Δ</td></tr>
    <tr><td><b>Resultado principal</b></td><td>Excel / CSV</td><td>Reporte automático</td><td>Escalar U + Diagnóstico IA</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# 🗺️ GUÍA DE NAVEGACIÓN RÁPIDA
# =============================================================================
st.info("👈 **Usa el menú lateral** para acceder a cada flujo individual o a la comparación detallada.", icon="🗺️")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 🙋 Flujo 1: Humano\nIngreso manual de datos y costeo ABC paso a paso por el auditor experto.")
with c2:
    st.markdown("### 🤖 Flujo 2: Agentes IA\nEnjambre autónomo de agentes que ejecutan el costeo ABC sin intervencion humana.")
with c3:
    st.markdown("### 🧬 Flujo 3: FIS\nSistema simbiomemésico: el Humano y los Agentes coevolucionan sobre la Cinta Inmutable.")

# =============================================================================
# 🎛️ SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding-bottom:12px; border-bottom: 2px solid #8B0000; margin-bottom:16px;">
        <h2 style="margin:0; color:#ff6b6b;">🏛️ URosario</h2>
        <span style="font-size:11px; color:#aaa;">Portal FIS v8.1 · Menú</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("portal_fis.py",                          label="🏠  Inicio — Comparación",        icon="🏠")
    st.page_link("pages/00_comparacion.py",                label="📊  Comparación Detallada",        icon="📊")
    st.page_link("pages/01_flujo_humano.py",               label="🙋  Flujo 1: Humano",              icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py",           label="🤖  Flujo 2: Agentes IA",          icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",                  label="🧬  Flujo 3: FIS Simbiomemésico",  icon="3️⃣")
    st.markdown("---")
    st.caption(f"Investigador: **Fredy Sarmiento**")
    st.caption(f"Motor: `{os.getenv('MODEL_NAME','gemini-2.5-flash')}`")
    if st.button("🗑️ Limpiar sesión", width="stretch"):
        st.session_state.clear()
        st.rerun()

# =============================================================================
# 📡 FOOTER TELEMETRÍA
# =============================================================================
st.markdown("---")
st.markdown("""
<div class="telemetria">
📡 <b>SISTEMA DE MONITOREO ACTIVO</b> | Vectores Forenses: 3072 dims | Enlace Pinecone: Estable | Sesión Local Protegida
</div>
""", unsafe_allow_html=True)
