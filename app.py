# **************************************************************
# BLOQUE 0: IMPORTACIÓN DE BIBLIOTECAS
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


# **************************************************************
# BLOQUE 1: CONFIGURACIÓN INICIAL DEL SISTEMA
# **************************************************************
app = Flask(__name__)
app.secret_key = "mototech_key_2025"
RUTA_JSON = 'registros.json'


# **************************************************************
# BLOQUE 2: FUNCIÓN CARGAR REGISTROS (INTERNA)
# **************************************************************
def cargar_registros():
    try:
        if os.path.exists(RUTA_JSON):
            with open(RUTA_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error al cargar JSON: {e}")
        return []


# **************************************************************
# BLOQUE 3: FUNCIÓN GUARDAR REGISTROS (INTERNA)
# **************************************************************
def guardar_registros(registros):
    with open(RUTA_JSON, 'w', encoding='utf-8') as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)


# **************************************************************
# BLOQUE 4: LÓGICA DE ALERTAS DE KILOMETRAJE (CORREGIDO)
# **************************************************************
def revisar_mantenimientos_logica():
    todos = cargar_registros()
    proximos = []

    for moto in todos:
        try:
            # Convertimos a número para poder restar
            km_p = int(moto.get('km_proximo_mantenimiento', 0))
            km_a = int(moto.get('km_actual', 0))

            faltan = km_p - km_a

            # Si faltan 500 km o menos, entra en la lista de alertas
            if faltan <= 500:
                # Si faltan 100 o menos es PELIGRO (Rojo), si no es AVISO (Amarillo)
                moto['clase_alerta'] = 'table-danger' if faltan <= 100 else 'table-warning'

                # AQUÍ CORREGIMOS EL TEXTO QUE SE VE EN LA TABLA:
                if faltan <= 0:
                    moto['estado'] = '¡VENCIDO!'
                elif faltan <= 100:
                    moto['estado'] = '¡URGENTE!'
                else:
                    moto['estado'] = 'AVISO'

                # Guardamos cuántos km faltan para mostrarlo también si quieres
                moto['faltan_km'] = faltan

                proximos.append(moto)
        except Exception as e:
            print(f"Error calculando alerta para {moto.get('placa')}: {e}")
            continue

    return proximos


# **************************************************************
# BLOQUE 5: RUTA PRINCIPAL (CORREGIDO PARA EVITAR TYPEERROR)
# **************************************************************
@app.route('/')
def index():
    # Cargamos los datos usando logic
    todos = logic.cargar_registros()
    
    # Lógica para edición
    placa_a_editar = request.args.get('editar_placa')
    cliente_a_editar = None
    if placa_a_editar:
        cliente_a_editar = next((c for c in todos if c.get('placa') == placa_a_editar), None)

    # Lógica de alertas de mantenimiento
    proximos = revisar_mantenimientos_logica()

    # --- SEGURIDAD PARA EL BALANCE TOTAL ---
    try:
        ingresos_totales = logic.calcular_balance_total(todos)
        if ingresos_totales is None:
            ingresos_totales = 0
    except Exception as e:
        print(f"Error al calcular balance: {e}")
        ingresos_totales = 0 
    # ---------------------------------------

    return render_template('index.html',
                           todos=todos,
                           proximos=proximos,
                           cliente_a_editar=cliente_a_editar,
                           placa_a_editar=placa_a_editar,
                           ingresos_totales=ingresos_totales) # Ahora siempre es un número

