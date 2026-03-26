"""
=============================================================================
PROYECTO: SLNFIS_4 (Simbiomemesis v9.1) - UNIVERSIDAD DEL ROSARIO
MODULO: Motor de Cálculo de Utilidad Simbiótica Escalar (v9.1 - Kali/WSL)
AUTOR: Ing. Fredy Alejandro Sarmiento Torres
DESCRIPCIÓN: 
    Calcula el valor puntual de Utilidad Simbiótica (U). 
    Actualización v9.1: Reemplaza validación binaria por un cuestionario 
    HITL de 1 a 5, normalizado a 0-1 para mayor precisión estocástica.
=============================================================================
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field

# =============================================================================
# 🛡️ GESTIÓN DE EXCEPCIONES MATEMÁTICAS DETALLADAS
# =============================================================================
class ErrorMatematicoUtilidadV9(Exception):
    def __init__(self, mensaje_error: str, componente_afectado: str):
        self.mensaje_error = mensaje_error
        self.componente_afectado = componente_afectado
        self.timestamp_error = datetime.now().isoformat()
        super().__init__(f"[FIS-V9-ERR] Fallo en {componente_afectado}: {mensaje_error}")

# =============================================================================
# 📋 MODELOS DE DATOS (INPUT/OUTPUT)
# =============================================================================
class DatosEntradaCintaV9(BaseModel):
    """Esquema del JSON requerido. Incluye el nuevo cuestionario HITL."""
    costo_directo_asignaturas: float = Field(..., description="Sumatoria de costos directos")
    inductor_actividad_valor: float = Field(..., description="Valor del driver (ej. horas)")
    tiempo_proceso_iteracion: int = Field(..., description="Marca de tiempo o iteración")
    utilidad_anterior_pinecone: float = Field(..., description="U de la iteración t-1")
    peso_autonomia_agente: float = Field(..., ge=0, le=1, description="Alpha (0-1)")
    
    # NUEVO: Cuestionario HITL (Escala 1 a 5)
    calificacion_q1_precision: int = Field(..., ge=1, le=5, description="Precisión percibida del costeo ABC")
    calificacion_q2_agente: int = Field(..., ge=1, le=5, description="Relevancia de la automatización")
    calificacion_q3_transparencia: int = Field(..., ge=1, le=5, description="Claridad de la Caja Blanca")
    calificacion_q4_confianza: int = Field(..., ge=1, le=5, description="Confianza general para auditoría")

class ResultadoCajaBlancaU(BaseModel):
    valor_utilidad_u_final: float
    componente_eficiencia_abc: float
    componente_validacion_humana_normalizada: float
    factor_atenuacion_temporal: float
    formula_matematica: str = "U = (α * log(C)) * (H_norm + e^-t)"
    trazabilidad_pasos: List[str]

# =============================================================================
# 📐 CLASE MAESTRA: CALCULADOR DE UTILIDAD SIMBIÓTICA
# =============================================================================
class AgenteCalculadorUtilidadV9:
    def __init__(self, datos_payload: Dict[str, Any]):
        try:
            self.entrada = DatosEntradaCintaV9(**datos_payload)
        except Exception as e:
            raise ErrorMatematicoUtilidadV9(f"Estructura JSON inválida: {str(e)}", "VALIDACION_INPUT")

    def ejecutar_calculo_utilidad_u(self) -> ResultadoCajaBlancaU:
        pasos_auditoria = []

        # --- PASO 1: Procesamiento del Componente de Costeo ABC ---
        if self.entrada.costo_directo_asignaturas <= 0:
            raise ErrorMatematicoUtilidadV9("Costo directo debe ser positivo para logaritmo", "LOG_COSTEO")
            
        eficiencia_base_abc = np.log1p(self.entrada.costo_directo_asignaturas) 
        pasos_auditoria.append(f"1. Eficiencia ABC (log1p): {eficiencia_base_abc:.4f}")

        # --- PASO 2: Procesamiento del Peso de Autonomía (Alpha) ---
        componente_ponderado_agente = self.entrada.peso_autonomia_agente * eficiencia_base_abc
        pasos_auditoria.append(f"2. Componente Ponderado Agente (α * Ef): {componente_ponderado_agente:.4f}")

        # --- PASO 3: Normalización de Validación Humana (HITL 1-5 a 0-1) ---
        # Fórmula: (Valor - 1) / 4
        norm_q1 = (self.entrada.calificacion_q1_precision - 1) / 4.0
        norm_q2 = (self.entrada.calificacion_q2_agente - 1) / 4.0
        norm_q3 = (self.entrada.calificacion_q3_transparencia - 1) / 4.0
        norm_q4 = (self.entrada.calificacion_q4_confianza - 1) / 4.0
        
        # Promedio de la percepción humana normalizada
        promedio_hitl_norm = np.mean([norm_q1, norm_q2, norm_q3, norm_q4])
        factor_confianza_humana = promedio_hitl_norm + 0.1 # Suelo mínimo de 0.1 para evitar anular la ecuación
        
        pasos_auditoria.append(f"3. Normalización HITL (Promedio 0-1): {promedio_hitl_norm:.4f} -> Confianza Base: {factor_confianza_humana:.4f}")

        # --- PASO 4: Cálculo de Atenuación Temporal ---
        atenuacion_temporal = np.exp(-self.entrada.tiempo_proceso_iteracion / 100)
        pasos_auditoria.append(f"4. Atenuación Temporal (e^-t): {atenuacion_temporal:.4f}")

        # --- PASO 5: ENSAMBLE DE LA ECUACIÓN MAESTRA U ---
        utilidad_u_calculada = componente_ponderado_agente * (factor_confianza_humana + atenuacion_temporal)
        pasos_auditoria.append(f"5. Ensamble Final: {componente_ponderado_agente:.4f} * ({factor_confianza_humana:.4f} + {atenuacion_temporal:.4f})")

        return ResultadoCajaBlancaU(
            valor_utilidad_u_final=round(utilidad_u_calculada, 8),
            componente_eficiencia_abc=round(eficiencia_base_abc, 6),
            componente_validacion_humana_normalizada=float(factor_confianza_humana),
            factor_atenuacion_temporal=float(atenuacion_temporal),
            trazabilidad_pasos=pasos_auditoria
        )

# =============================================================================
# 🚀 PUNTO DE ENTRADA
# =============================================================================
def procesar_evento_utilidad_v9(json_solicitud: Dict[str, Any]) -> Dict[str, Any]:
    try:
        calculador = AgenteCalculadorUtilidadV9(json_solicitud)
        resultado = calculador.ejecutar_calculo_utilidad_u()
        return {
            "status": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "payload_u": resultado.model_dump()
        }
    except ErrorMatematicoUtilidadV9 as emv9:
        return {"status": "ERROR", "error_detalle": emv9.mensaje_error, "componente": emv9.componente_afectado}
    except Exception as e:
        return {"status": "CRITICAL_FAILURE", "detalle": str(e)}

# =============================================================================
# 🖥️ INTERFAZ STREAMLIT — render() requerido por el cargador de plantillas
# =============================================================================
def render(etapa: dict, cf3: dict):
    """
    Punto de entrada para el sistema de pestañas dinámicas de 03_flujo_fis.py.
    calculaUtilidadSimbiotica.py es el motor matemático; la interfaz completa
    (gestor de sustrato, cuestionario HITL v9.1, Caja Blanca, historial)
    vive en formulario_hitl_utilidad.py.  Este método delega sin duplicar código.
    """
    import sys
    from pathlib import Path
    _here = Path(__file__).resolve().parent
    if str(_here) not in sys.path:
        sys.path.insert(0, str(_here))

    try:
        from formulario_hitl_utilidad import render as _render_formulario
        _render_formulario(etapa, cf3)
    except Exception as exc:
        import streamlit as st
        st.error(
            f"❌ No se pudo cargar `formulario_hitl_utilidad.py`: `{exc}`\n\n"
            "Asegúrate de que el archivo existe en la carpeta `/FLUJO_3_FIS/`.",
            icon="🚨"
        )


# --- EJEMPLO DE USO (TEST LOCAL KALI) ---
if __name__ == "__main__":
    payload_ejemplo = {
        "costo_directo_asignaturas": 15500.50,
        "inductor_actividad_valor": 45.0,
        "tiempo_proceso_iteracion": 2,
        "utilidad_anterior_pinecone": 12.5,
        "peso_autonomia_agente": 0.85,
        # Nuevas variables de la interfaz HITL (1 a 5)
        "calificacion_q1_precision": 4,  # Se convertirá en 0.75
        "calificacion_q2_agente": 5,     # Se convertirá en 1.0
        "calificacion_q3_transparencia": 3, # Se convertirá en 0.5
        "calificacion_q4_confianza": 4   # Se convertirá en 0.75
    }
    
    print("--- Iniciando Cálculo de Utilidad v9.1 ---")
    resultado_test = procesar_evento_utilidad_v9(payload_ejemplo)
    import json
    print(json.dumps(resultado_test, indent=4))