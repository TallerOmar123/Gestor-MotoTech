# **************************************************************
# BLOQUE 0: NÚCLEO DE LIBRERÍAS Y DEPENDENCIAS
# Función: Carga el motor Web (Flask), herramientas de archivos,
#          generador de PDFs (ReportLab) y lógica del negocio.
# **************************************************************

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import json
import urllib.parse
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import logic
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
from reportlab.lib.utils import ImageReader
import requests
from io import BytesIO



# --- CONFIGURACIÓN DE MONGO ---
# En Render, usaremos una variable de entorno, pero para probar localmente:
# Así debe verse tu línea de conexión:
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://admin:sereunprogramador999@mototech-db.c9q0e7q.mongodb.net/?retryWrites=true&w=majority")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['MotoTech-DB']
    motos_col = db['clientes']
    # Esto verifica si la conexión es exitosa al arrancar
    client.server_info() 
    print("✅ Conexión a MongoDB Atlas exitosa")
except Exception as e:
    print(f"❌ Error de conexión: {e}")





    # --- CONFIGURACIÓN DE CLOUDINARY ---
# Permite que la app suba imágenes a tu cuenta personal de Cloudinary
cloudinary.config( 
  cloud_name = "dk9ionytk", 
  api_key = "259288167272924", 
  api_secret = "fg3twnelW_jzLVFas4t2GrDGGgQ",
  secure = True
)





# **************************************************************
# BLOQUE 1: INICIALIZACIÓN Y GESTIÓN DE RECURSOS FÍSICOS
# Función: Configura la identidad de la App, define la base de
#          datos JSON y asegura la existencia de carpetas.
# **************************************************************

# --- 1. IDENTIDAD Y SEGURIDAD DEL SISTEMA ---
# Establece la clave de cifrado y el archivo de base de datos.
app = Flask(__name__)
app.secret_key = "mototech_key_2025"
RUTA_JSON = 'registros.json'

# --- 2. ARQUITECTURA DE DIRECTORIOS ---
# Define las rutas donde se almacenarán archivos y fotos.
CARPETA_FACTURAS = os.path.join('static', 'facturas')
CARPETA_FOTOS = os.path.join('static', 'fotos_mantenimiento')

# --- 3. AUTOMATIZACIÓN DE INFRAESTRUCTURA ---
# Crea físicamente las carpetas en el PC si aún no existen.
for carpeta in [CARPETA_FACTURAS, CARPETA_FOTOS]:
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

# --- 4. CONFIGURACIÓN DE CARGA (UPLOADS) ---
# Vincula la carpeta de facturas con la configuración de Flask.
app.config['UPLOAD_FOLDER'] = CARPETA_FACTURAS


# **************************************************************
# BLOQUE 2: GESTOR DE PERSISTENCIA CLOUD (LECTURA)
# Función: Establece comunicación con MongoDB Atlas para extraer
#          la información y sincronizarla con el estado local.
# **************************************************************

def cargar_registros():
    """Recupera los registros desde MongoDB Atlas."""
    try:
        # Traemos todo de la nube, ignorando el campo '_id' interno de Mongo
        registros = list(motos_col.find({}, {'_id': 0}))
        return registros
    except Exception as e:
        print(f"❌ Error al cargar desde MongoDB: {e}")
        return []


# **************************************************************
# BLOQUE 3: MOTOR DE SINCRONIZACIÓN EN LA NUBE (ESCRITURA)
# Función: Transmite y asegura los datos en el clúster remoto,
#          garantizando que la información sea persistente y eterna.
# **************************************************************

def guardar_registros(registros):
    """Sincroniza la base de datos en la nube."""
    try:
        # Borramos el contenido actual y subimos la lista actualizada
        # Esto mantiene tu lógica de 'sobrescribir' que usabas en el JSON
        motos_col.delete_many({})
        if registros:
            motos_col.insert_many(registros)
        print("💾 Datos sincronizados en MongoDB Atlas")
    except Exception as e:
        print(f"❌ Error al guardar en MongoDB: {e}")