# **************************************************************
# BLOQUE 6: LÓGICA DE GUARDAR/EDITAR (CORREGIDO)
# **************************************************************
@app.route('/agregar_cliente_web', methods=['POST'])
def agregar_cliente_web():
    # CORRECCIÓN: Nombres de función sincronizados con logic.py
    datos = logic.cargar_registros()

    placa = request.form.get('placa').upper().strip()
    dueño = request.form.get('dueño')
    telefono = request.form.get('telefono')
    moto = request.form.get('moto')
    km_actual = int(request.form.get('km_actual') or 0)
    km_prox = int(request.form.get('km_prox') or 0)

    cliente_existente = next((c for c in datos if c['placa'] == placa), None)

    if cliente_existente:
        cliente_existente['dueño'] = dueño
        cliente_existente['telefono'] = telefono
        cliente_existente['moto'] = moto
        cliente_existente['km_actual'] = km_actual
        cliente_existente['km_proximo_mantenimiento'] = km_prox
        flash(f"✅ Datos de {placa} actualizados correctamente", "success")
    else:
        nuevo_cliente = {
            "placa": placa,
            "dueño": dueño,
            "telefono": telefono,
            "moto": moto,
            "km_actual": km_actual,
            "km_proximo_mantenimiento": km_prox,
            "Mantenimientos": []
        }
        datos.append(nuevo_cliente)
        flash(f"🏍️ Moto {placa} registrada con éxito", "success")

    logic.guardar_registros(datos)  # CORRECCIÓN: Nombre sincronizado
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 7: RUTA PARA REGISTRAR TRABAJOS
# **************************************************************
@app.route('/mantenimiento', methods=['POST'])
def agregar_mantenimiento_web():
    placa = request.form.get('placa_mantenimiento').upper()
    registros = cargar_registros()
    cliente = next((m for m in registros if m.get('placa') == placa), None)
    if cliente:
        nuevo = {
            "Fecha": request.form.get('fecha_mantenimiento'),
            "KM": int(request.form.get('km_mantenimiento')),
            "Descripcion": request.form.get('descripcion_mantenimiento'),
            "Costo": int(request.form.get('costo_mantenimiento'))
        }

# ========================================================
        # INYECCIÓN: ACTUALIZACIÓN DE HOJA DE VIDA TÉCNICA
        # ========================================================
        cliente['estado_aceite'] = request.form.get('aceite')
        cliente['estado_frenos'] = request.form.get('frenos')
        cliente['estado_electrico'] = request.form.get('electrico')
        cliente['estado_kit'] = request.form.get('kit_arrastre')
        cliente['estado_clutch'] = request.form.get('clutch')
        cliente['estado_barras'] = request.form.get('barras')
        # ========================================================

        if 'Mantenimientos' not in cliente:
            cliente['Mantenimientos'] = []
        cliente['Mantenimientos'].append(nuevo)
        cliente['km_actual'] = nuevo['KM']
        guardar_registros(registros)
        flash(f"✅ ¡Éxito! Servicio guardado para {placa}", "warning")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 8: RUTA PARA ACTIVAR LA EDICIÓN
# **************************************************************
@app.route('/editar/<placa>')
def editar_cliente(placa):
    registros = logic.cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)
    if moto:
        return redirect(url_for('index', editar_placa=placa))
    flash("❌ Moto no encontrada", "danger")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 8.5: RUTA PARA GENERACIÓN DE REPORTES PDF
# **************************************************************
@app.route('/descargar_reporte/<placa>')
def descargar_reporte(placa):
    registros = cargar_registros()
    moto_encontrada = next(
        (m for m in registros if m.get('placa') == placa), None)
    if moto_encontrada:
        ruta_pdf = logic.generar_pdf_cliente(moto_encontrada)
        return send_file(ruta_pdf, as_attachment=True)
    flash("Error: No se pudo generar el reporte.", "danger")
    return redirect(url_for('index'))


# **************************************************************
# BLOQUE 9: RUTA PARA ELIMINAR CLIENTES
# **************************************************************
@app.route('/eliminar/<placa>')
def eliminar_cliente(placa):
    motos = cargar_registros()
    motos_actualizadas = [m for m in motos if m['placa'] != placa]
    guardar_registros(motos_actualizadas)
    return redirect(url_for('index'))


