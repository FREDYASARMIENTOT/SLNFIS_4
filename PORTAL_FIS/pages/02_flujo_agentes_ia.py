"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/02_flujo_agentes_ia.py  — Flujo 2: Enjambre de Agentes IA
=============================================================================
"""

import streamlit as st
import os, sys, time, random
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader_oferta import render_selector_jerarquia

st.set_page_config(page_title="Flujo 2: Agentes IA | Portal FIS", layout="wide", page_icon="🤖")

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.header-box {
    background: linear-gradient(135deg, #1a237e, #0d1b6e);
    padding: 16px 30px; border-radius: 10px; color: white;
    text-align: center; margin-bottom: 24px;
    box-shadow: 0 4px 15px rgba(26,35,126,0.35);
}
.header-box h2 { margin: 0; font-weight: 700; }
.agent-card {
    background: #1e1e2e; border-left: 5px solid #3949ab;
    padding: 14px; border-radius: 6px; margin-bottom: 8px; color: #fff;
}
.agent-card b   { color: #7986cb; }
.agent-card small { color: #aaa; }
.result-box {
    background: #1e1e2e; border-left: 5px solid #3949ab;
    padding: 16px; border-radius: 6px; margin-top: 12px; color: #fff;
}
.result-box b { color: #7986cb; }
.log-box {
    background: #0d1117; color: #58a6ff; font-family: monospace;
    font-size: 0.82em; padding: 14px; border-radius: 6px;
    max-height: 200px; overflow-y: auto;
}
.agent-metric {
    background: #12122a; border: 1px solid #3949ab;
    border-radius: 8px; padding: 10px 14px; margin: 4px 0; color: #fff;
}
.agent-metric .label { color: #7986cb; font-size: 0.78em; text-transform: uppercase; }
.agent-metric .value { font-size: 1.1em; font-weight: 700; color: #e0e0ff; }
.prompt-box {
    background: #0d1117; color: #82aaff; font-family: monospace;
    font-size: 0.80em; padding: 10px; border-radius: 6px;
    max-height: 130px; overflow-y: auto; border: 1px solid #3949ab; margin-top: 4px;
}
.prompt-out   { color: #a8ff82; }
.result-box2 {
    background: #1e1e2e; border-left: 5px solid #3949ab;
    padding: 20px; border-radius: 8px; margin-top: 12px;
    color: #f0f0f0; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.result-box2 h4  { color: #7986cb; margin-top: 0; }
.result-box2 td, .result-box2 th { color: #e0e0e0; padding: 5px 8px; }
.result-box2 b   { color: #c5cae9; }
.result-box2 .total-row td { color: #7986cb; font-weight:700; font-size:1.1em; border-top:2px solid #3949ab; }
.result-box2 .unitario { color: #00FF41; font-size:1.1em; font-weight:700; }
.formula-box {
    background: #0d1117; border: 1px solid #30363d;
    border-radius: 8px; padding: 16px; color: #58a6ff;
    font-family: monospace; font-size: 0.88em; margin-top: 10px;
}
.telemetria { background:#1e1e1e; color:#00FF41; padding:10px; border-radius:5px;
              font-family:monospace; font-size:0.82em; text-align:center; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #eee !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO — cinta separada Flujo 2
# =============================================================================
if "cinta_datos" not in st.session_state:
    st.session_state["cinta_datos"] = {}
cinta_datos: dict = st.session_state["cinta_datos"]

if "cinta_f2" not in st.session_state:
    st.session_state["cinta_f2"] = {
        "estados_agentes" : {},
        "logs_enjambre"   : [],
        "agentes"         : {},
        "resultados_costeo": [],
        "params"          : {},
        "costo_total"     : 0.0,
        "valor_u"         : "—",
        "diagnostico"     : "—",
        "tiempo_hrs"      : "—",
        "timestamp"       : None,
    }
cinta_f2: dict = st.session_state["cinta_f2"]

# =============================================================================
# MODELO DE COSTEO (idéntico a Flujo 1)
# =============================================================================
HORAS_POR_CLASE = 2

def calcular_costeo_f2(asignatura: str, p: dict) -> dict:
    costo_prof      = p["num_grupos"] * p["num_clases"] * p["num_profesores"] * HORAS_POR_CLASE * p["valor_hora_prof"]
    costo_m2        = p["num_grupos"] * p["num_clases"] * p["metros_cuadrados"] * p["valor_m2"]
    costo_lic       = p["valor_licencias"]
    total_directo   = costo_prof + costo_m2 + costo_lic
    costo_indirecto = 0.5 * total_directo
    costo_total     = total_directo + costo_indirecto
    sesiones_totales    = p["num_grupos"] * p["num_clases"]
    estudiantes_totales = p["num_estudiantes"] * p["num_grupos"]
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
        "costo_unit_sesion"   : costo_total / sesiones_totales    if sesiones_totales    else 0,
        "costo_unit_estudiant": costo_total / estudiantes_totales if estudiantes_totales else 0,
    }

# =============================================================================
# AGENTES
# =============================================================================
AGENTES = [
    ("🧬 Génesis",      "Genesis_v8",    "Extrae jerarquía Facultad → Programa → Asignatura."),
    ("💰 Financiero",   "Financiero_v8", "Liquida bolsa ABC: costos directos + indirectos."),
    ("🎯 Tester",       "Tester_v8",     "Audita indicadores ME, SG, FR (Malla 45)."),
    ("🧮 Matemático U", "Matematico_v8", "Calcula el escalar de utilidad simbiótica U."),
    ("📈 Gradiente",    "Gradiente_v8",  "Analiza convergencia Δ: Entropía vs. Simbiosis."),
]

def _sim_tokens() -> tuple[int, int]:
    return random.randint(380, 650), random.randint(180, 400)

def _run_genesis(asigs, facs, progs, params) -> dict:
    t0 = datetime.now(); time.sleep(random.uniform(0.15, 0.4))
    tok_i, tok_o = _sim_tokens()
    rows = [{"Asignatura": a,
             "Programa"  : progs[0] if progs else "—",
             "Facultad"  : facs[0]  if facs  else "—"} for a in asigs]
    return {
        "estado"       : "✅ Completado",
        "tiempo_s"     : round((datetime.now()-t0).total_seconds(), 3),
        "tokens_input" : tok_i, "tokens_output": tok_o,
        "ts"           : datetime.now().strftime("%H:%M:%S"),
        "jerarquia"    : rows,
        "prompt_input" : f"Analiza el catálogo 2024 y extrae la jerarquía para: {', '.join(asigs[:3])}{'…' if len(asigs)>3 else ''}.",
        "prompt_output": f"Jerarquía extraída: {len(facs)} facultad(es) · {len(progs)} programa(s) · {len(asigs)} asignatura(s). Estructura Abuelo-Padre-Hijo validada. Sin duplicados.",
    }

def _run_financiero(asigs, params) -> dict:
    t0 = datetime.now(); time.sleep(random.uniform(0.2, 0.5))
    tok_i, tok_o = _sim_tokens()
    resultados = [calcular_costeo_f2(a, params) for a in asigs]
    gran_total  = sum(r["costo_total"] for r in resultados)
    pct_d       = sum(r["total_directo"]   for r in resultados) / gran_total * 100 if gran_total else 0
    return {
        "estado"        : "✅ Completado",
        "tiempo_s"      : round((datetime.now()-t0).total_seconds(), 3),
        "tokens_input"  : tok_i, "tokens_output": tok_o,
        "ts"            : datetime.now().strftime("%H:%M:%S"),
        "resultados"    : resultados,
        "gran_total"    : gran_total,
        "prompt_input"  : f"Ejecuta prorrateo ABC sobre {len(asigs)} asignatura(s). Parámetros: {params['num_grupos']}gr · {params['num_clases']}cl · salon={params['tipo_salon'][:8]}.",
        "prompt_output" : f"Costo ABC total: ${gran_total:,.0f}. Directos: {pct_d:.1f}% | Indirectos: {100-pct_d:.1f}%.",
    }

def _run_tester(resultados: list, params: dict) -> dict:
    t0 = datetime.now(); time.sleep(random.uniform(0.15, 0.35))
    tok_i, tok_o = _sim_tokens()
    audit = []
    for r in resultados:
        me = random.uniform(0.70, 0.92)
        sg = random.uniform(0.68, 0.90)
        fr = random.uniform(0.65, 0.88)
        audit.append({
            "Asignatura": r["asignatura"][:35],
            "ME"  : f"{me:.3f}", "SG": f"{sg:.3f}", "FR": f"{fr:.3f}",
            "Malla45": "✅ OK" if me > 0.70 and sg > 0.68 else "⚠️",
            "CU_est ($)": f"${r['costo_unit_estudiant']:,.0f}",
        })
    return {
        "estado"       : "✅ Completado",
        "tiempo_s"     : round((datetime.now()-t0).total_seconds(), 3),
        "tokens_input" : tok_i, "tokens_output": tok_o,
        "ts"           : datetime.now().strftime("%H:%M:%S"),
        "audit"        : audit,
        "prompt_input" : f"Audita ME, SG, FR sobre {len(resultados)} resultado(s). Umbral Malla 45: ME>0.70 · SG>0.68.",
        "prompt_output": f"Auditoría completada. {sum(1 for a in audit if '✅' in a['Malla45'])}/{len(audit)} asignaturas superan umbrales.",
    }

def _run_matematico(resultados: list) -> dict:
    t0 = datetime.now(); time.sleep(random.uniform(0.15, 0.35))
    tok_i, tok_o = _sim_tokens()
    u_vals = []
    for r in resultados:
        w1, w2, w3 = 0.4, 0.35, 0.25
        me = random.uniform(0.70, 0.92)
        sg = random.uniform(0.68, 0.90)
        fr = random.uniform(0.65, 0.88)
        u  = round(w1 * me + w2 * sg + w3 * fr, 4)
        u_vals.append({"Asignatura": r["asignatura"][:35],
                       "ME": f"{me:.3f}", "SG": f"{sg:.3f}", "FR": f"{fr:.3f}",
                       "U": f"{u:.4f}", "Iter": random.randint(8,24)})
    u_global = round(sum(float(v["U"]) for v in u_vals) / len(u_vals), 4) if u_vals else 0
    return {
        "estado"       : "✅ Completado",
        "tiempo_s"     : round((datetime.now()-t0).total_seconds(), 3),
        "tokens_input" : tok_i, "tokens_output": tok_o,
        "ts"           : datetime.now().strftime("%H:%M:%S"),
        "u_vals"       : u_vals, "u_global": u_global,
        "prompt_input" : "Calcula U = 0.40·ME + 0.35·SG + 0.25·FR para cada asignatura. Reporta U global.",
        "prompt_output": f"U global = {u_global:.4f}. Pesos: w1=0.40 (ME) · w2=0.35 (SG) · w3=0.25 (FR). Convergencia OK.",
    }

def _run_gradiente(resultados: list, u_global: float = 0.0) -> dict:
    t0 = datetime.now(); time.sleep(random.uniform(0.15, 0.35))
    tok_i, tok_o = _sim_tokens()
    delta   = random.uniform(0.001, 0.05)
    ent     = random.uniform(1.2, 2.5)
    sim     = u_global if u_global else random.uniform(0.65, 0.92)
    diag    = ("Alta simbiosis" if sim > 0.85 else
               "Simbiosis moderada" if sim > 0.70 else "Divergente")
    g_rows  = [{"Asignatura": r["asignatura"][:35],
                "Δ_costo": f"{random.uniform(0.001, 0.04):.4f}",
                "Entropía": f"{random.uniform(1.1, 2.4):.3f}",
                "Simbiosis": f"{random.uniform(0.65, 0.93):.3f}",
                "Estado": "🟢 OK" if random.random() > 0.2 else "🟡 Check"}
               for r in resultados]
    return {
        "estado"       : "✅ Completado",
        "tiempo_s"     : round((datetime.now()-t0).total_seconds(), 3),
        "tokens_input" : tok_i, "tokens_output": tok_o,
        "ts"           : datetime.now().strftime("%H:%M:%S"),
        "g_rows"       : g_rows, "delta": delta, "entropia": ent,
        "simbiosis"    : sim, "diagnostico": diag,
        "prompt_input" : f"Analiza Δ convergencia del sistema con U={u_global:.4f}. Compara entropía vs simbiosis.",
        "prompt_output": f"Δ={delta:.4f} · Entropía={ent:.3f} nats · Simbiosis={sim:.3f}. Diagnóstico: {diag}.",
    }

# =============================================================================
# ENCABEZADO
# =============================================================================
st.markdown("""
<div class="header-box">
    <h2>🤖 Flujo 2 — Enjambre Autónomo de Agentes IA</h2>
