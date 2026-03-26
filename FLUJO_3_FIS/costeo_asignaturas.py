"""
=============================================================================
FLUJO_3_FIS / costeo_asignaturas.py
Agente IA de Costeo ABC — Claude claude-opus-4-6 con streaming
=============================================================================

Arquitectura de ejecución:
  1. Motor FIS determinista (_calcular) → resultados matemáticos exactos
  2. Claude claude-opus-4-6 → reporte narrativo paso a paso, en streaming
  3. Persistencia → YYYYMMDD_NNN_COSTEO_ABC_UR.json con metadata completa

Métricas capturadas por ejecución:
  - Tokens de entrada (input_tokens)
  - Tokens de salida (output_tokens)
  - Tiempo total y tiempo parcial (cálculo FIS vs. llamada LLM)
  - Costo USD estimado
  - Confirmación de ejecución de costeo_asignaturas.py
=============================================================================
"""

import os
import sys
import json
import time
import streamlit as st
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE      = Path(__file__).resolve().parent
_DATOS_DIR = _HERE.parent / "DATOS"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _persistencia import guardar_nodo, recuperar_estado, listar_nodos

# ── SDK Anthropic ─────────────────────────────────────────────────────────────
try:
    import anthropic
    _SDK_OK = True
except ImportError:
    _SDK_OK = False

_MODEL      = "claude-opus-4-6"
_PRECIO_IN  = 5.0    # USD por millón de tokens de entrada
_PRECIO_OUT = 25.0   # USD por millón de tokens de salida

# =============================================================================
# SYSTEM PROMPT — Reglas del modelo de costeo ABC
# =============================================================================

_SYSTEM_PROMPT = """
Eres el **Agente FIS de Costeo ABC** de la Universidad del Rosario.
Tu rol es generar un reporte de auditoría completo, paso a paso, sobre el costeo
de asignaturas universitarias ejecutado por el Motor FIS.

══════════════════════════════════════════════════════════
MODELO DE COSTEO ABC — FÓRMULAS OFICIALES
══════════════════════════════════════════════════════════

VARIABLES DE ENTRADA:
  G  = Número de grupos por asignatura
  C  = Número de clases por semestre
  Np = Número de profesores por grupo
  H  = Horas por clase
  VH = Valor hora-profesor ($)
  m² = Metros cuadrados del salón
  Vm = Valor por m² por sesión ($)
  L  = Costo de licencias de software ($)
  Ne = Número de estudiantes por grupo

FÓRMULAS:
  Costo Docente     = G × C × Np × H × VH
  Costo Espacio     = G × C × m² × Vm
  Total Directos    = Costo Docente + Costo Espacio + L
  Costo Indirecto   = 50% × Total Directos       ← regla institucional fija
  Costo Total       = Total Directos + Costo Indirecto
  Costo/Sesión      = Costo Total / (G × C)
  Costo/Estudiante  = Costo Total / (G × Ne)

══════════════════════════════════════════════════════════
INSTRUCCIONES PARA EL REPORTE
══════════════════════════════════════════════════════════

Para cada asignatura:
  1. Muestra los parámetros aplicados
  2. Sustituye los valores en cada fórmula y verifica el resultado
  3. Muestra el costo unitario por sesión y por estudiante
  4. Señala si algún costo es inusualmente alto o bajo

Al final:
  5. Tabla resumen comparativa (si hay múltiples asignaturas)
  6. Totales globales y participación porcentual de cada rubro
  7. Conclusión analítica: eficiencia, drivers dominantes, recomendaciones

Usa formato Markdown. Sé preciso, auditable y claro.
""".strip()


# =============================================================================
# MOTOR MATEMÁTICO FIS — determinista, sin LLM
# =============================================================================

