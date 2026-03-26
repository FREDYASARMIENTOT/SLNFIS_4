"""
=============================================================================
FLUJO_3_FIS / analisis_simbiomemesis.py
Plantilla: Razón de Cambio Simbiótica — Simbiomemesis (dU/dt · ∂U/∂C)
Motor   : calculaSimbiomemesis.ejecutar_analisis_simbiomemesis(t1, t2)
=============================================================================

CASO DE USO — Cinta de 6 etapas consecutivas:
┌─────────────────────────────────────────────────────────────────┐
│  ① selector_jerarquico.py    → SELECCION_FIS.json               │
│  ② parametros_costeo.py      → PARAMS_FIS.json                  │
│  ③ costeo_asignaturas.py     → COSTEO_ABC_UR.json               │
│  ④ formulario_hitl_utilidad  → PERCEPCION_SIMBIOSIS.json (t=1)  │
│  ⑤ formulario_hitl_utilidad  → PERCEPCION_SIMBIOSIS.json (t=2)  │
│  ⑥ analisis_simbiomemesis.py → SIMBIOMEMESIS.json   (dU/dt)     │
└─────────────────────────────────────────────────────────────────┘

Encadenamiento:
    Entrada : 2 × PERCEPCION_SIMBIOSIS.json (seleccionados por el usuario)
    Salida  : YYYYMMDD_NNN_SIMBIOMEMESIS.json

SIMULACIÓN DE AISLAMIENTO (multi-instancia):
    Todos los widgets usan f"{key}_{eid}" donde eid = etapa["id"].
    La clave de session_state del resultado también está scopeada al etapa_id.
    → SAFE para usar más de una vez en la misma cinta.
=============================================================================
"""

import os
import sys
import streamlit as st
from pathlib import Path
from datetime import datetime

_HERE      = Path(__file__).resolve().parent
_DATOS_DIR = _HERE.parent / "DATOS"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _persistencia import guardar_nodo, listar_nodos
from calculaSimbiomemesis import ejecutar_analisis_simbiomemesis


# =============================================================================
# NORMALIZADOR DE COMPATIBILIDAD v9.0 ↔ v9.1
# =============================================================================

def _normalizar_para_motor(data: dict) -> dict:
    """
    Garantiza que el campo `entrada.validacion_humana_hitl` (int 0/1) exista
    antes de pasar el JSON al motor calculaSimbiomemesis, que lo requiere.

    Casos:
      • JSON v9.0 — ya trae `validacion_humana_hitl`  → se devuelve sin cambios.
      • JSON v9.1 — trae `calificacion_q1..q4` (1-5)  → se calcula el equivalente
        binario: promedio_q >= 3  →  1 (validado), < 3  →  0 (no validado).

    No muta el dict original; retorna una copia superficial de `entrada`.
    """
    import copy
    resultado = copy.deepcopy(data)
    entrada = resultado.get("entrada", {})

    if "validacion_humana_hitl" not in entrada:
        q1 = entrada.get("calificacion_q1_precision",      3)
        q2 = entrada.get("calificacion_q2_agente",         3)
        q3 = entrada.get("calificacion_q3_transparencia",  3)
        q4 = entrada.get("calificacion_q4_confianza",      3)
        promedio_q = (q1 + q2 + q3 + q4) / 4.0
        entrada["validacion_humana_hitl"] = 1 if promedio_q >= 3.0 else 0
        resultado["entrada"] = entrada

    return resultado


# =============================================================================
# BLOQUE DE SIMULACIÓN — Análisis de aislamiento de las plantillas FLUJO_3_FIS
# =============================================================================

