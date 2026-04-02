"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/04_simulador_fis.py — Cinta Estigmérgica: Simulador Diferencial
AUTOR: Ing. Fredy Alejandro Sarmiento Torres
DESCRIPCIÓN:
    Simulador interactivo de la Utilidad Simbiótica U(t) para 3 flujos:
      · Flujo 1 — Humano    (crecimiento lineal, techo k=0.60)
      · Flujo 2 — IA Pura   (sube rápido, Sicofancia la degrada en el tiempo)
      · Flujo 3 — FIS       (Simbiomemésis, ecuación diferencial logística completa)
    Motor: Integración numérica de Euler (un paso por iteración).

    ⚠️  MÓDULO AUTOCONTENIDO
        Sin dependencias de FLUJO_3_FIS ni de otros módulos del ecosistema FIS.
        Comparte sidebar con el portal pero opera con su propio espacio de sesión
        (prefijo "sim_" en todas las claves de st.session_state).
=============================================================================
"""

import os
import math
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Simulador FIS | Cinta Estigmérgica",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CONSTANTES DEL MODELO DIFERENCIAL
# =============================================================================
_K_MADUREZ = 0.95   # Techo de homeostasis FIS (Flujo 3)
_K_HUMANO  = 0.60   # Techo del Flujo 1 (Humano)
_K_IA      = 0.80   # Techo del Flujo 2 (IA Pura)
_LAMBDA    = 1.2    # Peso Ortogonalidad (sinergia)
_MU        = 0.3    # Penalización por Redundancia
_SIGMA     = 0.6    # Penalización por Sicofancia
_PHI       = 0.2    # Costo de coordinación

_INITIAL_ITER = {
    "t": 0,
    "U1": 0.1, "U2": 0.1, "U3": 0.1,
    "dU1": 0.0, "dU2": 0.0, "dU3": 0.0,
    "vars": {"O": 0.5, "S": 0.5, "R": 0.5, "Cc": 0.5,
             "sinergia": 0.0, "friccion": 0.0, "logistica": 0.0},
}

# =============================================================================
# DEFINICIÓN DE ESCENARIOS
# =============================================================================
_SCENARIOS = {
    "base": {
        "label": "Base",
        "emoji": "⚖️",
        "desc": "Estado neutro de referencia (todos los indicadores en 3).",
        "color": "#546e7a",
        "config": {f"q{i}": 3 for i in range(1, 16)},
    },
    "sinergia": {
        "label": "Sinergia Máxima",
        "emoji": "🚀",
        "desc": "Alta eficiencia, alta simbiosis, baja fricción. FIS converge a k=0.95.",
        "color": "#3b82f6",
        "config": {f"q{i}": 5 for i in range(1, 16)},
    },
    "hitl": {
        "label": "HITL Óptimo",
        "emoji": "🤝",
        "desc": "Simbiosis perfecta: alta autonomía crítica y alineación humano-IA.",
        "color": "#10b981",
        "config": {
            "q1": 5, "q2": 4, "q3": 5, "q4": 4, "q5": 5,
            "q6": 5, "q7": 5, "q8": 5, "q9": 5, "q10": 4,
            "q11": 4, "q12": 5, "q13": 4, "q14": 5, "q15": 5,
        },
    },
    "sicofa": {
        "label": "Colapso Sycofántico",
        "emoji": "🪞",
        "desc": "IA técnicamente eficiente pero sin autonomía crítica. U2 decae por fatiga.",
        "color": "#ef4444",
        "config": {
            "q1": 5, "q2": 5, "q3": 4, "q4": 4, "q5": 5,
            "q6": 1, "q7": 1, "q8": 1, "q9": 2, "q10": 5,
            "q11": 3, "q12": 3, "q13": 3, "q14": 3, "q15": 3,
        },
    },
    "friccion": {
        "label": "Alta Fricción",
        "emoji": "⚙️",
        "desc": "Burocracia y redundancia institucional alta. Penaliza fuertemente al FIS.",
        "color": "#f59e0b",
        "config": {
            "q1": 3, "q2": 3, "q3": 3, "q4": 3, "q5": 3,
            "q6": 3, "q7": 3, "q8": 3, "q9": 3, "q10": 3,
            "q11": 5, "q12": 5, "q13": 5, "q14": 5, "q15": 5,
        },
    },
    "crisis": {
        "label": "Crisis Total",
        "emoji": "🔥",
        "desc": "Todos los indicadores degradados. Los 3 flujos colapsan simultáneamente.",
        "color": "#dc2626",
        "config": {
            "q1": 1, "q2": 1, "q3": 2, "q4": 1, "q5": 1,
            "q6": 1, "q7": 1, "q8": 1, "q9": 1, "q10": 1,
            "q11": 5, "q12": 5, "q13": 5, "q14": 5, "q15": 4,
        },
    },
    "humano": {
        "label": "Dominancia Humana",
        "emoji": "🧠",
        "desc": "Alta supervisión humana, eficiencia media. U1 lidera sobre la IA.",
        "color": "#8b5cf6",
        "config": {
            "q1": 3, "q2": 3, "q3": 4, "q4": 5, "q5": 4,
            "q6": 5, "q7": 5, "q8": 4, "q9": 3, "q10": 3,
            "q11": 2, "q12": 2, "q13": 2, "q14": 2, "q15": 4,
        },
    },
}

# Catálogo de indicadores
_ME_ITEMS = [
    ("q1",  "I1. Fidelidad Semántica"),
    ("q2",  "I2. Precisión del Inductor"),
    ("q3",  "I3. Consistencia Lógica"),
    ("q4",  "I4. Trazabilidad de Datos"),
    ("q5",  "I5. Capacidad de Síntesis"),
]
_SG_ITEMS = [
    ("q6",  "I6. Transparencia Algorítmica"),
    ("q7",  "I7. Autonomía Crítica (α)"),
    ("q8",  "I8. Validación de Sesgos"),
    ("q9",  "I9. Co-creación de Procesos"),
    ("q10", "I10. Confianza Percibida"),
]
_FR_ITEMS = [
    ("q11", "I11. Latencia de Coordinación"),
    ("q12", "I12. Redundancia de Pasos"),
    ("q13", "I13. Carga Cognitiva"),
    ("q14", "I14. Error de Comunicación"),
    ("q15", "I15. Estabilidad del Sistema"),
]

# =============================================================================
# CSS INSTITUCIONAL
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.header-sim {
    background: linear-gradient(135deg, #1a237e 0%, #283593 60%, #0d47a1 100%);
    padding: 16px 28px; border-radius: 10px; color: white;
    text-align: center; margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(26,35,126,.45);
}
.header-sim h2 { margin: 0; font-weight: 700; font-size: 1.55rem; }
.header-sim p  { margin: 4px 0 0; font-weight: 300; opacity: .85; font-size: .88rem; }

.scenario-header {
    background: #1e1e2e; border-radius: 10px 10px 0 0;
    padding: 10px 16px; border: 1px solid #2a2a3e; border-bottom: none;
}
.scenario-footer {
    background: #1a1a2e; border-radius: 0 0 10px 10px;
    padding: 10px 16px; border: 1px solid #2a2a3e; border-top: 1px solid #333;
    margin-bottom: 20px;
}
.badge-escenario {
    display: inline-block; padding: 3px 10px; border-radius: 10px;
    font-size: .78em; font-weight: 700; color: white; margin-left: 6px; vertical-align: middle;
}

.metric-sim {
    background: #1e1e2e; border-left: 4px solid #1a237e;
    padding: 10px 14px; border-radius: 8px; color: #fff; margin-bottom: 4px;
}
.metric-sim .val { font-size: 1.4rem; font-weight: 700; color: #90caf9; }
.metric-sim .lbl { font-size: .75rem; color: #aaa; margin-bottom: 2px; }

.audit-box {
    background: #0d1117; border: 1px solid #1a237e;
    border-radius: 10px; padding: 16px; color: #e0e0e0;
    font-family: 'Consolas', 'Monaco', monospace; font-size: .83em; margin-top: 12px;
}
.audit-title { color: #90caf9; font-size: .92rem; font-weight: 700; margin: 0 0 12px 0; }
.a-section { color: #ce93d8; font-weight: 700; margin: 12px 0 6px; }
.a-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 6px; background: #161b22; padding: 10px; border-radius: 6px; margin-bottom: 8px;
}
.a-block { background: #161b22; padding: 10px; border-radius: 6px; border-left: 4px solid #1a237e; }
.a-green  { color: #a5d6a7; font-weight: 700; }
.a-red    { color: #ef9a9a; font-weight: 700; }
.a-yellow { color: #ffd54f; font-weight: 700; }
.a-blue   { color: #90caf9; font-weight: 700; font-size: 1.15em; }
.a-result { margin-top: 10px; padding-top: 8px; border-top: 1px solid #30363d; }
.a-flujos { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 8px; }
.a-f1 { background: #161b22; padding: 8px; border-radius: 6px; border-left: 3px solid #9ca3af; }
.a-f2 { background: #161b22; padding: 8px; border-radius: 6px; border-left: 3px solid #ef4444; }
.a-f3 { background: #1a1f3a; padding: 8px; border-radius: 6px; border-left: 3px solid #3b82f6; }
.a-f-lbl-1 { color: #9ca3af; font-size: .73em; }
.a-f-lbl-2 { color: #ef9a9a; font-size: .73em; }
.a-f-lbl-3 { color: #90caf9; font-size: .73em; font-weight: 700; }
.a-f-val   { color: white; font-size: 1.1em; font-weight: 700; margin-top: 4px; }
.a-f-val-3 { color: #90caf9; font-size: 1.25em; font-weight: 700; margin-top: 4px; }

.telemetria {
    background: #1e1e1e; color: #00FF41; padding: 8px;
    border-radius: 5px; font-family: monospace; font-size: .80em; text-align: center;
}

[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #eee !important; }
[data-testid="stSidebar"] hr { border-color: #8B0000; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO DE SESIÓN (prefijo "sim_" — aislado del resto del portal)
# =============================================================================
def _init_state():
    if "sim_iteraciones" not in st.session_state:
        st.session_state["sim_iteraciones"] = [dict(_INITIAL_ITER)]
    if "sim_escenario" not in st.session_state:
        st.session_state["sim_escenario"] = None
    if "sim_periodo" not in st.session_state:
        st.session_state["sim_periodo"] = "2026-1"
    if "sim_proceso" not in st.session_state:
        st.session_state["sim_proceso"] = "Costeo ABC — Facultad de Ingeniería"
    for i in range(1, 16):
        if f"sim_q{i}" not in st.session_state:
            st.session_state[f"sim_q{i}"] = 3
    # Aplica actualizaciones pendientes de sliders ANTES de que se instancien los widgets
    if "sim_q_pending" in st.session_state:
        pending = st.session_state.pop("sim_q_pending")
        for q, v in pending.items():
            st.session_state[f"sim_{q}"] = v

_init_state()

# =============================================================================
# MOTOR MATEMÁTICO — Funciones puras (sin Streamlit)
# =============================================================================
def _norm(val: int) -> float:
    """Normaliza [1,5] → [0,1]"""
    return (val - 1) / 4.0


def _calcular_paso(iteraciones: list, qs: dict) -> dict:
    """
    Integración de Euler: avanza un paso temporal para los 3 flujos.
    qs: {q1..q15} valores enteros [1,5]
    """
    last  = iteraciones[-1]
    t_new = last["t"] + 1

    ME = _norm(sum(qs[f"q{i}"] for i in range(1,  6)) / 5)
    SG = _norm(sum(qs[f"q{i}"] for i in range(6,  11)) / 5)
    FR = _norm(sum(qs[f"q{i}"] for i in range(11, 16)) / 5)

    O  = ME           # Ortogonalidad ← eficiencia
    S  = 1.0 - SG     # Sicofancia    ← inversa de simbiosis
    R  = FR           # Redundancia   ← fricción
    Cc = FR           # Costo coord.  ← fricción

    # Flujo 1: Humano — crecimiento lento, techo k=0.60
    dU1  = (0.15 * O - 0.1 * R) * (1.0 - last["U1"] / _K_HUMANO)
    newU1 = max(0.0, min(last["U1"] + dU1, 1.0))

    # Flujo 2: IA Pura — sube rápido, fatiga sycofántica la destruye
    fatiga = t_new * 0.08 * S
    dU2   = (0.6 * O - fatiga) * (1.0 - last["U2"] / _K_IA)
    newU2 = max(0.0, min(last["U2"] + dU2, 1.0))

    # Flujo 3: FIS — ecuación diferencial logística completa
    sinergia  = _LAMBDA * O
    friccion  = (_MU * R) + (_SIGMA * S) + (_PHI * Cc)
    logistica = 1.0 - last["U3"] / _K_MADUREZ
    dU3       = (sinergia - friccion) * logistica
    newU3     = max(0.0, min(last["U3"] + dU3, 1.0))

    return {
        "t": t_new,
        "U1": newU1, "U2": newU2, "U3": newU3,
        "dU1": dU1,  "dU2": dU2,  "dU3": dU3,
        "vars": {
            "O": O, "S": S, "R": R, "Cc": Cc,
            "sinergia": sinergia, "friccion": friccion, "logistica": logistica,
        },
    }


def _qs_sesion() -> dict:
    """Lee los valores actuales de sliders desde session_state."""
    return {f"q{i}": st.session_state[f"sim_q{i}"] for i in range(1, 16)}


def _rafaga(n: int):
    """Ejecuta N pasos usando la configuración actual de sliders."""
    qs    = _qs_sesion()
    iters = list(st.session_state["sim_iteraciones"])
    for _ in range(n):
        iters.append(_calcular_paso(iters, qs))
    st.session_state["sim_iteraciones"] = iters


def _on_slider():
    """Callback: marcar como personalizado al mover cualquier slider."""
    st.session_state["sim_escenario"] = None

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="header-sim">
    <h2>📊 Cinta Estigmérgica FIS — Simulador Diferencial</h2>
    <p>Telemetría Cognitiva · Evolución de la Utilidad Simbiótica U(t) · Tres Flujos Comparativos</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SUBMENÚ DE ESCENARIOS (ancho completo, sobre ambas columnas)
# =============================================================================
esc_activo = st.session_state["sim_escenario"]

# — Cabecera del submenú
if esc_activo:
    sc_info = _SCENARIOS[esc_activo]
    badge = (f'<span class="badge-escenario" style="background:{sc_info["color"]};">'
             f'{sc_info["emoji"]} {sc_info["label"]}</span>')
else:
    badge = '<span class="badge-escenario" style="background:#546e7a;">✏️ Personalizado</span>'

st.markdown(
    f'<div class="scenario-header">'
    f'<b style="color:#90caf9;font-size:.95rem;">🎬 Escenarios de Simulación</b> &nbsp;{badge}'
    f'</div>',
    unsafe_allow_html=True,
)

# — Botones de escenarios (7 columnas)
sc_keys = list(_SCENARIOS.keys())
sc_cols = st.columns(len(sc_keys))
for key, col in zip(sc_keys, sc_cols):
    sc = _SCENARIOS[key]
    with col:
        if st.button(
            f"{sc['emoji']} {sc['label']}",
            key=f"sim_btn_sc_{key}",
            use_container_width=True,
            type="primary" if esc_activo == key else "secondary",
            help=sc["desc"],
        ):
            for q, v in sc["config"].items():
                st.session_state[f"sim_{q}"] = v
            st.session_state["sim_escenario"] = key
            st.rerun()

# — Descripción activa + ráfagas
if esc_activo:
    desc_txt = f"**{sc_info['emoji']} {sc_info['label']}:** {sc_info['desc']}"
else:
    desc_txt = "Ajusta los sliders manualmente para crear un escenario personalizado."

raf_c0, raf_c3, raf_c5, raf_c10, raf_cx = st.columns([3, 1, 1, 1, 3])
with raf_c0:
    st.markdown(f"<small style='color:#aaa;'>{desc_txt}</small>", unsafe_allow_html=True)
with raf_c3:
    if st.button("⚡ +3 iter.", key="sim_raf3", use_container_width=True, help="Ráfaga de 3 iteraciones"):
        _rafaga(3); st.rerun()
with raf_c5:
    if st.button("⚡ +5 iter.", key="sim_raf5", use_container_width=True, help="Ráfaga de 5 iteraciones"):
        _rafaga(5); st.rerun()
with raf_c10:
    if st.button("⚡ +10 iter.", key="sim_raf10", use_container_width=True, help="Ráfaga de 10 iteraciones"):
        _rafaga(10); st.rerun()
with raf_cx:
    st.markdown("<small style='color:#666;'>Ejecuta N pasos automáticos con el escenario actual</small>",
                unsafe_allow_html=True)

st.markdown('<div class="scenario-footer"></div>', unsafe_allow_html=True)

# =============================================================================
# LAYOUT PRINCIPAL
# =============================================================================
col_izq, col_der = st.columns([4, 8], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
#  PANEL IZQUIERDO — Contexto + Indicadores + Acciones
# ─────────────────────────────────────────────────────────────────────────────
with col_izq:

    with st.expander("📁 Contexto del Proceso", expanded=False):
        st.session_state["sim_periodo"] = st.text_input(
            "Periodo Académico", value=st.session_state["sim_periodo"], key="sim_inp_periodo",
        )
        st.session_state["sim_proceso"] = st.text_input(
            "Proceso a Evaluar", value=st.session_state["sim_proceso"], key="sim_inp_proceso",
        )

    # — Malla de Eficiencia (ME)
    st.markdown(
        '<p style="font-weight:700;color:#90caf9;background:#1a237e22;'
        'padding:4px 8px;border-radius:5px;border-left:3px solid #3b82f6;margin-bottom:4px;">'
        '🔵 Malla de Eficiencia (ME) → Ortogonalidad</p>',
        unsafe_allow_html=True,
    )
    for qid, lbl in _ME_ITEMS:
        st.slider(lbl, 1, 5, key=f"sim_{qid}", on_change=_on_slider)

    # — Simbiosis y Gestión (SG)
    st.markdown(
        '<p style="font-weight:700;color:#a5d6a7;background:#1b5e2022;'
        'padding:4px 8px;border-radius:5px;border-left:3px solid #10b981;margin-bottom:4px;margin-top:8px;">'
        '🟢 Simbiosis y Gestión (SG) → Sicofancia</p>',
        unsafe_allow_html=True,
    )
    for qid, lbl in _SG_ITEMS:
        st.slider(lbl, 1, 5, key=f"sim_{qid}", on_change=_on_slider)

    # — Fricción y Riesgo (FR)
    st.markdown(
        '<p style="font-weight:700;color:#ef9a9a;background:#b71c1c22;'
        'padding:4px 8px;border-radius:5px;border-left:3px solid #ef4444;margin-bottom:2px;margin-top:8px;">'
        '🔴 Fricción y Riesgo (FR) → Redundancia</p>',
        unsafe_allow_html=True,
    )
    st.caption("Escala directa: 5 = fricción/riesgo alto → penalización máxima al FIS.")
    for qid, lbl in _FR_ITEMS:
        st.slider(lbl, 1, 5, key=f"sim_{qid}", on_change=_on_slider)

    st.divider()

    # — Botones de acción
    iters    = st.session_state["sim_iteraciones"]
    last_t   = iters[-1]["t"]

    if st.button(
        f"▶️ Capturar Iteración (Día {last_t + 1})",
        type="primary", use_container_width=True, key="sim_btn_capturar",
    ):
        qs    = _qs_sesion()
        iters = list(st.session_state["sim_iteraciones"])
        iters.append(_calcular_paso(iters, qs))
        st.session_state["sim_iteraciones"] = iters
        st.rerun()

    if st.button(
        "🧬 Simular Auto-Aprendizaje FIS",
        use_container_width=True, key="sim_btn_autoaprendizaje",
        help="Mejora ME/SG (+1) y empeora FR (+1) luego captura la iteración",
    ):
        # Calcular nuevos valores SIN tocar las claves widget ya instanciadas
        new_qs = {}
        for i in range(1, 11):
            new_qs[f"q{i}"] = min(5, st.session_state[f"sim_q{i}"] + 1)
        for i in range(11, 16):
            new_qs[f"q{i}"] = min(5, st.session_state[f"sim_q{i}"] + 1)
        # Capturar iteración con los valores mejorados
        iters = list(st.session_state["sim_iteraciones"])
        iters.append(_calcular_paso(iters, new_qs))
        st.session_state["sim_iteraciones"] = iters
        # Programar actualización de sliders para el próximo ciclo de render
        st.session_state["sim_q_pending"] = new_qs
        st.session_state["sim_escenario"] = None
        st.rerun()

    if st.button(
        "🔄 Reiniciar Cinta Forense",
        use_container_width=True, key="sim_btn_reiniciar",
    ):
        st.session_state["sim_iteraciones"] = [dict(_INITIAL_ITER)]
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PANEL DERECHO — Métricas rápidas + Gráfico + Auditoría + Cinta
# ─────────────────────────────────────────────────────────────────────────────
with col_der:
    iters = st.session_state["sim_iteraciones"]
    last  = iters[-1]
    prev  = iters[-2] if len(iters) > 1 else iters[0]

    # — Métricas rápidas
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.markdown(
        f"<div class='metric-sim'><div class='lbl'>⏱ Iteraciones</div>"
        f"<div class='val'>{last['t']}</div></div>", unsafe_allow_html=True,
    )
    mc2.markdown(
        f"<div class='metric-sim'><div class='lbl'>🙋 U₁ Humano</div>"
        f"<div class='val' style='color:#9ca3af;'>{last['U1']:.3f}</div></div>", unsafe_allow_html=True,
    )
    mc3.markdown(
        f"<div class='metric-sim'><div class='lbl'>🤖 U₂ IA Pura</div>"
        f"<div class='val' style='color:#ef9a9a;'>{last['U2']:.3f}</div></div>", unsafe_allow_html=True,
    )
    mc4.markdown(
        f"<div class='metric-sim'><div class='lbl'>🧬 U₃ FIS</div>"
        f"<div class='val' style='color:#90caf9;font-size:1.6rem;'>{last['U3']:.3f}</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # — Gráfico de evolución
    st.markdown(
        '<p style="font-weight:700;color:#eee;margin-bottom:6px;">📈 Evolución de U(t)</p>',
        unsafe_allow_html=True,
    )

    ts  = [d["t"]  for d in iters]
    u1s = [d["U1"] for d in iters]
    u2s = [d["U2"] for d in iters]
    u3s = [d["U3"] for d in iters]

    fig, ax = plt.subplots(figsize=(9, 3.4))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    ax.plot(ts, u1s, color="#9ca3af", linewidth=2,   marker="o", markersize=4,   label="F1 Humano")
    ax.plot(ts, u2s, color="#ef4444", linewidth=2,   marker="o", markersize=4,   label="F2 IA Pura")
    ax.plot(ts, u3s, color="#3b82f6", linewidth=3.5, marker="o", markersize=5.5, label="F3 FIS")
    ax.axhline(y=_K_MADUREZ, color="#10b981", linestyle="--", linewidth=1.5,
               alpha=0.75, label=f"k={_K_MADUREZ}")

    ax.set_xlim(0, max(10, ts[-1]))
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Iteración (t)", color="#888", fontsize=9)
    ax.set_ylabel("Utilidad U",    color="#888", fontsize=9)
    ax.tick_params(colors="#555", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#333")
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax.grid(axis="y", color="#2a2a3e", linewidth=0.8)
    ax.legend(
        facecolor="#1e1e2e", edgecolor="#333",
        labelcolor="white", fontsize=8, loc="upper left",
    )
    plt.tight_layout(pad=0.5)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # — Auditoría Matemática (Caja Blanca)
    if last["t"] > 0:
        v = last["vars"]
        st.markdown(f"""
