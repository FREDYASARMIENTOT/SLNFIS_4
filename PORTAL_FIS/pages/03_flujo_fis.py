"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/03_flujo_fis.py  — Flujo 3: Cinta Agéntica Dinámica FIS
Modo: Mixto — Formulario manual + Chatbot Arquitecto + Artefactos UI
=============================================================================
"""

import importlib.util
import streamlit as st
import streamlit.components.v1 as components
import os, sys, json, random, time, textwrap
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Flujo 3: FIS | Portal v8.1", layout="wide", page_icon="🧬")

# =============================================================================
# PATHS
# =============================================================================
_PAGES_DIR  = Path(__file__).resolve().parent
_DATOS_DIR  = _PAGES_DIR.parent.parent / "DATOS"
_FLUJO3_DIR = _PAGES_DIR.parent.parent / "FLUJO_3_FIS"
_DATOS_DIR.mkdir(parents=True, exist_ok=True)
_FLUJO3_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.header-box{background:linear-gradient(135deg,#2e7d32,#1b5e20);padding:14px 28px;
  border-radius:10px;color:white;text-align:center;margin-bottom:20px;
  box-shadow:0 4px 15px rgba(46,125,50,.35);}
.header-box h2{margin:0;font-weight:700;}
.etapa-card{background:#1e1e2e;border-left:5px solid #2e7d32;padding:10px 14px;
  border-radius:8px;margin-bottom:6px;color:#fff;}
.etapa-card .badge{display:inline-block;background:#2e7d32;color:#fff;border-radius:50%;
  width:20px;height:20px;text-align:center;font-size:.75em;line-height:20px;margin-right:7px;font-weight:700;}
.etapa-card .tipo-tag{float:right;font-size:.73em;padding:2px 8px;border-radius:10px;color:#fff;}
.etapa-agente{background:#1565c0;} .etapa-hitl{background:#6a1b9a;}
.tab-header{background:#1e1e2e;border-radius:8px;padding:10px 14px;color:#fff;margin-bottom:10px;}
.estado-badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.80em;font-weight:600;color:#fff;}
.estado-pendiente{background:#546e7a;} .estado-completado{background:#2e7d32;} .estado-bloqueado{background:#b71c1c;}
.arq-box{background:#0d1117;border:1px solid #2e7d32;border-radius:8px;
  padding:10px;height:310px;overflow-y:auto;}
.arq-user{background:#1565c0;color:#fff;border-radius:8px;padding:6px 10px;
  margin:4px 0;max-width:90%;float:right;clear:both;font-size:.86em;}
.arq-bot{background:#1e1e2e;color:#a8ff82;border-radius:8px;padding:6px 10px;
  margin:4px 0;max-width:90%;float:left;clear:both;font-size:.86em;}
.json-box{background:#0d1117;color:#82aaff;font-family:monospace;font-size:.78em;
  padding:10px;border-radius:6px;border:1px solid #30363d;max-height:160px;overflow-y:auto;}
.telemetria{background:#1e1e1e;color:#00FF41;padding:8px;border-radius:5px;
  font-family:monospace;font-size:.80em;text-align:center;}
.crud-item{background:#1e1e2e;border-left:4px solid #2e7d32;padding:7px 11px;
  border-radius:6px;margin-bottom:5px;color:#fff;font-size:.88em;}
.form-section{background:#1a1a2e;border-radius:8px;padding:14px;margin-bottom:12px;}
[data-testid="stSidebar"]{background-color:#1a1a2e;}
[data-testid="stSidebar"] *{color:#eee !important;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO INICIAL  ─  prefijo _nf_ = borrador nueva etapa
# =============================================================================
_DEFAULT_F3 = {
    "nombre":"","descripcion":"","etapas":[],
    "guardada":False,"path":None,"timestamp":None,"arq_chat_history":[]
}
_DRAFT_DEFAULTS = {
    "_nf_version": 0,   # incrementar para limpiar el formulario sin tocar widgets ya renderizados
}

def _init_state():
    defaults = {
        "cinta_f3": dict(_DEFAULT_F3),
        "arq_chat":  [],
        "show_crud": False,
        "edit_cinta_idx": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    for k, v in _DRAFT_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _reset_draft():
    # Incrementar la versión cambia TODAS las keys de widgets del formulario.
    # Streamlit trata los widgets con key nueva como recién creados → renderiza vacíos.
    # Nunca tocamos directamente las keys bound a widgets ya renderizados.
    st.session_state["_nf_version"] = st.session_state.get("_nf_version", 0) + 1

# =============================================================================
# I/O — CINTA INMUTABLE
# =============================================================================

def _save_cinta(cf3: dict) -> str:
    if not cf3.get("nombre"):
        return ""
    cf3["arq_chat_history"] = st.session_state.get("arq_chat", [])
    safe = cf3["nombre"].replace(" ","_").lower()
    ruta = str(_DATOS_DIR / f"cinta_f3_{safe}.json")
    cf3["timestamp"] = datetime.now().isoformat()
    cf3["path"] = ruta
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(cf3, fh, ensure_ascii=False, indent=2)
    return ruta

def _list_cintas() -> list[Path]:
    return sorted(_DATOS_DIR.glob("cinta_f3_*.json"))

def _load_cinta(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    for e in data.get("etapas", []):
        e.setdefault("chat_history", [])
        e.setdefault("artefacto_path", None)
        e.setdefault("nombre_agente", e.get("nombre",""))
        e.setdefault("instrucciones_adicionales", "")
        e.setdefault("plantilla_archivo", None)
        e.setdefault("respuesta_hitl", None)
        e.setdefault("comentarios_hitl", "")
        e.setdefault("arq_context", [])
    return data

def _delete_cinta(path: str):
    if os.path.exists(path):
        os.remove(path)

def _rename_cinta(old_path: str, new_nombre: str, new_desc: str) -> str:
    data = {}
    if os.path.exists(old_path):
        with open(old_path, encoding="utf-8") as fh:
            data = json.load(fh)
    data.update({"nombre": new_nombre, "descripcion": new_desc})
    safe = new_nombre.replace(" ","_").lower()
    new_path = str(_DATOS_DIR / f"cinta_f3_{safe}.json")
    data["path"] = new_path
    data["timestamp"] = datetime.now().isoformat()
    with open(new_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    if old_path != new_path and os.path.exists(old_path):
        os.remove(old_path)
    return new_path

# =============================================================================
# PLANTILLAS FLUJO_3_FIS
# =============================================================================

def _list_templates() -> list[str]:
    return ["— ninguna —"] + [f.name for f in sorted(_FLUJO3_DIR.glob("*.py"))]

def _load_template(filename: str):
    """Carga dinámica de un módulo de plantilla desde FLUJO_3_FIS/."""
    if not filename or filename == "— ninguna —":
        return None
    path = _FLUJO3_DIR / filename
    if not path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("fis_tpl", path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        st.error(f"Error cargando plantilla `{filename}`: {e}")
        return None

# =============================================================================
# CHATBOT ARQUITECTO — respuestas de sugerencia
# =============================================================================

def _arq_responder(user_msg: str, etapa_draft: dict) -> str:
    m = user_msg.lower()
    sugs = []
    if any(k in m for k in ["hitl","validar","humano","aprobar","confirmar","decisión","decision"]):
        sugs.append("**Tipo sugerido:** HITL — el humano debe tomar una decisión antes de avanzar.")
        sugs.append("**System Prompt:** 'Eres asistente de validación. Presenta los hallazgos de forma concisa para que el usuario pueda aprobar o rechazar con criterio.'")
        sugs.append("**Tipo respuesta:** usa `si_no` para flujos lineales o `opcion_unica` si hay múltiples caminos posibles.")
    if any(k in m for k in ["agente","autónomo","calcular","procesar","analizar","generar"]):
        sugs.append("**Tipo sugerido:** Agente IA Autónomo — procesa y entrega resultado sin intervención humana.")
        sugs.append("**System Prompt:** 'Eres un agente especializado. Analiza los datos, aplica el algoritmo y devuelve resultado en JSON estructurado.'")
    if any(k in m for k in ["selección","seleccion","jerarquía","jerarquia","facultad","asignatura"]):
        sugs.append("**Plantilla sugerida:** `selector_jerarquico.py` — permite al usuario escoger Facultad → Programa → Asignatura desde el Excel real.")
    if any(k in m for k in ["costo","costeo","valor","precio"]):
        sugs.append("**Plantilla sugerida:** `costeo_asignaturas.py` — calcula costos ABC sobre la selección de la etapa anterior.")
        sugs.append("**También útil:** `parametros_costeo.py` — formulario para ingresar m², valor hora-profesor, licencias, etc.")
    if any(k in m for k in ["prompt","instrucción","instruccion","system"]):
        tipo = etapa_draft.get("tipo","agente")
        nombre = etapa_draft.get("nombre","esta etapa") or "esta etapa"
        sugs.append(f"**System Prompt para `{nombre}` ({tipo}):** 'Eres experto en {nombre}. Tu objetivo es [describe objetivo]. Devuelve resultados en formato estructurado.'")
    if not sugs:
        sugs = [
            "Describe el objetivo de la etapa y te sugiero el tipo, system prompt y plantilla adecuada.",
            "Puedo ayudarte a redactar el **System Prompt**, elegir entre **Agente IA** o **HITL**, y seleccionar la **plantilla de UI** correcta.",
        ]
    intro = random.choice([
        "Basado en tu descripción:",
        "Mis recomendaciones para esta etapa:",
        "Aquí el diseño sugerido:",
    ])
    return intro + "\n\n" + "\n\n".join(f"- {s}" for s in sugs)

# =============================================================================
# GENERADOR DE ARTEFACTOS HTML/CSS/JS
# =============================================================================

def _html_tabla(titulo, desc):
    return textwrap.dedent(f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{titulo}</title>
<style>body{{font-family:Inter,sans-serif;background:#0d1117;color:#e0e0e0;padding:14px;}}
h3{{color:#81c784;border-bottom:2px solid #2e7d32;padding-bottom:5px;}}
table{{width:100%;border-collapse:collapse;}}th{{background:#2e7d32;color:#fff;padding:8px 10px;text-align:left;}}
td{{padding:6px 10px;border-bottom:1px solid #333;}}tr:hover{{background:#1e1e2e;}}
</style></head><body><h3>📊 {titulo}</h3><p style="color:#aaa;font-size:.86em">{desc}</p>
<table><thead><tr><th>#</th><th>Concepto</th><th>Valor</th><th>Estado</th></tr></thead>
<tbody><tr><td>1</td><td>Ítem A</td><td>$1.200.000</td><td>Activo</td></tr>
<tr><td>2</td><td>Ítem B</td><td>$850.000</td><td>Activo</td></tr>
<tr><td>3</td><td>Ítem C</td><td>$430.000</td><td>Revisión</td></tr></tbody></table>
<script>console.log("Artefacto tabla — {titulo}");</script></body></html>""")