# **************************************************************
# BLOQUE 4: INTELIGENCIA PREVENTIVA Y GESTIÓN DE ALERTAS
# Función: Calcula el desgaste por kilometraje y clasifica el
#          estado de urgencia para cada motocicleta.
# **************************************************************

def revisar_mantenimientos_logica():
    """Analiza cada moto para determinar si requiere mantenimiento preventivo por kilometraje."""
    todos = cargar_registros()
    proximos = []

    # --- SUB-BLOQUE: ALGORITMO DE COMPARACIÓN ---
    # Cruza el odómetro actual contra el umbral de servicio programado.
    for moto in todos:
        try:
            km_p = int(moto.get('km_proximo_mantenimiento', 0))
            km_a = int(moto.get('km_actual', 0))
            faltan = km_p - km_a

            # --- SUB-BLOQUE: DIAGNÓSTICO Y SEMAFORIZACIÓN ---
            # Define la severidad de la alerta (Danger/Warning) según el remanente de km.
            if faltan <= 500:
                # Asigna colores para la interfaz visual (Rojo para crítico, Amarillo para aviso)
                moto['clase_alerta'] = 'table-danger' if faltan <= 100 else 'table-warning'

                if faltan <= 0:
                    moto['estado'] = '¡VENCIDO!'
                elif faltan <= 100:
                    moto['estado'] = '¡URGENTE!'
                else:
                    moto['estado'] = 'AVISO'

                moto['faltan_km'] = faltan
                proximos.append(moto)

        except Exception as e:
            print(
                f"Error en diagnóstico de mantenimiento (Placa {moto.get('placa')}): {e}")
            continue

    return proximos


# **************************************************************
# BLOQUE 5: INTERFAZ DE CONTROL CENTRAL (DASHBOARD)
# Función: Orquestador principal que consolida registros,
#          gestión de ediciones y métricas financieras.
# **************************************************************

@app.route('/')
def index():
    """Prepara y carga la página principal con tablas, alertas y balance financiero."""
    todos = logic.cargar_registros()

    # --- SUB-BLOQUE: MOTOR DE BÚSQUEDA PARA EDICIÓN ---
    # Captura la placa seleccionada y localiza al cliente para editar sus datos.
    placa_a_editar = request.args.get('editar_placa')
    cliente_a_editar = None
    if placa_a_editar:
        cliente_a_editar = next(
            (c for c in todos if c.get('placa') == placa_a_editar), None)

    # --- SUB-BLOQUE: ACTUALIZACIÓN DE ALERTAS ---
    # Ejecuta el análisis preventivo de kilometraje antes de mostrar la página.
    proximos = revisar_mantenimientos_logica()

    # --- SUB-BLOQUE: ANÁLISIS FINANCIERO INTEGRADO ---
    # Consolida el balance de ingresos totales procesados por el taller.
    try:
        ingresos_totales = logic.calcular_balance_total(todos)
        if ingresos_totales is None:
            ingresos_totales = 0
    except Exception as e:
        print(f"Error crítico en cálculo de balance: {e}")
        ingresos_totales = 0

    # --- SUB-BLOQUE: DESPLIEGE VISUAL ---
    # Envía toda la información procesada a la plantilla HTML 'index.html'.
    return render_template('index.html',
                        todos=todos,
                        proximos=proximos,
                        cliente_a_editar=cliente_a_editar,
                        placa_a_editar=placa_a_editar,
                        ingresos_totales=ingresos_totales)


# **************************************************************
# BLOQUE 6: MOTOR DE REGISTRO, ACTUALIZACIÓN E INVENTARIO
# Función: Gestiona la entrada de vehículos, captura datos de 
#          inventario y procesa archivos de facturación externa.
# **************************************************************

