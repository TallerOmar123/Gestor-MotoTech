# **************************************************************
# BLOQUE 0: IMPORTACIÓN DE BIBLIOTECAS
# Descripción: Carga de módulos necesarios para web, archivos, PDF y fechas.
# **************************************************************
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import json
import urllib.parse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os
from datetime import datetime
import logic
from werkzeug.utils import secure_filename

# Configuración de carpeta para fotos
CARPETA_FOTOS = os.path.join('static', 'fotos_mantenimiento')
if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)


# **************************************************************
# BLOQUE 1: CONFIGURACIÓN INICIAL DEL SISTEMA
# Descripción: Definición de la aplicación Flask, claves de seguridad y rutas de datos.
# **************************************************************
app = Flask(__name__)
app.secret_key = "mototech_key_2025"
RUTA_JSON = 'registros.json'


# **************************************************************
# BLOQUE 2: FUNCIÓN CARGAR REGISTROS (INTERNA)
# Descripción: Gestión de lectura del archivo de base de datos JSON.
# **************************************************************
def cargar_registros():
    """Lee el archivo JSON y devuelve la lista de clientes o una lista vacía."""
    # --- SUB-BLOQUE: INTENTO DE LECTURA ---
    # Verifica si el archivo existe para abrirlo y cargar los datos como objeto Python
    try:
        if os.path.exists(RUTA_JSON):
            with open(RUTA_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    # --- SUB-BLOQUE: CONTROL DE ERRORES ---
    # Si el archivo está corrupto o no se puede leer, evita que la app se caiga
    except Exception as e:
        print(f"Error al cargar JSON: {e}")
        return []


# **************************************************************
# BLOQUE 3: FUNCIÓN GUARDAR REGISTROS (INTERNA)
# Descripción: Gestión de escritura y persistencia de datos en el archivo JSON.
# **************************************************************
def guardar_registros(registros):
    """Escribe los datos actualizados en el archivo registros.json con formato legible."""
    # --- SUB-BLOQUE: ESCRITURA FÍSICA ---
    # Abre el archivo en modo escritura y guarda la lista con sangría (indent) para que sea legible
    with open(RUTA_JSON, 'w', encoding='utf-8') as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)


# **************************************************************
# BLOQUE 4: LÓGICA DE ALERTAS DE KILOMETRAJE
# Descripción: Cálculo de proximidad de mantenimientos basado en el kilometraje actual.
# **************************************************************
def revisar_mantenimientos_logica():
    """Analiza cada moto para determinar si requiere mantenimiento preventivo por kilometraje."""
    todos = cargar_registros()
    proximos = []

    # --- SUB-BLOQUE: PROCESAMIENTO POR MOTO ---
    # Recorre cada vehículo para comparar sus kilómetros actuales contra los del próximo cambio
    for moto in todos:
        try:
            km_p = int(moto.get('km_proximo_mantenimiento', 0))
            km_a = int(moto.get('km_actual', 0))
            faltan = km_p - km_a

            # --- SUB-BLOQUE: CLASIFICACIÓN DE ALERTA ---
            # Si faltan menos de 500km, se categoriza el estado (Vencido, Urgente o Aviso)
            if faltan <= 500:
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
            print(f"Error calculando alerta para {moto.get('placa')}: {e}")
            continue
    return proximos


# **************************************************************
# BLOQUE 5: RUTA PRINCIPAL
# Descripción: Punto de entrada del software que muestra el panel de control y balance.
# **************************************************************
@app.route('/')
def index():
    """Prepara y carga la página principal con tablas, alertas y balance financiero."""
    todos = logic.cargar_registros()

    # --- SUB-BLOQUE: GESTIÓN DE EDICIÓN ---
    # Detecta si el usuario hizo clic en "editar" para cargar los datos de una moto en el formulario
    placa_a_editar = request.args.get('editar_placa')
    cliente_a_editar = None
    if placa_a_editar:
        cliente_a_editar = next(
            (c for c in todos if c.get('placa') == placa_a_editar), None)

    proximos = revisar_mantenimientos_logica()

    # --- SUB-BLOQUE: CÁLCULO FINANCIERO ---
    # Llama a la lógica externa para sumar todos los costos de mantenimiento y dar el total
    try:
        ingresos_totales = logic.calcular_balance_total(todos)
        if ingresos_totales is None:
            ingresos_totales = 0
    except Exception as e:
        print(f"Error al calcular balance: {e}")
        ingresos_totales = 0

    return render_template('index.html',
                           todos=todos,
                           proximos=proximos,
                           cliente_a_editar=cliente_a_editar,
                           placa_a_editar=placa_a_editar,
                           ingresos_totales=ingresos_totales)