<div class="audit-box">
  <p class="audit-title">🔬 Auditoría Estigmérgica — Cálculo Diferencial · Iteración t = {last['t']}</p>

  <p class="a-section">// 1. Variables Maestras Normalizadas [0,1]</p>
  <div class="a-grid">
    <div>Ortogonalidad (O): <span class="a-green">{v['O']:.3f}</span></div>
    <div>Sicofancia (S): <span class="a-red">{v['S']:.3f}</span></div>
    <div>Redundancia (R): <span class="a-red">{v['R']:.3f}</span></div>
    <div>Costo (C_c): <span class="a-red">{v['Cc']:.3f}</span></div>
  </div>

  <p class="a-section">// 2. Razón de Cambio — Flujo 3 FIS</p>
  <div class="a-block">
    <div style="color:#aaa;margin-bottom:6px;">
      Ecuación: <span style="color:#ce93d8;">dU₃/dt = (λO − μR − σS − φC_c) · (1 − U₃/k)</span>
    </div>
    <div>Sinergia = λ({_LAMBDA}) × {v['O']:.3f} = <span class="a-green">{v['sinergia']:.4f}</span></div>
    <div>Fricción = {_MU}({v['R']:.3f}) + {_SIGMA}({v['S']:.3f}) + {_PHI}({v['Cc']:.3f}) = <span class="a-red">{v['friccion']:.4f}</span></div>
    <div>F. Logístico = (1 − {prev['U3']:.3f}/{_K_MADUREZ}) = <span class="a-yellow">{v['logistica']:.4f}</span></div>
    <div class="a-result">
      <b style="color:white;">dU₃/dt = </b>
      ({v['sinergia']:.4f} − {v['friccion']:.4f}) × {v['logistica']:.4f} =
      <span class="a-blue">{last['dU3']:.5f}</span>
    </div>
  </div>

  <p class="a-section">// 3. Integración por Flujo (Euler)</p>
  <div class="a-flujos">
    <div class="a-f1">
      <div class="a-f-lbl-1">Flujo 1 (Humano)</div>
      <div>U₁ = {prev['U1']:.3f} + {last['dU1']:.4f}</div>
      <div class="a-f-val">{last['U1']:.4f}</div>
    </div>
    <div class="a-f2">
      <div class="a-f-lbl-2">Flujo 2 (IA Pura)</div>
      <div>U₂ = {prev['U2']:.3f} + {last['dU2']:.4f}</div>
      <div class="a-f-val">{last['U2']:.4f}</div>
    </div>
    <div class="a-f3">
      <div class="a-f-lbl-3">Flujo 3 (FIS)</div>
      <div>U₃ = {prev['U3']:.3f} + {last['dU3']:.4f}</div>
      <div class="a-f-val-3">{last['U3']:.4f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.info("ℹ️ Ejecute una iteración para ver la Auditoría Matemática (Caja Blanca).", icon="🔬")

    # — Cinta Forense
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📼 Cinta Forense — Historial de Iteraciones", expanded=False):
        if len(iters) > 1:
            df = pd.DataFrame([{
                "t":             d["t"],
                "U₁ Humano":    round(d["U1"], 4),
                "U₂ IA Pura":   round(d["U2"], 4),
                "U₃ FIS":       round(d["U3"], 4),
                "dU₃/dt":       round(d["dU3"], 5),
                "O (Ortog.)":   round(d["vars"]["O"],        3),
                "S (Sicof.)":   round(d["vars"]["S"],        3),
                "R (Redun.)":   round(d["vars"]["R"],        3),
                "Sinergia":     round(d["vars"]["sinergia"], 3),
                "Fricción":     round(d["vars"]["friccion"], 3),
                "F.Logístico":  round(d["vars"]["logistica"],3),
            } for d in iters])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("Sin iteraciones registradas. Capture la primera iteración para iniciar la cinta.")

# =============================================================================
# SIDEBAR — Comparte menú con el resto del portal
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding-bottom:12px;border-bottom:2px solid #8B0000;margin-bottom:16px;">
        <h2 style="margin:0;color:#ff6b6b;">🏛️ URosario</h2>
        <span style="font-size:11px;color:#aaa;">Portal FIS v8.1 · Menú</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("portal_fis.py",                  label="🏠  Inicio — Comparación",        icon="🏠")
    st.page_link("pages/00_comparacion.py",         label="📊  Comparación Detallada",        icon="📊")
    st.page_link("pages/01_flujo_humano.py",        label="🙋  Flujo 1: Humano",              icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py",    label="🤖  Flujo 2: Agentes IA",          icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",           label="🧬  Flujo 3: FIS Simbiomemésico",  icon="3️⃣")
    st.page_link("pages/04_simulador_fis.py",              label="📊  Simulador Diferencial",          icon="📊")
    st.page_link("pages/05_fabrica_agentes.py",            label="🛠️  Fábrica & Skills",             icon="🛠️")
    st.markdown("---")
    st.caption(f"Investigador: **Fredy Sarmiento**")
    st.caption(f"Motor: `{os.getenv('MODEL_NAME', 'gemini-2.5-flash')}`")
    if st.button("🗑️ Limpiar sesión simulador", key="sim_btn_clear"):
        for k in [kk for kk in st.session_state if kk.startswith("sim_")]:
            del st.session_state[k]
        st.rerun()

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div class="telemetria">
📡 <b>SIMULADOR DIFERENCIAL FIS v1.0</b> &nbsp;|&nbsp;
Motor: Ecuaciones Diferenciales Logísticas · Integración Euler &nbsp;|&nbsp;
Módulo Autocontenido · Sin dependencias del ecosistema FIS operativo
</div>
""", unsafe_allow_html=True)