@app.route('/agregar_cliente_web', methods=['POST'])
def agregar_cliente_web():
    """Recibe datos del formulario para crear un nuevo cliente o actualizar uno existente."""
    datos = cargar_registros()

    # --- SUB-BLOQUE: NORMALIZACIÓN Y CAPTURA DE DATOS ---
    # Transforma entradas a mayúsculas y asegura formatos numéricos para cálculos.
    placa = request.form.get('placa').upper().strip()
    dueño = request.form.get('dueño')
    telefono = request.form.get('telefono')
    moto = request.form.get('moto')
    km_actual = int(request.form.get('km_actual') or 0)
    km_prox = int(request.form.get('km_prox') or 0)
    
    # NUEVOS CAMPOS TÉCNICOS (Hoja de Entrada)
    notas_ingreso = request.form.get('notas_ingreso')
    tipo_servicio = request.form.get('tipo_servicio')
    gasolina = request.form.get('inv_gasolina')

    # --- SUB-BLOQUE: GESTIÓN DE LIQUIDACIÓN Y ARCHIVOS ---
    # Gestión de liquidación y archivos
    detalle_repuestos = request.form.get('detalle_repuestos')
    valor_total_repuestos = request.form.get('valor_total_repuestos')

    # Procesamiento de evidencia física (Foto de la Factura)
    foto_f = request.files.get('foto_factura')
    nombre_foto_factura = ""

    if foto_f and foto_f.filename != '':
        try:
            # --- SUBIDA OPTIMIZADA A LA NUBE ---
            upload_result = cloudinary.uploader.upload(
                foto_f, 
                folder="MotoTech_Facturas",
                transformation=[
                    {'width': 1000, 'crop': "limit"}, # Limita el ancho a 1000px (suficiente para ver detalles)
                    {'quality': "auto"},              # Comprime la foto inteligentemente sin que se note
                    {'fetch_format': "auto"}          # Convierte a formatos modernos como WebP automáticamente
                ]
            )
            
            # Aquí guardamos el LINK DE INTERNET optimizado
            nombre_foto_factura = upload_result['secure_url']
            print(f"📸 Foto optimizada en la nube: {nombre_foto_factura}")
        except Exception as e:
            print(f"❌ Error Cloudinary: {e}")

    # Lógica de Checkboxes (Conversión de estado HTML a lenguaje de taller)
    inv_espejos = "SÍ" if request.form.get('inv_espejos') else "NO"
    inv_direccionales = "SÍ" if request.form.get('inv_direccionales') else "NO"
    inv_maletero = "SÍ" if request.form.get('inv_maletero') else "NO"

    # --- SUB-BLOQUE: BÚSQUEDA Y ACTUALIZACIÓN (UPSERT) ---
    cliente_existente = next((c for c in datos if c['placa'] == placa), None)

    if cliente_existente:
        # ACTUALIZACIÓN DE HISTORIAL EXISTENTE
        actualizacion = {
            "dueño": dueño, "telefono": telefono, "moto": moto,
            "km_actual": km_actual, "km_proximo_mantenimiento": km_prox,
            "notas_ingreso": notas_ingreso, "tipo_servicio": tipo_servicio,
            "gasolina": gasolina,
            "inventario": {
                "espejos": inv_espejos, "direccionales": inv_direccionales, "maletero": inv_maletero
            },
            "detalle_repuestos": detalle_repuestos,
            "valor_total_repuestos": valor_total_repuestos
        }
        
        # Solo actualizamos el link de la foto si realmente se subió una nueva
        if nombre_foto_factura:
            actualizacion["foto_factura"] = nombre_foto_factura
            
        cliente_existente.update(actualizacion)
        flash(f"✅ Datos de {placa} actualizados correctamente", "success")
        
    else:
        # CREACIÓN DE REGISTRO MAESTRO NUEVO
        nuevo_cliente = {
            "placa": placa, "dueño": dueño, "telefono": telefono, "moto": moto,
            "km_actual": km_actual, "km_proximo_mantenimiento": km_prox,
            "notas_ingreso": notas_ingreso, "tipo_servicio": tipo_servicio,
            "gasolina": gasolina,
            "inventario": {
                "espejos": inv_espejos, "direccionales": inv_direccionales, "maletero": inv_maletero
            },
            "detalle_repuestos": detalle_repuestos,
            "valor_total_repuestos": valor_total_repuestos,
            "foto_factura": nombre_foto_factura, # Aquí se guarda el link de Cloudinary
            "Mantenimientos": []
        }
        datos.append(nuevo_cliente)
        flash(f"🏍️ Moto {placa} registrada con éxito", "success")

    # --- SUB-BLOQUE: CIERRE DE TRANSACCIÓN ---
    # 1. Guardamos los datos en MongoDB Atlas
    guardar_registros(datos)
    
    # 2. Preparamos el mensaje que verá el usuario en pantalla
    flash("✅ Sincronizado con la Nube correctamente", "success")
    
    # 3. Finalizamos la función y volvemos a la página principal
    return redirect(url_for('index'))



