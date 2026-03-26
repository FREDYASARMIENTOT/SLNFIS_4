"""
=============================================================================
FLUJO_3_FIS / analista_simbiomemesis_ui.py
Plantilla: Analista de la Razón de Cambio — Simbiomemesis (Etapa 6)

Fixes aplicados:
    ✅ Import relativo (sys.path) — ya no depende de FIS.
    ✅ Rutas absolutas (_DATOS_DIR desde __file__)
    ✅ Lee AMBOS patrones de percepción (legacy + nuevo)
    ✅ Escape inválido \\p corregido (raw string)
    ✅ Salida con nomenclatura YYYYMMDD_NNN_ via _persistencia
    ✅ Acceso seguro a claves dict con .get()
=============================================================================
"""

import os
import sys
import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# ── Paths absolutos ───────────────────────────────────────────────────────────
_HERE      = Path(__file__).resolve().parent
_DATOS_DIR = _HERE.parent / "DATOS"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# ── Importaciones del ecosistema FIS ──────────────────────────────────────────
from calculaSimbiomemesis import ejecutar_analisis_simbiomemesis
from _persistencia import guardar_nodo, listar_nodos


# =============================================================================
# HELPERS
# =============================================================================

def _obtener_percepciones() -> list[Path]:
    """
    Recupera archivos de percepción simbiótica en /DATOS.
    Lee AMBOS patrones para compatibilidad:
      - Nuevo : YYYYMMDD_NNN_PERCEPCION_SIMBIOSIS.json
      - Legacy: percepcionSimbiosis_*.json
    """
    nuevo  = sorted(_DATOS_DIR.glob("*_PERCEPCION_SIMBIOSIS.json"))
    legacy = sorted(_DATOS_DIR.glob("percepcionSimbiosis_*.json"))
    # Unión sin duplicados, ordenada
    vistos = set()
    resultado = []
    for p in nuevo + legacy:
        if p.name not in vistos:
            vistos.add(p.name)
            resultado.append(p)
    return sorted(resultado)


def _cargar_json_seguro(path: Path) -> dict:
    """Carga un JSON con manejo de errores."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        st.error(f"Error leyendo `{path.name}`: {e}")
        return {}


def _extraer_u(data: dict) -> float:
    """Extrae valor_utilidad_u_final de forma segura (legacy + nuevo)."""
    # Nuevo formato (formulario_hitl_utilidad v2)
    v = data.get("resultado_u", {}).get("valor_utilidad_u_final")
    if v is not None:
        return float(v)
    # Legacy (formulario_hitl_utilidad v1)
    v = data.get("resultado_u", {}).get("valor_utilidad_u_final")
    return float(v) if v is not None else 0.0


# =============================================================================
# RENDER PRINCIPAL
# =============================================================================

def render(etapa: dict, cf3: dict):
    st.header("📈 Etapa 6: Analista de la Razón de Cambio (Simbiomemesis)")

    archivos = _obtener_percepciones()

    if len(archivos) < 2:
        st.warning(
            f"⚠️ Se requieren al menos **2** Percepciones Simbióticas. "
            f"Disponibles: **{len(archivos)}**. "
            "Regresa a la etapa anterior para generar más sustratos.",
            icon="🧬"
        )
        if archivos:
            st.caption(f"Encontrado: `{archivos[0].name}`")
        return

    st.markdown("### 1. Selección de Estados a Comparar")
    st.info(
        "Selecciona el estado base ($t_1$) y el estado subsecuente ($t_2$) "
        "para calcular la derivada total."
    )

    nombres = [p.name for p in archivos]
    col1, col2 = st.columns(2)
    with col1:
        nombre_t1 = st.selectbox(
            "Estado Anterior ($t_1$):", nombres,
            index=0, key=f"asm_t1_{etapa.get('id','x')}"
        )
    with col2:
        nombre_t2 = st.selectbox(
            "Estado Actual ($t_2$):", nombres,
            index=len(nombres)-1, key=f"asm_t2_{etapa.get('id','x')}"
        )

    if nombre_t1 == nombre_t2:
        st.error("❌ Selecciona dos archivos distintos para calcular la diferencia temporal.")
        return

    datos_t1 = _cargar_json_seguro(_DATOS_DIR / nombre_t1)
    datos_t2 = _cargar_json_seguro(_DATOS_DIR / nombre_t2)

    if not datos_t1 or not datos_t2:
        return

    # ── Resumen previo ────────────────────────────────────────────────────
    u1 = _extraer_u(datos_t1)
    u2 = _extraer_u(datos_t2)
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Utilidad $U_{t1}$",  f"{u1:.6f}")
    col_r2.metric("Utilidad $U_{t2}$",  f"{u2:.6f}")
    col_r3.metric("ΔU preliminar",      f"{u2 - u1:+.6f}")
    st.markdown("---")

    # ── Botón de cálculo ──────────────────────────────────────────────────
    if st.button(
        "🤖 Ejecutar Agente Analista (Calcular Simbiomemesis)",
        use_container_width=True, type="primary",
        key=f"btn_asm_{etapa.get('id','x')}"
    ):
        resultado = ejecutar_analisis_simbiomemesis(datos_t1, datos_t2)

        if resultado["status"] == "SUCCESS":
            da = resultado["payload_simbiomemesis"]

            st.subheader("📊 Resultados del Análisis Evolutivo")

            # Semáforo visual
            estado = da.get("estado_evolutivo_sistema","—")
            if "POSITIVA" in estado:
                st.success(f"**{estado}**")
            elif "REGRESIÓN" in estado or "REGRESION" in estado:
                st.error(f"**{estado}**")
            else:
                st.warning(f"**{estado}**")

            st.markdown(
                f"**Recomendación del Agente:** "
                f"*{da.get('recomendacion_agente_analista','—')}*"
            )

            # Métricas (escape correcto con raw-string o sin LaTeX en label)
            m1, m2 = st.columns(2)
            m1.metric(
                label="Simbiomemesis (dU/dt)",
                value=f"{da.get('derivada_temporal_simbiomemesis', 0):.6f}"
            )
            m2.metric(
                label=r"Sensibilidad al Costo (∂U/∂C)",
                value=f"{da.get('sensibilidad_al_costo_gradiente', 0):.8f}"
            )

            # Caja blanca
            with st.expander("🔍 Ver Desglose Matemático (Caja Blanca)"):
                for paso in da.get("trazabilidad_matematica", []):
                    st.code(paso, language="bash")

            # Persistir con nomenclatura YYYYMMDD_NNN_
            payload_guardar = {
                "tipo":               "SIMBIOMEMESIS",
                "cinta":              cf3.get("nombre",""),
                "etapa":              etapa.get("nombre",""),
                "etapa_id":           etapa.get("id",""),
                "archivo_t1":         nombre_t1,
                "archivo_t2":         nombre_t2,
                "resultado_completo": resultado,
                "timestamp_analisis": resultado.get("timestamp_analisis",""),
            }
            ruta = guardar_nodo("SIMBIOMEMESIS", payload_guardar)
            st.success(
                f"💾 Análisis persistido → `{Path(ruta).name}`\n\n"
                "Este archivo alimentará la **Etapa 7: Compara Flujos**."
            )

        else:
            st.error(
                f"💥 Falla matemática del agente: "
                f"`{resultado.get('detalle','Error desconocido')}`"
            )

    st.caption("FIS v9.0 | Simbiomemesis — Universidad del Rosario")