# **************************************************************
# BLOQUE 6: LÓGICA DE GUARDAR/EDITAR CLIENTES
# Descripción: Procesa el formulario de registro y actualización de datos básicos de motos.
# **************************************************************
@app.route('/agregar_cliente_web', methods=['POST'])
def agregar_cliente_web():
    """Recibe datos del formulario para crear un nuevo cliente o actualizar uno existente."""
    datos = logic.cargar_registros()

    # --- SUB-BLOQUE: CAPTURA DE DATOS ---
    # Limpia y convierte los datos recibidos desde los campos del formulario HTML
    placa = request.form.get('placa').upper().strip()
    dueño = request.form.get('dueño')
    telefono = request.form.get('telefono')
    moto = request.form.get('moto')
    km_actual = int(request.form.get('km_actual') or 0)
    km_prox = int(request.form.get('km_prox') or 0)

    # --- SUB-BLOQUE: VERIFICACIÓN DE EXISTENCIA ---
    # Busca si la placa ya está registrada para decidir si actualiza o crea un registro nuevo
    cliente_existente = next((c for c in datos if c['placa'] == placa), None)

    if cliente_existente:
        # Si existe, sobreescribe los valores actuales
        cliente_existente['dueño'] = dueño
        cliente_existente['telefono'] = telefono
        cliente_existente['moto'] = moto
        cliente_existente['km_actual'] = km_actual
        cliente_existente['km_proximo_mantenimiento'] = km_prox
        flash(f"✅ Datos de {placa} actualizados correctamente", "success")
    else:
        # Si no existe, crea la estructura inicial para el nuevo cliente
        nuevo_cliente = {
            "placa": placa, "dueño": dueño, "telefono": telefono, "moto": moto,
            "km_actual": km_actual, "km_proximo_mantenimiento": km_prox,
            "Mantenimientos": []
        }
        datos.append(nuevo_cliente)
        flash(f"🏍️ Moto {placa} registrada con éxito", "success")

    logic.guardar_registros(datos)
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 7: RUTA PARA REGISTRAR TRABAJOS (TALLER)
# Descripción: Registra los mantenimientos técnicos, captura fotos y estados mecánicos.
# **************************************************************
@app.route('/mantenimiento', methods=['POST'])
def agregar_mantenimiento_web():
    """Procesa el ingreso de un servicio al taller, incluyendo diagnóstico y archivos multimedia."""
    placa = request.form.get('placa_mantenimiento').upper()
    registros = cargar_registros()
    cliente = next((m for m in registros if m.get('placa') == placa), None)

    if cliente:
        costo_actual = int(request.form.get('costo_mantenimiento') or 0)

        # --- SUB-BLOQUE: PROCESAMIENTO DE IMÁGENES ---
        # Recorre la lista de fotos subidas, les asigna un nombre único con fecha y las guarda en disco
        lista_fotos = []
        if 'fotos' in request.files:
            archivos = request.files.getlist('fotos')
            for foto in archivos:
                if foto.filename != '':
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_seguro = secure_filename(
                        f"{placa}_{timestamp}_{foto.filename}")
                    foto.save(os.path.join(CARPETA_FOTOS, nombre_seguro))
                    lista_fotos.append(nombre_seguro)

        # --- SUB-BLOQUE: CREACIÓN DEL SERVICIO ---
        # Organiza los datos del mantenimiento realizado en un diccionario
        nuevo = {
            "Fecha": request.form.get('fecha_mantenimiento'),
            "KM": int(request.form.get('km_mantenimiento') or 0),
            "Descripcion": request.form.get('descripcion_mantenimiento'),
            "Costo": costo_actual,
            "Fotos": lista_fotos
        }

        # --- SUB-BLOQUE: ACTUALIZACIÓN TÉCNICA ---
        # Actualiza el estado actual de cada componente de la moto según lo marcado por el técnico
        cliente['estado_aceite'] = request.form.get('aceite')
        cliente['freno_del'] = request.form.get('freno_del')
        cliente['freno_tras'] = request.form.get('freno_tras')
        cliente['liq_frenos'] = request.form.get('liq_frenos')
        cliente['lavado_carburador'] = request.form.get('lavado_carburador')
        cliente['filtro_bujia'] = request.form.get('filtro_bujia')
        cliente['engrase_tijera'] = request.form.get('engrase_tijera')
        cliente['mantenimiento_guayas'] = request.form.get(
            'mantenimiento_guayas')
        cliente['estado_frenos'] = request.form.get('frenos')
        cliente['estado_electrico'] = request.form.get('electrico')
        cliente['estado_kit'] = request.form.get('kit_arrastre')
        cliente['estado_clutch'] = request.form.get('clutch')
        cliente['estado_barras'] = request.form.get('barras')
        cliente['ultimo_cobro'] = costo_actual

        # --- SUB-BLOQUE: FINALIZACIÓN DEL REGISTRO ---
        # Añade el nuevo mantenimiento al historial y actualiza el kilometraje global de la moto
        if 'Mantenimientos' not in cliente:
            cliente['Mantenimientos'] = []
        cliente['Mantenimientos'].append(nuevo)
        cliente['km_actual'] = nuevo['KM']
        guardar_registros(registros)
        flash(f"✅ ¡Éxito! Servicio guardado para {placa}", "warning")

    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 8: RUTA PARA ACTIVAR LA EDICIÓN
