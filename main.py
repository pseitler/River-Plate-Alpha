# ============================================================
#  MAIN ENTRY POINT — metals_model/main.py
# ============================================================
import sys
import traceback
from core.engine import run_week
from core.utils import ensure_directories_exist, validate_files_exist
from config import (
    BASE_DIR, DATA_DIR, PUBLIC_DIR, 
    TRANSACTIONS_FILE
)

def main():
    print("\n===================================================")
    print("   RIVER PLATE ALPHA — QUANT CORE   ")
    print("===================================================\n")

    # 1. Asegurar carpetas
    ensure_directories_exist([BASE_DIR, DATA_DIR, PUBLIC_DIR])

    # 2. Lista de archivos requeridos (Todos en la carpeta 'data')
    required_files = [TRANSACTIONS_FILE]

    # 3. Validar existencia
    print("[INFO] Verificando archivos requeridos...")
    if not validate_files_exist(required_files):
        print("\n[ERROR] Faltan archivos en la carpeta 'data'.")
        sys.exit(1)
    print("[INFO] Archivos requeridos encontrados.")

    # 4. Ejecutar análisis
    try:
        print("[INFO] Iniciando run_week()...")
        results = run_week()
        print("\n[OK] Reportes generados en la carpeta 'public' (Lista para Vercel).")
    except Exception as e:
        print(f"\n[ERROR CRITICO EXCEPCION]: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()