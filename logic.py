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
    



def calcular_balance_total(registros):
    total = 0 # 1 nivel de sangría (4 espacios)
    for moto in registros:
        # 2 niveles de sangría (8 espacios)
        servicios = moto.get('Mantenimientos', []) or moto.get('historial', [])
        for s in servicios:
            # 3 niveles de sangría (12 espacios)
            try:
                # 4 niveles de sangría (16 espacios)
                total += float(s.get('Costo', 0))
            except (ValueError, TypeError):
                continue
    return total # Regresa al nivel 1 (4 espacios)



def preparar_ingreso_cliente(datos_formulario):
    """
    Toma los datos del formulario y los organiza 
    para que el JSON siempre tenga la misma estructura.
    """
    placa = datos_formulario.get('placa', '').upper().strip()
    nuevo_registro = {
        "placa": placa,
        "dueño": datos_formulario.get('dueño', '').strip(),
        "telefono": datos_formulario.get('telefono', '').strip(),
        "moto": datos_formulario.get('moto', '').strip(),
        "km_actual": int(datos_formulario.get('km_actual') or 0),
        "km_proximo_mantenimiento": int(datos_formulario.get('km_prox') or 0),
        "fecha_ingreso": datetime.now().strftime("%d/%m/%Y"),
        "Mantenimientos": []
    }
    return nuevo_registro