# Descripción: Prepara la interfaz para modificar los datos de un cliente específico.
# **************************************************************
@app.route('/editar/<placa>')
def editar_cliente(placa):
    """Redirecciona al index cargando los datos de la placa seleccionada en el formulario superior."""
    # --- SUB-BLOQUE: BÚSQUEDA ---
    # Localiza la moto en la base de datos para asegurar que existe antes de intentar editarla
    registros = logic.cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if moto:
        return redirect(url_for('index', editar_placa=placa))
    flash("❌ Moto no encontrada", "danger")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 8.5: RUTA PARA GENERACIÓN DE REPORTES PDF
# Descripción: Crea y descarga el informe técnico en PDF para el cliente.
# **************************************************************
@app.route('/descargar_reporte/<placa>')
def descargar_reporte(placa):
    """Genera el documento PDF con el diagnóstico técnico y lo envía al navegador."""
    registros = cargar_registros()
    moto_encontrada = next(
        (m for m in registros if m.get('placa') == placa), None)

    # --- SUB-BLOQUE: GENERACIÓN Y ENVÍO ---
    # Si la moto existe, usa la lógica de reportes para crear el archivo y enviarlo como descarga
    if moto_encontrada:
        ruta_pdf = logic.generar_pdf_cliente(moto_encontrada)
        return send_file(ruta_pdf, as_attachment=True)
    flash("Error: No se pudo generar el reporte.", "danger")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 9: RUTA PARA ELIMINAR CLIENTES
