"""
=============================================================================
FLUJO_3_FIS / formulario_hitl_utilidad.py
Plantilla: Validación HITL + Cálculo de Utilidad Simbiótica U (v2)
=============================================================================

Encadenamiento de JSONs (Cinta Inmutable):
    Entrada : YYYYMMDD_NNN_COSTEO_ABC_UR.json       ← sustrato de costeo
    Salida  : YYYYMMDD_NNN_PERCEPCION_SIMBIOSIS.json ← sustrato para derivada

Mejoras sobre v1:
    ✅ Fix import relativo (FLUJO_3_FIS/, no FIS/)
    ✅ Fix campo JSON → total_general (compat. total_global legacy)
    ✅ Gestor de Sustrato con metadata, selección y eliminación con confirmación
    ✅ Nomenclatura de auditoría YYYYMMDD_NNN_ vía _persistencia.py
    ✅ Visualización de Caja Blanca del cálculo U (pasos + fórmula)
    ✅ Historial de experimentos en sesión con Δ entre iteraciones
    ✅ Reset quirúrgico (limpia solo estado HITL, preserva cinta_f3)
    ✅ Panel de auditoría de percepciones previas con carga de snapshot
=============================================================================
"""

import os
import sys
import json
import streamlit as st
from datetime import datetime
from pathlib import Path

# ── Paths y sys.path ─────────────────────────────────────────────────────────
_HERE      = Path(__file__).resolve().parent
_DATOS_DIR = _HERE.parent / "DATOS"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# ── Importaciones del ecosistema FIS ─────────────────────────────────────────
from _persistencia import guardar_nodo, listar_nodos
from calculaUtilidadSimbiotica import procesar_evento_utilidad_v9

# ── Clave de sesión para experimentos ────────────────────────────────────────
_KEY_EXP = "hitl_u_experimentos"


# =============================================================================
# SECCIÓN 1 — GESTOR DE SUSTRATO (COSTEO_ABC_UR)
# =============================================================================

def _render_gestor_sustrato() -> dict | None:
    """
    Muestra la lista de archivos COSTEO_ABC_UR disponibles en /DATOS.
    Permite seleccionar, ver metadata y eliminar con confirmación.
    Retorna el dict de datos del archivo seleccionado, o None.
    """
    st.subheader("📂 1. Gestor de Sustrato — Seleccionar JSON de Costeo")

    nodos = listar_nodos("COSTEO_ABC_UR", limite=20)

    if not nodos:
        st.warning(
            "⚠️ No se encontraron archivos `COSTEO_ABC_UR` en `/DATOS`. "
            "Completa la etapa de **Costeo de Asignaturas** primero.",
            icon="💰"
        )
        return None

    # Selectbox con nombre de archivo (más legible que ruta completa)
    opciones   = {n["archivo"]: n for n in nodos}
    sel_nombre = st.selectbox(
        "Archivo de costeo:",
        list(opciones.keys()),
        format_func=lambda x: x  # ya legible
    )
    nodo_sel = opciones[sel_nombre]
    datos    = nodo_sel["data"]

    # ── Metadata del archivo seleccionado ────────────────────────────────
    ts       = nodo_sel["timestamp"][:19].replace("T", " ")
    total    = datos.get("total_general") or datos.get("total_global") or 0.0
    n_asig   = datos.get("n_asignaturas", "?")
    periodo  = datos.get("periodo", "—")
    cinta    = datos.get("cinta", "—")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Costo Total",      f"${total:,.2f}")
    col_m2.metric("Asignaturas",      n_asig)
    col_m3.metric("Período",          periodo)
    col_m4.metric("Guardado",         ts)
    st.caption(f"Cinta: **{cinta}** | Etapa: {nodo_sel.get('etapa','—')}")

    # ── Eliminación con confirmación ──────────────────────────────────────
    col_info, col_chk, col_del = st.columns([3, 1, 1])
    with col_chk:
        confirmar = st.checkbox("Confirmar", key=f"chk_del_{sel_nombre}")
    with col_del:
        if st.button("🗑️ Eliminar", disabled=not confirmar,
                     key=f"btn_del_{sel_nombre}", type="secondary"):
            ruta = nodo_sel["path"]
            if os.path.exists(ruta):
                os.remove(ruta)
                st.toast(f"Archivo `{sel_nombre}` eliminado.", icon="🗑️")
                st.rerun()
    if confirmar:
        col_info.warning("⚠️ Marcado para eliminar. Haz clic en 🗑️ para confirmar.")

    st.success(f"✅ Sustrato cargado: **${total:,.2f}** (Costo Directo Total)", icon="💰")
    return datos


