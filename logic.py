# **************************************************************
# BLOQUE: IMPORTS EXISTENTES
# **************************************************************
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from pymongo import MongoClient
from reportlab.lib.utils import ImageReader




# **************************************************************
# CONFIGURACIÓN DE NUBE 
# **************************************************************
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://admin:sereunprogramador999@mototech-db.c9q0e7q.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db = client['MotoTech-DB']
motos_col = db['clientes']






# **************************************************************
# BLOQUE: LOCALIZACIÓN DE LA BASE DE DATOS
# **************************************************************
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(BASE_DIR, "registros.json")

# -----------------------------------------------------------
# CONSTANTE DE NEGOCIO
# -----------------------------------------------------------
MARGEN_ALERTA = 5000





# **************************************************************
# MOTOR DE PERSISTENCIA CLOUD (EXTRACCIÓN Y NORMALIZACIÓN)
# Función: Sincroniza la base de datos remota con el sistema local,
#          asegurando la integridad de los campos de mantenimiento.
# **************************************************************


def cargar_registros():
    """Recupera los registros directamente desde MongoDB Atlas."""
    try:
        # Traemos todo de la nube, ignorando el ID interno de Mongo
        registros = list(motos_col.find({}, {'_id': 0}))
        
        # Mantenemos tu lógica de reparación por si hay datos viejos
        for moto in registros:
            if 'fecha_entrada' not in moto:
                moto['fecha_entrada'] = "Previo 2026"
            if 'Mantenimientos' not in moto:
                moto['Mantenimientos'] = []
        return registros
    except Exception as e:
        print(f"❌ Error al cargar desde MongoDB: {e}")
        return []





# **************************************************************
# MOTOR DE PERSISTENCIA CLOUD (ESCRITURA Y SINCRONIZACIÓN)
# Función: Ejecuta un ciclo de limpieza y actualización masiva en 
#          la nube para garantizar la integridad del historial.
# **************************************************************


def guardar_registros(registros):
    """Sincroniza la lista completa con la base de datos en la nube."""
    try:
        # Borramos lo anterior para evitar duplicados y subimos lo nuevo
        motos_col.delete_many({})
        if registros:
            motos_col.insert_many(registros)
        print("💾 Datos sincronizados en MongoDB Atlas con éxito")
        return True
    except Exception as e:
        print(f"❌ Error al guardar en MongoDB: {e}")
        return False





# **************************************************************
# BLOQUE: LÓGICA DE ALERTAS (NUEVO PARA APP.PY)
# **************************************************************


def marcar_alerta(moto):
    """Determina si una moto necesita mantenimiento (Margen 500km)."""
    # --- SUB-BLOQUE: CÁLCULO DE DIFERENCIA ---
    # Realiza la operación matemática entre el kilometraje actual y el objetivo de mantenimiento.
    try:
        km_p = int(moto.get('km_proximo_mantenimiento', 0))
        km_a = int(moto.get('km_actual', 0))
        
        # --- SUB-BLOQUE: EVALUACIÓN BOOLEANA ---
        # Retorna Verdadero solo si la diferencia es igual o menor a 500 kilómetros.
        return (km_p - km_a) <= 500
    except:
        return False
    




def calcular_balance_total(registros):
    # --- SUB-BLOQUE: INICIALIZACIÓN DE CONTADOR ---
    # Establece el punto de partida del balance financiero en cero.
    total = 0 
    
    # --- SUB-BLOQUE: RECORRIDO DE HISTORIALES ---
    # Navega a través de cada moto y extrae sus mantenimientos o historial antiguo.
    for moto in registros:
        servicios = moto.get('Mantenimientos', []) or moto.get('historial', [])
        
        # --- SUB-BLOQUE: SUMATORIA DE COSTOS ---
        # Itera sobre cada servicio técnico realizado y acumula el valor en la variable total.
        for s in servicios:
            try:
                # Se realiza conversión a float para permitir decimales en los precios.
                total += float(s.get('Costo', 0))
            except (ValueError, TypeError):
                # Si el costo no es un número válido, lo ignora y continúa con el siguiente.
                continue
    return total





def preparar_ingreso_cliente(datos_formulario):
    """
    Toma los datos del formulario y los organiza 
    para que el JSON siempre tenga la misma estructura.
    """
    # --- SUB-BLOQUE: LIMPIEZA DE DATOS ---
    # Formatea la placa a mayúsculas y elimina espacios innecesarios en los textos.
    placa = datos_formulario.get('placa', '').upper().strip()
    
    # --- SUB-BLOQUE: CONSTRUCCIÓN DE OBJETO ---
    # Crea el diccionario estandarizado con la fecha automática del sistema y valores numéricos limpios.
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