# Descripción: Remoción definitiva de registros del sistema.
# **************************************************************
@app.route('/eliminar/<placa>')
def eliminar_cliente(placa):
    """Borra permanentemente la moto y todo su historial de la base de datos JSON."""
    # --- SUB-BLOQUE: FILTRADO ---
    # Crea una nueva lista que contiene todos los clientes MENOS el que se quiere eliminar
    motos = cargar_registros()
    motos_actualizadas = [m for m in motos if m['placa'] != placa]
    guardar_registros(motos_actualizadas)
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 9.5: RUTA PARA ELIMINAR UN SERVICIO ESPECÍFICO
# Descripción: Borra un solo registro del historial de mantenimientos.
# **************************************************************
@app.route('/eliminar_servicio/<placa>/<int:index>')
def eliminar_servicio(placa, index):
    """Elimina un mantenimiento específico usando su posición en la lista."""
    registros = cargar_registros()
    # 1. Buscamos al cliente por placa
    cliente = next((m for m in registros if m.get('placa') == placa), None)

    if cliente and 'Mantenimientos' in cliente:
        try:
            # 2. Eliminamos el elemento en la posición 'index'
            # .pop() elimina y devuelve el elemento en esa posición
            servicio_eliminado = cliente['Mantenimientos'].pop(index)

            # 3. Guardamos los cambios en el JSON
            guardar_registros(registros)
            flash(
                f"🗑️ Servicio del {servicio_eliminado.get('Fecha')} eliminado", "info")
        except IndexError:
            flash("❌ No se encontró el registro a eliminar", "danger")

    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 10: RUTA PARA NOTIFICACIÓN WHATSAPP
# Descripción: Genera enlaces de WhatsApp con mensajes personalizados y cobros.
# **************************************************************
@app.route('/enviar_whatsapp/<placa>')
def enviar_whatsapp(placa):
    """Construye un mensaje automático para avisar al cliente que su moto está lista."""
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if not moto:
        return "Moto no encontrada", 404

    # --- SUB-BLOQUE: FORMATEO DE DINERO ---
    # Convierte el número del costo en un formato legible con puntos (ej: 150.000)
    cobro = moto.get('ultimo_cobro', 0)
    cobro_formateado = f"{cobro:,.0f}".replace(",", ".")

    # --- SUB-BLOQUE: MENSAJE Y LINK ---
    # Codifica el texto para que sea compatible con una URL y limpia el número de teléfono
    texto = (
        f"✅ *MOTOTECH - MOTO LISTA*\n\n"
        f"Hola *{moto.get('dueño')}*,\n"
        f"Le informamos que el servicio técnico de su moto placa *{moto.get('placa')}* ha finalizado con éxito.\n\n"
        f"💰 *VALOR A PAGAR:* ${cobro_formateado}\n"
        f"📄 *REPORTE TÉCNICO:* Su informe detallado en PDF ya está disponible.\n\n"
        "Ya puede pasar al taller por su vehículo. ¡Gracias por elegirnos! 🏍️"
    )

    mensaje_codificado = urllib.parse.quote(texto)
    telefono = moto.get('telefono', '')
    telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
    link_wa = f"https://wa.me/57{telefono_limpio}?text={mensaje_codificado}"
    return redirect(link_wa)