# **************************************************************
# BLOQUE 7: MÓDULO TÉCNICO - HISTORIAL Y MULTIMEDIA
# Función: Orquestador de servicios mecánicos. Gestiona el ingreso
#          de mantenimientos, carga de evidencias y diagnóstico.
# **************************************************************

@app.route('/mantenimiento', methods=['POST'])
def agregar_mantenimiento_web():
    """Registra la intervención técnica y actualiza los indicadores del vehículo."""
    placa = request.form.get('placa_mantenimiento').upper()
    registros = cargar_registros()
    cliente = next((m for m in registros if m.get('placa') == placa), None)

    if cliente:
        costo_actual = int(request.form.get('costo_mantenimiento') or 0)

        # --- SUB-BLOQUE: GESTIÓN DE EVIDENCIA FOTOGRÁFICA ---
        # Procesa ráfagas de imágenes asignando metadatos temporales para unicidad.
        lista_fotos = []
        if 'fotos' in request.files:
            archivos = request.files.getlist('fotos')
            for foto in archivos:
                if foto.filename != '':
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_seguro = secure_filename(f"{placa}_{timestamp}_{foto.filename}")
                    foto.save(os.path.join(CARPETA_FOTOS, nombre_seguro))
                    lista_fotos.append(nombre_seguro)

        # --- SUB-BLOQUE: ESTRUCTURACIÓN DEL SERVICIO ---
        # Empaqueta los datos técnicos del mantenimiento realizado.
        nuevo = {
            "Fecha": request.form.get('fecha_mantenimiento'),
            "KM": int(request.form.get('km_mantenimiento') or 0),
            "Descripcion": request.form.get('descripcion_mantenimiento'),
            "Costo": costo_actual,
            "Fotos": lista_fotos
        }

        # --- SUB-BLOQUE: ACTUALIZACIÓN DE ESTADOS CRÍTICOS ---
        # Actualiza el semáforo técnico de los componentes de la motocicleta.
        cliente.update({
            'estado_aceite': request.form.get('aceite'),
            'freno_del': request.form.get('freno_del'),
            'freno_tras': request.form.get('freno_tras'),
            'liq_frenos': request.form.get('liq_frenos'),
            'lavado_carburador': request.form.get('lavado_carburador'),
            'filtro_bujia': request.form.get('filtro_bujia'),
            'engrase_tijera': request.form.get('engrase_tijera'),
            'mantenimiento_guayas': request.form.get('mantenimiento_guayas'),
            'estado_frenos': request.form.get('frenos'),
            'estado_electrico': request.form.get('electrico'),
            'estado_kit': request.form.get('kit_arrastre'),
            'estado_clutch': request.form.get('clutch'),
            'estado_barras': request.form.get('barras'),
            'ultimo_cobro': costo_actual
        })

        # --- SUB-BLOQUE: PERSISTENCIA Y CIERRE ---
        # Inyecta el registro en el historial y sincroniza el kilometraje actual.
        if 'Mantenimientos' not in cliente:
            cliente['Mantenimientos'] = []
        
        cliente['Mantenimientos'].append(nuevo)
        cliente['km_actual'] = nuevo['KM']
        
        guardar_registros(registros)
        flash(f"✅ ¡Éxito! Servicio guardado para {placa}", "warning")

        return redirect(url_for('index'))


# **************************************************************
# BLOQUE 8: CONTROL DE FLUJO PARA EDICIÓN (INTERFACE)
# Función: Gestiona la transición de la interfaz hacia el modo
#          de actualización de registros existentes.
# **************************************************************

