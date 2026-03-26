"""
=============================================================================
FLUJO_3_FIS / parametros_costeo.py
Plantilla: Formulario de parámetros de costeo ABC
Persistencia: YYYYMMDD_NNN_PARAMS_FIS.json (vía _persistencia.py)
Auto-recuperación: si session_state vacío, carga el último archivo guardado.
=============================================================================
"""

import os
import sys
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from _persistencia import guardar_nodo, recuperar_estado, listar_nodos

_DEFAULTS = {
    "num_grupos":            2,
    "num_clases":           10,
    "num_profesores":        2,
    "num_estudiantes":      10,
    "horas_por_clase":       2,
    "valor_hora_prof":   100000.0,
    "metros_cuadrados":     50.0,
    "valor_m2":           1500.0,
    "tipo_salon":          "Básico (Video beam + PC Profesor)",
    "valor_licencias_base": 500000.0,
    "periodo":             "2026-I",
}

_PERIODOS = ["2026-I","2026-II","2025-I","2025-II","Intersemestral"]


def render(etapa: dict, cf3: dict):
    st.markdown("#### ⚙️ Parámetros de Costeo ABC")

    # ── Auto-recuperación ────────────────────────────────────────────────
    prev = recuperar_estado("fis_params", "PARAMS_FIS") or _DEFAULTS
    if st.session_state.get("fis_params") is None:
        aud = listar_nodos("PARAMS_FIS", limite=1)
        if aud:
            ts = aud[0]["timestamp"][:19].replace("T"," ")
            st.info(f"♻️ **Parámetros recuperados desde disco** (guardados: {ts}). Modifica si necesitas.", icon="💾")

    st.caption("Valores aplicados a todas las asignaturas seleccionadas. Se persisten en /DATOS al guardar.")

    eid = etapa.get("id","e")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📚 Estructura académica**")
        num_grupos = st.number_input("👥 Grupos por asignatura", min_value=1,
                                     value=int(prev.get("num_grupos", _DEFAULTS["num_grupos"])),
                                     step=1, key=f"p_grupos_{eid}")
        num_clases = st.number_input("📅 Clases por semestre", min_value=1,
                                     value=int(prev.get("num_clases", _DEFAULTS["num_clases"])),
                                     step=1, key=f"p_clases_{eid}")
        horas_por_clase = st.number_input("⏱ Horas por clase", min_value=1,
                                          value=int(prev.get("horas_por_clase", _DEFAULTS["horas_por_clase"])),
                                          step=1, key=f"p_hpc_{eid}")
        periodo_prev = prev.get("periodo", "2026-I")
        periodo_idx  = _PERIODOS.index(periodo_prev) if periodo_prev in _PERIODOS else 0
        periodo = st.selectbox("🗓️ Período académico", _PERIODOS,
                               index=periodo_idx, key=f"p_periodo_{eid}")

    with col2:
        st.markdown("**👨‍🏫 Talento humano**")
        num_profesores = st.number_input("👨‍🏫 Profesores por grupo", min_value=1,
                                         value=int(prev.get("num_profesores", _DEFAULTS["num_profesores"])),
                                         step=1, key=f"p_prof_{eid}")
        num_estudiantes = st.number_input("👩‍🎓 Estudiantes por grupo", min_value=1,
                                          value=int(prev.get("num_estudiantes", _DEFAULTS["num_estudiantes"])),
                                          step=1, key=f"p_est_{eid}")
        valor_hora_prof = st.number_input("💵 Valor hora-profesor ($)", min_value=0.0,
                                          value=float(prev.get("valor_hora_prof", _DEFAULTS["valor_hora_prof"])),
                                          step=1000.0, format="%.0f", key=f"p_vhp_{eid}")

    with col3:
        st.markdown("**🏗️ Espacio y tecnología**")
        metros_cuadrados = st.number_input("📐 Metros cuadrados", min_value=1.0,
                                           value=float(prev.get("metros_cuadrados", _DEFAULTS["metros_cuadrados"])),
                                           step=1.0, key=f"p_m2_{eid}")
        valor_m2 = st.number_input("🏗️ Valor m² por sesión ($)", min_value=0.0,
                                   value=float(prev.get("valor_m2", _DEFAULTS["valor_m2"])),
                                   step=100.0, format="%.0f", key=f"p_vm2_{eid}")
        tipo_salon = st.radio("🖥️ Tipo de salón",
                              ["Avanzado (PCs por estudiante)", "Básico (Video beam + PC Profesor)"],
                              index=0 if "Avanzado" in prev.get("tipo_salon","Básico") else 1,
                              key=f"p_salon_{eid}")
        valor_licencias_base = st.number_input("💾 Licencias base ($)", min_value=0.0,
                                               value=float(prev.get("valor_licencias_base", _DEFAULTS["valor_licencias_base"])),
                                               step=10000.0, format="%.0f", key=f"p_lic_{eid}")

    valor_licencias = valor_licencias_base * (2.0 if "Avanzado" in tipo_salon else 1.0)
    st.info(
        f"💾 **Licencias aplicadas:** ${valor_licencias:,.0f} "
        f"({'×2 salón avanzado' if 'Avanzado' in tipo_salon else 'base'})",
        icon="ℹ️"
    )

    # ── Vista previa ─────────────────────────────────────────────────────
    sesiones_tot  = num_grupos * num_clases
    costo_doc     = sesiones_tot * num_profesores * horas_por_clase * valor_hora_prof
    costo_esp     = sesiones_tot * metros_cuadrados * valor_m2
    total_dir     = costo_doc + costo_esp + valor_licencias
    costo_ind     = 0.5 * total_dir
    costo_tot_est = total_dir + costo_ind
    est_tot       = num_grupos * num_estudiantes
    cu_est        = costo_tot_est / max(est_tot, 1)

    with st.expander("📊 Vista previa — costo estimado por asignatura", expanded=True):
        mp1, mp2, mp3, mp4 = st.columns(4)
        mp1.metric("Costo Docente",    f"${costo_doc:,.0f}")
        mp2.metric("Costo Espacio",    f"${costo_esp:,.0f}")
        mp3.metric("Costo Total",      f"${costo_tot_est:,.0f}")
        mp4.metric("Costo/Estudiante", f"${cu_est:,.0f}")

    # ── Guardar ──────────────────────────────────────────────────────────
    if st.button("💾 Guardar Parámetros", key=f"btn_params_{eid}", type="primary"):
        params = {
            "tipo":              "PARAMS_FIS",
            "cinta":             cf3.get("nombre",""),
            "etapa":             etapa.get("nombre",""),
            "etapa_id":          etapa.get("id",""),
            "periodo":           periodo,
            "num_grupos":        num_grupos,
            "num_clases":        num_clases,
            "num_profesores":    num_profesores,
            "num_estudiantes":   num_estudiantes,
            "horas_por_clase":   horas_por_clase,
            "valor_hora_prof":   valor_hora_prof,
            "metros_cuadrados":  metros_cuadrados,
            "valor_m2":          valor_m2,
            "tipo_salon":        tipo_salon,
            "valor_licencias_base": valor_licencias_base,
            "valor_licencias":   valor_licencias,
        }
        ruta = guardar_nodo("PARAMS_FIS", params)
        st.session_state["fis_params"] = params
        st.success(f"✅ Parámetros persistidos → `{os.path.basename(ruta)}`")

    # ── Panel de auditoría ────────────────────────────────────────────────
    historial = listar_nodos("PARAMS_FIS")
    if historial:
        with st.expander(f"🔍 Historial de auditoría — PARAMS_FIS ({len(historial)} registros)", expanded=False):
            for nodo in historial:
                ts  = nodo["timestamp"][:19].replace("T"," ")
                per = nodo["data"].get("periodo","—")
                col_a, col_b, col_c = st.columns([2, 1, 2])
                col_a.markdown(f"`{nodo['archivo']}`")
                col_b.markdown(f"**{per}**")
                col_c.markdown(f"_{ts}_")
                if st.button("📂 Cargar snapshot", key=f"load_param_{nodo['archivo']}",
                             use_container_width=True):
                    limpio = {k: v for k, v in nodo["data"].items() if k != "_auditoria"}
                    st.session_state["fis_params"] = limpio
                    st.success(f"✅ Snapshot `{nodo['archivo']}` cargado.")
                    st.rerun()
                st.markdown("---")