# =============================================================================
# SECCIÓN 2 — FORMULARIO DE VARIABLES SIMBIÓTICAS
# =============================================================================

def _render_formulario(costo_directo_base: float, etapa: dict) -> dict | None:
    """
    Renderiza el formulario de variables para la ecuación U.
    Retorna el payload si se envía, o None.
    """
    st.divider()
    st.subheader("🧬 2. Parámetros de Utilidad Simbiótica (v9.1)")
    st.latex(r"U = (\alpha \cdot \ln(1+C_{ABC})) \cdot (H_{norm} + e^{-t})")
    st.caption(
        "v9.1: la validación HITL binaria fue reemplazada por un cuestionario "
        "de 4 preguntas en escala 1–5, normalizado a 0–1."
    )

    eid = etapa.get("id", "x")
    with st.form(f"form_simbiosis_v9_{eid}", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Datos del Costeo (automáticos)**")
            c_directo = st.number_input(
                "Costo Directo Asignaturas ($)",
                value=float(costo_directo_base), disabled=True,
                help="Importado automáticamente del sustrato seleccionado."
            )
            inductor = st.number_input(
                "Inductor de Actividad (Horas / Driver)", value=1.0, step=0.1,
                min_value=0.01,
                help="Valor del driver de costos (ej. horas-profesor, grupos)."
            )
            t_proceso = st.number_input(
                "Iteración del Proceso (t)", value=1, step=1, min_value=1,
                help="Número de iteración en la cinta. Afecta la atenuación temporal e^-t."
            )
            u_anterior = st.number_input(
                "Utilidad Anterior — Pinecone (U_{t-1})", value=0.0, step=0.0001,
                format="%.6f",
                help="U calculada en la iteración previa. 0.0 si es la primera."
            )
            peso_agente = st.slider(
                "Coeficiente de Autonomía Agente (α)", 0.0, 1.0, 0.85, step=0.01,
                help="Peso del agente IA en el cálculo. 1.0 = totalmente autónomo."
            )

        with col2:
            st.markdown("**🙋 Cuestionario HITL — Escala 1 (bajo) a 5 (alto)**")
            st.caption("Normalización: (valor - 1) / 4  →  rango 0–1")
            q1 = st.slider(
                "Q1 · Precisión percibida del costeo ABC",
                min_value=1, max_value=5, value=4, step=1,
                help="¿Qué tan preciso considera el resultado del costeo?"
            )
            q2 = st.slider(
                "Q2 · Relevancia de la automatización del agente",
                min_value=1, max_value=5, value=4, step=1,
                help="¿En qué medida el agente IA agrega valor al proceso?"
            )
            q3 = st.slider(
                "Q3 · Claridad de la Caja Blanca (trazabilidad)",
                min_value=1, max_value=5, value=3, step=1,
                help="¿El desglose paso a paso es comprensible y auditable?"
            )
            q4 = st.slider(
                "Q4 · Confianza general para auditoría forense",
                min_value=1, max_value=5, value=4, step=1,
                help="¿Confiaría en este resultado para una auditoría formal?"
            )
            # Vista previa de normalización
            normas = [(q1-1)/4, (q2-1)/4, (q3-1)/4, (q4-1)/4]
            promedio = sum(normas) / 4
            st.metric("Promedio HITL normalizado (H_norm)", f"{promedio:.3f}",
                      delta=f"factor_confianza = {promedio + 0.1:.3f}")

        st.divider()
        confirmacion = st.checkbox(
            "☑️ Confirmo que los parámetros son correctos y deseo calcular la Utilidad Simbiótica."
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit = st.form_submit_button("🚀 Calcular Utilidad U", type="primary",
                                           use_container_width=True)
        with col_btn2:
            reset = st.form_submit_button("♻️ Reiniciar Experimentos",
                                          use_container_width=True)

    if reset:
        _reset_hitl_state()
        st.rerun()

    if submit:
        if not confirmacion:
            st.error("❌ Marca la casilla de confirmación antes de calcular.", icon="⚠️")
            return None
        return {
            "costo_directo_asignaturas":   float(c_directo),
            "inductor_actividad_valor":    float(inductor),
            "tiempo_proceso_iteracion":    int(t_proceso),
            "utilidad_anterior_pinecone":  float(u_anterior),
            "peso_autonomia_agente":       float(peso_agente),
            # Cuestionario HITL v9.1 (escala 1-5, requerido por DatosEntradaCintaV9)
            "calificacion_q1_precision":      int(q1),
            "calificacion_q2_agente":         int(q2),
            "calificacion_q3_transparencia":  int(q3),
            "calificacion_q4_confianza":      int(q4),
        }

    return None


# =============================================================================
# SECCIÓN 3 — PROCESAMIENTO Y VISUALIZACIÓN DE CAJA BLANCA
# =============================================================================

def _procesar_y_mostrar(payload: dict, datos_costeo: dict, etapa: dict, cf3: dict):
    """
    Llama a procesar_evento_utilidad_v9, muestra resultados de Caja Blanca
    y persiste la percepción simbiótica.
    """
    st.divider()
    st.subheader("🔬 3. Resultado — Caja Blanca del Cálculo U")

    with st.spinner("Motor FIS v9 calculando Utilidad Simbiótica…"):
        resultado = procesar_evento_utilidad_v9(payload)

    # ── Fallo del motor ──────────────────────────────────────────────────
    if resultado["status"] != "SUCCESS":
        st.error(
            f"💥 Falla en el motor FIS: `{resultado.get('error_detalle', resultado.get('detalle',''))}`\n\n"
            f"Componente: `{resultado.get('componente','—')}`",
            icon="🚨"
        )
        return

    # ── Extracción de resultados ─────────────────────────────────────────
    payload_u  = resultado["payload_u"]
    u_final    = payload_u["valor_utilidad_u_final"]
    ef_abc     = payload_u["componente_eficiencia_abc"]
    # v9.1: campo renombrado (era componente_validacion_humana)
    conf_h     = payload_u["componente_validacion_humana_normalizada"]
    atenuacion = payload_u["factor_atenuacion_temporal"]
    pasos      = payload_u["trazabilidad_pasos"]

    # ── Delta vs experimento anterior ────────────────────────────────────
    experimentos = st.session_state.get(_KEY_EXP, [])
    u_prev  = experimentos[-1]["resultado_u"]["valor_utilidad_u_final"] if experimentos else None
    delta_u = round(u_final - u_prev, 8) if u_prev is not None else None

    # Reconstruir promedio HITL para la tabla de variables
    q1 = payload.get("calificacion_q1_precision", 0)
    q2 = payload.get("calificacion_q2_agente", 0)
    q3 = payload.get("calificacion_q3_transparencia", 0)
    q4 = payload.get("calificacion_q4_confianza", 0)
    promedio_hitl = ((q1-1) + (q2-1) + (q3-1) + (q4-1)) / 16.0  # 4 * 4

    # ── Métricas principales ─────────────────────────────────────────────
    st.markdown("**📐 Componentes de la Ecuación**")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("🎯 Utilidad U Final", f"{u_final:.6f}",
               delta=f"Δ {delta_u:+.6f}" if delta_u is not None else None)
    mc2.metric("📊 Eficiencia ABC\n(log₁p C)", f"{ef_abc:.4f}")
    mc3.metric("🙋 H_norm + 0.1\n(confianza HITL)", f"{conf_h:.4f}")
    mc4.metric("⏱ Atenuación\n(e^-t)", f"{atenuacion:.4f}")

    # ── Fórmula y traza de pasos ─────────────────────────────────────────
    col_form, col_trace = st.columns([1, 1.4])
    with col_form:
        st.markdown("**Fórmula v9.1 aplicada:**")
        st.latex(r"U = (\alpha \cdot \ln(1+C)) \cdot (H_{norm} + e^{-t})")
        st.markdown(f"""
| Variable | Valor |
|---|---|
| α (autonomía)  | `{payload['peso_autonomia_agente']}` |
| C (costo ABC)  | `${payload['costo_directo_asignaturas']:,.2f}` |
| Q1–Q4 (1–5)    | `{q1}`, `{q2}`, `{q3}`, `{q4}` |
| H_norm         | `{promedio_hitl:.4f}` → factor `{conf_h:.4f}` |
| t (iteración)  | `{payload['tiempo_proceso_iteracion']}` |
""")
    with col_trace:
        st.markdown("**🔍 Trazabilidad Paso a Paso (Auditoría):**")
        for paso in pasos:
            st.markdown(f"- `{paso}`")

    # ── Persistencia: PERCEPCION_SIMBIOSIS ───────────────────────────────
    percepcion = {
        "tipo":                   "PERCEPCION_SIMBIOSIS",
        "cinta":                  cf3.get("nombre", ""),
        "etapa":                  etapa.get("nombre", ""),
        "etapa_id":               etapa.get("id", ""),
        "n_experimento":          len(experimentos) + 1,
        "entrada":                payload,
        "resultado_u":            payload_u,
        "delta_u_vs_anterior":    delta_u,
        "archivo_costeo_origen":  datos_costeo.get("_auditoria", {}).get("archivo", "—"),
        "costo_total_costeo":     datos_costeo.get("total_general") or datos_costeo.get("total_global", 0),
        "seleccion_asignaturas":  datos_costeo.get("seleccion", {}).get("asignaturas", []),
    }
    ruta_guardada = guardar_nodo("PERCEPCION_SIMBIOSIS", percepcion)

    # ── Registro en historial de sesión ──────────────────────────────────
    experimentos.append({
        "n":               len(experimentos) + 1,
        "timestamp":       resultado["timestamp"],
        "payload":         payload,
        "resultado_u":     payload_u,
        "archivo_costeo":  datos_costeo.get("_auditoria", {}).get("archivo", "—"),
        "archivo_guardado":os.path.basename(ruta_guardada),
    })
    st.session_state[_KEY_EXP] = experimentos

    # ── Confirmación ─────────────────────────────────────────────────────
    st.balloons()
    st.success(
        f"💾 Percepción Simbiótica persistida → `{os.path.basename(ruta_guardada)}`\n\n"
        "Este archivo servirá de sustrato para el cálculo de la **Razón de Cambio (Simbiomemesis)**.",
        icon="🧬"
    )


# =============================================================================
# SECCIÓN 4 — HISTORIAL DE EXPERIMENTOS EN SESIÓN
# =============================================================================

def _resumen_hitl(payload: dict) -> str:
    """
    Genera un resumen legible del componente HITL compatible con v9.0 y v9.1.
    - v9.1: usa calificacion_q1..q4 (escala 1-5)
    - v9.0 (legacy): usa validacion_humana_hitl (binario 0/1)
    """
    # v9.1
    if "calificacion_q1_precision" in payload:
        q1 = payload.get("calificacion_q1_precision", 0)
        q2 = payload.get("calificacion_q2_agente", 0)
        q3 = payload.get("calificacion_q3_transparencia", 0)
        q4 = payload.get("calificacion_q4_confianza", 0)
        promedio = (q1 + q2 + q3 + q4) / 4.0
        return f"Q̄={promedio:.1f}/5"
    # v9.0 legacy
    val = payload.get("validacion_humana_hitl")
    if val is not None:
        return "✅ Sí" if val else "❌ No"
    return "—"


def _render_historial_sesion():
    """Tabla de experimentos realizados en esta sesión con Δ U."""
    experimentos = st.session_state.get(_KEY_EXP, [])
    if not experimentos:
        return

    st.divider()
    st.subheader(f"📈 4. Historial de Experimentos — Sesión Actual ({len(experimentos)} runs)")

    try:
        import pandas as pd
        filas = []
        for i, exp in enumerate(experimentos):
            u_val  = exp["resultado_u"]["valor_utilidad_u_final"]
            u_prev = experimentos[i-1]["resultado_u"]["valor_utilidad_u_final"] if i > 0 else None
            delta  = round(u_val - u_prev, 8) if u_prev is not None else "—"
            filas.append({
                "#":       exp["n"],
                "Timestamp":    exp["timestamp"][:19].replace("T"," "),
                "U Final":      f"{u_val:.6f}",
                "Δ vs anterior":f"{delta:+.6f}" if isinstance(delta, float) else delta,
                "α":            exp["payload"]["peso_autonomia_agente"],
                "HITL":         _resumen_hitl(exp["payload"]),
                "t":            exp["payload"]["tiempo_proceso_iteracion"],
                "Archivo":      exp["archivo_guardado"],
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        # Gráfica de evolución de U
        if len(filas) > 1:
            vals = [e["resultado_u"]["valor_utilidad_u_final"] for e in experimentos]
            st.line_chart(
                data={"Utilidad U": vals},
                use_container_width=True,
                height=200,
            )
    except ImportError:
        for exp in experimentos:
            u = exp["resultado_u"]["valor_utilidad_u_final"]
            st.markdown(f"- Exp {exp['n']}: **U = {u:.6f}** @ {exp['timestamp'][:19]}")


# =============================================================================
# SECCIÓN 5 — PANEL DE AUDITORÍA (PERCEPCIONES PREVIAS EN DISCO)
# =============================================================================

def _render_auditoria_percepciones():
    """Histórico de PERCEPCION_SIMBIOSIS en /DATOS con carga de snapshot."""
    historial = listar_nodos("PERCEPCION_SIMBIOSIS", limite=10)
    if not historial:
        return

    with st.expander(
        f"🔍 Historial de auditoría — PERCEPCION_SIMBIOSIS ({len(historial)} archivos)", expanded=False
    ):
        for nodo in historial:
            ts       = nodo["timestamp"][:19].replace("T"," ")
            u_val    = nodo["data"].get("resultado_u", {}).get("valor_utilidad_u_final", "—")
            n_exp    = nodo["data"].get("n_experimento", "—")
            origen   = nodo["data"].get("archivo_costeo_origen", "—")

            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            col_a.markdown(f"`{nodo['archivo']}`")
            col_b.markdown(f"U = **{u_val:.6f}**" if isinstance(u_val, float) else f"U = {u_val}")
            col_c.markdown(f"Exp #{n_exp}")
            col_d.markdown(f"_{ts}_")
            st.caption(f"Origen costeo: `{origen}`")

            col_load, col_json = st.columns([1, 2])
            if col_load.button("📂 Cargar al historial", key=f"load_perc_{nodo['archivo']}",
                               use_container_width=True):
                exp_recuperado = {
                    "n":               n_exp,
                    "timestamp":       nodo["timestamp"],
                    "payload":         nodo["data"].get("entrada", {}),
                    "resultado_u":     nodo["data"].get("resultado_u", {}),
                    "archivo_costeo":  origen,
                    "archivo_guardado":nodo["archivo"],
                }
                exps = st.session_state.get(_KEY_EXP, [])
                exps.append(exp_recuperado)
                st.session_state[_KEY_EXP] = exps
                st.success(f"✅ Snapshot cargado al historial de sesión.")
                st.rerun()

            with col_json.expander("Ver JSON"):
                st.json({
                    k: v for k, v in nodo["data"].items()
                    if k not in ("_auditoria","resultado_u","entrada")
                })
            st.markdown("---")


# =============================================================================
# RESET QUIRÚRGICO
# =============================================================================

def _reset_hitl_state():
    """
    Limpia únicamente el estado HITL (experimentos de sesión).
    Preserva: cinta_f3, fis_seleccion, fis_params, fis_costeo_resultados.
    """
    claves_a_limpiar = [k for k in list(st.session_state.keys())
                        if k.startswith("hitl_") or k == _KEY_EXP]
    for k in claves_a_limpiar:
        del st.session_state[k]
    st.toast("♻️ Historial de experimentos reiniciado. Los datos de la cinta se preservan.", icon="✅")


# =============================================================================
# PUNTO DE ENTRADA — render(etapa, cf3)
# =============================================================================

def render(etapa: dict, cf3: dict):
    st.markdown("#### 🙋 Validación HITL: Interfaz de Utilidad Simbiótica")
    st.caption(
        "Encadenamiento: `COSTEO_ABC_UR.json` → Motor FIS v9 → `PERCEPCION_SIMBIOSIS.json`"
    )

    # ── 1. Gestor de Sustrato ─────────────────────────────────────────────
    datos_costeo = _render_gestor_sustrato()
    if datos_costeo is None:
        return

    costo_base = datos_costeo.get("total_general") or datos_costeo.get("total_global") or 0.0

    # ── 2. Formulario ─────────────────────────────────────────────────────
    payload = _render_formulario(costo_base, etapa)

    # ── 3. Cálculo y visualización ────────────────────────────────────────
    if payload:
        _procesar_y_mostrar(payload, datos_costeo, etapa, cf3)

    # ── 4. Historial de sesión ────────────────────────────────────────────
    _render_historial_sesion()

    # ── 5. Auditoría en disco ─────────────────────────────────────────────
    _render_auditoria_percepciones()

    st.caption("FIS v9.0 | Kali-WSL | Universidad del Rosario — Simbiomemesis")