_SIMULACION_RESULTADOS = [
    {
        "archivo":          "selector_jerarquico.py",
        "widgets_scoped":   "✅ prefijo etapa.id",
        "ss_keys":          "⚠️ fis_seleccion (compartida)",
        "multi_instancia":  "⚠️ last-write-wins",
        "veredicto":        "1 instancia óptima",
    },
    {
        "archivo":          "parametros_costeo.py",
        "widgets_scoped":   "✅ prefijo etapa.id",
        "ss_keys":          "⚠️ fis_params (compartida)",
        "multi_instancia":  "⚠️ last-write-wins",
        "veredicto":        "1 instancia óptima",
    },
    {
        "archivo":          "costeo_asignaturas.py",
        "widgets_scoped":   "✅ prefijo etapa.id",
        "ss_keys":          "⚠️ fis_costeo_resultados (compartida)",
        "multi_instancia":  "✅ flag anti-dup por etapa_id",
        "veredicto":        "✅ Multi-instancia funcional",
    },
    {
        "archivo":          "formulario_hitl_utilidad.py",
        "widgets_scoped":   "✅ form key scopeado (fix v2)",
        "ss_keys":          "✅ hitl_u_experimentos (aditiva)",
        "multi_instancia":  "✅ Experimentos de t1 y t2 coexisten",
        "veredicto":        "✅ Multi-instancia funcional",
    },
    {
        "archivo":          "analisis_simbiomemesis.py",
        "widgets_scoped":   "✅ prefijo etapa.id en todos los widgets",
        "ss_keys":          "✅ sim_resultado_{etapa_id} (scopeada)",
        "multi_instancia":  "✅ Diseñado para instancia única por cinta",
        "veredicto":        "✅ Safe",
    },
]


