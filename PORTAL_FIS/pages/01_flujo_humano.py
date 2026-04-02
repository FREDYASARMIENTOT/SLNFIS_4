"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/01_flujo_humano.py  — Flujo 1: Costeo ABC Manual (Humano)
AUTOR: Ing. Fredy Alejandro Sarmiento Torres
DESCRIPCIÓN:
    Interfaz granular de costeo ABC por asignatura con:
    - Selección múltiple en cascada: Facultad → Programa → Asignatura (RAG Pinecone)
    - Parámetros estándar configurables por asignatura
    - Modelo de costeo: Directos + Indirectos (50% de directos)
    - Costo unitario de aula = (Prof + m2 + Licencias + Indirectos) / (Grupos×Clases×Estudiantes)
    - Simulación dinámica en tiempo real con gráfica de torta
=============================================================================
"""

import streamlit as st
import os
import sys
import json
import pandas as pd
from datetime import datetime

# Agregar utils al path (PORTAL_FIS/utils/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader_oferta import render_selector_jerarquia

st.set_page_config(page_title="Flujo 1: Humano | Portal FIS", layout="wide", page_icon="🙋")

# =============================================================================
# CSS INSTITUCIONAL — MODO OSCURO PRO
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

/* Tarjeta de resultados — fondo oscuro para legibilidad */
.result-box {
    background: #1e1e2e;
    border-left: 5px solid #ff4b4b;
    padding: 20px; border-radius: 8px; margin-top: 12px;
    color: #f0f0f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.result-box h4 { color: #ff6b6b; margin-top: 0; }
.result-box td, .result-box th { color: #e0e0e0; padding: 5px 8px; }
.result-box b { color: #ffcccc; }
.result-box .total-row td { color: #ff4b4b; font-weight: 700; font-size: 1.1em; border-top: 2px solid #ff4b4b; }
.result-box .unitario { color: #00FF41; font-size: 1.1em; font-weight: 700; }

/* Tarjeta de fórmula */
.formula-box {
    background: #0d1117; border: 1px solid #30363d;
    border-radius: 8px; padding: 16px; color: #58a6ff;
    font-family: monospace; font-size: 0.88em; margin-top: 10px;
}

/* Indicadores de selección activa */
.seleccion-badge {
    display: inline-block; background: #8B0000; color: white;
    padding: 3px 8px; border-radius: 12px; font-size: 0.78em;
    margin: 2px;
}
.telemetria { background:#1e1e1e; color:#00FF41; padding:10px; border-radius:5px;
              font-family:monospace; font-size:0.82em; text-align:center; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #eee !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO COMPARTIDO
# =============================================================================
if "cinta_datos" not in st.session_state:
    st.session_state["cinta_datos"] = {}
cinta_datos: dict = st.session_state["cinta_datos"]

if "f1_costeos" not in st.session_state:
    st.session_state["f1_costeos"] = []

# =============================================================================
# ENCABEZADO
# =============================================================================
st.markdown("""
<div class="header-box">
    <h2>🙋 Flujo 1 — Costeo ABC Manual Granular (Asignatura por Asignatura)</h2>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SECCIÓN 1: SELECCIÓN EN CASCADA — desde Excel de Oferta Académica 2024
# =============================================================================
st.subheader("📂 1. Selección en Cascada")
facultades_sel, programas_sel, asignaturas_sel = render_selector_jerarquia(key_prefix="f1")

if not asignaturas_sel:
    st.info("Selecciona al menos una asignatura para continuar.", icon="ℹ️")
    st.stop()

st.markdown(
    f"**{len(asignaturas_sel)} asignatura(s) seleccionada(s):** " +
    " ".join([f"<span class='seleccion-badge'>{a}</span>" for a in asignaturas_sel]),
    unsafe_allow_html=True
)