def _calcular(asignatura: str, p: dict) -> dict:
    """Modelo de costeo ABC (igual a Flujo 1 — Humano)."""
    ng  = p["num_grupos"]
    nc  = p["num_clases"]
    np_ = p["num_profesores"]
    hpc = p["horas_por_clase"]
    ne  = p["num_estudiantes"]
    vhp = p["valor_hora_prof"]
    m2  = p["metros_cuadrados"]
    vm2 = p["valor_m2"]
    lic = p["valor_licencias"]

    costo_doc = ng * nc * np_ * hpc * vhp
    costo_esp = ng * nc * m2 * vm2
    total_dir = costo_doc + costo_esp + lic
    costo_ind = 0.5 * total_dir
    costo_tot = total_dir + costo_ind
    sesiones  = ng * nc
    est_tot   = ne * ng

    return {
        "asignatura":            asignatura,
        "costo_docente":         round(costo_doc, 2),
        "costo_espacio_m2":      round(costo_esp, 2),
        "costo_licencias":       round(lic, 2),
        "total_directos":        round(total_dir, 2),
        "costo_indirecto_50pct": round(costo_ind, 2),
        "costo_total":           round(costo_tot, 2),
        "costo_por_sesion":      round(costo_tot / sesiones, 2) if sesiones else 0,
        "costo_por_estudiante":  round(costo_tot / est_tot,  2) if est_tot  else 0,
        "sesiones_totales":      sesiones,
        "estudiantes_totales":   est_tot,
    }


# =============================================================================
# AGENTE IA — genera el reporte narrativo con streaming
# =============================================================================

def _get_api_key() -> str | None:
    """Obtiene la API key de Anthropic desde varias fuentes."""
    # 1. Variable de entorno
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    # 2. Streamlit secrets (si está configurado)
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
        if key:
            return key
    except Exception:
        pass
    return None


def _construir_prompt_usuario(asignaturas: list, params: dict, resultados: list) -> str:
    """Construye el mensaje del usuario con todos los datos para el reporte."""
    p = params
    params_display = {
        "grupos_por_asignatura":    p.get("num_grupos"),
        "clases_por_semestre":      p.get("num_clases"),
        "profesores_por_grupo":     p.get("num_profesores"),
        "horas_por_clase":          p.get("horas_por_clase"),
        "estudiantes_por_grupo":    p.get("num_estudiantes"),
        "valor_hora_profesor_COP":  p.get("valor_hora_prof"),
        "metros_cuadrados_salon":   p.get("metros_cuadrados"),
        "valor_m2_por_sesion_COP":  p.get("valor_m2"),
        "valor_licencias_COP":      p.get("valor_licencias"),
        "tipo_salon":               p.get("tipo_salon"),
        "periodo_academico":        p.get("periodo"),
    }
    total_gral = sum(r["costo_total"] for r in resultados)

    return f"""
Genera el **Reporte Completo de Auditoría de Costeo ABC** para las siguientes asignaturas.

═══════════════════════════════════════════════════
DATOS DEL PERÍODO: {p.get('periodo', 'N/A')}
ASIGNATURAS ({len(asignaturas)} en total): {', '.join(asignaturas)}
═══════════════════════════════════════════════════

PARÁMETROS CONFIGURADOS:
{json.dumps(params_display, ensure_ascii=False, indent=2)}

RESULTADOS DEL MOTOR FIS costeo_asignaturas.py — _calcular():
{json.dumps(resultados, ensure_ascii=False, indent=2)}

TOTAL GLOBAL CALCULADO: ${total_gral:,.2f} COP

═══════════════════════════════════════════════════
ESTRUCTURA SOLICITADA DEL REPORTE:
1. Para CADA asignatura: sustitución de valores en las fórmulas, verificación
   del cálculo y costo unitario (sesión + estudiante).
2. Tabla comparativa multi-asignatura (si aplica).
3. Totales globales y participación % de cada rubro.
4. Análisis y conclusiones.
═══════════════════════════════════════════════════
""".strip()


