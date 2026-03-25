"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/03_flujo_fis.py  — Flujo 3: Cinta Agéntica Dinámica FIS
=============================================================================
"""

import streamlit as st
import os, sys, json, random, time
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Flujo 3: FIS | Portal v8.1", layout="wide", page_icon="🧬")

# =============================================================================
# PATHS
# =============================================================================
_PAGES_DIR = Path(__file__).resolve().parent
_DATOS_DIR = _PAGES_DIR.parent.parent / "DATOS"
_DATOS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.header-box {
    background: linear-gradient(135deg, #2e7d32, #1b5e20);
    padding: 16px 30px; border-radius: 10px; color: white;
    text-align: center; margin-bottom: 24px;
    box-shadow: 0 4px 15px rgba(46,125,50,0.35);
}
.header-box h2 { margin: 0; font-weight: 700; }
/* Tarjeta de etapa en el builder */
.etapa-card {
    background: #1e1e2e; border-left: 5px solid #2e7d32;
    padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; color: #fff;
}
.etapa-card .badge {
    display:inline-block; background:#2e7d32; color:#fff;
    border-radius:50%; width:22px; height:22px; text-align:center;
    font-size:0.78em; line-height:22px; margin-right:8px; font-weight:700;
}
.etapa-card .tipo-tag {
    float:right; font-size:0.75em; padding:2px 8px;
    border-radius:10px; color:#fff;
}
.etapa-agente { background:#1565c0; }
.etapa-hitl   { background:#6a1b9a; }
/* Tab de etapa en ejecución */
.tab-header {
    background:#1e1e2e; border-radius:8px; padding:12px 16px;
    color:#fff; margin-bottom:12px;
}
.estado-badge {
    display:inline-block; padding:3px 10px; border-radius:12px;
    font-size:0.80em; font-weight:600; color:#fff;
}
.estado-pendiente  { background:#546e7a; }
.estado-completado { background:#2e7d32; }
.estado-bloqueado  { background:#b71c1c; }
/* Formulario de nueva etapa */
.form-box {
    background:#12122a; border:2px dashed #2e7d32;
    border-radius:10px; padding:20px; margin-top:12px;
}
/* Prompt del agente asistente */
.assist-box {
    background:#0d1117; color:#a8ff82; font-family:monospace;
    font-size:0.82em; padding:12px; border-radius:6px;
    border:1px solid #2e7d32; max-height:140px; overflow-y:auto;
}
/* Resumen cinta */
.resumen-box {
    background:#1e1e2e; border:1px solid #2e7d32;
    border-radius:10px; padding:18px; color:#fff; margin-top:16px;
}
.resumen-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:6px 10px; margin:3px 0; border-radius:6px; background:#12122a;
}
/* Chatbot */
.chat-user { background:#1565c0; color:#fff; border-radius:10px;
             padding:8px 12px; margin:4px 0; max-width:85%; float:right; clear:both; }
.chat-bot  { background:#1e1e2e; color:#a8ff82; border-radius:10px;
             padding:8px 12px; margin:4px 0; max-width:85%; float:left; clear:both; }
.telemetria { background:#1e1e1e; color:#00FF41; padding:10px; border-radius:5px;
              font-family:monospace; font-size:0.82em; text-align:center; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #eee !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO SESIÓN
# =============================================================================
if "cinta_datos" not in st.session_state:
    st.session_state["cinta_datos"] = {}
cinta_datos: dict = st.session_state["cinta_datos"]

_DEFAULT_F3 = {
    "nombre": "", "descripcion": "", "etapas": [],
    "guardada": False, "path": None, "timestamp": None, "chat_history": [],
}
if "cinta_f3" not in st.session_state:
    st.session_state["cinta_f3"] = dict(_DEFAULT_F3)
cinta_f3: dict = st.session_state["cinta_f3"]

if "f3_form" not in st.session_state:
    st.session_state["f3_form"] = {"open": False, "edit_idx": None}

# =============================================================================
# HELPERS
# =============================================================================
def _save_cinta(cf3: dict) -> str:
    nombre_safe = (cf3["nombre"] or "sin_nombre").replace(" ", "_").lower()
    ruta = str(_DATOS_DIR / f"cinta_f3_{nombre_safe}.json")
    cf3["timestamp"] = datetime.now().isoformat()
    serializable = {k: v for k, v in cf3.items() if k != "chat_history"}
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(serializable, fh, ensure_ascii=False, indent=2)
    return ruta

def _list_cintas() -> list[Path]:
    return sorted(_DATOS_DIR.glob("cinta_f3_*.json"))

def _load_cinta(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("chat_history", [])
    return data

def _is_desbloqueada(etapas: list, idx: int) -> bool:
    if idx == 0:
        return True
    return etapas[idx - 1].get("estado") == "completado"

def _demo_agente_response(etapa: dict, cinta_nombre: str) -> str:
    sp = etapa.get("system_prompt", "") or "Agente de propósito general."
    resps = [
        f"Procesando '{etapa['nombre']}' conforme al lineamiento: {sp[:60]}…",
        f"Análisis completado. La etapa '{etapa['nombre']}' no presenta anomalías.",
        f"Resultado generado para '{etapa['nombre']}'. Datos consistentes con la cinta '{cinta_nombre}'.",
        f"Agente ejecutado exitosamente. Salida registrada en la cinta estigmérgica.",
    ]
    return random.choice(resps)

def _demo_asistente_hitl(etapa: dict) -> str:
    preg = etapa.get("pregunta", "")
    return (
        f"Como asistente HITL analizo: «{preg[:80]}». "
        f"Basado en el contexto de la cinta, sugiero revisar los indicadores "
        f"disponibles antes de responder. Los datos previos muestran tendencia favorable."
    )

def _chatbot_response(prompt: str, cf3: dict) -> str:
    etapas      = cf3.get("etapas", [])
    completadas = [e["nombre"] for e in etapas if e.get("estado") == "completado"]
    pendientes  = [e["nombre"] for e in etapas if e.get("estado") == "pendiente"]
    respuestas  = [
        f"Soy el Agente FIS de la cinta '{cf3.get('nombre','sin nombre')}'. "
        f"Hay {len(completadas)} etapa(s) completadas y {len(pendientes)} pendientes.",
        f"Sobre '{prompt[:50]}': en el contexto de la cinta, las etapas completadas son: "
        f"{', '.join(completadas) or 'ninguna aún'}.",
        f"Recomendación: {'continúa con la siguiente etapa.' if pendientes else 'todas las etapas están completas, puedes guardar los resultados.'}",
        f"Analizando tu consulta con respecto a la cinta agéntica '{cf3.get('nombre','')}'. "
        f"El sistema está operando en modo {'ejecución' if cf3.get('guardada') else 'construcción'}.",
    ]
    return random.choice(respuestas)

# =============================================================================
# ENCABEZADO
# =============================================================================
st.markdown("""
<div class="header-box">
    <h2>🧬 Flujo 3 — Cinta Agéntica Dinámica FIS</h2>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# BARRA SUPERIOR: selector de modo / cinta guardada
