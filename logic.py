# **************************************************************
# BLOQUE: IMPORTS EXISTENTES
# **************************************************************
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# **************************************************************
# BLOQUE: LOCALIZACIÓN DE LA BASE DE DATOS
# **************************************************************
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(BASE_DIR, "registros.json")

# -----------------------------------------------------------
# CONSTANTE DE NEGOCIO
# -----------------------------------------------------------
MARGEN_ALERTA = 5000 

# -----------------------------------------------------------
# FUNCIONES DE PERSISTENCIA
# -----------------------------------------------------------
def cargar_registros():
    """Carga los registros siempre como una LISTA []."""
    try:
        if os.path.exists(ARCHIVO):
            with open(ARCHIVO, 'r', encoding='utf-8') as file:
                datos = json.load(file)
                return datos if isinstance(datos, list) else []
        return []
    except Exception as e:
        print(f"Error al cargar: {e}")
        return []

def guardar_registros(registros):
    """Guarda la lista de registros en el JSON."""
    try:
        with open(ARCHIVO, 'w', encoding='utf-8') as file:
            json.dump(registros, file, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

# **************************************************************
# BLOQUE: LÓGICA DE ALERTAS (NUEVO PARA APP.PY)
# **************************************************************
def marcar_alerta(moto):
    """Determina si una moto necesita mantenimiento (Margen 500km)."""
    try:
        km_p = int(moto.get('km_proximo_mantenimiento', 0))
        km_a = int(moto.get('km_actual', 0))
        return (km_p - km_a) <= 500
    except:
        return False