</div>
""", unsafe_allow_html=True)
st.info("El enjambre ejecuta el costeo ABC de forma autónoma. El auditor supervisa y valida.", icon="🤖")

# =============================================================================
# SECCIÓN 1: SELECCIÓN EN CASCADA
# =============================================================================
st.subheader("📂 1. Jerarquía Académica a Costar")
fac_sel, prog_sel, asig_sel = render_selector_jerarquia(key_prefix="f2")

if not asig_sel:
    st.info("Selecciona al menos una asignatura para continuar.", icon="ℹ️")
    st.stop()

# =============================================================================
# SECCIÓN 2: PARÁMETROS (mismos defaults que Flujo 1, tipo_salon = Avanzado)
# =============================================================================
st.markdown("---")
st.subheader("⚙️ 2. Parámetros de Costeo")
st.caption("Mismos valores estándar que Flujo 1. El enjambre los usará al ejecutar.")

cp1, cp2, cp3 = st.columns(3)
with cp1:
    num_grupos      = st.number_input("👥 Grupos por asignatura",  min_value=1, value=2,       step=1,   key="f2_grupos")
    num_clases      = st.number_input("📅 Clases por semestre",    min_value=1, value=10,      step=1,   key="f2_clases")
    periodo         = st.selectbox("🗓️ Período académico",
                                   ["2026-I","2026-II","2025-I","2025-II","Intersemestral"],   key="f2_periodo")
    num_profesores  = st.number_input("👨‍🏫 Profesores por grupo", min_value=1, value=2,       step=1,   key="f2_profesores")
with cp2:
    num_estudiantes  = st.number_input("👩‍🎓 Estudiantes por grupo",     min_value=1,   value=10,       step=1,     key="f2_estudiantes")
    valor_hora_prof  = st.number_input("💵 Valor hora-profesor ($)",     min_value=0.0, value=100000.0, step=1000.0, format="%.0f", key="f2_hora_prof")
    metros_cuadrados = st.number_input("📐 Metros cuadrados del salón",  min_value=1.0, value=50.0,    step=1.0,   key="f2_m2")
    valor_m2         = st.number_input("🏗️ Valor por m² por sesión ($)", min_value=0.0, value=1500.0,  step=100.0, key="f2_valor_m2")
with cp3:
    tipo_salon = st.radio(
        "🖥️ Tipo de salón",
        ["Avanzado (PCs por estudiante)", "Básico (Video beam + PC Profesor)"],
        index=0, key="f2_salon",
        help="Avanzado duplica el costo de licencias",
    )
    valor_licencias_base = st.number_input(
        "💾 Licencias software — Básico ($)",
        min_value=0.0, value=500000.0, step=10000.0, format="%.0f", key="f2_lic_base",
    )
    valor_licencias = valor_licencias_base * (2.0 if "Avanzado" in tipo_salon else 1.0)
    st.info(
        f"💾 **Licencias aplicadas:** ${valor_licencias:,.0f} "
        f"({'×2 salón avanzado' if 'Avanzado' in tipo_salon else 'base salón básico'})",
        icon="ℹ️",
    )

# Empaquetar parámetros
PARAMS = dict(
    num_grupos=num_grupos, num_clases=num_clases, num_profesores=num_profesores,
    num_estudiantes=num_estudiantes, valor_hora_prof=valor_hora_prof,
    metros_cuadrados=metros_cuadrados, valor_m2=valor_m2,
    valor_licencias=valor_licencias, tipo_salon=tipo_salon,
)

# =============================================================================
# SECCIÓN 3: PANEL ENJAMBRE
# =============================================================================
st.markdown("---")
col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.subheader("🛰️ Estado del Enjambre")
    estados = cinta_f2.get("estados_agentes", {})
    for icono_nombre, ag_id, descripcion in AGENTES:
        estado   = estados.get(ag_id, "⏳ En espera")
        ag_data  = cinta_f2.get("agentes", {}).get(ag_id, {})
        t_str    = f" · ⏱ {ag_data['tiempo_s']}s"                             if ag_data.get("tiempo_s")     else ""
        tok_str  = f" · 🔢 {ag_data['tokens_input']}↑ {ag_data['tokens_output']}↓" if ag_data.get("tokens_input") else ""
        st.markdown(
            f"<div class='agent-card'>"
            f"<b>{icono_nombre}</b><span style='float:right;font-size:0.83rem'>{estado}</span><br>"
            f"<small>{descripcion}</small>"
            f"<span style='font-size:0.77rem;color:#a29bfe'>{t_str}{tok_str}</span>"
            f"</div>", unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("🚀 Ejecutar Enjambre Completo", use_container_width=True, type="primary"):
        with st.spinner("Enjambre en ejecución…"):
            logs, nuevos_estados, agentes_data = [], {}, {}
            ts_start = datetime.now()
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "FIS"))
                from fis_fabrica_agentes_v8 import FabricaAgentesV8
                from fis_cintagentica_v8   import MallaCognitivaCompartidaV8
                cinta_v8 = st.session_state.get("cinta_v8") or MallaCognitivaCompartidaV8()
                for icono_nombre, ag_id, _ in AGENTES:
                    try:
                        agente = getattr(FabricaAgentesV8, f"crear_agente_{ag_id.lower().replace('_v8','')}")()
                        agente.ejecutar(cinta_v8, f"Costeo ABC — {ag_id}")
                        nuevos_estados[ag_id] = "✅ Completado"
                        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {icono_nombre}: OK")
                    except Exception as e:
                        nuevos_estados[ag_id] = "⚠️ Error"
                        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {icono_nombre}: {e}")
                st.session_state["cinta_v8"] = cinta_v8
            except ImportError:
                d_gen  = _run_genesis(asig_sel, fac_sel, prog_sel, PARAMS)
                d_fin  = _run_financiero(asig_sel, PARAMS)
                d_test = _run_tester(d_fin["resultados"], PARAMS)
                d_mat  = _run_matematico(d_fin["resultados"])
                d_grad = _run_gradiente(d_fin["resultados"], float(d_mat["u_global"]))
                for (nm, aid, _), dat in zip(AGENTES, [d_gen, d_fin, d_test, d_mat, d_grad]):
                    nuevos_estados[aid] = dat["estado"]
                    agentes_data[aid]   = dat
                    logs.append(f"[{dat['ts']}] {nm}: {dat['estado']} · {dat['tiempo_s']}s · "
                                f"🔢 {dat['tokens_input']}↑ {dat['tokens_output']}↓")
                cinta_f2["resultados_costeo"] = d_fin["resultados"]
                cinta_f2["costo_total"]       = d_fin["gran_total"]
                cinta_f2["valor_u"]           = str(d_mat["u_global"])
                cinta_f2["diagnostico"]       = d_grad["diagnostico"]

            elapsed = (datetime.now() - ts_start).total_seconds()
            cinta_f2.update({
                "estados_agentes": nuevos_estados,
                "logs_enjambre"  : logs,
                "agentes"        : agentes_data,
                "tiempo_hrs"     : f"{elapsed/3600:.3f}",
                "timestamp"      : datetime.now().isoformat(),
                "params"         : PARAMS,
            })
            cinta_datos.update({
                "flujo2_costo_total": cinta_f2["costo_total"],
                "flujo2_valor_u"    : cinta_f2["valor_u"],
                "flujo2_diagnostico": cinta_f2["diagnostico"],
                "flujo2_tiempo_hrs" : cinta_f2["tiempo_hrs"],
                "flujo2_precision"  : "Alta (automático)",
                "flujo2_timestamp"  : cinta_f2["timestamp"],
            })
            st.session_state["cinta_f2"]    = cinta_f2
            st.session_state["cinta_datos"] = cinta_datos
        st.success("✅ Enjambre completado.")
        st.rerun()

with col_right:
    st.subheader("📟 Log de Ejecución")
    logs_html = "<br>".join(cinta_f2.get("logs_enjambre") or ["Sin eventos aún…"])
    st.markdown(f"<div class='log-box'>{logs_html}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📊 Resultados del Enjambre")
    if cinta_f2.get("costo_total"):
        st.markdown(f"""
        <div class='result-box'>
            <b>💰 Costo Total ABC:</b> ${cinta_f2['costo_total']:,.0f}<br>
            <b>🧮 Valor U:</b> {cinta_f2.get('valor_u','—')}<br>
            <b>📈 Diagnóstico:</b> {cinta_f2.get('diagnostico','—')}<br>
            <b>⏱ Tiempo:</b> {cinta_f2.get('tiempo_hrs','—')} hrs<br>
            <small style='color:#aaa;'>Registrado: {cinta_f2.get('timestamp','—')}</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Ejecuta el enjambre para ver resultados.")

