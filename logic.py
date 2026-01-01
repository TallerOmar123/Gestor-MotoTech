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

# **************************************************************
# BLOQUE: FUNCIÓN GENERAR_PDF_CLIENTE
# **************************************************************
def generar_pdf_cliente(moto):
    carpeta = "reportes"
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    nombre_archivo = f"Reporte_{moto['placa']}.pdf"
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    
    c = canvas.Canvas(ruta_completa, pagesize=letter)
    ancho, alto = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, alto - 50, "REPORTE TÉCNICO MOTO-TECH")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, alto - 80, f"Placa: {moto['placa']}")
    c.drawString(50, alto - 100, f"Cliente: {moto['dueño']}")
    c.drawString(50, alto - 120, f"Moto: {moto.get('moto', 'N/A')}")
    c.drawString(50, alto - 140, f"Kilometraje Actual: {moto['km_actual']} km")
    
    c.line(50, alto - 150, 550, alto - 150)
    
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, alto - 180, "HISTORIAL DE SERVICIOS:")
    
    y = alto - 210
    c.setFont("Helvetica", 10)
    
    servicios = moto.get('Mantenimientos', []) or moto.get('historial', [])
    
    if not servicios:
        c.drawString(70, y, "No hay servicios registrados previamente.")
    else:
        for serv in servicios:
            texto_servicio = f"- {serv.get('Fecha', 'S/F')}: {serv.get('Descripcion', 'Sin descripción')} (${serv.get('Costo', 0)})"
            c.drawString(70, y, texto_servicio)
            y -= 20
    
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 30, "Documento generado automáticamente por Sistema MotoTech 2025")
    c.save()
    
    return ruta_completa