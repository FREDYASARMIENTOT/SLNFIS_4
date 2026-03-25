#!/bin/bash
# =============================================================================
# PROYECTO: SLN_FIS4 (SYMBIOMEMESIS v8.1) - UNIVERSIDAD DEL ROSARIO
# SCRIPT: Orquestador Maestro y Terminal de Auditoría Forense (v8.1.0)
# ENTORNO: WSL Kali-Linux | Entorno Conda: venvFIS_Rosario
# AUTOR: Ing. Fredy Alejandro Sarmiento Torres
# =============================================================================

ENTORNO="venvFIS_Rosario"
ORQUESTADOR="fis_orquestador_v8.py"
PROJ_DIR="/home/fredyast/projects/SLNFIS_4"

echo "🏛️  Iniciando Ecosistema Symbiomemesis v8.1 (SLN_FIS4)..."

# 1. Validación de Ruta y Estructura FIS v8
mkdir -p $PROJ_DIR
cd $PROJ_DIR || { echo "❌ Error: No se pudo acceder a $PROJ_DIR"; exit 1; }

echo "📂 Sincronizando arquitectura de carpetas FIS v8..."
mkdir -p ARCHIVOS LOGS PINECONE TEST ORIGENDATOS PROCESOMODELADO FIS CINTA

# 2. Creación de Archivos Raíz (Caja Blanca) si no existen
if [ ! -f ".env" ]; then
    echo "📝 Generando plantilla .env..."
    cat <<EOT > .env
GOOGLE_API_KEY=AIzaSyAn-PhZ-jqI0uP_VxbD_1Y4oivxOB69tpY
MODEL_NAME=gemini-2.0-flash
PINECONE_API_KEY=pcsk_4nRA7R_MoQ3kBYv4sUEoRq5NDc3bhDdHHa8ZtXSd9x4nckRyPsWrKVwVbP5sm39hH9KyJ7
PINECONE_INDEX=symbiomemesis-v7-index
PINECONE_NAMESPACE=auditoria-v8-ur
EOT
fi

# 3. Limpieza y Optimización
echo "🧹 Limpiando artefactos de ejecuciones previas..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 4. Localización y Activación de Conda
CONDA_BASE=$(conda info --base 2>/dev/null)
if [ -z "$CONDA_BASE" ]; then
    CONDA_BASE="/home/fredyast/miniconda3" 
fi
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 5. Validación del Entorno
conda activate $ENTORNO
if [ $? -ne 0 ]; then
    echo "❌ ERROR: El entorno $ENTORNO no existe. Ejecute conda env create primero."
    exit 1
fi

# 6. Lanzamiento del Orquestador (Streamlit)
echo "🚀 Lanzando Orquestador Maestro FIS v8 (HITL Interface)..."
if [ ! -f "$ORQUESTADOR" ]; then
    echo "import streamlit as st; st.title('FIS v8.1: Orquestador Maestro')" > $ORQUESTADOR
fi

# Matar procesos previos en el puerto 8501 para evitar conflictos
fuser -k 8501/tcp 2>/dev/null

streamlit run $ORQUESTADOR --server.address 0.0.0.0 --server.port 8501 &
STREAMLIT_PID=$!
sleep 4

# 7. Terminal de Control Interactiva para el Auditor
echo "🕵️  Terminal de Auditoría v8.1 Activa | Auditor: Ing. Fredy Sarmiento."
echo "🔄 Sincronizado con entorno Conda: $ENTORNO"

COMANDOS_INICIO="
source $CONDA_BASE/etc/profile.d/conda.sh; 
conda activate $ENTORNO; 
export PYTHONPATH=\$PYTHONPATH:$PROJ_DIR;
echo '--------------------------------------------------';
echo '📊 ESTADO DEL REPOSITORIO SLN_FIS4 (v8.1):';
ls -F; 
echo '--------------------------------------------------';
echo '📁 CAPAS ACTIVAS:';
echo ' - FIS: Lógica de Utilidad (U)';
echo ' - CINTA: Persistencia Estigmérgica';
echo ' - ORIGENDATOS: Insumos Maestro UR';
echo '--------------------------------------------------';
echo '💡 TIP: Use \"kill $STREAMLIT_PID\" para detener el Orquestador.';
"

exec bash --init-file <(echo "$COMANDOS_INICIO")