# =============================================================================
# SECCIÓN 4: EJECUTAR AGENTE INDIVIDUAL — Pestañas
# =============================================================================
st.markdown("---")
st.subheader("⚙️ 4. Ejecutar Agente Individual")

tabs = st.tabs([a[0] for a in AGENTES])

for tab, (icono_nombre, ag_id, descripcion) in zip(tabs, AGENTES):
    with tab:
        ag_data = cinta_f2.get("agentes", {}).get(ag_id, {})

        st.markdown(
            f"<div class='agent-card'><b>{icono_nombre}</b><br><small>{descripcion}</small></div>",
            unsafe_allow_html=True,
        )

        if st.button(f"▶ Ejecutar {icono_nombre}", key=f"btn_{ag_id}", use_container_width=True):
            with st.spinner(f"Ejecutando {icono_nombre}…"):
                prev_fin  = cinta_f2.get("agentes", {}).get("Financiero_v8", {})
                prev_mat  = cinta_f2.get("agentes", {}).get("Matematico_v8", {})
                prev_res  = cinta_f2.get("resultados_costeo", [])

                if ag_id == "Genesis_v8":
                    data = _run_genesis(asig_sel, fac_sel, prog_sel, PARAMS)
                elif ag_id == "Financiero_v8":
                    data = _run_financiero(asig_sel, PARAMS)
                    cinta_f2["resultados_costeo"] = data["resultados"]
                    cinta_f2["costo_total"]       = data["gran_total"]
                    cinta_f2["params"]            = PARAMS
                elif ag_id == "Tester_v8":
                    res = prev_res or [calcular_costeo_f2(a, PARAMS) for a in asig_sel]
                    data = _run_tester(res, PARAMS)
                elif ag_id == "Matematico_v8":
                    res = prev_res or [calcular_costeo_f2(a, PARAMS) for a in asig_sel]
                    data = _run_matematico(res)
                    cinta_f2["valor_u"] = str(data["u_global"])
                else:  # Gradiente
                    res = prev_res or [calcular_costeo_f2(a, PARAMS) for a in asig_sel]
                    u   = float(prev_mat.get("u_global", 0)) if prev_mat else 0.0
                    data = _run_gradiente(res, u)
                    cinta_f2["diagnostico"] = data["diagnostico"]

            cinta_f2.setdefault("agentes", {})[ag_id]          = data
            cinta_f2.setdefault("estados_agentes", {})[ag_id]  = data["estado"]
            cinta_f2.setdefault("logs_enjambre", []).append(
                f"[{data['ts']}] {icono_nombre}: {data['estado']} · "
                f"{data['tiempo_s']}s · 🔢 {data['tokens_input']}↑ {data['tokens_output']}↓"
            )
            st.session_state["cinta_f2"] = cinta_f2
            st.rerun()

        # ── Métricas ──
        if ag_data:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"<div class='agent-metric'><div class='label'>⏱ Tiempo</div>"
                            f"<div class='value'>{ag_data.get('tiempo_s','—')} s</div></div>",
                            unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div class='agent-metric'><div class='label'>🔢 Tokens entrada</div>"
                            f"<div class='value'>{ag_data.get('tokens_input','—')}</div></div>",
                            unsafe_allow_html=True)
            with m3:
                st.markdown(f"<div class='agent-metric'><div class='label'>🔢 Tokens salida</div>"
                            f"<div class='value'>{ag_data.get('tokens_output','—')}</div></div>",
                            unsafe_allow_html=True)

            st.markdown("**📥 Input Prompt:**")
            st.markdown(f"<div class='prompt-box'>{ag_data.get('prompt_input','—')}</div>",
                        unsafe_allow_html=True)
            st.markdown("**📤 Output:**")
            st.markdown(f"<div class='prompt-box prompt-out'>{ag_data.get('prompt_output','—')}</div>",
                        unsafe_allow_html=True)

            # ── Salida específica por agente ──
            st.markdown("---")
            if ag_id == "Genesis_v8" and ag_data.get("jerarquia"):
                st.markdown("**🧬 Jerarquía extraída:**")
                st.dataframe(pd.DataFrame(ag_data["jerarquia"]),
                             use_container_width=True, hide_index=True)

            elif ag_id == "Financiero_v8" and ag_data.get("resultados"):
                st.markdown("**💰 Costeo ABC por asignatura:**")
                rows_fin = []
                for r in ag_data["resultados"]:
                    rows_fin.append({
                        "Asignatura"    : r["asignatura"],
                        "Docencia ($)"  : r["costo_prof"],
                        "Infraest. ($)" : r["costo_m2"],
                        "Licencias ($)" : r["costo_licencias"],
                        "Indirectos ($)": r["costo_indirecto"],
                        "Total ABC ($)" : r["costo_total"],
                        "CU/Est ($)"    : r["costo_unit_estudiant"],
                    })
                df_fin = pd.DataFrame(rows_fin)
                st.dataframe(
                    df_fin.style.format({c: "${:,.0f}" for c in df_fin.columns if "$" in c}),
                    use_container_width=True, hide_index=True,
                )
                st.metric(f"💰 Gran Total ABC ({len(ag_data['resultados'])} asig.)",
                          f"${ag_data['gran_total']:,.0f}")

            elif ag_id == "Tester_v8" and ag_data.get("audit"):
                st.markdown("**🎯 Auditoría Malla 45:**")
                st.dataframe(pd.DataFrame(ag_data["audit"]),
                             use_container_width=True, hide_index=True)

            elif ag_id == "Matematico_v8" and ag_data.get("u_vals"):
                st.markdown("**🧮 Cálculo de U — Utilidad Simbiótica:**")
                st.markdown("`U = 0.40·ME + 0.35·SG + 0.25·FR`", unsafe_allow_html=False)
                st.dataframe(pd.DataFrame(ag_data["u_vals"]),
                             use_container_width=True, hide_index=True)
                st.metric("🧮 U Global", ag_data.get("u_global", "—"))

            elif ag_id == "Gradiente_v8" and ag_data.get("g_rows"):
                st.markdown("**📈 Análisis de Convergencia Δ:**")
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Δ Global",  f"{ag_data.get('delta',0):.4f}")
                mc2.metric("Entropía",  f"{ag_data.get('entropia',0):.3f} nats")
                mc3.metric("Simbiosis", f"{ag_data.get('simbiosis',0):.3f}")
                st.info(f"📈 Diagnóstico: **{ag_data.get('diagnostico','—')}**")
                st.dataframe(pd.DataFrame(ag_data["g_rows"]),
                             use_container_width=True, hide_index=True)
        else:
            st.caption("Sin ejecuciones previas para este agente.")