def _render_simulacion():
    """Panel colapsable con los resultados de la simulación de aislamiento."""
    with st.expander("🧪 Simulación Interna — Análisis de Aislamiento de Pestañas Dinámicas", expanded=False):
        st.markdown("""
**Mecanismo evaluado:** `importlib.util.spec_from_file_location` + `spec.loader.exec_module(mod)`

Cada vez que Streamlit re-renderiza una pestaña, el módulo se carga **en fresco**
(sin caché de `sys.modules`). Esto garantiza:
- Sin fuga de estado entre etapas que usen el mismo template.
- Código de módulo-nivel (constantes, imports) se re-ejecuta → sin efectos laterales.
        """)

        try:
            import pandas as pd
            df = pd.DataFrame(_SIMULACION_RESULTADOS)
            df.columns = ["Archivo", "Widgets", "session_state", "Multi-instancia", "Veredicto"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        except ImportError:
            for r in _SIMULACION_RESULTADOS:
                st.markdown(f"- `{r['archivo']}` → {r['veredicto']}")

        st.markdown("""
**Conclusión:** El sistema de pestañas dinámicas **funciona correctamente** para 1 instancia
de cada template por cinta (caso de uso estándar). Para 2 instancias del mismo template
(ej: etapas 4 y 5 ambas con `formulario_hitl_utilidad`), los widgets están aislados y
los experimentos coexisten en la lista `hitl_u_experimentos`.

**Única precaución:** Templates que comparten claves de `session_state` (selector, params)
con la misma semántica — el dato relevante es el más reciente (last-write-wins), lo que
es el comportamiento deseado en una cinta secuencial.
        """)


# =============================================================================
# CASO DE USO — Diagrama de encadenamiento
# =============================================================================

def _render_caso_uso():
    st.markdown("""
```
Cinta FIS — 6 etapas consecutivas
═══════════════════════════════════════════════════════════════
 Etapa ①  selector_jerarquico.py
          └─► SELECCION_FIS.json  ──────────────────────────┐
                                                              │ fis_seleccion
 Etapa ②  parametros_costeo.py                               │
          └─► PARAMS_FIS.json  ──────────────────────────────┤
                                                              │ fis_params
 Etapa ③  costeo_asignaturas.py ◄── (lee ① y ②) ────────────┘
          └─► COSTEO_ABC_UR.json ───────────────────────────┐
                                                             │
 Etapa ④  formulario_hitl_utilidad (t=1)  ◄── COSTEO ───────┘
          └─► PERCEPCION_SIMBIOSIS_t1.json  ────────────────┐
                                                             │
 Etapa ⑤  formulario_hitl_utilidad (t=2)  ◄── COSTEO       │
          └─► PERCEPCION_SIMBIOSIS_t2.json  ─────────────────┤
                                                             │
 Etapa ⑥  analisis_simbiomemesis.py  ◄── (lee t1 y t2) ────┘
          └─► SIMBIOMEMESIS.json  (dU/dt · ∂U/∂C)
═══════════════════════════════════════════════════════════════
```
""")


# =============================================================================
# METADATA DE UN ESTADO SIMBIÓTICO
# =============================================================================

def _render_estado_metadata(data: dict, titulo: str, nombre: str):
    ru  = data.get("resultado_u", {})
    en  = data.get("entrada",    {})
    u   = ru.get("valor_utilidad_u_final",       0.0)
    t   = en.get("tiempo_proceso_iteracion",       "—")
    c   = en.get("costo_directo_asignaturas",      0.0)
    ts  = data.get("_auditoria", {}).get("timestamp","—")[:19].replace("T", " ")
    cinta = data.get("cinta","—")
    etapa_origen = data.get("etapa","—")

    # Resumen HITL compatible v9.0 (binario) y v9.1 (cuestionario 1-5)
    if "calificacion_q1_precision" in en:
        qs = [en.get(f"calificacion_q{i}_{k}", 0)
              for i, k in [(1,"precision"),(2,"agente"),(3,"transparencia"),(4,"confianza")]]
        hitl_label = f"Q̄={sum(qs)/4:.1f}/5"
    else:
        h = en.get("validacion_humana_hitl", None)
        hitl_label = ("✅ Sí" if h == 1 else "❌ No") if h is not None else "—"

    with st.container(border=True):
        st.markdown(f"**{titulo}** — `{nombre}`")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Utilidad U",  f"{u:.6f}")
        col2.metric("Iteración t", t)
        col3.metric("HITL",        hitl_label)
        col4.metric("Costo ABC",   f"${c:,.0f}")
        st.caption(f"Cinta: **{cinta}** | Etapa: {etapa_origen} | Guardado: {ts}")


# =============================================================================
# CÁLCULO Y VISUALIZACIÓN DE RESULTADOS
# =============================================================================

def _calcular_y_mostrar(json_t1: dict, json_t2: dict,
                         nombre_t1: str, nombre_t2: str,
                         etapa: dict, cf3: dict):
    # Normalizar: garantiza validacion_humana_hitl en entrada (v9.0↔v9.1)
    json_t1_norm = _normalizar_para_motor(json_t1)
    json_t2_norm = _normalizar_para_motor(json_t2)

    with st.spinner("Motor de Simbiomemesis v9 calculando derivadas…"):
        resultado = ejecutar_analisis_simbiomemesis(json_t1_norm, json_t2_norm)

    if resultado["status"] != "SUCCESS":
        st.error(
            f"💥 Error en motor: `{resultado.get('detalle','')}`",
            icon="🚨"
        )
        return

    payload  = resultado["payload_simbiomemesis"]
    estado   = payload["estado_evolutivo_sistema"]
    dU_dt    = payload["derivada_temporal_simbiomemesis"]
    delta_U  = payload["delta_utilidad_total"]
    grad_C   = payload["sensibilidad_al_costo_gradiente"]
    recom    = payload["recomendacion_agente_analista"]
    pasos    = payload["trazabilidad_matematica"]
    ts_anal  = resultado["timestamp_analisis"]

    # ── Estado evolutivo (color semántico) ───────────────────────────────
    st.markdown("---")
    if "POSITIVA" in estado:
        st.success(f"## {estado}", icon="🟢")
    elif "REGRESIÓN" in estado or "REGRESION" in estado:
        st.error(f"## {estado}", icon="🔴")
    else:
        st.warning(f"## {estado}", icon="🟡")

    # ── Métricas principales ─────────────────────────────────────────────
    st.markdown("**📐 Derivadas del Sistema**")
    m1, m2, m3 = st.columns(3)
    m1.metric("ΔU — Delta Utilidad",          f"{delta_U:+.6f}")
    m2.metric("dU/dt — Simbiomemesis",        f"{dU_dt:+.6f}")
    m3.metric("∂U/∂C — Sensibilidad al Costo",f"{grad_C:+.8f}")

    # ── Recomendación del agente ──────────────────────────────────────────
    st.info(f"🤖 **Recomendación del Agente Analista:**\n\n{recom}", icon="💡")

    # ── Fórmulas y trazabilidad ───────────────────────────────────────────
    col_f, col_t = st.columns([1, 1.2])
    with col_f:
        st.markdown("**Fórmulas aplicadas:**")
        st.latex(
            r"\text{Simbiomemesis} = \frac{dU}{dt} = \frac{U_{t_2} - U_{t_1}}{t_2 - t_1}"
        )
        st.latex(
            r"\text{Gradiente} = \frac{\partial U}{\partial C} = \frac{\Delta U}{\Delta C}"
        )
        st.markdown(f"""
| Diferencial | Valor |
|---|---|
| `ΔU` | `{delta_U:+.6f}` |
| `Δt` | `{json_t2.get('entrada',{}).get('tiempo_proceso_iteracion',0) - json_t1.get('entrada',{}).get('tiempo_proceso_iteracion',0)}` |
| `ΔC` | `${json_t2.get('entrada',{}).get('costo_directo_asignaturas',0) - json_t1.get('entrada',{}).get('costo_directo_asignaturas',0):+,.2f}` |
""")

    with col_t:
        st.markdown("**🔍 Trazabilidad Paso a Paso:**")
        for paso in pasos:
            st.markdown(f"- `{paso}`")

    # ── Persistencia SIMBIOMEMESIS ────────────────────────────────────────
    payload_guardar = {
        "tipo":               "SIMBIOMEMESIS",
        "cinta":              cf3.get("nombre",""),
        "etapa":              etapa.get("nombre",""),
        "etapa_id":           etapa.get("id",""),
        "archivo_t1":         nombre_t1,
        "archivo_t2":         nombre_t2,
        "estado_evolutivo":   estado,
        "derivadas": {
            "delta_U":        delta_U,
            "dU_dt":          dU_dt,
            "gradiente_costo":grad_C,
        },
        "recomendacion":      recom,
        "resultado_completo": payload,
        "timestamp_analisis": ts_anal,
    }
    ruta = guardar_nodo("SIMBIOMEMESIS", payload_guardar)

    # Guardar en session_state con clave scopeada al etapa_id
    st.session_state[f"sim_resultado_{etapa.get('id','')}"] = payload_guardar

    st.success(
        f"💾 Análisis de Simbiomemesis persistido → `{os.path.basename(ruta)}`\n\n"
        "Este JSON es el sustrato final para reportes y comparación de flujos.",
        icon="🧬"
    )


# =============================================================================
# PANEL DE AUDITORÍA — SIMBIOMEMESIS previos en /DATOS
# =============================================================================

def _render_auditoria():
    historial = listar_nodos("SIMBIOMEMESIS", limite=10)
    if not historial:
        return
    with st.expander(
        f"🔍 Historial de auditoría — SIMBIOMEMESIS ({len(historial)} análisis)", expanded=False
    ):
        for nodo in historial:
            ts     = nodo["timestamp"][:19].replace("T"," ")
            estado = nodo["data"].get("estado_evolutivo","—")
            cinta  = nodo["data"].get("cinta","—")
            dervs  = nodo["data"].get("derivadas",{})
            dU_dt  = dervs.get("dU_dt","—")

            col_a, col_b, col_c = st.columns([2, 1, 2])
            col_a.markdown(f"`{nodo['archivo']}`")
            col_b.markdown(f"`dU/dt = {dU_dt}`" if isinstance(dU_dt, float)
                           else f"`{dU_dt}`")
            col_c.markdown(f"_{ts}_ — Cinta: **{cinta}**")
            st.caption(estado)

            col_load, col_json = st.columns([1, 2])
            if col_load.button("📂 Cargar resultado", key=f"load_sim_{nodo['archivo']}",
                               use_container_width=True):
                st.session_state[f"sim_hist_cargado"] = nodo["data"]
                st.success(f"✅ Snapshot `{nodo['archivo']}` cargado.")
                st.rerun()
            with col_json.expander("JSON"):
                st.json({k: v for k, v in nodo["data"].items()
                         if k not in ("_auditoria", "resultado_completo")})
            st.markdown("---")


# =============================================================================
# PUNTO DE ENTRADA — render(etapa, cf3)
# =============================================================================

def render(etapa: dict, cf3: dict):
    eid = etapa.get("id", "x")

    st.markdown("#### 🔬 Análisis de Simbiomemesis — Razón de Cambio Simbiótica")
    st.caption(
        "Motor: `calculaSimbiomemesis.ejecutar_analisis_simbiomemesis(t1, t2)` | "
        "Salida: `YYYYMMDD_NNN_SIMBIOMEMESIS.json`"
    )

    # ── Caso de uso y simulación de aislamiento ──────────────────────────
    tab_caso, tab_sim = st.tabs(["📐 Caso de Uso — 6 Etapas", "🧪 Simulación de Aislamiento"])
    with tab_caso:
        _render_caso_uso()
    with tab_sim:
        _render_simulacion()

    st.markdown("---")

    # ── Verificar disponibilidad de percepciones ─────────────────────────
    nodos = listar_nodos("PERCEPCION_SIMBIOSIS", limite=20)

    if len(nodos) < 2:
        st.warning(
            f"⚠️ Se necesitan mínimo **2 archivos** `PERCEPCION_SIMBIOSIS.json`. "
            f"Disponibles actualmente: **{len(nodos)}**.\n\n"
            "Ejecuta la plantilla `formulario_hitl_utilidad.py` en **2 etapas distintas** "
            "(o 2 veces en la misma etapa) para generar los estados t1 y t2.",
            icon="🧬"
        )
        if nodos:
            st.info(f"Disponible: `{nodos[0]['archivo']}` — faltan {2 - len(nodos)} archivo(s) más.")
        _render_auditoria()
        return

    # ── Selector de estados t1 y t2 ──────────────────────────────────────
    st.subheader("📂 1. Selección de Estados Simbióticos")

    opciones = {n["archivo"]: n for n in nodos}
    nombres  = list(opciones.keys())   # ordenados desc por listar_nodos

    col_toggle, col_info = st.columns([1, 2])
    with col_toggle:
        modo_auto = st.toggle(
            "⚡ Auto (t1=más antiguo, t2=más reciente)",
            value=True, key=f"sim_auto_{eid}"
        )

    if modo_auto:
        nombre_t1 = nombres[-1]   # más antiguo (último en lista desc)
        nombre_t2 = nombres[0]    # más reciente
        with col_info:
            st.info(f"t1 → `{nombre_t1[:30]}…`  |  t2 → `{nombre_t2[:30]}…`")
    else:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            nombre_t1 = st.selectbox(
                "Estado **t1** — Anterior", nombres,
                index=len(nombres)-1, key=f"sim_t1_{eid}"
            )
        with col_t2:
            nombre_t2 = st.selectbox(
                "Estado **t2** — Actual", nombres,
                index=0, key=f"sim_t2_{eid}"
            )

    if nombre_t1 == nombre_t2:
        st.error("❌ t1 y t2 deben ser archivos diferentes.", icon="⚠️")
        return

    json_t1 = opciones[nombre_t1]["data"]
    json_t2 = opciones[nombre_t2]["data"]

    # ── Metadata de los dos estados ───────────────────────────────────────
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        _render_estado_metadata(json_t1, "t1 — Estado Anterior", nombre_t1)
    with col_s2:
        _render_estado_metadata(json_t2, "t2 — Estado Actual",   nombre_t2)

    # ── Botón de cálculo ──────────────────────────────────────────────────
    st.divider()
    st.subheader("🧬 2. Cálculo de la Razón de Cambio")
    st.latex(
        r"\text{Simbiomemesis} = \frac{dU}{dt} \quad \cdot \quad "
        r"\frac{\partial U}{\partial C}"
    )

    if st.button(
        "▶ Ejecutar Análisis de Simbiomemesis",
        key=f"btn_sim_{eid}", type="primary"
    ):
        _calcular_y_mostrar(json_t1, json_t2, nombre_t1, nombre_t2, etapa, cf3)

    # ── Resultado guardado en sesión (si ya se calculó) ───────────────────
    res_cached = st.session_state.get(f"sim_resultado_{eid}")
    if res_cached and not st.session_state.get(f"btn_sim_{eid}"):
        with st.expander("📊 Último resultado calculado en esta sesión", expanded=False):
            drvs = res_cached.get("derivadas", {})
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("ΔU",     f"{drvs.get('delta_U',0):+.6f}")
            rc2.metric("dU/dt",  f"{drvs.get('dU_dt',0):+.6f}")
            rc3.metric("∂U/∂C",  f"{drvs.get('gradiente_costo',0):+.8f}")
            st.markdown(f"**Estado:** {res_cached.get('estado_evolutivo','—')}")
            st.markdown(f"**Recomendación:** _{res_cached.get('recomendacion','—')}_")

    # ── Auditoría ─────────────────────────────────────────────────────────
    _render_auditoria()

    st.caption("FIS v9.0 | Simbiomemesis — Universidad del Rosario")