@app.route('/editar/<placa>')
def editar_cliente(placa):
    """Activa el estado de edición en el Dashboard para un vehículo específico."""
    
    # --- SUB-BLOQUE: VERIFICACIÓN DE INTEGRIDAD ---
    # Valida la existencia del registro antes de conceder acceso a la edición.
    registros = logic.cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if moto:
        # --- SUB-BLOQUE: REDIRECCIONAMIENTO CON PARÁMETROS ---
        # Envía la placa de vuelta al index para activar los campos de edición.
        return redirect(url_for('index', editar_placa=placa))

    # --- SUB-BLOQUE: GESTIÓN DE ERRORES ---
    # Notifica al usuario si el registro fue movido o eliminado previamente.
    flash("❌ Moto no encontrada en el sistema", "danger")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 9: MOTOR DE GENERACIÓN DE DOCUMENTACIÓN TÉCNICA (PDF)
# Función: Gestiona la creación de informes profesionales, 
#          exportando el diagnóstico a un formato descargable.
# **************************************************************

@app.route('/descargar_reporte/<placa>')
def descargar_reporte(placa):
    """Genera el documento PDF con el diagnóstico técnico y lo envía al navegador."""
    registros = cargar_registros()
    moto_encontrada = next(
        (m for m in registros if m.get('placa') == placa), None)

    # --- SUB-BLOQUE: PROCESAMIENTO Y SALIDA DE ARCHIVO ---
    # Si el registro es válido, invoca la lógica de renderizado PDF 
    # y prepara el archivo para la transferencia segura al cliente.
    if moto_encontrada:
        ruta_pdf = logic.generar_pdf_cliente(moto_encontrada)
        return send_file(ruta_pdf, as_attachment=True)

    # --- SUB-BLOQUE: CONTROL DE EXCEPCIONES ---
    # En caso de no localizar el registro, se dispara una alerta de sistema.
    flash("Error: No se pudo localizar el registro para generar el reporte.", "danger")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 10: GESTIÓN DE DEPURACIÓN Y ELIMINACIÓN DE REGISTROS
# Función: Ejecuta la remoción definitiva de activos del sistema
#          y garantiza la integridad de la persistencia de datos.
# **************************************************************

@app.route('/eliminar/<placa>')
def eliminar_cliente(placa):
    """Borra permanentemente la moto y todo su historial de la base de datos JSON."""
    
    # --- SUB-BLOQUE: LÓGICA DE FILTRADO DE SEGURIDAD ---
    # Reconstruye la estructura de datos excluyendo el identificador (placa) 
    # seleccionado, asegurando una depuración limpia en memoria.
    motos = cargar_registros()
    motos_actualizadas = [m for m in motos if m['placa'] != placa]
    
    # --- SUB-BLOQUE: SINCRONIZACIÓN DE BASE DE DATOS ---
    # Persiste los cambios en el archivo maestro y refresca la vista principal.
    guardar_registros(motos_actualizadas)
    
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 11: GESTIÓN DE DEPURACIÓN CRONOLÓGICA (HISTORIAL)
# Función: Permite la remoción selectiva de servicios individuales 
#          dentro del historial técnico de un vehículo.
# **************************************************************

@app.route('/eliminar_servicio/<placa>/<int:index>')
def eliminar_servicio(placa, index):
    """Elimina un mantenimiento específico usando su identificador de posición."""
    registros = cargar_registros()
    
    # --- SUB-BLOQUE: LOCALIZACIÓN DE REGISTRO MAESTRO ---
    # Identifica al propietario del historial antes de proceder con la edición.
    cliente = next((m for m in registros if m.get('placa') == placa), None)

    if cliente and 'Mantenimientos' in cliente:
        try:
            # --- SUB-BLOQUE: OPERACIÓN DE REMOCIÓN ---
            # Extrae el servicio mediante su índice y confirma la integridad del historial.
            servicio_eliminado = cliente['Mantenimientos'].pop(index)

            # --- SUB-BLOQUE: SINCRONIZACIÓN Y FEEDBACK ---
            # Actualiza la base de datos y notifica la fecha del registro removido.
            guardar_registros(registros)
            flash(
                f"🗑️ Servicio del {servicio_eliminado.get('Fecha')} eliminado", "info")
        
        except IndexError:
            # Captura de error en caso de que el índice ya no exista.
            flash("❌ Error de consistencia: No se encontró el registro a eliminar", "danger")

    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 12: INTEGRACIÓN DE COMUNICACIÓN EXTERNA (WHATSAPP API)
