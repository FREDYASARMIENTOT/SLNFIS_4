"""
=============================================================================
PROYECTO: SYMBIOMEMESIS v8.1 - UNIVERSIDAD DEL ROSARIO
MODULO: utils/loader_oferta.py
DESCRIPCIÓN:
    Carga la jerarquía Facultad → Programa Académico → Asignatura
    desde el archivo Excel de oferta académica 2024.
    Detecta automáticamente las columnas mediante múltiples variantes de nombre.
=============================================================================
"""

import os
import pathlib
import pandas as pd
import streamlit as st


def _buscar_excel() -> str:
    """
    Busca el archivo Excel subiendo desde la ubicación real del módulo y
    desde el cwd, tolerando que __file__ sea un path relativo (ocurre cuando
    Streamlit agrega '..' al sys.path y el módulo se importa con ruta relativa).
    """
    nombre_relativo = os.path.join("DATOS", "OFERTA ACADEMICA ASIGNATURAS 2024.xlsx")
    puntos_de_inicio = [
        pathlib.Path(__file__).resolve().parent,   # directorio real de este módulo
        pathlib.Path(os.getcwd()),                 # directorio de trabajo actual
    ]
    for inicio in puntos_de_inicio:
        actual = inicio
        for _ in range(6):                         # sube hasta 6 niveles
            candidato = actual / "DATOS" / "OFERTA ACADEMICA ASIGNATURAS 2024.xlsx"
            if candidato.exists():
                return str(candidato)
            actual = actual.parent
    # Fallback: ruta clásica (para que el mensaje de error sea legible)
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        nombre_relativo,
    )


_EXCEL_PATH = _buscar_excel()

# Variantes aceptadas para cada nivel jerárquico (mayúsculas/sin tildes)
_VARIANTES_FACULTAD = [
    "FACULTAD", "FACULTAD ", "FAC", "UNIDAD", "DECANATURA", "ESCUELA",
    "CENTRO", "División", "DIVISION", "NOMBRE_FACULTAD", "NOM_FACULTAD",
    "FACULTY", "NOMBRE FACULTAD", "FACULTAD_ASIGNATURA",
]
_VARIANTES_PROGRAMA = [
    "PROGRAMA", "PROGRAMA ACADÉMICO", "PROGRAMA ACADEMICO",
    "PLAN", "CARRERA", "POSGRADO", "PREGRADO",
    "NOMBRE_PROGRAMA", "NOM_PROGRAMA", "PROGRAM", "NOMBRE PROGRAMA",
]
_VARIANTES_ASIGNATURA = [
    "ASIGNATURA", "MATERIA", "CURSO", "NOMBRE_ASIGNATURA",
    "NOM_ASIGNATURA", "SUBJECT", "NOMBRE ASIGNATURA",
    "NOMBRE MATERIA", "NOMBRE CURSO", "NOMBRE_MATERIA",
]


def _normalizar(col: str) -> str:
    """Normaliza un nombre de columna para comparación robusta."""
    return (col.upper()
               .strip()
               .replace("Á", "A").replace("É", "E").replace("Í", "I")
               .replace("Ó", "O").replace("Ú", "U").replace("Ü", "U"))


def _detectar_columna(columnas: list[str], variantes: list[str]) -> str | None:
    """Busca la primera columna que coincida con alguna variante normalizada."""
    norm_cols = {_normalizar(c): c for c in columnas}
    norm_vars_set = {_normalizar(v) for v in variantes}
    for nk, orig in norm_cols.items():
        if nk in norm_vars_set:
            return orig
    # Búsqueda parcial como fallback
    for nk, orig in norm_cols.items():
        for v in norm_vars_set:
            if v in nk or nk in v:
                return orig
    return None


