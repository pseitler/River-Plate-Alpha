# ============================================================
#  CONFIGURATION FILE — metals_model/config.py
# ============================================================
# Define las rutas y nombres de archivos para el modelo.
# IMPORTANTE: Todos los archivos deben estar en la carpeta 'data'.
# ============================================================

import os

# 1. DIRECTORIOS BASE
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# Aseguramos que las carpetas existan al importar el archivo
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

# 2. NOMBRES DE ARCHIVOS EXACTOS (Ubicados en carpeta 'data')
# ------------------------------------------------------------
# Ledger transaccional
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")

# 3. ARCHIVOS DE SALIDA (PUBLIC/VERCEL)
# ------------------------------------------------------------
HTML_REPORT_FILE = os.path.join(PUBLIC_DIR, "index.html")
XLSX_REPORT_FILE = os.path.join(PUBLIC_DIR, "reporte_semanal.xlsx")

# ============================================================
# END OF CONFIG FILE
# ============================================================