# =============================================================================
top_c1, top_c2, top_c3 = st.columns([2, 1.2, 1])
with top_c1:
    cintas_disponibles = _list_cintas()
    if cintas_disponibles:
        opts = ["— Nueva cinta —"] + [p.stem.replace("cinta_f3_", "") for p in cintas_disponibles]
        sel = st.selectbox("📂 Cargar cinta guardada", opts, key="f3_selector")
        if sel != "— Nueva cinta —" and st.button("⬆ Cargar", key="f3_load_btn"):
            idx_p = opts.index(sel) - 1
            loaded = _load_cinta(cintas_disponibles[idx_p])
            st.session_state["cinta_f3"] = loaded
            cinta_f3 = loaded
            st.rerun()
with top_c2:
    if cinta_f3.get("guardada") and st.button("✏️ Editar cinta actual", use_container_width=True):
        cinta_f3["guardada"] = False
        st.session_state["cinta_f3"] = cinta_f3
        st.rerun()
with top_c3:
    if st.button("🗑 Nueva cinta vacía", use_container_width=True):
        st.session_state["cinta_f3"] = dict(_DEFAULT_F3)
        st.session_state["f3_form"]  = {"open": False, "edit_idx": None}
        st.rerun()

st.markdown("---")

# =============================================================================
# ══════════════════  MODO CONSTRUCCIÓN  ══════════════════
# =============================================================================
if not cinta_f3.get("guardada"):
    st.subheader("🏗️ Constructor de Cinta Agéntica")

    # Nombre y descripción
    bc1, bc2 = st.columns([2, 1])
    with bc1:
        nombre_cinta = st.text_input("Nombre de la cinta", value=cinta_f3.get("nombre",""),
                                     placeholder="Ej: Costeo ABC Semestre 2026-I", key="f3_nombre_cinta")
        cinta_f3["nombre"] = nombre_cinta
    with bc2:
        desc_cinta = st.text_input("Descripción breve", value=cinta_f3.get("descripcion",""),
                                   placeholder="Objetivo o contexto…", key="f3_desc_cinta")
        cinta_f3["descripcion"] = desc_cinta
    st.session_state["cinta_f3"] = cinta_f3

    st.markdown("---")
    st.markdown(f"##### 📋 Etapas ({len(cinta_f3['etapas'])} creadas)")

    # ── Lista de etapas existentes ──────────────────────────────────────────
    for i, etapa in enumerate(cinta_f3["etapas"]):
        tipo_tag  = ("agente-tag etapa-agente" if etapa["tipo"] == "agente"
                     else "hitl-tag etapa-hitl")
        tipo_text = "🤖 Agente IA" if etapa["tipo"] == "agente" else "🙋 HITL"
        extra     = (f"<br><small style='color:#aaa'>Prompt: {etapa['system_prompt'][:60]}…</small>"
                     if etapa["tipo"] == "agente" and etapa.get("system_prompt") else
                     f"<br><small style='color:#aaa'>❓ {etapa['pregunta'][:60]}…</small>"
                     if etapa.get("pregunta") else "")
        col_card, col_del = st.columns([10, 1])
        with col_card:
            st.markdown(
                f"<div class='etapa-card'>"
                f"<span class='badge'>{i+1}</span><b>{etapa['nombre']}</b>"
                f"<span class='tipo-tag {('etapa-agente' if etapa['tipo']=='agente' else 'etapa-hitl')}'>"
                f"{tipo_text}</span>{extra}"
                f"</div>", unsafe_allow_html=True,
            )
        with col_del:
            if st.button("🗑", key=f"del_{i}", help="Eliminar etapa"):
                cinta_f3["etapas"].pop(i)
                st.session_state["cinta_f3"] = cinta_f3
                st.rerun()

    # ── Formulario nueva etapa ──────────────────────────────────────────────
    f3_form = st.session_state["f3_form"]

    if not f3_form["open"]:
        if st.button("➕ Crear Etapa", use_container_width=True, type="secondary"):
            f3_form["open"] = True
            st.session_state["f3_form"] = f3_form
            st.rerun()
    else:
        st.markdown("<div class='form-box'>", unsafe_allow_html=True)
        st.markdown("##### ➕ Nueva Etapa")

        fn_nombre = st.text_input("Nombre de la etapa *", placeholder="Ej: Validación de Costos", key="f3_fn")
        fn_tipo   = st.radio("Tipo de etapa", ["🤖 Agente IA", "🙋 HITL — Humano"],
                             horizontal=True, key="f3_ft")

        if "Agente" in fn_tipo:
            fn_sp    = st.text_area("📝 System Prompt del agente", height=100, key="f3_fsp",
                                    placeholder="Eres un agente experto en costeo ABC universitario…")
            fn_preg  = ""
            fn_tr    = "sino"
            fn_opts  = []
        else:
            fn_sp   = ""
            fn_preg = st.text_area("❓ Pregunta de validación para el humano", height=80,
                                   key="f3_fpreg",
                                   placeholder="¿Los costos calculados están dentro del presupuesto aprobado?")
            fn_tr_raw = st.radio("Tipo de respuesta", ["✅ Sí / No", "📋 Selección Única (múltiples opciones)"],
                                 horizontal=True, key="f3_ftr")
            fn_tr = "sino" if "Sí" in fn_tr_raw else "seleccion"
            fn_opts = []
            if fn_tr == "seleccion":
                opts_raw = st.text_input("Opciones separadas por coma",
                                         placeholder="Aprobado, Rechazado, Requiere revisión", key="f3_fopts")
                fn_opts = [o.strip() for o in opts_raw.split(",") if o.strip()]

        fa, fb = st.columns(2)
        if fa.button("✅ Agregar Etapa", use_container_width=True, type="primary", key="f3_add"):
            if fn_nombre.strip():
                nueva = {
                    "id"            : f"etapa_{len(cinta_f3['etapas'])+1:03d}",
                    "nombre"        : fn_nombre.strip(),
                    "tipo"          : "agente" if "Agente" in fn_tipo else "hitl",
                    "system_prompt" : fn_sp,
                    "pregunta"      : fn_preg,
                    "tipo_respuesta": fn_tr,
                    "opciones"      : fn_opts,
                    "estado"        : "pendiente",
                    "resultado"     : None,
                    "ts_completado" : None,
                }
                cinta_f3["etapas"].append(nueva)
                f3_form["open"] = False
                st.session_state["cinta_f3"] = cinta_f3
                st.session_state["f3_form"]  = f3_form
                st.rerun()
            else:
                st.warning("El nombre de la etapa es obligatorio.")

        if fb.button("✖ Cancelar", use_container_width=True, key="f3_cancel"):
            f3_form["open"] = False
            st.session_state["f3_form"] = f3_form
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Guardar Cinta ───────────────────────────────────────────────────────
    if cinta_f3["etapas"]:
        if not cinta_f3["nombre"].strip():
            st.warning("⚠️ Asigna un nombre a la cinta antes de guardar.")
        else:
            if st.button("💾 Guardar Cinta", use_container_width=True, type="primary"):
                cinta_f3["guardada"] = True
                ruta = _save_cinta(cinta_f3)
                cinta_f3["path"] = ruta
                st.session_state["cinta_f3"] = cinta_f3
                st.success(f"✅ Cinta guardada en `{ruta}`")
                st.rerun()
    else:
        st.info("Crea al menos una etapa antes de guardar.", icon="💡")

