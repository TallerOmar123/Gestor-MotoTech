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
# BLOQUE 7: RUTA PARA REGISTRAR TRABAJOS (ACTUALIZADO)
# **************************************************************
@app.route('/mantenimiento', methods=['POST'])
def agregar_mantenimiento_web():
    placa = request.form.get('placa_mantenimiento').upper()
    registros = cargar_registros()
    cliente = next((m for m in registros if m.get('placa') == placa), None)
    
    if cliente:
        costo_actual = int(request.form.get('costo_mantenimiento') or 0)
        nuevo = {
            "Fecha": request.form.get('fecha_mantenimiento'),
            "KM": int(request.form.get('km_mantenimiento') or 0),
            "Descripcion": request.form.get('descripcion_mantenimiento'),
            "Costo": costo_actual
        }

        # ACTUALIZACIÓN DE HOJA DE VIDA TÉCNICA
        cliente['estado_aceite'] = request.form.get('aceite')
        # --- NUEVA INYECCIÓN: SUBDIVISIONES TÉCNICAS ---
        cliente['freno_del'] = request.form.get('freno_del')
        cliente['freno_tras'] = request.form.get('freno_tras')
        cliente['liq_frenos'] = request.form.get('liq_frenos')
        cliente['lavado_carburador'] = request.form.get('lavado_carburador')
        cliente['filtro_bujia'] = request.form.get('filtro_bujia')
        cliente['engrase_tijera'] = request.form.get('engrase_tijera')
        cliente['mantenimiento_guayas'] = request.form.get('mantenimiento_guayas')
        # -----------------------------------------------
        cliente['estado_frenos'] = request.form.get('frenos')
        cliente['estado_electrico'] = request.form.get('electrico')
        cliente['estado_kit'] = request.form.get('kit_arrastre')
        cliente['estado_clutch'] = request.form.get('clutch')
        cliente['estado_barras'] = request.form.get('barras')

        # REGISTRO DE ÚLTIMO COBRO PARA WHATSAPP
        cliente['ultimo_cobro'] = costo_actual

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

    # Formatear el precio con puntos de miles (ej: 150.000)
    cobro = moto.get('ultimo_cobro', 0)
    cobro_formateado = f"{cobro:,.0f}".replace(",", ".")

    # Construcción del mensaje de SALIDA
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


    # NUEVA ESTRUCTURA DE DIAGNÓSTICO DETALLADO
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
        # Si es un título de sección (los que tienen ---)
        if "---" in nombre:
            y -= 10
            c.setFillColor(colors.HexColor("#D5D8DC"))
            c.rect(40, y-5, 520, 15, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y, nombre)
            y -= 20
            continue

        # Dibujar nombre del ítem
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(50, y, nombre)
        
        # LÓGICA DE SEMÁFORO (Colores dinámicos)
        color_celda = colors.white
        texto_prioridad = "S.D" # Sin Datos
        
        if estado == "✅ Óptimo":
            color_celda = colors.lightgreen
            texto_prioridad = "OK - OPTIMO"
        elif estado == "⚠️ Pronto Cambio":
            color_celda = colors.yellow
            texto_prioridad = "SEGUIMIENTO"
        elif estado == "🚨 Urgente":
            color_celda = colors.tomato
            texto_prioridad = "CAMBIO URGENTE"

        # Dibujar el cuadro de estado
        c.setFillColor(color_celda)
        c.rect(400, y-5, 120, 15, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(460, y, texto_prioridad)
        y -= 20

    # BLOQUE DE RECOMENDACIONES AUTOMÁTICAS
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "OBSERVACIONES Y RECOMENDACIONES:")
    c.line(40, y-2, 250, y-2)
    y -= 20
    c.setFont("Helvetica-Oblique", 9)
    
    # Lógica inteligente de texto
    recom_txt = "Se recomienda realizar los cambios marcados como URGENTE para garantizar su seguridad."
    c.drawString(50, y, recom_txt)


    # --- NUEVA INYECCIÓN: RESUMEN DE INVERSIÓN Y PRÓXIMA CITA ---
    y -= 45
    # Dibujamos un rectángulo suave de fondo para el resumen
    c.setFillColor(colors.HexColor("#F2F4F4"))
    c.rect(40, y-10, 520, 40, fill=1, stroke=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    
    # Formateamos el costo con puntos de miles para que se vea profesional
    ultimo_cobro = moto.get('ultimo_cobro', 0)
    costo_formateado = f"{ultimo_cobro:,.0f}".replace(",", ".")
    
    c.drawString(60, y+15, f"VALOR TOTAL DEL SERVICIO: $ {costo_formateado}")
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1B2631"))
    km_prox = moto.get('km_proximo_mantenimiento', '---')
    c.drawString(60, y, f"SUGERENCIA PRÓXIMA VISITA: {km_prox} KM")
    # ------------------------------------------------------------

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