def _ejecutar_agente_streaming(
    asignaturas: list,
    params: dict,
    resultados: list,
    etapa: dict,
    cf3: dict
) -> dict:
    """
    Ejecuta el agente Claude con streaming.
    Retorna dict con: reporte_texto, tokens_in, tokens_out, tiempo_llm,
    tiempo_calculo_fis, tiempo_total, costo_usd, guardado_en.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "API_KEY_NOT_SET"}

    cliente = anthropic.Anthropic(api_key=api_key)
    prompt  = _construir_prompt_usuario(asignaturas, params, resultados)

    # ── Placeholders de streaming ──────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"#### 📄 Reporte del Agente `{_MODEL}`")
    st.caption(f"Transmitiendo en tiempo real… ({len(asignaturas)} asignatura(s))")

    report_placeholder  = st.empty()
    thinking_expander   = st.expander("🧠 Razonamiento interno del agente (thinking)", expanded=False)
    thinking_placeholder = thinking_expander.empty()

    report_text  = ""
    thinking_text = ""
    tokens_in    = 0
    tokens_out   = 0

    t_llm_inicio = time.time()

    try:
        with cliente.messages.stream(
            model=_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for event in stream:
                # Deltas de thinking
                if (event.type == "content_block_delta"
                        and event.delta.type == "thinking_delta"):
                    thinking_text += event.delta.thinking
                    thinking_placeholder.markdown(
                        f"```\n{thinking_text[-2000:]}\n```"
                    )
                # Deltas de texto (reporte)
                elif (event.type == "content_block_delta"
                        and event.delta.type == "text_delta"):
                    report_text += event.delta.text
                    report_placeholder.markdown(report_text + "\n\n▌")

            # Mensaje final con métricas de tokens
            msg_final  = stream.get_final_message()
            tokens_in  = msg_final.usage.input_tokens
            tokens_out = msg_final.usage.output_tokens

    except anthropic.AuthenticationError:
        return {"error": "ANTHROPIC_API_KEY inválida o sin permisos."}
    except anthropic.RateLimitError:
        return {"error": "Rate limit alcanzado. Espera un momento y vuelve a intentar."}
    except Exception as e:
        return {"error": str(e)}

    t_llm_total = time.time() - t_llm_inicio

    # Quitar cursor parpadeante al finalizar
    report_placeholder.markdown(report_text)

    # Costo estimado
    costo_usd = (tokens_in * _PRECIO_IN + tokens_out * _PRECIO_OUT) / 1_000_000

    return {
        "reporte_texto":              report_text,
        "tokens_input":               tokens_in,
        "tokens_output":              tokens_out,
        "tiempo_llm_segundos":        round(t_llm_total, 3),
        "costo_usd_estimado":         round(costo_usd, 6),
        "ejecuto_costeo_asignaturas_py": True,
        "funcion_ejecutada":          "_calcular() en FLUJO_3_FIS/costeo_asignaturas.py",
        "pudo_imprimir_paso_a_paso":  True,
    }


# =============================================================================
# RENDER PRINCIPAL
# =============================================================================

def render(etapa: dict, cf3: dict):
    st.markdown("#### 💰 Agente IA de Costeo ABC — URosario")

    # ── Auto-recuperación de dependencias ────────────────────────────────
    sel    = recuperar_estado("fis_seleccion", "SELECCION_FIS")    or {}
    params = recuperar_estado("fis_params",    "PARAMS_FIS")       or {}

    asignaturas = sel.get("asignaturas", [])

    if not asignaturas:
        st.warning(
            "⚠️ Sin asignaturas. Completa una etapa con **`selector_jerarquico.py`**.",
            icon="🎓"
        )
        _render_historial_costeos()
        return

    if not params:
        st.warning(
            "⚠️ Sin parámetros. Completa una etapa con **`parametros_costeo.py`**.",
            icon="⚙️"
        )
        _render_historial_costeos()
        return

    # ── Indicadores de contexto ───────────────────────────────────────────
    ci1, ci2 = st.columns(2)
    ci1.success(
        f"📌 **Selección activa:** {sel.get('etapa_origen','')} — {len(asignaturas)} asig.",
        icon="🎓"
    )
    ci2.info(
        f"⚙️ **Params:** {params.get('num_grupos','?')}g × "
        f"{params.get('num_clases','?')}c | {params.get('periodo','?')}",
        icon="📐"
    )

    # ── Motor FIS (cálculo determinista) ─────────────────────────────────
    t_fis_inicio = time.time()
    resultados   = [_calcular(a, params) for a in asignaturas]
    t_fis        = round(time.time() - t_fis_inicio, 4)

    total_gral  = sum(r["costo_total"] for r in resultados)
    est_unicos  = resultados[0]["estudiantes_totales"] if resultados else 1
    cu_global   = total_gral / max(len(asignaturas) * est_unicos, 1)

    # ── Métricas rápidas ──────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Asignaturas",         len(asignaturas))
    m2.metric("Costo Total Global",  f"${total_gral:,.0f}")
    m3.metric("Promedio/Asig.",      f"${total_gral/max(len(asignaturas),1):,.0f}")
    m4.metric("⏱ Motor FIS",         f"{t_fis*1000:.1f}ms")

    # ── Tabla de resultados (motor FIS) ───────────────────────────────────
    st.markdown("---")
    st.markdown("**📋 Resultados del Motor FIS**")
    cols_d = [
        "asignatura","costo_docente","costo_espacio_m2",
        "costo_licencias","total_directos","costo_indirecto_50pct",
        "costo_total","costo_por_estudiante"
    ]
    try:
        import pandas as pd
        df = pd.DataFrame(resultados)[cols_d].copy()
        cols_num = [c for c in cols_d if c != "asignatura"]
        for col in cols_num:
            df[col] = df[col].apply(lambda x: f"${x:,.0f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    except ImportError:
        for r in resultados:
            st.code(" | ".join(str(r.get(c,"")) for c in cols_d))

    # ── Resumen por rubro ─────────────────────────────────────────────────
    rubros = {
        "Costo Docente":          sum(r["costo_docente"]          for r in resultados),
        "Costo Espacio":          sum(r["costo_espacio_m2"]        for r in resultados),
        "Costo Licencias":        sum(r["costo_licencias"]         for r in resultados),
        "Costo Indirecto (50%)":  sum(r["costo_indirecto_50pct"]   for r in resultados),
    }
    r1, r2, r3, r4 = st.columns(4)
    for col_st, (rubro, valor) in zip([r1, r2, r3, r4], rubros.items()):
        pct = valor / total_gral * 100 if total_gral else 0
        col_st.metric(rubro, f"${valor:,.0f}", f"{pct:.1f}%")

    # ── Guardar siempre en sesión ─────────────────────────────────────────
    resultado_base = {
        "tipo":               "COSTEO_ABC_UR",
        "cinta":              cf3.get("nombre",""),
        "etapa":              etapa.get("nombre",""),
        "etapa_id":           etapa.get("id",""),
        "periodo":            params.get("periodo",""),
        "n_asignaturas":      len(asignaturas),
        "total_general":      total_gral,
        "costo_promedio_asig":total_gral / max(len(asignaturas), 1),
        "costo_unitario_est": cu_global,
        "rubros":             rubros,
        "seleccion": {
            "facultades":  sel.get("facultades",[]),
            "programas":   sel.get("programas",[]),
            "asignaturas": asignaturas,
        },
        "parametros":  {k: v for k, v in params.items() if k != "tipo"},
        "filas":       resultados,
        "tiempo_motor_fis_segundos": t_fis,
    }
    st.session_state["fis_costeo_resultados"] = resultado_base

    # ── BOTÓN: Ejecutar Agente IA ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 Reporte Narrativo del Agente IA")

    # Verificar disponibilidad del SDK y API key
    if not _SDK_OK:
        st.error("❌ Paquete `anthropic` no está instalado. Ejecuta: `pip install anthropic`")
        _auto_guardar(resultado_base, cf3, etapa)
        return

    api_key = _get_api_key()
    if not api_key:
        st.warning(
            "⚠️ `ANTHROPIC_API_KEY` no está configurada. "
            "Configúrala como variable de entorno para habilitar el agente IA.",
            icon="🔑"
        )
        with st.expander("Configurar API Key temporalmente (solo esta sesión)"):
            tmp_key = st.text_input("API Key de Anthropic", type="password",
                                    key=f"tmp_key_{etapa.get('id','x')}")
            if tmp_key.strip():
                os.environ["ANTHROPIC_API_KEY"] = tmp_key.strip()
                st.success("✅ API Key cargada en sesión. Haz clic en 'Ejecutar Agente' de nuevo.")
        _auto_guardar(resultado_base, cf3, etapa)
        return

    eid_btn = etapa.get("id","x")
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        ejecutar = st.button(
            "▶ Ejecutar Agente de Costeo",
            key=f"btn_agente_{eid_btn}",
            type="primary",
            use_container_width=True
        )
    with col_info:
        st.caption(
            f"Modelo: `{_MODEL}` | Thinking: adaptive | Streaming: activado\n\n"
            f"Generará un reporte detallado paso a paso para "
            f"**{len(asignaturas)} asignatura(s)**."
        )

    # Mostrar último reporte guardado si existe
    clave_reporte = f"reporte_agente_{eid_btn}"
    reporte_guardado = st.session_state.get(clave_reporte)
    if reporte_guardado and not ejecutar:
        _mostrar_metricas(reporte_guardado)
        _render_historial_costeos()
        _auto_guardar(resultado_base, cf3, etapa)
        return

    if not ejecutar:
        st.info("Haz clic en **▶ Ejecutar Agente de Costeo** para generar el reporte narrativo.")
        _render_historial_costeos()
        _auto_guardar(resultado_base, cf3, etapa)
        return

    # ── Ejecución del agente ──────────────────────────────────────────────
    t_total_inicio = time.time()

    with st.spinner(f"Agente `{_MODEL}` analizando {len(asignaturas)} asignatura(s)…"):
        pass  # El spinner se cierra al comenzar el streaming

    meta_agente = _ejecutar_agente_streaming(
        asignaturas=asignaturas,
        params=params,
        resultados=resultados,
        etapa=etapa,
        cf3=cf3
    )

    t_total = round(time.time() - t_total_inicio, 3)
    meta_agente["tiempo_total_segundos"] = t_total
    meta_agente["tiempo_motor_fis_segundos"] = t_fis

    if "error" in meta_agente:
        st.error(f"💥 Error del agente: `{meta_agente['error']}`", icon="🚨")
        _render_historial_costeos()
        return

    # Guardar en sesión para re-uso
    st.session_state[clave_reporte] = meta_agente

    # ── Métricas de ejecución ─────────────────────────────────────────────
    _mostrar_metricas(meta_agente)

    # ── Persistencia completa con reporte IA ─────────────────────────────
    resultado_completo = {
        **resultado_base,
        "reporte_ia": meta_agente,
        "timestamp_agente": datetime.now().isoformat(),
    }
    ruta = guardar_nodo("COSTEO_ABC_UR", resultado_completo)
    st.session_state["fis_costeo_resultados"] = resultado_completo

    st.success(
        f"✅ Reporte completo persistido → `{Path(ruta).name}`",
        icon="💾"
    )
    st.caption("Disponible en `fis_costeo_resultados` para etapas posteriores (HITL, Simbiomemesis).")

    _render_historial_costeos()


# =============================================================================
# HELPERS DE UI
# =============================================================================

def _mostrar_metricas(meta: dict):
    """Muestra el panel de métricas de ejecución del agente."""
    st.markdown("---")
    st.markdown("**📊 Métricas de Ejecución del Agente**")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("⏱ Tiempo total",     f"{meta.get('tiempo_total_segundos', 0):.2f}s")
    col2.metric("🔧 Motor FIS",         f"{meta.get('tiempo_motor_fis_segundos', 0)*1000:.1f}ms")
    col3.metric("📥 Tokens entrada",   f"{meta.get('tokens_input', 0):,}")
    col4.metric("📤 Tokens salida",    f"{meta.get('tokens_output', 0):,}")
    col5.metric("💵 Costo estimado",   f"${meta.get('costo_usd_estimado', 0):.5f}")

    with st.expander("🔬 Metadata de Auditoría del Agente", expanded=False):
        st.json({
            "modelo_llm":                    _MODEL,
            "thinking":                      "adaptive",
            "ejecuto_costeo_asignaturas_py": meta.get("ejecuto_costeo_asignaturas_py"),
            "funcion_ejecutada":             meta.get("funcion_ejecutada"),
            "pudo_imprimir_paso_a_paso":     meta.get("pudo_imprimir_paso_a_paso"),
            "tiempo_total_s":                meta.get("tiempo_total_segundos"),
            "tiempo_motor_fis_ms":           round(meta.get("tiempo_motor_fis_segundos",0)*1000, 2),
            "tiempo_llm_s":                  meta.get("tiempo_llm_segundos"),
            "tokens_input":                  meta.get("tokens_input"),
            "tokens_output":                 meta.get("tokens_output"),
            "tokens_total":                  meta.get("tokens_input",0) + meta.get("tokens_output",0),
            "costo_usd_estimado":            meta.get("costo_usd_estimado"),
            "precio_input_usd_1M":           _PRECIO_IN,
            "precio_output_usd_1M":          _PRECIO_OUT,
        })


def _auto_guardar(resultado: dict, cf3: dict, etapa: dict):
    """Auto-guarda el resultado base (sin IA) si no se ha guardado hoy."""
    from datetime import date
    hoy  = date.today().strftime("%Y%m%d")
    flag = f"_costeo_base_guardado_{hoy}_{etapa.get('id','')}"
    if not st.session_state.get(flag):
        try:
            ruta = guardar_nodo("COSTEO_ABC_UR", resultado)
            st.session_state[flag] = ruta
            st.toast(f"💾 Costeo base guardado → `{Path(ruta).name}`", icon="✅")
        except Exception:
            pass


def _render_historial_costeos():
    """Panel colapsable con los COSTEO_ABC_UR previos en /DATOS."""
    historial = listar_nodos("COSTEO_ABC_UR", limite=8)
    if not historial:
        return

    with st.expander(
        f"🔍 Historial de auditoría — COSTEO_ABC_UR ({len(historial)} registros)",
        expanded=False
    ):
        for nodo in historial:
            ts      = nodo["timestamp"][:19].replace("T"," ")
            total   = nodo["data"].get("total_general", 0)
            n_asig  = nodo["data"].get("n_asignaturas","?")
            tiene_ia = "✅ IA" if "reporte_ia" in nodo["data"] else "—"
            periodo  = nodo["data"].get("periodo","—")

            ca, cb, cc, cd, ce = st.columns([2, 1, 1, 1, 1])
            ca.markdown(f"`{nodo['archivo']}`")
            cb.markdown(f"**{n_asig}** asig.")
            cc.markdown(f"`{periodo}`")
            cd.markdown(f"${total:,.0f}" if isinstance(total,(int,float)) else "—")
            ce.markdown(tiene_ia)

            col_load, col_json = st.columns([1, 2])
            if col_load.button("📂 Restaurar", key=f"rest_costeo_{nodo['archivo']}",
                               use_container_width=True):
                limpio = {k: v for k, v in nodo["data"].items() if k != "_auditoria"}
                st.session_state["fis_costeo_resultados"] = limpio
                if "seleccion"  in limpio: st.session_state["fis_seleccion"] = limpio["seleccion"]
                if "parametros" in limpio: st.session_state["fis_params"]    = limpio["parametros"]
                st.success(f"✅ Snapshot restaurado en memoria.")
                st.rerun()
            with col_json.expander("JSON"):
                st.json({k: v for k, v in nodo["data"].items()
                         if k not in ("_auditoria","filas","reporte_ia","parametros","seleccion")})
            st.markdown("---")