# =============================================================================
# ══════════════════  MODO EJECUCIÓN  ══════════════════
# =============================================================================
else:
    etapas  = cinta_f3["etapas"]
    n_et    = len(etapas)
    n_ok    = sum(1 for e in etapas if e.get("estado") == "completado")

    # ── Banner estado global ────────────────────────────────────────────────
    prog_col, stat_col = st.columns([3, 1])
    with prog_col:
        st.progress(n_ok / n_et if n_et else 0,
                    text=f"{n_ok}/{n_et} etapas completadas — Cinta: **{cinta_f3['nombre']}**")
    with stat_col:
        if n_ok == n_et:
            st.success("✅ Cinta completa")
        else:
            st.info(f"⏳ Etapa {n_ok+1}/{n_et} activa")

    st.markdown("---")

    # ── Pestañas de ejecución ───────────────────────────────────────────────
    tab_labels = [f"{'✅' if e.get('estado')=='completado' else ('🔵' if _is_desbloqueada(etapas,i) else '🔒')} {i+1}. {e['nombre']}"
                  for i, e in enumerate(etapas)]
    tabs = st.tabs(tab_labels)

    for t_idx, (tab, etapa) in enumerate(zip(tabs, etapas)):
        with tab:
            desbloqueada = _is_desbloqueada(etapas, t_idx)
            estado       = etapa.get("estado", "pendiente")
            tipo         = etapa["tipo"]

            # Header tarjeta
            tipo_label = "🤖 Agente IA" if tipo == "agente" else "🙋 HITL — Humano"
            badge_class = ("estado-completado" if estado == "completado" else
                           "estado-pendiente"  if desbloqueada else "estado-bloqueado")
            badge_text  = ("✅ Completado" if estado == "completado" else
                           "🔵 En espera" if desbloqueada else "🔒 Bloqueado")
            st.markdown(
                f"<div class='tab-header'>"
                f"<b>{tipo_label}</b> &nbsp;&nbsp;"
                f"<span class='estado-badge {badge_class}'>{badge_text}</span>"
                f"<span style='float:right;color:#aaa;font-size:0.85em'>"
                f"Etapa {t_idx+1} de {n_et}</span>"
                f"</div>", unsafe_allow_html=True,
            )

            # Configurar (expander)
            with st.expander("⚙️ Configurar", expanded=(estado=="pendiente" and desbloqueada)):
                if tipo == "agente":
                    nuevo_sp = st.text_area("System Prompt", value=etapa.get("system_prompt",""),
                                            height=90, key=f"cfg_sp_{t_idx}")
                    if st.button("💾 Actualizar prompt", key=f"cfg_save_{t_idx}"):
                        cinta_f3["etapas"][t_idx]["system_prompt"] = nuevo_sp
                        st.session_state["cinta_f3"] = cinta_f3
                        _save_cinta(cinta_f3)
                        st.success("Prompt actualizado y guardado.")
                else:
                    nueva_preg = st.text_area("Pregunta de validación", value=etapa.get("pregunta",""),
                                              height=70, key=f"cfg_preg_{t_idx}")
                    tr_disp = ("✅ Sí / No" if etapa.get("tipo_respuesta","sino")=="sino"
                               else "📋 Selección")
                    st.caption(f"Tipo de respuesta: **{tr_disp}**")
                    if etapa.get("opciones"):
                        st.caption(f"Opciones: {' · '.join(etapa['opciones'])}")
                    if st.button("💾 Actualizar pregunta", key=f"cfg_psave_{t_idx}"):
                        cinta_f3["etapas"][t_idx]["pregunta"] = nueva_preg
                        st.session_state["cinta_f3"] = cinta_f3
                        _save_cinta(cinta_f3)
                        st.success("Pregunta actualizada y guardada.")

            st.markdown("---")

            # ── ETAPA BLOQUEADA ─────────────────────────────────────────────
            if not desbloqueada:
                prev = etapas[t_idx - 1]["nombre"]
                st.warning(f"🔒 Completa la etapa anterior **«{prev}»** para desbloquear esta.", icon="🔒")

            # ── ETAPA YA COMPLETADA ─────────────────────────────────────────
            elif estado == "completado":
                st.success(f"✅ Completada el {etapa.get('ts_completado','—')}")
                res = etapa.get("resultado")
                if res:
                    if tipo == "agente":
                        st.markdown("**📤 Respuesta del agente:**")
                        st.markdown(f"<div class='assist-box'>{res}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Respuesta registrada:** `{res}`")
                if st.button("↩ Reabrir etapa", key=f"reopen_{t_idx}", use_container_width=False):
                    cinta_f3["etapas"][t_idx]["estado"]        = "pendiente"
                    cinta_f3["etapas"][t_idx]["resultado"]      = None
                    cinta_f3["etapas"][t_idx]["ts_completado"]  = None
                    # Bloquear las siguientes
                    for j in range(t_idx + 1, n_et):
                        cinta_f3["etapas"][j]["estado"]       = "pendiente"
                        cinta_f3["etapas"][j]["resultado"]    = None
                        cinta_f3["etapas"][j]["ts_completado"]= None
                    st.session_state["cinta_f3"] = cinta_f3
                    st.rerun()

            # ── ETAPA PENDIENTE Y DESBLOQUEADA ──────────────────────────────
            else:
                # Agente asistente HITL (siempre presente)
                ag_col, ej_col = st.columns([1.4, 1])

                with ag_col:
                    asistente_label = (f"🤖 Agente — {etapa['nombre']}"
                                       if tipo == "agente" else
                                       f"🤖 Asistente para «{etapa['nombre']}»")
                    st.markdown(f"**{asistente_label}**")
                    if tipo == "agente":
                        st.caption(f"System prompt: _{etapa.get('system_prompt','—')[:70]}_")
                    else:
                        st.caption("El agente analiza el contexto para asistir tu decisión.")

                    if st.button("▶ Consultar agente", key=f"ask_ag_{t_idx}", use_container_width=True):
                        with st.spinner("Agente procesando…"):
                            time.sleep(random.uniform(0.3, 0.7))
                            resp = _demo_agente_response(etapa, cinta_f3["nombre"])
                            if tipo == "hitl":
                                resp = _demo_asistente_hitl(etapa)
                        cinta_f3["etapas"][t_idx]["asistente_resp"] = resp
                        st.session_state["cinta_f3"] = cinta_f3
                        st.rerun()

                    if etapa.get("asistente_resp"):
                        st.markdown("<div class='assist-box'>"
                                    + etapa["asistente_resp"] + "</div>",
                                    unsafe_allow_html=True)

                with ej_col:
                    if tipo == "agente":
                        # ── AGENTE IA: ejecutar y completar ────────────────
                        st.markdown("**▶ Ejecutar etapa**")
                        if st.button("🚀 Ejecutar agente", key=f"run_{t_idx}",
                                     use_container_width=True, type="primary"):
                            with st.spinner(f"Ejecutando «{etapa['nombre']}»…"):
                                time.sleep(random.uniform(0.4, 0.9))
                                resultado = _demo_agente_response(etapa, cinta_f3["nombre"])
                            cinta_f3["etapas"][t_idx].update({
                                "estado"       : "completado",
                                "resultado"    : resultado,
                                "ts_completado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            })
                            st.session_state["cinta_f3"] = cinta_f3
                            _save_cinta(cinta_f3)
                            st.rerun()

                    else:
                        # ── HITL: mostrar pregunta y capturar respuesta ─────
                        st.markdown("**🙋 Tu validación**")
                        st.markdown(f"_{etapa.get('pregunta','—')}_")

                        tr = etapa.get("tipo_respuesta", "sino")
                        if tr == "sino":
                            hc1, hc2 = st.columns(2)
                            if hc1.button("✅ Sí", key=f"hitl_si_{t_idx}", use_container_width=True, type="primary"):
                                cinta_f3["etapas"][t_idx].update({
                                    "estado": "completado", "resultado": "Sí",
                                    "ts_completado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                })
                                st.session_state["cinta_f3"] = cinta_f3
                                _save_cinta(cinta_f3)
                                st.rerun()
                            if hc2.button("❌ No", key=f"hitl_no_{t_idx}", use_container_width=True):
                                cinta_f3["etapas"][t_idx].update({
                                    "estado": "completado", "resultado": "No",
                                    "ts_completado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                })
                                st.session_state["cinta_f3"] = cinta_f3
                                _save_cinta(cinta_f3)
                                st.rerun()
                        else:
                            opciones = etapa.get("opciones") or ["Opción A", "Opción B", "Opción C"]
                            sel_op   = st.radio("Selecciona una opción:", opciones,
                                                key=f"hitl_sel_{t_idx}")
                            if st.button("✅ Confirmar selección", key=f"hitl_conf_{t_idx}",
                                         use_container_width=True, type="primary"):
                                cinta_f3["etapas"][t_idx].update({
                                    "estado": "completado", "resultado": sel_op,
                                    "ts_completado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                })
                                st.session_state["cinta_f3"] = cinta_f3
                                _save_cinta(cinta_f3)
                                st.rerun()

    # ── RESUMEN CINTA ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='resumen-box'>", unsafe_allow_html=True)
    st.markdown(f"### 📋 Resumen — Cinta: **{cinta_f3['nombre']}**")
    if cinta_f3.get("descripcion"):
        st.caption(cinta_f3["descripcion"])
    st.markdown(f"**{n_et} etapas** · {n_ok} completadas · guardada: `{cinta_f3.get('path','—')}`")
    st.markdown("---")

    for i, e in enumerate(etapas):
        icono_tipo   = "🤖" if e["tipo"] == "agente" else "🙋"
        icono_estado = "✅" if e["estado"] == "completado" else ("🔵" if _is_desbloqueada(etapas,i) else "🔒")
        resultado_str = f"→ `{e['resultado']}`" if e.get("resultado") else ""
        st.markdown(
            f"<div class='resumen-row'>"
            f"<span><b>{i+1}.</b> {icono_tipo} {e['nombre']}</span>"
            f"<span style='color:#aaa;font-size:0.82em'>"
            f"{icono_estado} {e['estado'].title()} {resultado_str}</span>"
            f"</div>", unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# CHATBOT FIS — inferior izquierdo (sidebar, colapsable)
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding-bottom:10px;border-bottom:2px solid #2e7d32;margin-bottom:14px;">
        <h2 style="margin:0;color:#81c784;">🏛️ URosario</h2>
        <span style="font-size:11px;color:#aaa;">Portal FIS v8.1</span>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("portal_fis.py",               label="🏠  Inicio",              icon="🏠")
    st.page_link("pages/00_comparacion.py",      label="📊  Comparación",         icon="📊")
    st.page_link("pages/01_flujo_humano.py",     label="🙋  Flujo 1: Humano",     icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py", label="🤖  Flujo 2: Agentes IA", icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",        label="🧬  Flujo 3: FIS",        icon="3️⃣")

    st.markdown("---")
    # Métricas rápidas de la cinta
    if cinta_f3.get("nombre"):
        et = cinta_f3.get("etapas", [])
        n_c = sum(1 for e in et if e.get("estado") == "completado")
        st.metric("🧬 Cinta activa", cinta_f3["nombre"][:20])
        st.metric("✅ Progreso", f"{n_c}/{len(et)} etapas")

    st.markdown("---")

    # ── Chatbot (al final del sidebar, siempre último) ──────────────────────
    with st.expander("🤖 Asistente FIS — Chatbot", expanded=False):
        chat_h = cinta_f3.get("chat_history", [])

        # Mostrar historial
        chat_container = st.container()
        with chat_container:
            for msg in chat_h[-10:]:   # últimos 10 mensajes
                if msg["role"] == "user":
                    st.markdown(
                        f"<div class='chat-user'>👤 {msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div class='chat-bot'>🤖 {msg['content']}</div>",
                        unsafe_allow_html=True,
                    )

        user_input = st.text_input("Escribe tu consulta…", key="f3_chat_input",
                                   label_visibility="collapsed",
                                   placeholder="Pregunta al Agente FIS…")
        if st.button("Enviar", key="f3_chat_send", use_container_width=True):
            if user_input.strip():
                with st.spinner("FIS pensando…"):
                    time.sleep(random.uniform(0.2, 0.5))
                    resp = _chatbot_response(user_input, cinta_f3)
                chat_h.append({"role": "user",      "content": user_input.strip()})
                chat_h.append({"role": "assistant", "content": resp})
                cinta_f3["chat_history"] = chat_h
                st.session_state["cinta_f3"] = cinta_f3
                st.rerun()

        if chat_h and st.button("🗑 Limpiar chat", key="f3_clear_chat",
                                use_container_width=True):
            cinta_f3["chat_history"] = []
            st.session_state["cinta_f3"] = cinta_f3
            st.rerun()

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""<div class="telemetria">
🧬 <b>FIS SIMBIOMEMÉSICO ACTIVO</b> | Cinta Agéntica Dinámica v8.1 | Pinecone: 3072 dims | URosario
</div>""", unsafe_allow_html=True)
