"""
=============================================================================
FLUJO_3_FIS / _persistencia.py
Nodo de Persistencia JSON — Serialización con nomenclatura de auditoría
=============================================================================

Nomenclatura de archivos:
    YYYYMMDD_NNN_PATRON.json
    NNN = consecutivo diario (001, 002, …) para evitar colisiones.

Patrones canónicos:
    SELECCION_FIS   → selección jerárquica (facultad/programa/asignatura)
    PARAMS_FIS      → parámetros de costeo ABC
    COSTEO_ABC_UR   → resultado completo del costeo

Soluciona:
    - Volatilidad: datos sobreviven al refresco del navegador
    - Trazabilidad: histórico físico en /DATOS para auditoría forense
    - Acoplamiento débil: etapas leen del disco si la RAM está vacía
=============================================================================
"""

import json
from datetime import datetime, date
from pathlib import Path

# /DATOS está 2 niveles arriba de /FLUJO_3_FIS
_DATOS_DIR = Path(__file__).resolve().parent.parent / "DATOS"
_DATOS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# NOMENCLATURA
# ---------------------------------------------------------------------------

def _next_nombre(patron: str) -> str:
    """
    Retorna el próximo nombre (sin extensión) con formato YYYYMMDD_NNN_PATRON.
    NNN = cantidad de archivos del patrón creados HOY + 1.
    """
    hoy = date.today().strftime("%Y%m%d")
    existentes = list(_DATOS_DIR.glob(f"{hoy}_*_{patron}.json"))
    nnn = len(existentes) + 1
    return f"{hoy}_{nnn:03d}_{patron}"


# ---------------------------------------------------------------------------
# ESCRITURA
# ---------------------------------------------------------------------------

def guardar_nodo(patron: str, data: dict) -> str:
    """
    Persiste `data` en /DATOS/YYYYMMDD_NNN_PATRON.json.

    Agrega automáticamente el bloque `_auditoria` con:
        - patron, archivo, timestamp, version
    Retorna la ruta absoluta del archivo creado.
    """
    nombre = _next_nombre(patron)
    ruta   = _DATOS_DIR / f"{nombre}.json"

    payload = dict(data)          # copia superficial para no mutar el original
    payload["_auditoria"] = {
        "patron":    patron,
        "archivo":   f"{nombre}.json",
        "ruta":      str(ruta),
        "timestamp": datetime.now().isoformat(),
        "version":   "FIS-v8.1",
    }

    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    return str(ruta)


# ---------------------------------------------------------------------------
# LECTURA
# ---------------------------------------------------------------------------

def cargar_ultimo(patron: str) -> dict | None:
    """
    Carga el archivo más reciente que coincida con *_PATRON.json en /DATOS.
    Retorna None si no existe ninguno.
    """
    archivos = sorted(_DATOS_DIR.glob(f"*_{patron}.json"))
    if not archivos:
        return None
    try:
        with open(archivos[-1], encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def listar_nodos(patron: str, limite: int = 10) -> list[dict]:
    """
    Lista los `limite` archivos más recientes del patrón, ordenados desc.
    Cada entrada contiene: archivo, path, timestamp, cinta, etapa, data.
    """
    archivos = sorted(_DATOS_DIR.glob(f"*_{patron}.json"), reverse=True)[:limite]
    resultado = []
    for a in archivos:
        try:
            with open(a, encoding="utf-8") as fh:
                d = json.load(fh)
            resultado.append({
                "archivo":   a.name,
                "path":      str(a),
                "timestamp": d.get("_auditoria", {}).get("timestamp", "—"),
                "cinta":     d.get("cinta", "—"),
                "etapa":     d.get("etapa", "—"),
                "data":      d,
            })
        except Exception:
            pass
    return resultado


# ---------------------------------------------------------------------------
# RECUPERACIÓN (RAM → Disco)
# ---------------------------------------------------------------------------

def recuperar_estado(ss_key: str, patron: str):
    """
    Estrategia de recuperación de dos niveles:
    1. session_state[ss_key] si existe y no está vacío  →  retorna ese valor.
    2. Último archivo *_PATRON.json en /DATOS           →  lo inyecta en
       session_state y lo retorna.
    3. Si no hay nada                                   →  retorna None.

    Importa streamlit internamente para que el módulo sea cargable
    fuera de un contexto Streamlit (tests, CLI).
    """
    try:
        import streamlit as st
        val = st.session_state.get(ss_key)
        if val:
            return val
        recuperado = cargar_ultimo(patron)
        if recuperado:
            # Limpiar metadata de auditoría antes de inyectar
            limpio = {k: v for k, v in recuperado.items() if k != "_auditoria"}
            st.session_state[ss_key] = limpio
            return limpio
    except Exception:
        pass
    return None