# =============================================================================
# SECCIÓN 2: PARÁMETROS ESTÁNDAR (GLOBALES) — Aplicados a TODAS las asignaturas
# =============================================================================
st.markdown("---")
st.subheader("⚙️ 2. Parámetros de Configuración")
st.caption("Estos valores se aplican a **todas** las asignaturas seleccionadas. Valores estándar precargados.")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    num_grupos     = st.number_input("👥 Grupos por asignatura",    min_value=1, value=2,  step=1)
    num_clases     = st.number_input("📅 Clases por semestre",      min_value=1, value=10, step=1)
    periodo        = st.selectbox("🗓️ Período académico",
                                   ["2026-I", "2026-II", "2025-I", "2025-II", "Intersemestral"])
    num_profesores = st.number_input("👨‍🏫 Profesores por grupo",    min_value=1, value=2,  step=1)

with col_p2:
    num_estudiantes  = st.number_input("👩‍🎓 Estudiantes por grupo",      min_value=1,    value=10,      step=1)
    valor_hora_prof  = st.number_input("💵 Valor hora-profesor ($)",      min_value=0.0,  value=100000.0, step=1000.0, format="%.0f")
    metros_cuadrados = st.number_input("📐 Metros cuadrados del salón",   min_value=1.0,  value=50.0,    step=1.0)
    valor_m2         = st.number_input("🏗️ Valor por m² por sesión ($)", min_value=0.0,  value=1500.0,  step=100.0,
                                        help="Costo de ocupación del espacio físico por cada sesión de clase")

with col_p3:
    tipo_salon = st.radio(
        "🖥️ Tipo de salón",
        ["Avanzado (PCs por estudiante)", "Básico (Video beam + PC Profesor)"],
        index=0,
        help="El salón avanzado duplica el costo de licencias de software"
    )
    valor_licencias_base = st.number_input(
        "💾 Valor licencias software — Básico ($)",
        min_value=0.0, value=500000.0, step=10000.0, format="%.0f",
        help="El tipo Avanzado automáticamente duplica este valor"
    )
    # Badge de licencias aplicadas — en la misma columna
    valor_licencias = valor_licencias_base * (2.0 if "Avanzado" in tipo_salon else 1.0)
    st.info(
        f"💾 **Licencias aplicadas:** ${valor_licencias:,.0f} "
        f"({'x2 por salón avanzado' if 'Avanzado' in tipo_salon else 'base para salón básico'})",
        icon="ℹ️"
)

# Licencias ya calculadas en col_p3 arriba
# (variable valor_licencias disponible para el modelo de costeo)

# =============================================================================
# MODELO DE COSTEO ABC — Lógica principal
# =============================================================================
HORAS_POR_CLASE = 2  # Cada sesión dura 2 horas

def calcular_costeo(asignatura: str) -> dict:
    """Calcula el modelo de costeo completo para UNA asignatura."""
    # — COSTOS DIRECTOS —
    costo_prof  = num_grupos * num_clases * num_profesores * HORAS_POR_CLASE * valor_hora_prof
    costo_m2    = num_grupos * num_clases * metros_cuadrados * valor_m2
    costo_lic   = valor_licencias
    total_directo = costo_prof + costo_m2 + costo_lic

    # — COSTO INDIRECTO = 50% de los directos —
    costo_indirecto = 0.5 * total_directo

    # — COSTO TOTAL —
    costo_total = total_directo + costo_indirecto

    # — COSTO UNITARIO POR SESIÓN DE AULA —
    # Unidad = 1 sesión de clase × 1 grupo
    # Total sesiones-grupo = grupos × clases
    sesiones_totales   = num_grupos * num_clases
    estudiantes_totales = num_estudiantes * num_grupos

    # Costo unitario de AULA (por sesión, distribuido por estudiante)
    costo_unit_sesion   = costo_total / sesiones_totales if sesiones_totales > 0 else 0
    costo_unit_estudiant = costo_total / estudiantes_totales if estudiantes_totales > 0 else 0

    return {
        "asignatura"          : asignatura,
        "costo_prof"          : costo_prof,
        "costo_m2"            : costo_m2,
        "costo_licencias"     : costo_lic,
        "total_directo"       : total_directo,
        "costo_indirecto"     : costo_indirecto,
        "costo_total"         : costo_total,
        "sesiones_totales"    : sesiones_totales,
        "estudiantes_totales" : estudiantes_totales,
        "costo_unit_sesion"   : costo_unit_sesion,
        "costo_unit_estudiant": costo_unit_estudiant,
    }