def _html_chart(titulo, desc):
    return textwrap.dedent(f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{titulo}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{{font-family:Inter,sans-serif;background:#0d1117;color:#e0e0e0;padding:14px;}}
h3{{color:#81c784;border-bottom:2px solid #2e7d32;padding-bottom:5px;}}canvas{{max-height:220px;}}
</style></head><body><h3>📈 {titulo}</h3><p style="color:#aaa;font-size:.86em">{desc}</p>
<canvas id="c"></canvas>
<script>new Chart(document.getElementById('c').getContext('2d'),{{type:'bar',
data:{{labels:['E1','E2','E3','E4','E5'],
datasets:[{{label:'{titulo}',data:[1200000,850000,430000,970000,610000],
backgroundColor:['#2e7d32','#1565c0','#6a1b9a','#e65100','#00695c'],borderRadius:6}}]}},
options:{{responsive:true,plugins:{{legend:{{labels:{{color:'#e0e0e0'}}}}}},
scales:{{x:{{ticks:{{color:'#aaa'}},grid:{{color:'#333'}}}},y:{{ticks:{{color:'#aaa'}},grid:{{color:'#333'}}}}}}
}}}});</script></body></html>""")

def _html_form(titulo, desc):
    return textwrap.dedent(f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{titulo}</title>
<style>body{{font-family:Inter,sans-serif;background:#0d1117;color:#e0e0e0;padding:14px;}}
h3{{color:#81c784;border-bottom:2px solid #2e7d32;padding-bottom:5px;}}
.fg{{margin-bottom:10px;}}label{{display:block;color:#81c784;font-size:.84em;margin-bottom:3px;}}
input,select,textarea{{width:100%;padding:6px 9px;background:#1e1e2e;color:#e0e0e0;
  border:1px solid #2e7d32;border-radius:5px;font-size:.88em;}}
button{{background:#2e7d32;color:#fff;border:none;padding:8px 18px;border-radius:5px;cursor:pointer;margin-top:6px;}}
button:hover{{background:#388e3c;}}#msg{{color:#a8ff82;margin-top:8px;display:none;font-size:.86em;}}
</style></head><body><h3>📝 {titulo}</h3><p style="color:#aaa;font-size:.86em">{desc}</p>
<form onsubmit="s(event)">
<div class="fg"><label>Concepto</label><input type="text" required placeholder="Ej: Honorarios…"/></div>
<div class="fg"><label>Valor ($)</label><input type="number" min="0" placeholder="0"/></div>
<div class="fg"><label>Categoría</label><select><option>Costo Directo</option>
<option>Costo Indirecto</option><option>Overhead</option></select></div>
<div class="fg"><label>Observaciones</label><textarea rows="2"></textarea></div>
<button type="submit">✅ Registrar</button></form>
<div id="msg">✔ Registrado correctamente.</div>
<script>function s(e){{e.preventDefault();var m=document.getElementById('msg');
m.style.display='block';setTimeout(()=>m.style.display='none',2500);}}</script></body></html>""")

def _html_dashboard(titulo, desc):
    return textwrap.dedent(f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{titulo}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{{font-family:Inter,sans-serif;background:#0d1117;color:#e0e0e0;padding:12px;margin:0;}}
h3{{color:#81c784;margin:0 0 4px;font-size:1.05em;}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px;}}
.card{{background:#1e1e2e;border-left:4px solid #2e7d32;border-radius:7px;padding:9px 12px;}}
.card .label{{color:#aaa;font-size:.74em;text-transform:uppercase;}}
.card .value{{color:#81c784;font-size:1.3em;font-weight:700;}}
.card .delta{{color:#ffb300;font-size:.78em;}}canvas{{max-height:170px;}}
</style></head><body>
<h3>📊 {titulo}</h3><p style="color:#aaa;font-size:.82em;margin:0 0 10px">{desc}</p>
<div class="grid">
<div class="card"><div class="label">Costo Total</div><div class="value">$2.48M</div><div class="delta">↑ 3.2%</div></div>
<div class="card"><div class="label">Asignaturas</div><div class="value">14</div><div class="delta">Sin cambio</div></div>
<div class="card"><div class="label">Utilidad Simbiótica</div><div class="value">87.4</div><div class="delta">↑ 1.8pts</div></div>
</div><canvas id="d"></canvas>
<script>new Chart(document.getElementById('d').getContext('2d'),{{type:'line',
data:{{labels:['Ene','Feb','Mar','Abr','May','Jun'],
datasets:[{{label:'Costo ($M)',data:[2.1,2.3,2.2,2.4,2.5,2.48],
borderColor:'#81c784',backgroundColor:'rgba(46,125,50,.15)',fill:true,tension:.4,
pointBackgroundColor:'#81c784'}}]}},
options:{{responsive:true,plugins:{{legend:{{labels:{{color:'#e0e0e0'}}}}}},
scales:{{x:{{ticks:{{color:'#aaa'}},grid:{{color:'#333'}}}},y:{{ticks:{{color:'#aaa'}},grid:{{color:'#333'}}}}}}
}}}});</script></body></html>""")

def _html_generico(titulo, desc):
    return textwrap.dedent(f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{titulo}</title>
<style>body{{font-family:Inter,sans-serif;background:#0d1117;color:#e0e0e0;
  padding:20px;display:flex;flex-direction:column;align-items:center;}}
.panel{{background:#1e1e2e;border:1px solid #2e7d32;border-radius:10px;padding:22px 26px;
  max-width:580px;width:100%;text-align:center;}}
h3{{color:#81c784;margin-top:0;}}p{{color:#aaa;font-size:.90em;line-height:1.6;}}
.badge{{background:#2e7d32;color:#fff;border-radius:12px;padding:4px 14px;font-size:.84em;
  display:inline-block;margin-top:10px;}}
</style></head><body><div class="panel">
<h3>🧬 {titulo}</h3><p>{desc}</p>
<span class="badge">Artefacto FIS — URosario v8.1</span>
</div></body></html>""")

def _generar_html_artefacto(desc: str, titulo: str) -> str:
    d = desc.lower()
    if any(k in d for k in ["tabla","table","lista","grid"]): return _html_tabla(titulo, desc)
    if any(k in d for k in ["gráfica","grafica","chart","barras","línea","linea","pie"]): return _html_chart(titulo, desc)
    if any(k in d for k in ["formulario","form","captura","input","parámetro","parametro","campo"]): return _html_form(titulo, desc)
    if any(k in d for k in ["dashboard","panel","métricas","metricas","resumen","kpi"]): return _html_dashboard(titulo, desc)
    return _html_generico(titulo, desc)

def _save_artefacto(cf3: dict, etapa_id: str, html: str) -> str:
    safe  = cf3.get("nombre","cinta").replace(" ","_").lower()
    fname = f"artefacto_{safe}_{etapa_id}.html"
    ruta  = str(_DATOS_DIR / fname)
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(html)
    return ruta

# =============================================================================
# PILAR 1 — SIDEBAR CRUD
# =============================================================================

def render_sidebar_crud():
    cf3 = st.session_state["cinta_f3"]
    with st.sidebar:
        st.markdown("""<div style="text-align:center;padding-bottom:10px;
            border-bottom:2px solid #2e7d32;margin-bottom:12px;">
            <h2 style="margin:0;color:#81c784;">🏛️ URosario</h2>
            <span style="font-size:11px;color:#aaa;">Portal FIS v8.1</span>
            </div>""", unsafe_allow_html=True)
        st.page_link("portal_fis.py",               label="🏠  Inicio")
        st.page_link("pages/00_comparacion.py",      label="📊  Comparación")
        st.page_link("pages/01_flujo_humano.py",     label="🙋  Flujo 1: Humano")
        st.page_link("pages/02_flujo_agentes_ia.py", label="🤖  Flujo 2: Agentes IA")
        st.page_link("pages/03_flujo_fis.py",        label="🧬  Flujo 3: FIS")
        st.markdown("---")

        if st.button("📂 Consultar Flujos", key="btn_crud", use_container_width=True):
            st.session_state["show_crud"] = not st.session_state["show_crud"]
        if st.button("➕ Nueva Cinta", key="btn_new", use_container_width=True):
            st.session_state["cinta_f3"] = dict(_DEFAULT_F3)
            st.session_state["arq_chat"] = []
            _reset_draft()
            st.rerun()

        if st.session_state["show_crud"]:
            st.markdown("##### Flujos Guardados")
            cintas = _list_cintas()
            if not cintas:
                st.info("No hay flujos guardados.")
            else:
                for idx, c in enumerate(cintas):
                    nd = c.stem.replace("cinta_f3_","").replace("_"," ").title()
                    st.markdown(f"<div class='crud-item'><b>{nd}</b></div>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    if c1.button("📂", key=f"load_{idx}", help="Cargar"):
                        st.session_state["cinta_f3"] = _load_cinta(c)
                        st.session_state["arq_chat"] = st.session_state["cinta_f3"].get("arq_chat_history", [])
                        st.rerun()
                    if c2.button("✏️", key=f"edit_{idx}", help="Editar"):
                        st.session_state["edit_cinta_idx"] = idx
                        st.rerun()
                    if c3.button("🗑", key=f"del_{idx}", help="Eliminar"):
                        _delete_cinta(str(c))
                        if cf3.get("path") == str(c):
                            st.session_state["cinta_f3"] = dict(_DEFAULT_F3)
                        st.rerun()
                    if st.session_state.get("edit_cinta_idx") == idx:
                        _render_edit_inline(c, idx)

def _render_edit_inline(cinta_path: Path, idx: int):
    data = _load_cinta(cinta_path)
    with st.form(key=f"frm_edit_{idx}"):
        st.markdown("**Editar metadatos**")
        nn = st.text_input("Nombre", value=data.get("nombre",""))
        nd = st.text_input("Descripción", value=data.get("descripcion",""))
        ok, can = st.columns(2)
        sv = ok.form_submit_button("💾 Guardar")
        cx = can.form_submit_button("✖")
    if sv and nn.strip():
        np = _rename_cinta(str(cinta_path), nn.strip(), nd.strip())
        cf3 = st.session_state["cinta_f3"]
        if cf3.get("path") == str(cinta_path):
            cf3.update({"nombre": nn.strip(), "descripcion": nd.strip(), "path": np})
        st.session_state["edit_cinta_idx"] = None
        st.rerun()
    if cx:
        st.session_state["edit_cinta_idx"] = None
        st.rerun()

# =============================================================================
# PILAR 2 — CONSTRUCTOR MIXTO
# =============================================================================

def render_arquitecto_builder():
    cf3 = st.session_state["cinta_f3"]
    st.subheader("🏗️ Constructor de Cinta Agéntica")

    # ── Metadatos del flujo ──────────────────────────────────────────────
    mc1, mc2 = st.columns([2,1])
    with mc1:
        cf3["nombre"] = st.text_input("Nombre de la cinta", value=cf3.get("nombre",""),
            placeholder="Ej: Costeo ABC Semestre 2026-I")
    with mc2:
        cf3["descripcion"] = st.text_input("Descripción", value=cf3.get("descripcion",""),
            placeholder="Objetivo del flujo…")

    st.markdown("---")

    # ── Layout: Formulario izquierda | Arquitecto derecha ────────────────
    col_form, col_arq = st.columns([1.25, 1])

    # ── COLUMNA IZQUIERDA: FORMULARIO MANUAL ─────────────────────────────
    with col_form:
        st.markdown("##### ➕ Definir Nueva Etapa")

        # Versión actual del formulario — cambia al limpiar (patrón anti-StreamlitAPIException)
        v = st.session_state.get("_nf_version", 0)

        # Campos básicos
        cc1, cc2 = st.columns(2)
        with cc1:
            st.text_input("Nombre de la etapa *", key=f"_nf_nombre_{v}",
                          placeholder="Ej: Selección de Asignaturas")
        with cc2:
            st.text_input("Nombre del Agente IA", key=f"_nf_nombre_agente_{v}",
                          placeholder="Ej: Agente Selector Académico")

        st.text_input("Descripción de la etapa", key=f"_nf_desc_{v}",
                      placeholder="¿Qué hace esta etapa?")

        tipo_et = st.radio("Tipo de etapa", ["agente","hitl"], key=f"_nf_tipo_{v}",
                           format_func=lambda x: "🤖 Agente IA Autónomo" if x=="agente" else "🙋 HITL (Humano en el Loop)",
                           horizontal=True)

        st.text_area("System Prompt del agente", key=f"_nf_sp_{v}", height=80,
                     placeholder="Ej: Eres un experto en costear asignaturas universitarias…")

        st.text_area("Instrucciones adicionales para la pestaña", key=f"_nf_instrucciones_{v}", height=60,
                     placeholder="Ej: Mostrar tabla de resultados y gráfica de torta al ejecutar.")

        # Selector de plantilla
        templates = _list_templates()
        st.selectbox("Plantilla de interfaz (FLUJO_3_FIS/)", templates,
                     index=0, key=f"_nf_plantilla_{v}")

        # ── Campos HITL (solo si tipo == hitl) ──────────────────────────
        if tipo_et == "hitl":
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("**⚙️ Configuración HITL**")
            st.text_input("Pregunta de validación", key=f"_nf_pregunta_{v}",
                          placeholder="¿Confirma los valores registrados?")
            tipo_resp = st.radio("Tipo de respuesta", ["si_no","opcion_unica"], key=f"_nf_tipo_resp_{v}",
                                 format_func=lambda x: "✅/❌ Sí / No" if x=="si_no" else "☑ Opción única (múltiple respuesta)",
                                 horizontal=True)
            if tipo_resp == "opcion_unica":
                st.caption("Define hasta 5 opciones (deja vacío lo que no uses):")
                oc1, oc2 = st.columns(2)
                with oc1:
                    st.text_input("Opción 1", key=f"_nf_opt0_{v}", placeholder="Ej: Aprobado")
                    st.text_input("Opción 2", key=f"_nf_opt1_{v}", placeholder="Ej: Aprobado con observaciones")
                    st.text_input("Opción 3", key=f"_nf_opt2_{v}", placeholder="Ej: Rechazado")
                with oc2:
                    st.text_input("Opción 4", key=f"_nf_opt3_{v}", placeholder="(opcional)")
                    st.text_input("Opción 5", key=f"_nf_opt4_{v}", placeholder="(opcional)")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Valores por defecto para campos HITL no renderizados en este tipo
            tipo_resp = "si_no"

        # ── Botón Agregar ────────────────────────────────────────────────
        if st.button("➕ Agregar Etapa al Flujo", type="primary", use_container_width=True):
            # Leer todos los valores usando las keys versionadas (v ya fijo para este run)
            nombre_v    = st.session_state.get(f"_nf_nombre_{v}",           "").strip()
            agente_v    = st.session_state.get(f"_nf_nombre_agente_{v}",    "").strip()
            desc_v      = st.session_state.get(f"_nf_desc_{v}",             "").strip()
            tipo_v      = st.session_state.get(f"_nf_tipo_{v}",             "agente")
            sp_v        = st.session_state.get(f"_nf_sp_{v}",               "").strip()
            inst_v      = st.session_state.get(f"_nf_instrucciones_{v}",    "").strip()
            tpl_v_val   = st.session_state.get(f"_nf_plantilla_{v}",        "— ninguna —")
            pregunta_v  = st.session_state.get(f"_nf_pregunta_{v}",         "").strip()
            tipo_resp_v = st.session_state.get(f"_nf_tipo_resp_{v}",        "si_no")

            if not nombre_v:
                st.warning("⚠️ El nombre de la etapa es obligatorio.")
            else:
                idx_nuevo = len(cf3["etapas"]) + 1
                opciones_v = []
                if tipo_v == "hitl" and tipo_resp_v == "opcion_unica":
                    opciones_v = [
                        st.session_state.get(f"_nf_opt{i}_{v}", "").strip()
                        for i in range(5)
                        if st.session_state.get(f"_nf_opt{i}_{v}", "").strip()
                    ]
                arq_ctx = st.session_state.get("arq_chat", [])[-6:]
                nueva = {
                    "id":                        f"etapa_{idx_nuevo:03d}",
                    "nombre":                    nombre_v,
                    "nombre_agente":             agente_v or nombre_v,
                    "descripcion":               desc_v,
                    "tipo":                      tipo_v,
                    "system_prompt":             sp_v,
                    "instrucciones_adicionales": inst_v,
                    "plantilla_archivo":         (tpl_v_val if tpl_v_val != "— ninguna —" else None),
                    "pregunta":                  pregunta_v,
                    "tipo_respuesta":            tipo_resp_v,
                    "opciones":                  opciones_v,
                    "arq_context":               arq_ctx,
                    "estado":                    "pendiente",
                    "resultado":                 None,
                    "respuesta_hitl":            None,
                    "comentarios_hitl":          "",
                    "ts_completado":             None,
                    "chat_history":              [],
                    "artefacto_path":            None,
                }
                cf3["etapas"].append(nueva)
                if cf3.get("nombre"):
                    _save_cinta(cf3)
                # Limpiar formulario: solo incrementa el contador, nunca toca keys de widgets
                _reset_draft()
                st.rerun()

        # ── Lista de etapas ──────────────────────────────────────────────
        st.markdown(f"##### 📋 Etapas creadas ({len(cf3.get('etapas',[]))})")
        for i, et in enumerate(cf3.get("etapas",[])):
            tipo_lbl   = "🤖 Agente IA" if et["tipo"]=="agente" else "🙋 HITL"
            tipo_class = "etapa-agente" if et["tipo"]=="agente" else "etapa-hitl"
            sp_prev    = et.get("system_prompt","")[:55]
            tpl_v      = et.get("plantilla_archivo") or "—"
            col_c, col_d = st.columns([11,1])
            with col_c:
                st.markdown(
                    f"<div class='etapa-card'>"
                    f"<span class='badge'>{i+1}</span>"
                    f"<b>{et['nombre']}</b> <small style='color:#aaa'>({et.get('nombre_agente','')[:25]})</small>"
                    f"<span class='tipo-tag {tipo_class}'>{tipo_lbl}</span>"
                    f"<br><small style='color:#aaa'>Plantilla: <code>{tpl_v}</code> | "
                    f"{sp_prev}{'…' if sp_prev else ''}</small>"
                    f"</div>", unsafe_allow_html=True)
            with col_d:
                if st.button("🗑", key=f"del_et_{i}"):
                    cf3["etapas"].pop(i)
                    if cf3.get("nombre"): _save_cinta(cf3)
                    st.rerun()

        st.markdown("---")

        # ── Bloquear y ejecutar ──────────────────────────────────────────
        if cf3.get("etapas"):
            if not cf3.get("nombre","").strip():
                st.warning("⚠️ Asigna un nombre al flujo.")
            else:
                if st.button("💾 Bloquear y pasar a Ejecución", type="primary", use_container_width=True):
                    cf3["guardada"] = True
                    ruta = _save_cinta(cf3)
                    st.success(f"✅ Cinta guardada: `{ruta}`")
                    time.sleep(0.5)
                    st.rerun()

    # ── COLUMNA DERECHA: CHATBOT ARQUITECTO ──────────────────────────────
    with col_arq:
        st.markdown("##### 🤖 Asistente Arquitecto")
        st.caption("Consulta sugerencias de system prompt, tipo, plantilla UI, etc. El contexto se guardará en el JSON de cada etapa al agregarla.")

        arq_chat = st.session_state["arq_chat"]

        # Construir HTML del historial
        chat_html = ""
        for msg in arq_chat:
            if msg["role"] == "user":
                chat_html += f"<div class='arq-user'>👤 {msg['content']}</div>"
            else:
                txt = msg["content"].replace("\n", "<br>")
                # Negrita básica
                import re
                txt = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", txt)
                chat_html += f"<div class='arq-bot'>🏗️ {txt}</div>"
        if not chat_html:
            chat_html = "<div style='color:#546e7a;text-align:center;padding:30px;font-size:.86em;'>El Arquitecto está listo.<br>Descríbele una etapa para obtener sugerencias.</div>"

        st.markdown(f"<div class='arq-box'>{chat_html}</div>", unsafe_allow_html=True)

        arq_inp = st.text_input("Mensaje", placeholder="Ej: ¿Qué system prompt uso para validar costos HITL?",
                                key="arq_inp_txt", label_visibility="collapsed")
        if st.button("➤ Enviar", key="btn_arq_send", use_container_width=True):
            if arq_inp.strip():
                arq_chat.append({"role":"user","content":arq_inp.strip()})
                etapa_draft = {
                    "nombre": st.session_state.get("_nf_nombre",""),
                    "tipo": st.session_state.get("_nf_tipo","agente"),
                }
                with st.spinner("Arquitecto pensando..."):
                    time.sleep(0.35)
                    resp = _arq_responder(arq_inp.strip(), etapa_draft)
                arq_chat.append({"role":"assistant","content":resp})
                st.rerun()

        if arq_chat:
            if st.button("🗑 Limpiar Arquitecto", key="btn_arq_clear", use_container_width=True):
                st.session_state["arq_chat"] = []
                st.rerun()

        # Preview JSON de la última etapa agregada
        if cf3.get("etapas"):
            with st.expander("📄 JSON última etapa guardada", expanded=False):
                last = {k: v for k, v in cf3["etapas"][-1].items() if k != "chat_history"}
                st.markdown(f"<div class='json-box'>{json.dumps(last, ensure_ascii=False, indent=2)}</div>",
                            unsafe_allow_html=True)

# =============================================================================
# PILAR 3 — PESTAÑAS DE EJECUCIÓN DINÁMICA
# =============================================================================

def _is_desbloqueada(etapas: list, idx: int) -> bool:
    if idx == 0: return True
    return etapas[idx-1].get("estado") == "completado"

def _mock_agente_resp(etapa: dict, user_msg: str) -> str:
    sp = etapa.get("system_prompt","")[:50]
    agente = etapa.get("nombre_agente", etapa.get("nombre",""))
    return random.choice([
        f"[{agente}] Operando bajo: *'{sp}...'*. Insumo recibido: '{user_msg}'. Procesando.",
        f"[{agente}] Análisis completado sobre '{user_msg}'. Los parámetros son consistentes.",
        f"[{agente}] Validación concluida. Sistema listo para ejecutar esta etapa.",
        f"[{agente}] Registros FIS sincronizados. El artefacto intermedio está disponible.",
    ])

def _complete_hitl(cf3: dict, t_idx: int, respuesta: str):
    comentario = st.session_state.get(f"hitl_com_{t_idx}", "")
    cf3["etapas"][t_idx].update({
        "estado": "completado",
        "respuesta_hitl": respuesta,
        "comentarios_hitl": comentario,
        "resultado": f"HITL → {respuesta}" + (f" | {comentario}" if comentario else ""),
        "ts_completado": datetime.now().isoformat()
    })
    _save_cinta(cf3)
    st.rerun()

def render_ejecucion_tabs():
    cf3    = st.session_state["cinta_f3"]
    etapas = cf3.get("etapas", [])
    n_et   = len(etapas)
    n_ok   = sum(1 for e in etapas if e.get("estado")=="completado")

    pc, sc, ec = st.columns([3,1,1])
    with pc:
        st.progress(n_ok/n_et if n_et else 0,
                    text=f"{n_ok}/{n_et} etapas — **{cf3['nombre']}**")
    with sc:
        st.info("✅ Finalizado" if n_ok==n_et else "⏳ En progreso")
    with ec:
        if st.button("✏️ Editar Flujo", key="btn_back"):
            cf3["guardada"] = False
            st.rerun()

    st.markdown("---")
    if n_et == 0:
        st.warning("No hay etapas.")
        return

    labels = [
        f"{'✅' if e.get('estado')=='completado' else ('🔵' if _is_desbloqueada(etapas,i) else '🔒')} "
        f"{i+1}. {e['nombre']}"
        for i, e in enumerate(etapas)
    ]
    for tab, etapa, t_idx in zip(st.tabs(labels), etapas, range(n_et)):
        with tab:
            _render_tab_etapa(cf3, etapas, etapa, t_idx)


def _render_tab_etapa(cf3, etapas, etapa, t_idx):
    desbloqueada = _is_desbloqueada(etapas, t_idx)
    estado = etapa.get("estado","pendiente")
    tipo   = etapa.get("tipo","agente")
    agente = etapa.get("nombre_agente", etapa.get("nombre",""))

    tipo_lbl    = f"🤖 {agente}" if tipo=="agente" else f"🙋 HITL — {agente}"
    badge_class = ("estado-completado" if estado=="completado"
                   else "estado-pendiente" if desbloqueada else "estado-bloqueado")
    badge_text  = ("✅ Completado" if estado=="completado"
                   else "🔵 Activo" if desbloqueada else "🔒 Bloqueado")
    sp_prev = etapa.get("system_prompt","")[:90]
    add_ins = etapa.get("instrucciones_adicionales","")

    st.markdown(
        f"<div class='tab-header'><b>{tipo_lbl}</b> &nbsp;"
        f"<span class='estado-badge {badge_class}'>{badge_text}</span>"
        f"<br><small style='color:#aaa'>Prompt: {sp_prev}{'…' if sp_prev else ''}</small>"
        + (f"<br><small style='color:#6a9fb5'>Instrucciones: {add_ins}</small>" if add_ins else "")
        + "</div>", unsafe_allow_html=True)

    if not desbloqueada:
        prev = etapas[t_idx-1]["nombre"] if t_idx>0 else ""
        st.warning(f"🔒 Completa **«{prev}»** primero.")
        return

    if estado == "completado":
        resp_h = etapa.get("respuesta_hitl")
        com_h  = etapa.get("comentarios_hitl","")
        st.success(f"✅ {etapa.get('resultado','N/A')}")
        if resp_h:
            st.info(f"Respuesta HITL: **{resp_h}**" + (f" | Comentario: _{com_h}_" if com_h else ""))
        st.caption(f"Completado: {etapa.get('ts_completado','')}")
        art_p = etapa.get("artefacto_path")
        if art_p and os.path.exists(art_p):
            with st.expander("🎨 Ver Artefacto UI", expanded=False):
                with open(art_p, encoding="utf-8") as fh:
                    components.html(fh.read(), height=320, scrolling=True)
        if st.button("↩ Reabrir etapa", key=f"reopen_{t_idx}"):
            for j in range(t_idx, len(etapas)):
                cf3["etapas"][j]["estado"] = "pendiente"
                cf3["etapas"][j]["respuesta_hitl"] = None
                cf3["etapas"][j]["comentarios_hitl"] = ""
            _save_cinta(cf3)
            st.rerun()
        return

    # ── Chat | Ejecutar ──────────────────────────────────────────────────
    col_chat, col_right = st.columns([1.5,1])
    chat_h = etapa.setdefault("chat_history",[])
    n_inter = sum(1 for m in chat_h if m["role"]=="user")

    with col_chat:
        st.markdown(f"**💬 Chat — `{agente}`**")
        with st.container(height=260, border=True):
            if not chat_h:
                st.caption("Interactúa con el agente al menos una vez antes de ejecutar.")
            for msg in chat_h:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        agent_inp = st.chat_input(f"Escribe a {agente}…", key=f"chat_in_{t_idx}")
        if agent_inp:
            chat_h.append({"role":"user","content":agent_inp})
            with st.spinner("Procesando..."):
                time.sleep(0.35)
                chat_h.append({"role":"assistant","content":_mock_agente_resp(etapa, agent_inp)})
            _save_cinta(cf3)
            st.rerun()

    with col_right:
        can_exec = n_inter > 0
        st.metric("Interacciones con agente", n_inter, help="Mínimo 1 requerida")
        if not can_exec:
            st.caption("⚠️ Interactúa con el agente primero.")

        # ── Disparador según tipo ────────────────────────────────────────
        if tipo == "agente":
            if st.button("▶ Ejecutar Agente", disabled=not can_exec,
                         key=f"exec_{t_idx}", type="primary", use_container_width=True):
                with st.spinner("Ejecutando..."):
                    time.sleep(0.8)
                    cf3["etapas"][t_idx].update({
                        "estado": "completado",
                        "resultado": "Procesamiento autónomo exitoso. Artefacto JSON generado.",
                        "ts_completado": datetime.now().isoformat()
                    })
                _save_cinta(cf3)
                st.rerun()
        else:
            # HITL
            st.markdown("---")
            pregunta = etapa.get("pregunta","¿Confirma la acción?")
            tipo_resp = etapa.get("tipo_respuesta","si_no")
            st.markdown(f"**❓ {pregunta}**")

            if tipo_resp == "si_no":
                cs, cn = st.columns(2)
                if cs.button("✅ Sí", disabled=not can_exec, key=f"hitl_si_{t_idx}", use_container_width=True):
                    _complete_hitl(cf3, t_idx, "Sí")
                if cn.button("❌ No", disabled=not can_exec, key=f"hitl_no_{t_idx}", use_container_width=True):
                    _complete_hitl(cf3, t_idx, "No")
            else:
                opciones = [o for o in etapa.get("opciones",[]) if o]
                if opciones:
                    sel_op = st.radio("Seleccione:", opciones, key=f"hitl_sel_{t_idx}",
                                      disabled=not can_exec)
                    if st.button("✅ Confirmar Selección", disabled=not can_exec,
                                 key=f"hitl_conf_{t_idx}", type="primary", use_container_width=True):
                        _complete_hitl(cf3, t_idx, sel_op)
                else:
                    st.warning("No hay opciones definidas para esta etapa HITL.")

            st.text_area("Comentarios", key=f"hitl_com_{t_idx}", height=70,
                         disabled=not can_exec,
                         placeholder="Observaciones sobre la decisión tomada…")

        # ── Generador de Artefacto HTML/CSS/JS ──────────────────────────
        st.markdown("---")
        st.markdown("**🎨 Artefacto UI dinámico**")
        art_desc = st.text_area("Describe el HTML/CSS/JS que quieres",
                                placeholder="Ej: Dashboard con KPIs y gráfica de barras de costos.",
                                height=72, key=f"art_desc_{t_idx}", label_visibility="collapsed")
        cg, cv = st.columns(2)
        if cg.button("⚙️ Generar", key=f"btn_gen_{t_idx}", use_container_width=True):
            if art_desc.strip():
                with st.spinner("Generando..."):
                    time.sleep(0.4)
                    html_c = _generar_html_artefacto(art_desc.strip(), etapa["nombre"])
                    sp     = _save_artefacto(cf3, etapa["id"], html_c)
                cf3["etapas"][t_idx]["artefacto_path"] = sp
                _save_cinta(cf3)
                st.success(f"✅ `{Path(sp).name}`")
                st.rerun()
            else:
                st.warning("Describe primero el artefacto.")

        art_p = etapa.get("artefacto_path")
        btn_ver_dis = not (art_p and os.path.exists(art_p))
        if cv.button("👁 Ver", key=f"btn_ver_{t_idx}", use_container_width=True, disabled=btn_ver_dis):
            key_show = f"show_art_{t_idx}"
            st.session_state[key_show] = not st.session_state.get(key_show, False)
            st.rerun()

        if art_p and os.path.exists(art_p) and st.session_state.get(f"show_art_{t_idx}"):
            with open(art_p, encoding="utf-8") as fh:
                components.html(fh.read(), height=320, scrolling=True)

    # ── Plantilla FLUJO_3_FIS (ancho completo) ───────────────────────────
    plantilla = etapa.get("plantilla_archivo")
    if plantilla:
        st.markdown("---")
        st.markdown(f"**📐 Plantilla: `{plantilla}`**")
        mod = _load_template(plantilla)
        if mod and hasattr(mod, "render"):
            mod.render(etapa, cf3)
        elif mod:
            st.warning(f"La plantilla `{plantilla}` no tiene función `render(etapa, cf3)`.")

# =============================================================================
# MAIN
# =============================================================================

def main():
    _init_state()
    st.markdown("""<div class="header-box">
        <h2>🧬 Flujo 3 — Cinta Agéntica Dinámica (Meta-Agentes)</h2>
    </div>""", unsafe_allow_html=True)
    render_sidebar_crud()
    cf3 = st.session_state["cinta_f3"]
    if not cf3.get("guardada"):
        render_arquitecto_builder()
    else:
        render_ejecucion_tabs()
    st.markdown("---")
    st.markdown("""<div class="telemetria">
    🧬 <b>FIS SIMBIOMEMÉSICO ACTIVO</b> | Cinta Inmutable Auto-Guardada | URosario v8.1
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