# Función: Automatiza la generación de notificaciones de salida,
#          formateo de costos y enlace dinámico de mensajería.
# **************************************************************

@app.route('/enviar_whatsapp/<placa>')
def enviar_whatsapp(placa):
    """Construye un protocolo de salida para avisar al cliente que su moto está lista."""
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if not moto:
        # --- SUB-BLOQUE: VALIDACIÓN DE DESTINO ---
        return "Error crítico: Identificador de vehículo no localizado", 404

    # --- SUB-BLOQUE: NORMALIZACIÓN FINANCIERA ---
    # Transforma el valor numérico en una representación monetaria estándar.
    cobro = moto.get('ultimo_cobro', 0)
    cobro_formateado = f"{cobro:,.0f}".replace(",", ".")

    # --- SUB-BLOQUE: COMPOSICIÓN DINÁMICA DEL MENSAJE ---
    # Estructura el cuerpo del mensaje utilizando sintaxis enriquecida de WhatsApp.
    texto = (
        f"✅ *MOTOTECH - NOTIFICACIÓN DE SALIDA*\n\n"
        f"Hola *{moto.get('dueño')}*,\n"
        f"Le informamos que el servicio técnico de su moto placa *{moto.get('placa')}* ha finalizado con éxito.\n\n"
        f"💰 *VALOR A PAGAR:* ${cobro_formateado}\n"
        f"📄 *REPORTE TÉCNICO:* Su informe detallado en PDF ya se encuentra disponible.\n\n"
        "Ya puede pasar al taller por su vehículo. ¡Gracias por confiar en nuestro servicio! 🏍️"
    )

    # --- SUB-BLOQUE: CODIFICACIÓN Y LIMPIEZA DE DATOS ---
    # Sanea el número telefónico y codifica el texto para transporte URL seguro.
    mensaje_codificado = urllib.parse.quote(texto)
    telefono = moto.get('telefono', '')
    telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
    
    # Construcción del punto de enlace (Endpoint) para la API de WhatsApp
    link_wa = f"https://wa.me/57{telefono_limpio}?text={mensaje_codificado}"
    
    return redirect(link_wa)


# **************************************************************
# BLOQUE 13: MOTOR GRÁFICO DE RENDERING PDF (REPORT ENGINE)
# Función: Construcción dinámica de informes técnicos, procesamiento
#          de matrices de estado, anexos multimedia y liquidación.
# **************************************************************