# Calcular para todas las asignaturas seleccionadas
resultados = [calcular_costeo(a) for a in asignaturas_sel]
costo_gran_total = sum(r["costo_total"] for r in resultados)

# =============================================================================
# SECCIÓN 3: SIMULACIÓN DINÁMICA — Resultados por asignatura
# =============================================================================
st.markdown("---")
st.subheader(f"📊 3. Simulación de Costeo ABC — {periodo} | {len(asignaturas_sel)} asignatura(s)")

for r in resultados:
    with st.expander(f"📘 {r['asignatura']} — Total: ${r['costo_total']:,.0f}", expanded=True):
        col_tabla, col_grafica = st.columns([1, 1.2])

        with col_tabla:
            pct_prof = r['costo_prof'] / r['costo_total'] * 100 if r['costo_total'] else 0
            pct_m2   = r['costo_m2']  / r['costo_total'] * 100 if r['costo_total'] else 0
            pct_lic  = r['costo_licencias'] / r['costo_total'] * 100 if r['costo_total'] else 0
            pct_ind  = r['costo_indirecto'] / r['costo_total'] * 100 if r['costo_total'] else 0

            st.markdown(f"""
            <div class='result-box'>
                <h4>💰 {r['asignatura']}</h4>
                <table style="width:100%;">
                    <tr><th style="text-align:left;">Rubro</th><th style="text-align:right;">Valor</th><th style="text-align:right;">%</th></tr>
                    <tr><td>👨‍🏫 Docencia</td>
                        <td style="text-align:right">${r['costo_prof']:,.0f}</td>
                        <td style="text-align:right">{pct_prof:.1f}%</td></tr>
                    <tr><td>🏗️ Infraestructura (m²)</td>
                        <td style="text-align:right">${r['costo_m2']:,.0f}</td>
                        <td style="text-align:right">{pct_m2:.1f}%</td></tr>
                    <tr><td>💾 Licencias Software</td>
                        <td style="text-align:right">${r['costo_licencias']:,.0f}</td>
                        <td style="text-align:right">{pct_lic:.1f}%</td></tr>
                    <tr><td colspan="3" style="color:#aaa; font-size:0.85em; padding-top:6px;">
                        <i>Subtotal Costos Directos: ${r['total_directo']:,.0f}</i></td></tr>
                    <tr><td>⚙️ Indirectos (50% Directos)</td>
                        <td style="text-align:right">${r['costo_indirecto']:,.0f}</td>
                        <td style="text-align:right">{pct_ind:.1f}%</td></tr>
                    <tr class="total-row">
                        <td style="padding-top:8px;"><b>TOTAL ABC</b></td>
                        <td style="text-align:right;color:#ff4b4b;font-weight:700;font-size:1.15em;">${r['costo_total']:,.0f}</td>
                        <td style="text-align:right;color:#ff4b4b;">100%</td></tr>
                </table>
                <hr style="border-color:#333; margin:12px 0;">
                <p class="unitario">
                    🎓 Costo unitario / estudiante-semestre: ${r['costo_unit_estudiant']:,.0f}<br>
                    🏛️ Costo unitario / sesión-aula: ${r['costo_unit_sesion']:,.0f}
                </p>
                <p style="color:#aaa; font-size:0.8em; margin-top:6px;">
                    Sesiones totales ({r['sesiones_totales']:,}) = {num_grupos}gr × {num_clases}cl &nbsp;|&nbsp;
                    Estudiantes totales ({r['estudiantes_totales']:,}) = {num_grupos}gr × {num_estudiantes}est
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_grafica:
            df_g = pd.DataFrame({
                "Rubro": ["Docencia", "Infraestructura m²", "Licencias", "Indirectos (50%)"],
                "Costo": [r['costo_prof'], r['costo_m2'], r['costo_licencias'], r['costo_indirecto']]
            })
            try:
                import plotly.express as px
                fig = px.pie(
                    df_g, values="Costo", names="Rubro", hole=0.38,
                    color_discrete_sequence=["#ff4b4b", "#ff8c42", "#ffd166", "#a29bfe"],
                    title=f"Distribución de Costos — {r['asignatura']}"
                )
                fig.update_traces(
                    textposition="inside",
                    texttemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}",
                    hovertemplate="<b>%{label}</b><br>Valor: $%{value:,.0f}<br>Participación: %{percent:.1%}<extra></extra>",
                )
                fig.update_layout(
                    margin=dict(t=40, b=0, l=0, r=0), height=330,
                    paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white", size=11),
                    title_font=dict(size=12, color="#ff6b6b"),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                df_g["Porcentaje"] = (df_g["Costo"] / df_g["Costo"].sum() * 100).round(1).astype(str) + " %"
                st.dataframe(df_g[["Rubro", "Costo", "Porcentaje"]], use_container_width=True, hide_index=True)

# =============================================================================
# GRÁFICA CONSOLIDADA — Distribución global de rubros (todas las asignaturas)
# =============================================================================
st.markdown("---")
st.subheader("🥧 Distribución Global de Costos por Rubro")

_tot_prof = sum(r['costo_prof']      for r in resultados)
_tot_m2   = sum(r['costo_m2']        for r in resultados)
_tot_lic  = sum(r['costo_licencias'] for r in resultados)
_tot_ind  = sum(r['costo_indirecto'] for r in resultados)
_gran_tot = _tot_prof + _tot_m2 + _tot_lic + _tot_ind

df_global = pd.DataFrame({
    "Rubro"  : ["👨‍🏫 Docencia", "🏗️ Infraestructura m²", "💾 Licencias", "⚙️ Indirectos (50%)"],
    "Valor"  : [_tot_prof, _tot_m2, _tot_lic, _tot_ind],
    "Porcentaje": [
        round(_tot_prof / _gran_tot * 100, 1) if _gran_tot else 0,
        round(_tot_m2   / _gran_tot * 100, 1) if _gran_tot else 0,
        round(_tot_lic  / _gran_tot * 100, 1) if _gran_tot else 0,
        round(_tot_ind  / _gran_tot * 100, 1) if _gran_tot else 0,
    ]
})

try:
    import plotly.graph_objects as go

    _colores = ["#ff4b4b", "#ff8c42", "#ffd166", "#a29bfe"]
    _etiquetas_limpias = ["Docencia", "Infraestructura m²", "Licencias", "Indirectos (50%)"]

    fig_global = go.Figure(go.Pie(
        labels=_etiquetas_limpias,
        values=df_global["Valor"].tolist(),
        hole=0.42,
        marker=dict(colors=_colores, line=dict(color="#1e1e2e", width=2)),
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}",
        textposition="outside",
        hovertemplate="<b>%{label}</b><br>Valor: $%{value:,.0f}<br>Participación: %{percent:.1%}<extra></extra>",
        insidetextorientation="radial",
    ))
    fig_global.update_layout(
        annotations=[dict(
            text=f"<b>TOTAL</b><br>${_gran_tot:,.0f}",
            x=0.5, y=0.5, font_size=13, font_color="white",
            showarrow=False, align="center",
        )],
        margin=dict(t=20, b=20, l=120, r=120),
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=12),
        showlegend=True,
        legend=dict(
            orientation="v", x=1.02, y=0.5,
            font=dict(size=11, color="white"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    col_pie, col_tabla_g = st.columns([1.6, 1])
    with col_pie:
        st.plotly_chart(fig_global, use_container_width=True)
    with col_tabla_g:
        st.markdown("#### Resumen por Rubro")
        for _, fila in df_global.iterrows():
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:6px 10px;margin:3px 0;border-radius:6px;"
                f"background:#1e1e2e;border-left:4px solid #ff4b4b'>"
                f"<span style='color:#eee'>{fila['Rubro']}</span>"
                f"<span style='color:#ffd166;font-weight:600'>"
                f"${fila['Valor']:,.0f} &nbsp;<span style='color:#a29bfe'>({fila['Porcentaje']}%)</span>"
                f"</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"padding:8px 10px;margin:6px 0;border-radius:6px;"
            f"background:#3a0000;border-left:4px solid #ff0000'>"
            f"<span style='color:white;font-weight:700'>💰 TOTAL ABC</span>"
            f"<span style='color:#ff4b4b;font-weight:700;font-size:1.05em'>${_gran_tot:,.0f}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
except ImportError:
    st.dataframe(
        df_global.style.format({"Valor": "${:,.0f}", "Porcentaje": "{:.1f}%"}),
        use_container_width=True, hide_index=True,
    )

# =============================================================================
# SECCIÓN 4: CUADRO CONSOLIDADO GRAN TOTAL
# =============================================================================
if len(resultados) > 1:
    st.markdown("---")
    st.subheader(f"📋 4. Consolidado — {len(asignaturas_sel)} asignaturas seleccionadas")

    rows = []
    for r in resultados:
        rows.append({
            "Asignatura"         : r["asignatura"],
            "Docencia ($)"       : r["costo_prof"],
            "Infraest. ($)"      : r["costo_m2"],
            "Licencias ($)"      : r["costo_licencias"],
            "Indirectos ($)"     : r["costo_indirecto"],
            "Total ABC ($)"      : r["costo_total"],
            "Costo/Est ($)"      : r["costo_unit_estudiant"],
        })

    df_cons = pd.DataFrame(rows)
    st.dataframe(df_cons.style
                 .format({c: "{:,.0f}" for c in df_cons.columns if "$" in c})
                 .highlight_max(subset=["Total ABC ($)"], color="#5a0000"),
                 width="stretch", hide_index=True)

    st.metric(f"💰 GRAN TOTAL ABC ({len(asignaturas_sel)} asignatura(s))", f"${costo_gran_total:,.0f}")

# =============================================================================
# SECCIÓN 5: FÓRMULA RECOMENDADA — COSTO UNITARIO DE AULA
# =============================================================================
st.markdown("---")
with st.expander("📐 ¿Cómo se calcula el Costo Unitario de Aula? (Fórmula Recomendada)", expanded=False):
    st.markdown("""
    <div class="formula-box">
    <b>MODELO DE COSTO ABC GRANULAR POR SESIÓN</b><br><br>

    <b>① Costos Directos:</b><br>
    &nbsp; C_prof = Grupos × Clases × Profesores × Horas/clase × Valor_hora_prof<br>
    &nbsp; C_m2   = Grupos × Clases × m² × Valor_m²<br>
    &nbsp; C_lic  = Valor_licencias (×2 si salón Avanzado)<br>
    &nbsp; Total_Directos = C_prof + C_m2 + C_lic<br><br>

    <b>② Costos Indirectos:</b><br>
    &nbsp; C_ind = 0.50 × Total_Directos<br><br>

    <b>③ Costo Total ABC:</b><br>
    &nbsp; C_total = Total_Directos + C_ind<br><br>

    <b>④ Costo Unitario de AULA (por sesión-grupo):</b><br>
    &nbsp; CU_aula = C_total / (Grupos × Clases)<br>
    &nbsp; → Cuánto cuesta ABRIR una sesión de esa asignatura en UN grupo<br><br>

    <b>⑤ Costo Unitario por ESTUDIANTE-SEMESTRE:</b><br>
    &nbsp; CU_est = C_total / (Grupos × Estudiantes_por_grupo)<br>
    &nbsp; → Cuánto cuesta UN estudiante cursar toda la asignatura un semestre<br><br>

    <b>💡 Recomendación para el VALOR UNITARIO DE AULA compuesto:</b><br>
    &nbsp; Si deseas distribuir el costo por "hora-estudiante-aula":<br>
    &nbsp; CU_hora_est = C_total / (Grupos × Clases × Horas_clase × Estudiantes_por_grupo)<br>
    &nbsp; → Expresado en: $ / (hora × estudiante)<br>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# BOTÓN DE CONSOLIDACIÓN EN LA CINTA
# =============================================================================
st.markdown("---")
if st.button("💾 Guardar Costeo en la Cinta Compartida", type="primary", width="stretch"):
    entrada = {
        "timestamp"      : datetime.now().isoformat(),
        "periodo"        : periodo,
        "facultades"     : facultades_sel,
        "programas"      : programas_sel,
        "asignaturas"    : asignaturas_sel,
        "num_grupos"     : num_grupos,
        "num_clases"     : num_clases,
        "tipo_salon"     : tipo_salon,
        "gran_total"     : costo_gran_total,
        "detalle"        : resultados,
    }
    st.session_state["f1_costeos"].append(entrada)
    cinta_datos["flujo1_costo_total"]  = sum(e["gran_total"] for e in st.session_state["f1_costeos"])
    cinta_datos["flujo1_facultad"]     = ", ".join(facultades_sel)
    cinta_datos["flujo1_programa"]     = ", ".join(programas_sel)
    cinta_datos["flujo1_timestamp"]    = datetime.now().isoformat()
    cinta_datos["flujo1_precision"]    = "Alta (Granular Manual)"
    cinta_datos["flujo1_tiempo_hrs"]   = "Manual"
    st.session_state["cinta_datos"]    = cinta_datos

    st.success(f"✅ Costeo de **{len(asignaturas_sel)}** asignatura(s) consolidado. "
               f"Acumulado Flujo 1: **${cinta_datos['flujo1_costo_total']:,.0f}**")
    st.balloons()

# Historial de costeos guardados
if st.session_state["f1_costeos"]:
    st.markdown("---")
    st.subheader("📜 Historial de Costeos Guardados esta Sesión")
    for i, ent in enumerate(reversed(st.session_state["f1_costeos"]), 1):
        st.caption(f"[{ent['timestamp'][:19]}] {ent['periodo']} | "
                   f"{len(ent['asignaturas'])} asignatura(s) | Total: ${ent['gran_total']:,.0f}")

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding-bottom:12px; border-bottom:2px solid #8B0000; margin-bottom:16px;">
        <h2 style="margin:0; color:#ff6b6b;">🏛️ URosario</h2>
        <span style="font-size:11px; color:#aaa;">Portal FIS v8.1 · Menú</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("portal_fis.py",               label="🏠  Inicio — Comparación",       icon="🏠")
    st.page_link("pages/00_comparacion.py",      label="📊  Comparación Detallada",       icon="📊")
    st.page_link("pages/01_flujo_humano.py",     label="🙋  Flujo 1: Humano",             icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py", label="🤖  Flujo 2: Agentes IA",         icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",        label="🧬  Flujo 3: FIS Simbiomemésico", icon="3️⃣")
    st.page_link("pages/04_simulador_fis.py",    label="📊  Simulador Diferencial",        icon="📊")
    st.page_link("pages/05_fabrica_agentes.py",  label="🛠️  Fábrica & Skills",             icon="🛠️")
    st.markdown("---")
    st.metric("💰 Total ABC actual", f"${costo_gran_total:,.0f}")
    acumulado = cinta_datos.get('flujo1_costo_total', 0)
    if acumulado:
        st.metric("📦 Acumulado guardado", f"${acumulado:,.0f}")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div class="telemetria">
🙋 <b>FLUJO 1 — MODO HUMANO ACTIVO</b> | RAG Pinecone | Selección Múltiple | Simulación Dinámica | FIS v8.1
</div>
""", unsafe_allow_html=True)