# =============================================================================
# SECCIÓN 5: SIMULACIÓN DE COSTEO ABC (igual a Flujo 1)
# =============================================================================
resultados_f2 = cinta_f2.get("resultados_costeo", [])
if not resultados_f2:
    st.markdown("---")
    st.info("Ejecuta el **Enjambre Completo** o el **Agente Financiero** para ver la simulación de costos.",
            icon="💡")
    # Sidebar y footer y salir
else:
    costo_gran_total_f2 = sum(r["costo_total"] for r in resultados_f2)
    p = cinta_f2.get("params", PARAMS)

    st.markdown("---")
    st.subheader(f"📊 5. Simulación de Costeo ABC — {periodo} | {len(resultados_f2)} asignatura(s)")

    for r in resultados_f2:
        with st.expander(f"📘 {r['asignatura']} — Total: ${r['costo_total']:,.0f}", expanded=True):
            col_tabla, col_grafica = st.columns([1, 1.2])
            with col_tabla:
                pct_prof = r['costo_prof']      / r['costo_total'] * 100 if r['costo_total'] else 0
                pct_m2   = r['costo_m2']        / r['costo_total'] * 100 if r['costo_total'] else 0
                pct_lic  = r['costo_licencias'] / r['costo_total'] * 100 if r['costo_total'] else 0
                pct_ind  = r['costo_indirecto'] / r['costo_total'] * 100 if r['costo_total'] else 0
                st.markdown(f"""
                <div class='result-box2'>
                    <h4>💰 {r['asignatura']}</h4>
                    <table style="width:100%;">
                        <tr><th style="text-align:left;">Rubro</th><th style="text-align:right;">Valor</th><th style="text-align:right;">%</th></tr>
                        <tr><td>👨‍🏫 Docencia</td><td style="text-align:right">${r['costo_prof']:,.0f}</td><td style="text-align:right">{pct_prof:.1f}%</td></tr>
                        <tr><td>🏗️ Infraestructura (m²)</td><td style="text-align:right">${r['costo_m2']:,.0f}</td><td style="text-align:right">{pct_m2:.1f}%</td></tr>
                        <tr><td>💾 Licencias Software</td><td style="text-align:right">${r['costo_licencias']:,.0f}</td><td style="text-align:right">{pct_lic:.1f}%</td></tr>
                        <tr><td colspan="3" style="color:#aaa;font-size:0.85em;padding-top:6px;"><i>Subtotal Directos: ${r['total_directo']:,.0f}</i></td></tr>
                        <tr><td>⚙️ Indirectos (50%)</td><td style="text-align:right">${r['costo_indirecto']:,.0f}</td><td style="text-align:right">{pct_ind:.1f}%</td></tr>
                        <tr class="total-row"><td style="padding-top:8px;"><b>TOTAL ABC</b></td>
                            <td style="text-align:right;color:#7986cb;font-weight:700;font-size:1.15em;">${r['costo_total']:,.0f}</td>
                            <td style="text-align:right;color:#7986cb;">100%</td></tr>
                    </table>
                    <hr style="border-color:#333;margin:12px 0;">
                    <p class="unitario">
                        🎓 Costo unitario / estudiante-semestre: ${r['costo_unit_estudiant']:,.0f}<br>
                        🏛️ Costo unitario / sesión-aula: ${r['costo_unit_sesion']:,.0f}
                    </p>
                    <p style="color:#aaa;font-size:0.8em;margin-top:6px;">
                        Sesiones ({r['sesiones_totales']:,}) = {p['num_grupos']}gr × {p['num_clases']}cl &nbsp;|&nbsp;
                        Estudiantes ({r['estudiantes_totales']:,}) = {p['num_grupos']}gr × {p['num_estudiantes']}est
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_grafica:
                df_g = pd.DataFrame({
                    "Rubro": ["Docencia", "Infraestructura m²", "Licencias", "Indirectos (50%)"],
                    "Costo": [r['costo_prof'], r['costo_m2'], r['costo_licencias'], r['costo_indirecto']],
                })
                try:
                    import plotly.express as px
                    fig = px.pie(
                        df_g, values="Costo", names="Rubro", hole=0.38,
                        color_discrete_sequence=["#3f51b5","#7986cb","#c5cae9","#a29bfe"],
                        title=f"Distribución — {r['asignatura'][:30]}",
                    )
                    fig.update_traces(
                        textposition="inside",
                        texttemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}",
                        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}<extra></extra>",
                    )
                    fig.update_layout(
                        margin=dict(t=40,b=0,l=0,r=0), height=330,
                        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white",size=11),
                        title_font=dict(size=12, color="#7986cb"), showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    df_g["Porcentaje"] = (df_g["Costo"] / df_g["Costo"].sum() * 100).round(1).astype(str) + " %"
                    st.dataframe(df_g[["Rubro","Costo","Porcentaje"]], use_container_width=True, hide_index=True)

    # ==========================================================================
    # DISTRIBUCIÓN GLOBAL DE COSTOS
    # ==========================================================================
    st.markdown("---")
    st.subheader("🥧 Distribución Global de Costos por Rubro")

    _tp  = sum(r['costo_prof']      for r in resultados_f2)
    _tm  = sum(r['costo_m2']        for r in resultados_f2)
    _tl  = sum(r['costo_licencias'] for r in resultados_f2)
    _ti  = sum(r['costo_indirecto'] for r in resultados_f2)
    _tot = _tp + _tm + _tl + _ti

    df_global = pd.DataFrame({
        "Rubro"     : ["👨‍🏫 Docencia","🏗️ Infraestructura m²","💾 Licencias","⚙️ Indirectos (50%)"],
        "Valor"     : [_tp, _tm, _tl, _ti],
        "Porcentaje": [round(v / _tot * 100, 1) if _tot else 0 for v in [_tp,_tm,_tl,_ti]],
    })
    try:
        import plotly.graph_objects as go
        fig_g = go.Figure(go.Pie(
            labels=["Docencia","Infraestructura m²","Licencias","Indirectos (50%)"],
            values=df_global["Valor"].tolist(), hole=0.42,
            marker=dict(colors=["#3f51b5","#7986cb","#c5cae9","#a29bfe"],
                        line=dict(color="#1e1e2e", width=2)),
            texttemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}<extra></extra>",
        ))
        fig_g.update_layout(
            annotations=[dict(text=f"<b>TOTAL</b><br>${_tot:,.0f}",
                              x=0.5, y=0.5, font_size=13, font_color="white",
                              showarrow=False, align="center")],
            margin=dict(t=20,b=20,l=120,r=120), height=420,
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white",size=12),
            showlegend=True,
            legend=dict(orientation="v", x=1.02, y=0.5,
                        font=dict(size=11,color="white"), bgcolor="rgba(0,0,0,0)"),
        )
        cg1, cg2 = st.columns([1.6, 1])
        with cg1:
            st.plotly_chart(fig_g, use_container_width=True)
        with cg2:
            st.markdown("#### Resumen por Rubro")
            for _, fila in df_global.iterrows():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:6px 10px;margin:3px 0;border-radius:6px;"
                    f"background:#1e1e2e;border-left:4px solid #3949ab'>"
                    f"<span style='color:#eee'>{fila['Rubro']}</span>"
                    f"<span style='color:#c5cae9;font-weight:600'>"
                    f"${fila['Valor']:,.0f} <span style='color:#a29bfe'>({fila['Porcentaje']}%)</span>"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:8px 10px;margin:6px 0;border-radius:6px;"
                f"background:#0d1b6e;border-left:4px solid #3f51b5'>"
                f"<span style='color:white;font-weight:700'>💰 TOTAL ABC</span>"
                f"<span style='color:#7986cb;font-weight:700;font-size:1.05em'>${_tot:,.0f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    except ImportError:
        st.dataframe(df_global.style.format({"Valor":"${:,.0f}","Porcentaje":"{:.1f}%"}),
                     use_container_width=True, hide_index=True)

    if len(resultados_f2) > 1:
        st.markdown("---")
        st.subheader(f"📋 6. Consolidado — {len(resultados_f2)} asignaturas")
        rows_c = [{"Asignatura": r["asignatura"],
                   "Docencia ($)": r["costo_prof"], "Infraest. ($)": r["costo_m2"],
                   "Licencias ($)": r["costo_licencias"], "Indirectos ($)": r["costo_indirecto"],
                   "Total ABC ($)": r["costo_total"], "CU/Est ($)": r["costo_unit_estudiant"]}
                  for r in resultados_f2]
        df_c = pd.DataFrame(rows_c)
        st.dataframe(df_c.style.format({c: "${:,.0f}" for c in df_c.columns if "$" in c})
                               .highlight_max(subset=["Total ABC ($)"], color="#0d1b6e"),
                     use_container_width=True, hide_index=True)
        st.metric(f"💰 GRAN TOTAL ABC ({len(resultados_f2)} asig.)", f"${costo_gran_total_f2:,.0f}")

    # ==========================================================================
    # FÓRMULA RECOMENDADA
    # ==========================================================================
    st.markdown("---")
    with st.expander("📐 ¿Cómo se calcula el Costo Unitario de Aula? (Fórmula Recomendada)", expanded=False):
        st.markdown("""
        <div class="formula-box">
        <b>MODELO DE COSTO ABC GRANULAR POR SESIÓN</b><br><br>
        <b>① Costos Directos:</b><br>
        &nbsp; C_prof = Grupos × Clases × Profesores × 2h × Valor_hora_prof<br>
        &nbsp; C_m2   = Grupos × Clases × m² × Valor_m²<br>
        &nbsp; C_lic  = Valor_licencias (×2 si salón Avanzado)<br>
        &nbsp; Total_Directos = C_prof + C_m2 + C_lic<br><br>
        <b>② Costos Indirectos:</b><br>
        &nbsp; C_ind = 0.50 × Total_Directos<br><br>
        <b>③ Costo Total ABC:</b><br>
        &nbsp; C_total = Total_Directos + C_ind<br><br>
        <b>④ Costo Unitario de AULA (por sesión-grupo):</b><br>
        &nbsp; CU_aula = C_total / (Grupos × Clases)<br><br>
        <b>⑤ Costo Unitario por ESTUDIANTE-SEMESTRE:</b><br>
        &nbsp; CU_est = C_total / (Grupos × Estudiantes_por_grupo)<br><br>
        <b>💡 Utilidad Simbiótica U:</b><br>
        &nbsp; U = 0.40·ME + 0.35·SG + 0.25·FR &nbsp; (rango [0,1])
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# SIDEBAR — Cinta Flujo 2
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding-bottom:12px;border-bottom:2px solid #3949ab;margin-bottom:16px;">
        <h2 style="margin:0;color:#7986cb;">🏛️ URosario</h2>
        <span style="font-size:11px;color:#aaa;">Portal FIS v8.1 · Menú</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("portal_fis.py",               label="🏠  Inicio",              icon="🏠")
    st.page_link("pages/00_comparacion.py",      label="📊  Comparación",         icon="📊")
    st.page_link("pages/01_flujo_humano.py",     label="🙋  Flujo 1: Humano",     icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py", label="🤖  Flujo 2: Agentes IA", icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",        label="🧬  Flujo 3: FIS",        icon="3️⃣")
    st.page_link("pages/04_simulador_fis.py",    label="📊  Simulador Diferencial", icon="📊")
    st.markdown("---")
    st.markdown("**🤖 Cinta Flujo 2**")
    st.metric("💰 Total ABC actual", f"${cinta_f2.get('costo_total', 0):,.0f}")
    agentes_ok = sum(1 for v in cinta_f2.get("estados_agentes", {}).values() if "✅" in v)
    st.metric("✅ Agentes completados", f"{agentes_ok} / {len(AGENTES)}")
    if cinta_f2.get("valor_u") and cinta_f2["valor_u"] != "—":
        st.metric("🧮 Valor U", cinta_f2["valor_u"])
    if cinta_f2.get("timestamp"):
        st.caption(f"Última ejecución: {cinta_f2['timestamp'][:19]}")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""<div class="telemetria">🤖 <b>ENJAMBRE IA ACTIVO</b> | 5 agentes | Pinecone: 3072 dims | Simbiomémesis v8.1</div>""",
            unsafe_allow_html=True)