@app.route('/enviar_whatsapp/<placa>')
def enviar_whatsapp(placa):
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if not moto:
        return "Moto no encontrada", 404

    # Diccionario de estados en texto puro y limpio
    estados_texto = {
        "✅ Óptimo": "BIEN",
        "⚠️ Pronto Cambio": "AVISO / PRONTO CAMBIO",
        "🚨 Urgente": "CRITICO / CAMBIO URGENTE"
    }

    # Procesar estados (si no hay datos, pone "No registrado")
    aceite = estados_texto.get(moto.get('estado_aceite'), "No registrado")
    frenos = estados_texto.get(moto.get('estado_frenos'), "No registrado")
    elec = estados_texto.get(moto.get('estado_electrico'), "No registrado")
    kit = estados_texto.get(moto.get('estado_kit'), "No registrado")
    clutch = estados_texto.get(moto.get('estado_clutch'), "No registrado")
    barras = estados_texto.get(moto.get('estado_barras'), "No registrado")

    # Construcción del mensaje (Sin emojis, solo formato de texto WhatsApp)
    texto = (
        "*MOTOTECH - REPORTE TECNICO*\n"
        f"Placa: *{moto.get('placa')}*\n"
        "------------------------------------------\n\n"
        f"Hola *{moto.get('dueño')}*,\n"
        "Este es el diagnostico de su moto:\n\n"
        f"1. ACEITE MOTOR: {aceite}\n"
        f"2. SISTEMA FRENOS: {frenos}\n"
        f"3. SISTEMA ELECTRICO: {elec}\n"
        f"4. KIT ARRASTRE: {kit}\n"
        f"5. CLUTCH: {clutch}\n"
        f"6. BARRAS / SUSPENSION: {barras}\n\n"
        "------------------------------------------\n"
        f"KM ACTUAL: {moto.get('km_actual')} km\n"
        f"PROXIMA CITA: {moto.get('km_proximo_mantenimiento')} km\n\n"
        "Su reporte detallado en PDF ha sido generado.\n"
        "Gracias por confiar en MOTOTECH."
    )

    mensaje_codificado = urllib.parse.quote(texto)
    telefono = moto.get('telefono', '')
    telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
    link_wa = f"https://wa.me/57{telefono_limpio}?text={mensaje_codificado}"
    return redirect(link_wa)


@app.route('/generar_pdf/<placa>')
def generar_pdf(placa):
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)

    if not moto:
        return "Moto no encontrada", 404

    nombre_archivo = f"Reporte_{placa}.pdf"
    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    width, height = letter
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    # --- 1. ENCABEZADO LIMPIO ---
    c.setFillColor(colors.HexColor("#1B2631"))
    c.rect(0, height - 80, width, 80, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 50, "MOTOTECH - REPORTE TECNICO")

    # --- 2. DATOS DEL CLIENTE ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, f"CLIENTE: {moto.get('dueño')}")
    c.drawString(40, height - 130, f"PLACA: {moto.get('placa')}")
    c.drawString(350, height - 110, f"KM ACTUAL: {moto.get('km_actual')}")

    # --- 3. TABLA DE ESTADOS ---
    y = height - 170
    items = [
        ("ACEITE MOTOR", moto.get('estado_aceite')),
        ("SISTEMA FRENOS", moto.get('estado_frenos')),
        ("SISTEMA ELECTRICO", moto.get('estado_electrico')),
        ("KIT ARRASTRE", moto.get('estado_kit')),
        ("CLUTCH", moto.get('estado_clutch')),
        ("BARRAS", moto.get('estado_barras'))
    ]

    for nombre, estado in items:
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(50, y, nombre)
        
        color_celda = colors.white
        texto_prioridad = "NORMAL"
        
        if estado == "✅ Óptimo":
            color_celda = colors.lightgreen
            texto_prioridad = "BIEN"
        elif estado == "⚠️ Pronto Cambio":
            color_celda = colors.yellow
            texto_prioridad = "AVISO"
        elif estado == "🚨 Urgente":
            color_celda = colors.tomato
            texto_prioridad = "CRITICO"

        c.setFillColor(color_celda)
        c.rect(320, y-5, 100, 15, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(370, y, texto_prioridad)
        y -= 25

    # --- 4. PIE DE PÁGINA: SELLO DE MARCA Y FECHA ---
    # Definimos la base del footer
    y_footer = 30

    # Texto de propiedad (Izquierda)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(40, y_footer, "Este reporte es propiedad de MotoTech. Verifique su próximo mantenimiento.")

    # Fecha del reporte (Derecha, arriba del logo)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.black)
    c.drawRightString(550, y_footer + 35, f"Fecha de emisión: {fecha_hoy}")

    # Sello de Marca (Derecha inferior)
    ruta_logo = os.path.join(app.root_path, 'static', 'logo.jpg')
    if os.path.exists(ruta_logo):
        # Ubicación: X=460, Y=y_footer - 10 (bien abajo a la derecha)
        c.drawImage(ruta_logo, 460, y_footer - 10, width=100, preserveAspectRatio=True, mask='auto')

    c.save()
    return send_file(nombre_archivo, as_attachment=True)

if __name__ == '__main__':
    # host='0.0.0.0' abre la conexión para el celular
    app.run(host='0.0.0.0', port=5000, debug=True)
