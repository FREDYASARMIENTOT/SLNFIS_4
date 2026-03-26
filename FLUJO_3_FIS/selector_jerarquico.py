"""
=============================================================================
FLUJO_3_FIS / selector_jerarquico.py
Plantilla: Selector jerárquico Facultad → Programa → Asignatura
Persistencia: YYYYMMDD_NNN_SELECCION_FIS.json (vía _persistencia.py)
Auto-recuperación: si session_state está vacío, carga el último archivo.
=============================================================================
"""

import os
import sys
import streamlit as st

# ── Paths ────────────────────────────────────────────────────────────────────
_HERE   = os.path.dirname(os.path.abspath(__file__))
_PORTAL = os.path.join(_HERE, "..", "PORTAL_FIS")
if _PORTAL not in sys.path:
    sys.path.insert(0, _PORTAL)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ── Importaciones opcionales ─────────────────────────────────────────────────
try:
    from utils.loader_oferta import render_selector_jerarquia
    _EXCEL_OK = True
except ImportError:
    _EXCEL_OK = False

from _persistencia import guardar_nodo, recuperar_estado, listar_nodos

# ── Jerarquía de demo ────────────────────────────────────────────────────────
_MOCK = {
    "FACULTAD DE ECONOMÍA": {
        "Economía": ["Microeconomía I", "Macroeconomía I", "Teoría del Crecimiento", "Econometría I"],
        "Finanzas y Comercio": ["Finanzas Corporativas", "Mercados de Capitales", "Derivados Financieros"],
    },
    "FACULTAD DE ADMINISTRACIÓN": {
        "Administración de Empresas": ["Gestión de Costos", "Estrategia Empresarial", "Marketing"],
        "Contaduría Pública": ["Contabilidad General", "Auditoría I", "Costos I", "Costos II"],
    },
    "FACULTAD DE JURISPRUDENCIA": {
        "Derecho": ["Derecho Civil", "Derecho Comercial", "Derecho Tributario"],
    },
}


def _render_mock(key_prefix: str):
    st.info("ℹ️ Excel de oferta no encontrado — usando datos de demostración.", icon="📂")
    j = _MOCK
    col_f, col_p, col_a = st.columns(3)
    with col_f:
        fac_sel = st.multiselect("1️⃣ Facultad(es)", sorted(j.keys()),
                                  default=[sorted(j.keys())[0]], key=f"{key_prefix}_fac")
    progs = sorted({p for f in fac_sel for p in j.get(f, {}).keys()})
    with col_p:
        prog_sel = st.multiselect("2️⃣ Programa(s)", progs,
                                   default=progs[:1] if progs else [], key=f"{key_prefix}_prog")
    asigs = sorted({a for f in fac_sel for p in prog_sel for a in j.get(f, {}).get(p, [])})
    with col_a:
        asig_sel = st.multiselect("3️⃣ Asignatura(s)", asigs,
                                   default=asigs[:1] if asigs else [], key=f"{key_prefix}_asig")
    return fac_sel, prog_sel, asig_sel


def render(etapa: dict, cf3: dict):
    st.markdown("#### 🎓 Selección Jerárquica: Facultad → Programa → Asignatura")

    # ── Auto-recuperación desde disco si la RAM está vacía ───────────────
    recuperado = recuperar_estado("fis_seleccion", "SELECCION_FIS")
    if recuperado and recuperado.get("asignaturas"):
        aud = listar_nodos("SELECCION_FIS", limite=1)
        ts  = aud[0]["timestamp"][:19].replace("T"," ") if aud else "—"
        st.info(
            f"♻️ **Selección recuperada desde disco** (guardada: {ts}) — "
            f"{len(recuperado['asignaturas'])} asignatura(s). "
            "Puedes cambiarla y volver a guardar.",
            icon="💾"
        )

    st.caption("Selecciona las asignaturas a costear. Al guardar, se persiste en /DATOS con nomenclatura de auditoría.")

    kp = f"sel_{etapa.get('id','e')}"

    # ── Selector ─────────────────────────────────────────────────────────
    if _EXCEL_OK:
        try:
            fac_sel, prog_sel, asig_sel = render_selector_jerarquia(key_prefix=kp)
        except Exception as ex:
            st.warning(f"Error con Excel: {ex}. Usando demo.")
            fac_sel, prog_sel, asig_sel = _render_mock(kp)
    else:
        fac_sel, prog_sel, asig_sel = _render_mock(kp)

    # Badges de asignaturas seleccionadas
    if asig_sel:
        st.markdown(
            f"**{len(asig_sel)} asignatura(s):** " +
            " ".join([
                f"<span style='background:#2e7d32;color:#fff;padding:2px 8px;"
                f"border-radius:10px;font-size:.78em;margin:2px'>{a}</span>"
                for a in asig_sel
            ]),
            unsafe_allow_html=True
        )

    # ── Acciones ─────────────────────────────────────────────────────────
    col_g, col_v = st.columns([1, 2])

    with col_g:
        if st.button("💾 Guardar Selección", key=f"btn_sel_{etapa.get('id')}",
                     use_container_width=True, type="primary"):
            data = {
                "tipo":         "SELECCION_FIS",
                "cinta":        cf3.get("nombre",""),
                "etapa":        etapa.get("nombre",""),
                "etapa_id":     etapa.get("id",""),
                "facultades":   fac_sel,
                "programas":    prog_sel,
                "asignaturas":  asig_sel,
                "n_asignaturas":len(asig_sel),
                "etapa_origen": etapa.get("nombre",""),
                "cinta_nombre": cf3.get("nombre",""),
            }
            ruta = guardar_nodo("SELECCION_FIS", data)
            st.session_state["fis_seleccion"] = data
            st.success(f"✅ {len(asig_sel)} asignatura(s) persistidas → `{os.path.basename(ruta)}`")

    with col_v:
        sel_act = st.session_state.get("fis_seleccion", {})
        if sel_act.get("asignaturas"):
            st.info(
                f"📌 **Activo en memoria:** {sel_act.get('etapa_origen','')} — "
                f"{len(sel_act['asignaturas'])} asignatura(s)"
            )

    # ── Panel de auditoría ────────────────────────────────────────────────
    historial = listar_nodos("SELECCION_FIS")
    if historial:
        with st.expander(f"🔍 Historial de auditoría — SELECCION_FIS ({len(historial)} registros)", expanded=False):
            for nodo in historial:
                ts  = nodo["timestamp"][:19].replace("T"," ")
                n_a = nodo["data"].get("n_asignaturas", "?")
                col_a, col_b, col_c = st.columns([2, 1, 2])
                col_a.markdown(f"`{nodo['archivo']}`")
                col_b.markdown(f"**{n_a}** asig.")
                col_c.markdown(f"_{ts}_")
                # Botón cargar desde archivo
                if st.button("📂 Cargar este snapshot", key=f"load_snap_{nodo['archivo']}",
                             use_container_width=True):
                    limpio = {k: v for k, v in nodo["data"].items() if k != "_auditoria"}
                    st.session_state["fis_seleccion"] = limpio
                    st.success(f"✅ Snapshot `{nodo['archivo']}` cargado en memoria.")
                    st.rerun()
                st.markdown("---")
