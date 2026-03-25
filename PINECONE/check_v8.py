#!/usr/bin/env python3
# =============================================================================
# PROYECTO: SLN_FIS4 (FIS v8.1) - UNIVERSIDAD DEL ROSARIO
# MODULO: Validación de Índice Existente (v7 -> v8)
# =============================================================================

import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Localizar .env en la raíz
ruta_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(ruta_env)

def validar_indice_reutilizado():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = "symbiomemesis-v7-index" # Forzado por directriz del Auditor
    namespace_v8 = "auditoria-v8-ur" # Aislamiento para SLNFIS_4

    pc = Pinecone(api_key=api_key)
    
    print(f"\n\033[1;33m=== AUDITORÍA DE INFRAESTRUCTURA REUTILIZADA ===\033[0m")
    
    try:
        desc = pc.describe_index(index_name)
        dim = desc.dimension
        print(f"✅ Índice detectado: {index_name}")
        print(f"📊 Dimensiones actuales: {dim}")
        
        if dim != 3072:
            print(f"⚠️ ADVERTENCIA: El índice tiene {dim} dimensiones. "
                  f"Asegúrese de que el modelo en el .env sea compatible.")
        
        # Verificar si el Namespace v8 ya existe o está listo
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        print(f"📂 Namespaces detectados: {list(stats['namespaces'].keys())}")
        print(f"🚀 Namespace objetivo: {namespace_v8}")
        print(f"\033[1;32m[SISTEMA] Listo para colonización semántica v8.1.\033[0m")

    except Exception as e:
        print(f"❌ ERROR: No se pudo acceder al índice v7. Verifique API Key. {e}")

if __name__ == "__main__":
    validar_indice_reutilizado()