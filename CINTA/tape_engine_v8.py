"""
tape_engine_v8.py
=================
Motor de Persistencia - Registro Inmutable (CINTA)

Responsabilidades:
- Mantener ledger inmutable de todas las operaciones
- Generar trazabilidad total (audit trail)
- Persistir eventos del orquestador y agentes
- Interfaz con Pinecone para vectorización de auditoría

Namespace: auditoria-v8-ur (índice v7)
"""

import json
from datetime import datetime
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class TapeEngine:
    """Motor de cinta inmutable para FIS v8.1"""

    def __init__(self, namespace: str = "auditoria-v8-ur"):
        self.namespace = namespace
        self.log_entries: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()

    def record_event(
        self,
        event_type: str,
        agent_id: str,
        payload: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Registra un evento inmutable en la cinta.

        Args:
            event_type: Tipo de evento (ej: 'costeo', 'utilidad', 'agente_creado')
            agent_id: ID del agente que generó el evento
            payload: Datos del evento
            metadata: Información adicional (opcional)

        Returns:
            Diccionario con el evento registrado
        """
        timestamp = datetime.now().isoformat()
        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "agent_id": agent_id,
            "namespace": self.namespace,
            "payload": payload,
            "metadata": metadata or {},
        }
        self.log_entries.append(event)
        logger.info(f"[TAPE] Evento registrado: {event_type} por {agent_id}")
        return event

    def get_audit_trail(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """Obtiene el historial de auditoría (opcional: filtrado por agente)"""
        if agent_id:
            return [e for e in self.log_entries if e["agent_id"] == agent_id]
        return self.log_entries

    def export_to_json(self, filepath: str) -> None:
        """Exporta la cinta a archivo JSON"""
        with open(filepath, "w") as f:
            json.dump(self.log_entries, f, indent=2, default=str)
        logger.info(f"[TAPE] Cinta exportada a {filepath}")


# Instancia global
tape = TapeEngine()
