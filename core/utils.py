# ============================================================
#  UTILITIES — metals_model/core/utils.py
# ============================================================
# Herramientas de soporte para validación y limpieza de datos.
# ============================================================

import os
import pandas as pd

# ------------------------------------------------------------
# BLOQUE 1: GESTIÓN DE DIRECTORIOS
# ------------------------------------------------------------
def ensure_directories_exist(directories):
    """Crea las carpetas necesarias si no existen (data, reports)."""
    for d in directories:
        if not os.path.exists(d):
            os.makedirs(d)

# ------------------------------------------------------------
# BLOQUE 2: VALIDACIÓN DE ARCHIVOS
# ------------------------------------------------------------
def validate_files_exist(file_list):
    """Asegura que todos los archivos (Excel y CSV) estén en su sitio."""
    all_exist = True
    for f in file_list:
        if not os.path.exists(f):
            print(f"[ERROR] ARCHIVO NO ENCONTRADO: {f}")
            all_exist = False
    return all_exist

# ------------------------------------------------------------
# BLOQUE 3: LIMPIEZA NUMÉRICA INTELIGENTE (ACTUALIZADO)
# Fundamental para evitar errores de cálculo por formatos de 
# miles y decimales mixtos.
# ------------------------------------------------------------
def clean_numeric(df, cols):
    """
    Limpia formatos numéricos de texto de manera inteligente.
    Detecta si el punto o la coma se están usando como decimales,
    lo que evita inflar los valores del portafolio.
    """
    for col in cols:
        if col in df.columns:
            # 1. Convertimos a texto y quitamos símbolos de moneda o espacios
            s = df[col].astype(str).str.replace(r'[$\s%]', '', regex=True)
            
            # 2. Analizador lógico número por número
            def parse_value(val):
                if pd.isna(val) or str(val).lower() == 'nan':
                    return float('nan')
                val = str(val).strip()
                
                # Caso A: Tiene coma y punto (Ej: 1,000.50 o 1.000,50)
                if '.' in val and ',' in val:
                    if val.rfind('.') > val.rfind(','):
                        # El punto está al final -> Es decimal (Formato US)
                        return float(val.replace(',', ''))
                    else:
                        # La coma está al final -> Es decimal (Formato Europeo)
                        return float(val.replace('.', '').replace(',', '.'))
                        
                # Caso B: Solo tiene comas (Ej: 40,77 o 1,000,000)
                elif ',' in val:
                    if val.count(',') == 1:
                        # Si hay una sola coma, asumimos que es decimal
                        return float(val.replace(',', '.'))
                    else:
                        # Varias comas, son separadores de miles
                        return float(val.replace(',', ''))
                        
                # Caso C: Solo tiene puntos (Ej: 15533.37 de tu fichero)
                else:
                    try:
                        # Python nativamente entiende el punto como decimal
                        return float(val)
                    except:
                        return float('nan')
                        
            # 3. Aplicamos la regla a toda la columna
            df[col] = s.apply(parse_value)
    return df