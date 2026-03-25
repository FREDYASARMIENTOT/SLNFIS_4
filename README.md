# SLN_FIS4: Simbiomémesis v8.0 🏫🧬

**Proyecto de Investigación - Maestría ICT - Universidad del Rosario**

## 📑 Resumen
SLN_FIS4 es la implementación avanzada del Framework de Ingeniería Simbiomemésica (FIS v8). Su objetivo es optimizar el costeo ABC mediante un enjambre de agentes especializados que coevolucionan con el experto humano sobre una **Cinta Estigmérgica Inmutable**.

## 📂 Arquitectura del Proyecto
- `FIS/`: Lógica central de la utilidad simbiótica $U$.
- `CINTA/`: Motor de persistencia de mensajes y estados.
- `PROCESOMODELADO/`: Algoritmos de costeo ABC para la UR.
- `ORIGENDATOS/`: Insumos maestros (Facultades, Programas, Costos).
- `PINECONE/`: Gestión de memoria semántica de largo plazo.

## 🚀 Ejecución
Para iniciar el ecosistema en Kali-WSL:
```bash
chmod +x init_slnfis4_v8.sh
./init_slnfis4_v8.sh
Ecuación de Estado$$U = \Sigma \cdot x_1 \cdot \left( \frac{ME + C_{bi}}{1 + x_2 + x_3} \right)$$
---

### 5. Script Maestro: `init_slnfis4_v8.sh`
He actualizado la lógica para que respete el nombre de su entorno `venvFIS_Rosario` y la nueva ruta.

```bash
#!/bin/bash
# =============================================================================
# PROYECTO: SLN_FIS4 (FIS v8.0) - UNIVERSIDAD DEL ROSARIO
# =============================================================================

ENTORNO="venvFIS_Rosario"
ORQUESTADOR="fis_orquestador_v8.py"
PROJ_DIR="/home/fredyast/projects/SLNFIS_4"

echo "🏛️ Iniciando Ecosistema Symbiomemesis v8.0 (SLN_FIS4)..."

# 1. Validación de Carpeta
cd $PROJ_DIR || exit 1

# 2. Localización de Conda
CONDA_BASE=$(conda info --base 2>/dev/null)
[ -z "$CONDA_BASE" ] && CONDA_BASE="/home/fredyast/miniconda3"
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 3. Activación y Lanzamiento
conda activate $ENTORNO
echo "🚀 Ejecutando Orquestador en segundo plano..."
streamlit run $ORQUESTADOR --server.address 0.0.0.0 &

# 4. Terminal Interactiva
COMANDOS="
source $CONDA_BASE/etc/profile.d/conda.sh; 
conda activate $ENTORNO; 
echo '--------------------------------------------------';
echo '🕵️ AUDITOR FREDY: AMBIENTE LISTO EN SLNFIS_4';
echo '--------------------------------------------------';
"
exec bash --init-file <(echo "$COMANDOS")