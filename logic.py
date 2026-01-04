# **************************************************************
# BLOQUE: IMPORTS EXISTENTES
# **************************************************************
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime





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
    # Definimos la ruta dentro de la función por seguridad
    ruta = 'registros.json'
    
    # --- SUB-BLOQUE: VALIDACIÓN DE ARCHIVO ---
    # Se asegura de que el archivo exista y sea legible antes de intentar procesarlo.
    try:
        import os
        import json
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                
                # --- SUB-BLOQUE: NORMALIZACIÓN DE FORMATO ---
                # Verifica que los datos cargados sean una lista; de lo contrario, limpia la base de datos.
                if not isinstance(datos, list):
                    return []
                
                # --- SUB-BLOQUE: REPARACIÓN Y COMPATIBILIDAD ---
                # Recorre cada objeto para inyectar campos faltantes, evitando errores en versiones nuevas del software.
                for moto in datos:
                    if 'fecha_entrada' not in moto:
                        moto['fecha_entrada'] = "Previo 2026"
                    if 'Mantenimientos' not in moto:
                        moto['Mantenimientos'] = []
                return datos
        return []
        
    # --- SUB-BLOQUE: CONTROL DE EXCEPCIONES ---
    # Captura errores de lectura o sintaxis en el JSON y retorna una lista segura para que la app no colapse.
    except Exception as e:
        print(f"Error al cargar registros: {e}")
        return []





def guardar_registros(registros):
    """Guarda la lista de registros en el JSON."""
    # --- SUB-BLOQUE: ESCRITURA SEGURA ---
    # Intenta abrir el archivo en modo escritura con codificación UTF-8 para soportar caracteres especiales.
    try:
        with open(ARCHIVO, 'w', encoding='utf-8') as file:
            # --- SUB-BLOQUE: SERIALIZACIÓN ---
            # Convierte los objetos de Python a texto JSON con indentación para facilitar auditorías manuales.
            json.dump(registros, file, indent=4, ensure_ascii=False)
        return True
        
    # --- SUB-BLOQUE: GESTIÓN DE FALLOS DE DISCO ---
    # Informa si hubo un problema físico o de permisos al intentar guardar la información.
    except Exception as e:
        print(f"Error al guardar: {e}")
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