"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: pages/05_fabrica_agentes.py — Fábrica y Creador de Skills
=============================================================================
"""

import streamlit as st
import os, sys, json, time
from datetime import datetime

st.set_page_config(page_title="Fábrica de Agentes & Skills | Portal FIS", layout="wide", page_icon="🛠️")

# =============================================================================
# VARIABLES Y RUTAS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, ".agents")
SKILLS_DIR = os.path.join(AGENTS_DIR, "skills")
CUSTOM_AGENTS_FILE = os.path.join(AGENTS_DIR, "agentes_custom.json")

# Aseguramos que existan los directorios
os.makedirs(SKILLS_DIR, exist_ok=True)
if not os.path.exists(CUSTOM_AGENTS_FILE):
    with open(CUSTOM_AGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

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
.result-box {
    background: #1e1e2e; border-left: 5px solid #3949ab;
    padding: 16px; border-radius: 6px; margin-top: 12px; color: #fff;
}
.agent-card {
    background: #1e1e2e; border: 1px solid #3949ab;
    padding: 14px; border-radius: 6px; margin-bottom: 8px; color: #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.agent-card h4 { color: #7986cb; margin-top: 0; }
.telemetria { background:#1e1e1e; color:#00FF41; padding:10px; border-radius:5px;
              font-family:monospace; font-size:0.82em; text-align:center; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #eee !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ENCABEZADO
# =============================================================================
st.markdown("""
<div class="header-box">
    <h2>🛠️ Fábrica de Agentes & Creador de Skills</h2>
</div>
""", unsafe_allow_html=True)
st.info("Permite crear dinámicamente nuevas habilidades (skills) y fabricar agentes que las consumen al vuelo.", icon="🧙")

# =============================================================================
# TABS PRINCIPALES
# =============================================================================
tab1, tab2 = st.tabs(["🧩 Creador de Skills", "🤖 Fábrica de Agentes"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: CREADOR DE SKILLS
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### 🧩 Crear nueva Skill")
    st.write("Genera una nueva skill en disco siguiendo la especificación del motor.")
    
    with st.form("skill_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            skill_name = st.text_input("Nombre de la Skill", placeholder="ej: auditor_financiero")
            skill_description = st.text_input("Descripción breve", placeholder="¿Para qué sirve esta skill?")
        with col2:
            skill_instructions = st.text_area("Instrucciones detalladas (Markdown)", height=150, 
                                              placeholder="Escribe el prompt o comportamiento detallado aquí...")
        
        btn_crear_skill = st.form_submit_button("Crear y Guardar Skill", type="primary")
        
        if btn_crear_skill:
            if not skill_name.strip() or not skill_instructions.strip():
                st.error("El nombre y las instrucciones son obligatorios.")
            else:
                s_name_clean = skill_name.strip().replace(" ", "_")
                filename = f"skill:{s_name_clean}.md"
                # Formato Markdown + Frontmatter
                skill_content = f"""---
name: {s_name_clean}
description: {skill_description.strip()}
created: {datetime.now().isoformat()}
---

# {s_name_clean}