# **************************************************************
# BLOQUE 11: GENERACIÓN DETALLADA DE PDF
# Descripción: Motor gráfico para construir el PDF con tablas de estado y fotos.
# **************************************************************
@app.route('/generar_pdf/<placa>')
def generar_pdf(placa):
    """Dibuja hoja por hoja el reporte técnico profesional con evidencia fotográfica."""
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if not moto:
        return "Moto no encontrada", 404

    # --- SUB-BLOQUE: PREPARACIÓN MULTIMEDIA ---
    # Busca las fotos guardadas en el último mantenimiento para anexarlas al reporte
    ultimas_fotos = []
    if moto.get('Mantenimientos'):
        ultimo_servicio = moto['Mantenimientos'][-1]
        ultimas_fotos = ultimo_servicio.get('Fotos', [])

    nombre_archivo = f"Reporte_{placa}.pdf"
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    width, height = letter
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    # --- SUB-BLOQUE: DISEÑO DE ENCABEZADO ---
    # Dibuja el rectángulo azul oscuro y el título del taller en la parte superior
    c.setFillColor(colors.HexColor("#1B2631"))
    c.rect(0, height - 80, width, 80, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 50, "MOTOTECH - REPORTE TECNICO")

    # --- SUB-BLOQUE: DATOS DEL VEHÍCULO ---
    # Imprime la información del cliente, placa y kilómetros actuales en la cabecera
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, f"CLIENTE: {moto.get('dueño')}")
    c.drawString(40, height - 130, f"PLACA: {moto.get('placa')}")
    c.drawString(350, height - 110, f"KM ACTUAL: {moto.get('km_actual')}")

    # --- SUB-BLOQUE: DIBUJO DE TABLA TÉCNICA ---
    # Itera sobre la lista de ítems para pintar las barras de estado y colores según la prioridad
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

        # --- LÓGICA DE COLORES DE SEMÁFORO ---
        # Define si el cuadro es Verde (Óptimo), Amarillo (Seguimiento) o Rojo (Urgente)
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

    # --- SUB-BLOQUE: OBSERVACIONES ---
    # Añade el texto de recomendaciones finales al pie de la primera hoja
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "OBSERVACIONES Y RECOMENDACIONES:")
    c.line(40, y-2, 250, y-2)
    y -= 20
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        50, y, "Se recomienda realizar los cambios marcados como URGENTE para garantizar su seguridad.")

    # --- SUB-BLOQUE: ANEXO FOTOGRÁFICO ---
    # Si hay imágenes, crea una nueva página y las organiza en una cuadrícula de 2x2
    if ultimas_fotos:
        c.showPage()
        c.setFillColor(colors.HexColor("#1B2631"))
        c.rect(0, height - 50, width, 50, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 35, "EVIDENCIA FOTOGRÁFICA DEL SERVICIO")
        y_total = height - 250
        x_foto = 50
        for idx, nombre_foto in enumerate(ultimas_fotos):
            ruta_img = os.path.join(CARPETA_FOTOS, nombre_foto)
            if os.path.exists(ruta_img):
                c.drawImage(ruta_img, x_foto, y_total, width=240,
                            height=180, preserveAspectRatio=True)
                x_foto += 270
                if (idx + 1) % 2 == 0:
                    x_foto = 50
                    y_total -= 220
                if y_total < 150:
                    c.showPage()
                    y_total = height - 100
        y_final = y_total - 50
    else:
        y_final = y - 60

    # --- SUB-BLOQUE: TOTALES Y CIERRE ---
    # Muestra el precio final cobrado y la sugerencia de kilometraje para la próxima visita
    c.setFillColor(colors.HexColor("#F2F4F4"))
    c.rect(40, y_final-10, 520, 40, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    ultimo_cobro = moto.get('ultimo_cobro', 0)
    costo_formateado = f"{ultimo_cobro:,.0f}".replace(",", ".")
    c.drawString(60, y_final+15,
                 f"VALOR TOTAL DEL SERVICIO: $ {costo_formateado}")
    km_prox = moto.get('km_proximo_mantenimiento', '---')
    c.drawString(60, y_final, f"SUGERENCIA PRÓXIMA VISITA: {km_prox} KM")

    # --- SUB-BLOQUE: PIE DE PÁGINA ---
    # Coloca los derechos de autor, la fecha de emisión y el logotipo del taller
    y_footer = 30
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(
        40, y_footer, "Este reporte es propiedad de MotoTech. Verifique su próximo mantenimiento.")
    c.drawRightString(550, y_footer + 35, f"Fecha de emisión: {fecha_hoy}")
    ruta_logo = os.path.join(app.root_path, 'static', 'logo.jpg')
    if os.path.exists(ruta_logo):
        c.drawImage(ruta_logo, 460, y_footer - 10, width=100,
                    preserveAspectRatio=True, mask='auto')

    c.save()
    return send_file(nombre_archivo, as_attachment=True)


# **************************************************************
# BLOQUE 12: INICIO DEL SERVIDOR
# Descripción: Configuración de red y puerto para arrancar la aplicación.
# **************************************************************
if __name__ == '__main__':
    # host='0.0.0.0' permite que otros dispositivos (celulares) se conecten en la misma red.
    app.run(host='0.0.0.0', port=5000, debug=True)
