"""
=============================================================================
PROYECTO: SLNFIS_4 (Simbiomemesis v9.0) - UNIVERSIDAD DEL ROSARIO
MODULO: Motor de Cálculo de Simbiomemesis (Razón de Cambio)
UBICACIÓN: /projects/SLNFIS_4/FIS/
AUTOR: Ing. Fredy Alejandro Sarmiento Torres
DESCRIPCIÓN: 
    Calcula la derivada total y las derivadas parciales entre dos estados 
    de Utilidad Simbiótica (U) para determinar la dirección de aprendizaje 
    del ecosistema (HITL + Agentes).
=============================================================================
"""

import numpy as np
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field

# =============================================================================
# 📋 MODELOS DE DATOS (INPUT/OUTPUT)
# =============================================================================
class EstadoSimbiotico(BaseModel):
    """Representa un punto en el tiempo (t) del sistema."""
    valor_utilidad_u: float
    costo_directo: float
    tiempo_iteracion_t: int
    validacion_hitl: int

class ResultadoRazonDeCambio(BaseModel):
    """Caja Blanca del cálculo de la derivada de Simbiomemesis."""
    delta_utilidad_total: float
    derivada_temporal_simbiomemesis: float
    sensibilidad_al_costo_gradiente: float
    estado_evolutivo_sistema: str
    recomendacion_agente_analista: str
    trazabilidad_matematica: list[str]

# =============================================================================
# 📐 CLASE MAESTRA: ANALISTA DE LA RAZÓN DE CAMBIO
# =============================================================================
class AgenteAnalistaSimbiomemesisV9:
    """
    Agente matemático que calcula la evolución del sistema evaluando 
    la diferencia entre el estado anterior (t-1) y el actual (t).
    """
    def __init__(self, estado_anterior_t1: Dict[str, Any], estado_actual_t2: Dict[str, Any]):
        # Extracción segura de variables desde los JSON de percepción
        self.estado_t1 = EstadoSimbiotico(
            valor_utilidad_u=estado_anterior_t1["resultado_u"]["valor_utilidad_u_final"],
            costo_directo=estado_anterior_t1["entrada"]["costo_directo_asignaturas"],
            tiempo_iteracion_t=estado_anterior_t1["entrada"]["tiempo_proceso_iteracion"],
            validacion_hitl=estado_anterior_t1["entrada"]["validacion_humana_hitl"]
        )
        
        self.estado_t2 = EstadoSimbiotico(
            valor_utilidad_u=estado_actual_t2["resultado_u"]["valor_utilidad_u_final"],
            costo_directo=estado_actual_t2["entrada"]["costo_directo_asignaturas"],
            tiempo_iteracion_t=estado_actual_t2["entrada"]["tiempo_proceso_iteracion"],
            validacion_hitl=estado_actual_t2["entrada"]["validacion_humana_hitl"]
        )

    def calcular_derivadas_y_razon_cambio(self) -> ResultadoRazonDeCambio:
        pasos_calculo = []
        
        # 1. Diferenciales (Deltas)
        delta_u = self.estado_t2.valor_utilidad_u - self.estado_t1.valor_utilidad_u
        delta_t = self.estado_t2.tiempo_iteracion_t - self.estado_t1.tiempo_iteracion_t
        delta_c = self.estado_t2.costo_directo - self.estado_t1.costo_directo
        
        pasos_calculo.append(f"1. Diferencial de Utilidad (ΔU): {delta_u:.6f}")
        pasos_calculo.append(f"2. Diferencial de Tiempo (Δt): {delta_t}")
        pasos_calculo.append(f"3. Diferencial de Costo (ΔC): {delta_c:.2f}")

        # 2. SIMBIOMEMESIS (Derivada Temporal discreta dU/dt)
        # Aseguramos que delta_t no sea 0 para evitar divisiones por cero.
        dt_efectivo = max(delta_t, 1)
        simbiomemesis_temporal = delta_u / dt_efectivo
        pasos_calculo.append(f"4. Simbiomemesis (dU/dt): {simbiomemesis_temporal:.6f}")

        # 3. SENSIBILIDAD AL COSTO (Derivada Parcial discreta ∂U/∂C)
        # Cuánto cambió la utilidad en función de cuánto cambió el costo
        if abs(delta_c) > 0.001:
            sensibilidad_costo = delta_u / delta_c
        else:
            sensibilidad_costo = 0.0 # El costo no cambió
        pasos_calculo.append(f"5. Gradiente de Costo (∂U/∂C): {sensibilidad_costo:.8f}")

        # 4. ANÁLISIS DE ESTADO EVOLUTIVO
        if simbiomemesis_temporal > 0.01:
            estado = "🟢 EVOLUCIÓN POSITIVA (Simbiosis Creciente)"
            recomendacion = "Mantener los parámetros de distribución ABC actuales. El sistema genera mayor utilidad."
        elif simbiomemesis_temporal < -0.01:
            estado = "🔴 REGRESIÓN (Fricción Sistémica)"
            recomendacion = "Revisar variables HITL o inductores. La eficiencia de la utilidad está decayendo."
        else:
            estado = "🟡 ESTABILIDAD (Simbiosis Neutra)"
            recomendacion = "El sistema alcanzó un óptimo local. No se requieren ajustes mayores."

        return ResultadoRazonDeCambio(
            delta_utilidad_total=round(delta_u, 6),
            derivada_temporal_simbiomemesis=round(simbiomemesis_temporal, 6),
            sensibilidad_al_costo_gradiente=round(sensibilidad_costo, 8),
            estado_evolutivo_sistema=estado,
            recomendacion_agente_analista=recomendacion,
            trazabilidad_matematica=pasos_calculo
        )

# =============================================================================
# 🚀 FUNCIÓN DE ACCESO PARA LA UI / CINTA
# =============================================================================
def ejecutar_analisis_simbiomemesis(json_t1: Dict, json_t2: Dict) -> Dict:
    try:
        analista = AgenteAnalistaSimbiomemesisV9(json_t1, json_t2)
        resultado = analista.calcular_derivadas_y_razon_cambio()
        return {
            "status": "SUCCESS",
            "timestamp_analisis": datetime.now().isoformat(),
            "payload_simbiomemesis": resultado.model_dump()
        }
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}