{skill_instructions.strip()}
"""
                filepath = os.path.join(SKILLS_DIR, filename)
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(skill_content)
                    st.success(f"✅ Skill exitosamente guardada en: `{filepath}`")
                except Exception as e:
                    st.error(f"Error al guardar la skill: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: FÁBRICA DE AGENTES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🤖 Creador y Registro de Agentes IA")
    colA, colB = st.columns([1.5, 1])
    
    with colA:
        st.write("Asocia las skills creadas a un nuevo perfil de agente.")
        
        # Leer skills disponibles
        available_skills = []
        if os.path.exists(SKILLS_DIR):
            available_skills = [f for f in os.listdir(SKILLS_DIR) if f.endswith(".md")]
            
        with st.form("agent_form"):
            agente_name = st.text_input("Nombre del Agente", placeholder="Ej: Inspector XYZ")
            agente_role = st.selectbox("Rol del Agente", ["Auditor", "Especialista ABC", "Financiero", "Validador", "Explorador"])
            
            if available_skills:
                agente_skill = st.selectbox("Asociar Skill Principal", available_skills)
            else:
                agente_skill = st.selectbox("Asociar Skill Principal", ["Ninguna - ¡Crea una skill primero!"])
                
            agente_llm = st.selectbox("Modelo LLM preferido", ["gemini-2.5-flash", "gemini-2.5-pro", "claude-3-haiku"])
            
            btn_crear_agente = st.form_submit_button("Registrar Agente", type="primary")
            
            if btn_crear_agente:
                if not agente_name.strip() or not available_skills:
                    st.error("Debes dar un nombre al agente y asegurarte de tener al menos una skill creada.")
                else:
                    try:
                        with open(CUSTOM_AGENTS_FILE, "r", encoding="utf-8") as f:
                            agents_db = json.load(f)
                    except:
                        agents_db = []
                        
                    new_agent = {
                        "id": f"agent_{int(time.time())}",
                        "name": agente_name.strip(),
                        "role": agente_role,
                        "skill_file": agente_skill,
                        "llm": agente_llm,
                        "created_at": datetime.now().isoformat()
                    }
                    agents_db.append(new_agent)
                    
                    with open(CUSTOM_AGENTS_FILE, "w", encoding="utf-8") as f:
                        json.dump(agents_db, f, indent=4)
                        
                    st.success(f"✅ ¡Agente **{agente_name.strip()}** registrado y equipado con `{agente_skill}`!")

    with colB:
        st.markdown("#### 📂 Agentes Registrados")
        try:
            with open(CUSTOM_AGENTS_FILE, "r", encoding="utf-8") as f:
                agents_db = json.load(f)
            
            if not agents_db:
                st.info("Aún no hay agentes creados.")
            else:
                for ag in reversed(agents_db[-5:]): # Mostrar ultimos 5
                    st.markdown(f"""
                    <div class='agent-card'>
                        <h4>🥷 {ag['name']}</h4>
                        <b>Rol:</b> {ag['role']}<br>
                        <b>Skill:</b> {ag['skill_file']}<br>
                        <small>Motor: {ag['llm']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error("No se pudo cargar el registro de agentes.")

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding-bottom:12px;border-bottom:2px solid #3949ab;margin-bottom:16px;">
        <h2 style="margin:0;color:#7986cb;">🏛️ URosario</h2>
        <span style="font-size:11px;color:#aaa;">Portal FIS v8.1 · Menú</span>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit page_link paths are ALWAYS relative to the entrypoint dir (PORTAL_FIS/)
    # From pages/ subdir: entrypoint = "portal_fis.py", other pages = "pages/XX.py"
    st.page_link("portal_fis.py",              label="🏠  Inicio",              icon="🏠")
    st.page_link("pages/00_comparacion.py",    label="📊  Comparación",         icon="📊")
    st.page_link("pages/01_flujo_humano.py",   label="🙋  Flujo 1: Humano",     icon="1️⃣")
    st.page_link("pages/02_flujo_agentes_ia.py", label="🤖  Flujo 2: Agentes IA", icon="2️⃣")
    st.page_link("pages/03_flujo_fis.py",      label="🧬  Flujo 3: FIS",        icon="3️⃣")
    st.page_link("pages/04_simulador_fis.py",  label="📊  Simulador Diferencial", icon="📊")
    st.page_link("pages/05_fabrica_agentes.py", label="🛠️  Fábrica & Skills",  icon="🛠️")
    st.markdown("---")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""<div class="telemetria">🛠️ <b>FÁBRICA DE AGENTES ACTIVA</b> | Engine: Local Skills | Simbiomémesis v8.1</div>""", unsafe_allow_html=True)