@app.route('/generar_pdf/<placa>')
def generar_pdf(placa):
    """Dibuja hoja por hoja el reporte técnico profesional con evidencia fotográfica."""
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if not moto:
        return "Error: Identificador de vehículo no localizado", 404

    # --- SUB-BLOQUE: PREPARACIÓN DE ACTIVOS MULTIMEDIA ---
    ultimas_fotos = []
    if moto.get('Mantenimientos'):
        ultimo_servicio = moto['Mantenimientos'][-1]
        # Buscamos de forma segura en mayúsculas y minúsculas
        evidencias = ultimo_servicio.get('fotos') or ultimo_servicio.get('Fotos') or []
        
        # Si es una lista (varias fotos), la usamos. Si es un solo texto (una foto), la metemos en una lista.
        if isinstance(evidencias, list):
            ultimas_fotos = evidencias
        elif evidencias:
            ultimas_fotos = [evidencias]

    # Configuración de rutas y lienzo (Canvas)
    nombre_archivo = f"Reporte_{placa}.pdf"
    ruta_pdf = os.path.join('static', nombre_archivo)
    c = canvas.Canvas(ruta_pdf, pagesize=letter)
    width, height = letter
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    # --- SUB-BLOQUE: BRANDING Y ENCABEZADO ---
    # Implementación de identidad visual y metadatos de cabecera.
    c.setFillColor(colors.HexColor("#1B2631"))
    c.rect(0, height - 80, width, 80, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 50, "MOTOTECH - REPORTE TÉCNICO")

    # Información Base del Cliente y Vehículo
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, f"CLIENTE: {moto.get('dueño')}")
    c.drawString(40, height - 130, f"PLACA: {moto.get('placa')}")
    c.drawString(350, height - 110, f"KM ACTUAL: {moto.get('km_actual')}")

    # --- SUB-BLOQUE: MÓDULO DE RECEPCIÓN TÉCNICA (INVENTARIO) ---
    c.setStrokeColor(colors.HexColor("#007bff"))
    c.rect(340, height - 160, 220, 45, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(345, height - 125, "RECEPCIÓN TÉCNICA:")

    c.setFont("Helvetica", 8)
    gas = moto.get('gasolina', 'No registrada')
    inv = moto.get('inventario', {})
    c.drawString(345, height - 140, f"⛽ Gasolina: {gas}")
    c.drawString(345, height - 153, 
                 f"🔎 Esp: {inv.get('espejos','NO')} | Luces: {inv.get('direccionales','NO')} | Mal: {inv.get('maletero','NO')}")

    # --- SUB-BLOQUE: MATRIZ DE DIAGNÓSTICO (TABLA TÉCNICA) ---
    # Itera sobre los sistemas críticos aplicando lógica de semáforo visual.
    y = height - 170
    items = [
        ("--- SISTEMA DE FRENOS ---", ""),
        ("Freno Delantero", moto.get('freno_del')),
        ("Freno Trasero", moto.get('freno_tras')),
        ("Líquido / Caliper", moto.get('liq_frenos')),
        ("--- MOTOR Y SINCRONIZACIÓN ---", ""),
        ("Aceite Motor", moto.get('estado_aceite')),
        ("Lavado Carburador", moto.get('lavado_carburador')),
        ("Filtro Aire / Bujía", moto.get('filtro_bujia')),
        ("--- CHASIS Y CONTROL ---", ""),
        ("Aceite Barras", moto.get('estado_barras')),
        ("Engrase Tijera", moto.get('engrase_tijera')),
        ("Mantenimiento Guayas", moto.get('mantenimiento_guayas')),
        ("Sistema Eléctrico", moto.get('estado_electrico'))
    ]

    for nombre, estado in items:
        if "---" in nombre:
            y -= 10
            c.setFillColor(colors.HexColor("#D5D8DC"))
            c.rect(40, y-5, 520, 15, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y, nombre)
            y -= 20
            continue

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(50, y, nombre)

        # Lógica de Colorimetría Técnica (Semáforo de Seguridad)
        color_celda = colors.white
        texto_prioridad = "S.D"
        if estado == "✅ Óptimo":
            color_celda = colors.lightgreen
            texto_prioridad = "OK - OPTIMO"
        elif estado == "⚠️ Pronto Cambio":
            color_celda = colors.yellow
            texto_prioridad = "SEGUIMIENTO"
        elif estado == "🚨 Urgente":
            color_celda = colors.tomato
            texto_prioridad = "CAMBIO URGENTE"

        c.setFillColor(color_celda)
        c.rect(400, y-5, 120, 15, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(460, y, texto_prioridad)
        y -= 20

    # --- SUB-BLOQUE: OBSERVACIONES Y LIQUIDACIÓN ---
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "OBSERVACIONES Y RECOMENDACIONES:")
    y -= 35
    
    c.setFillColor(colors.HexColor("#EBEDEF"))
    c.rect(40, y-45, 520, 55, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "LIQUIDACIÓN DE REPUESTOS / INSUMOS:")
    c.setFont("Helvetica", 9)
    c.drawString(50, y-15, f"Detalle: {moto.get('detalle_repuestos', 'N/A')}")
    c.drawString(50, y-30, f"Total Repuestos: $ {moto.get('valor_total_repuestos', '0')}")

    # ==========================================================
    # --- BLOQUE DE DIAGNÓSTICO DE IMÁGENES (REEMPLAZO) ---
    # ==========================================================
    todas_las_fotos = []
    log_debug = []

    # 1. RASTREO DE FOTO PRINCIPAL
    foto_p = moto.get('foto_factura') or moto.get('foto_soporte') or moto.get('Foto_Factura')
    if foto_p:
        todas_las_fotos.append(foto_p)
        log_debug.append("✅ Foto principal detectada")
    else:
        log_debug.append("❌ No se halló link en 'foto_factura' o 'foto_soporte'")

    # 2. RASTREO DE MANTENIMIENTOS (EXTRACCIÓN FORZADA)
    mantes = moto.get('Mantenimientos') or moto.get('mantenimientos') or []
    if not mantes:
        log_debug.append("❌ Lista de Mantenimientos VACÍA")
    else:
        ultimo = mantes[-1]
        log_debug.append(f"🔎 Campos: {list(ultimo.keys())}")
        
        # Intentamos capturar el valor tal cual esté, sin filtros
        valor_fotos = ultimo.get('Fotos')
        
        if valor_fotos is not None:
            log_debug.append(f"❓ Contenido de 'Fotos' es tipo: {type(valor_fotos).__name__}")
            
            if isinstance(valor_fotos, list) and len(valor_fotos) > 0:
                urls = [str(u).strip() for u in valor_fotos if u]
                todas_las_fotos.extend(urls)
                log_debug.append(f"✅ ¡ÉXITO! {len(urls)} fotos encontradas")
            elif isinstance(valor_fotos, str) and valor_fotos.startswith('http'):
                todas_las_fotos.append(valor_fotos.strip())
                log_debug.append("✅ 1 foto encontrada (texto)")
            else:
                log_debug.append(f"⚠️ 'Fotos' existe pero es: '{valor_fotos}'")
        else:
            log_debug.append("❌ El campo 'Fotos' devolvió None (está nulo)")

    # 3. RENDERIZADO Y REPORTE DE ERRORES EN EL PDF
    if todas_las_fotos:
        c.showPage()
        y_f = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y_f, "ANEXO FOTOGRÁFICO Y DIAGNÓSTICO")
        y_f -= 30
        
        # Escribir el log de diagnóstico en el PDF (Para ver el error en el celular)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        for msg in log_debug:
            c.drawString(40, y_f, msg)
            y_f -= 12
        
        c.setFillColor(colors.black)
        y_f -= 20

        for idx, url in enumerate(todas_las_fotos):
            try:
                link = str(url).strip()
                if not link.startswith('http'): continue

                if y_f < 260:
                    c.showPage()
                    y_f = height - 60
                
                # Puente de memoria
                resp = requests.get(link, timeout=15)
                img_data = BytesIO(resp.content)
                img = ImageReader(img_data)
                
                y_f -= 250
                c.drawImage(img, 40, y_f, width=500, height=240, preserveAspectRatio=True)
                
                c.setFont("Helvetica-Oblique", 7)
                c.drawString(40, y_f - 10, f"Evidencia #{idx+1} - Fuente: Cloudinary")
                y_f -= 30
            except Exception as e:
                c.setFont("Helvetica", 9)
                c.drawString(40, y_f, f"⚠️ Error en foto {idx+1}: {str(e)[:60]}")
                y_f -= 20
    else:
        # PÁGINA DE ERROR SI NO HAY FOTOS
        c.showPage()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, height - 80, "INFORME TÉCNICO DE FALLO DE IMÁGENES")
        y_e = height - 110
        c.setFont("Helvetica", 10)
        for msg in log_debug:
            c.drawString(40, y_e, msg)
            y_e -= 18

    # --- CIERRE FINAL ---
    c.save()
    return send_file(ruta_pdf, as_attachment=True)


# **************************************************************
# BLOQUE 14: PUNTO DE ENTRADA Y DESPLIEGUE DEL SERVIDOR
# Función: Inicializa el entorno de ejecución, configura el 
#          acceso a la red local y activa el modo de depuración.
# **************************************************************

if __name__ == '__main__':
    # --- CONFIGURACIÓN DE ACCESIBILIDAD ---
    # host='0.0.0.0' habilita la visibilidad del servidor en la red local (LAN),
    # permitiendo la conexión de dispositivos móviles y tablets externas.
    
    # port=5000 define el canal de comunicación estándar de Flask.
    # debug=True activa el hot-reload para reflejar cambios sin reiniciar.
    
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True
    )