@st.cache_data(show_spinner="📂 Cargando oferta académica 2024...")
def cargar_jerarquia() -> tuple[dict, str]:
    """
    Carga las tres columnas jerárquicas del Excel y construye un dict:
        { facultad: { programa: [asignatura1, asignatura2, ...] } }

    Devuelve (jerarquia, mensaje_estado).
    """
    ruta = os.path.abspath(_EXCEL_PATH)

    if not os.path.exists(ruta):
        return {}, f"❌ Archivo no encontrado: {ruta}"

    try:
        xl = pd.ExcelFile(ruta)

        # Buscar la hoja que tenga las tres columnas requeridas
        df = None
        hoja_usada = None
        col_fac = col_prog = col_asig = None
        for nombre_hoja in xl.sheet_names:
            df_candidato = pd.read_excel(xl, sheet_name=nombre_hoja)
            cols = list(df_candidato.columns)
            cf  = _detectar_columna(cols, _VARIANTES_FACULTAD)
            cp  = _detectar_columna(cols, _VARIANTES_PROGRAMA)
            ca  = _detectar_columna(cols, _VARIANTES_ASIGNATURA)
            if cf and cp and ca:
                df, hoja_usada = df_candidato, nombre_hoja
                col_fac, col_prog, col_asig = cf, cp, ca
                break

        # Si ninguna hoja tuvo las tres columnas, reportar las disponibles
        if df is None:
            resumen = "; ".join(
                f"{h}: {list(pd.read_excel(xl, sheet_name=h).columns)}"
                for h in xl.sheet_names
            )
            return {}, (
                f"⚠️ No se pudieron mapear las columnas en ninguna hoja.\n"
                f"Hojas y columnas disponibles: {resumen}"
            )

        cols = list(df.columns)

        # Construir jerarquía
        df_clean = df[[col_fac, col_prog, col_asig]].dropna()
        
        # Compatibilidad con pandas modernos
        if hasattr(df_clean, "map"):
            df_clean = df_clean.astype(str).map(str.strip)
        else:
            df_clean = df_clean.astype(str).applymap(str.strip)
            
        df_clean = df_clean[df_clean[col_fac] != ""]

        jerarquia: dict = {}
        for _, row in df_clean.iterrows():
            fac  = row[col_fac].upper().strip()
            prog = row[col_prog].strip()
            asig = row[col_asig].strip()
            jerarquia.setdefault(fac, {}).setdefault(prog, set()).add(asig)

        # Convertir sets a listas sorted
        for f in jerarquia:
            for p in jerarquia[f]:
                jerarquia[f][p] = sorted(jerarquia[f][p])

        n_fac  = len(jerarquia)
        n_prog = sum(len(ps) for ps in jerarquia.values())
        n_asig = sum(len(a) for ps in jerarquia.values() for a in ps.values())

        estado = (
            f"✅ Oferta 2024 cargada | hoja '{hoja_usada}' | "
            f"Col: {col_fac} / {col_prog} / {col_asig} | "
            f"{n_fac} facultades · {n_prog} programas · {n_asig} asignaturas"
        )
        return jerarquia, estado

    except Exception as e:
        return {}, f"❌ Error leyendo el Excel: {e}"


def render_selector_jerarquia(key_prefix: str = "h") -> tuple[list, list, list]:
    """
    Renderiza los tres multi-selects en cascada (Facultad / Programa / Asignatura)
    en una fila de 3 columnas. Muestra el badge de estado del Excel.

    Args:
        key_prefix: prefijo único para evitar colisiones de key entre páginas.

    Returns:
        Tupla (facultades_sel, programas_sel, asignaturas_sel)
    """
    jerarquia, estado = cargar_jerarquia()

    # Banner de estado
    if jerarquia:
        st.success(estado, icon="📂")
    else:
        st.error(estado, icon="📂")
        st.stop()

    col_f, col_pr, col_as = st.columns(3)

    # Nivel 1: Facultades
    todas_fac = sorted(jerarquia.keys())
    with col_f:
        fac_sel = st.multiselect(
            "1️⃣ Facultad(es)",
            options=todas_fac,
            default=todas_fac[:1] if todas_fac else [],
            key=f"{key_prefix}_facultades",
            help="Filtra programas y asignaturas"
        )

    # Nivel 2: Programas filtrados
    progs_disp = sorted({
        prog
        for fac in fac_sel
        for prog in jerarquia.get(fac, {}).keys()
    })
    with col_pr:
        prog_sel = st.multiselect(
            "2️⃣ Programa(s)",
            options=progs_disp,
            default=progs_disp[:1] if progs_disp else [],
            key=f"{key_prefix}_programas",
            help="Filtrado por Facultades"
        )

    # Nivel 3: Asignaturas filtradas
    asigs_disp = sorted({
        asig
        for fac in fac_sel
        for prog in prog_sel
        for asig in jerarquia.get(fac, {}).get(prog, [])
    })
    with col_as:
        if not asigs_disp:
            st.warning("Selecciona Facultad y Programa primero.", icon="⚠️")
            asig_sel = []
        else:
            asig_sel = st.multiselect(
                "3️⃣ Asignatura(s)",
                options=asigs_disp,
                default=asigs_disp[:1] if asigs_disp else [],
                key=f"{key_prefix}_asignaturas",
                help="Filtrado por Programas"
            )

    if asig_sel:
        st.markdown(
            f"**{len(asig_sel)} asignatura(s):** " +
            " ".join([
                f"<span style='background:#8B0000;color:white;padding:2px 8px;"
                f"border-radius:10px;font-size:0.78em;margin:2px'>{a}</span>"
                for a in asig_sel
            ]),
            unsafe_allow_html=True
        )

    return fac_sel, prog_sel, asig_sel
