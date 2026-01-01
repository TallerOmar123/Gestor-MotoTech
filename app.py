# **************************************************************
# BLOQUE 0: IMPORTACIÓN DE BIBLIOTECAS
# **************************************************************
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import json
import urllib.parse
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
# BLOQUE 5: RUTA PRINCIPAL
# **************************************************************
@app.route('/')
def index():
    todos = logic.cargar_registros()
    placa_a_editar = request.args.get('editar_placa')
    cliente_a_editar = None
    
    if placa_a_editar:
        cliente_a_editar = next((c for c in todos if c.get('placa') == placa_a_editar), None)

    # CAMBIAMOS ESTA LÍNEA para que use la lógica de arriba:
    proximos = revisar_mantenimientos_logica() 
    
    return render_template('index.html', 
                           todos=todos, 
                           proximos=proximos, 
                           cliente_a_editar=cliente_a_editar, 
                           placa_a_editar=placa_a_editar)







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

    logic.guardar_registros(datos) # CORRECCIÓN: Nombre sincronizado
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
    moto_encontrada = next((m for m in registros if m.get('placa') == placa), None)
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


# **************************************************************
# BLOQUE 10: GENERADOR DE MENSAJE DE WHATSAPP (HOJA DE VIDA)
# **************************************************************
@app.route('/enviar_whatsapp/<placa>')
def enviar_whatsapp(placa):
    registros = cargar_registros()
    moto = next((m for m in registros if m.get('placa') == placa), None)
    
    # Diccionario de Barras de Color (Más visibles que los círculos)
    # Usamos bloques para simular una tabla de colores
    semaforo = {
        "✅ Óptimo": "🟩 BIEN",
        "⚠️ Pronto Cambio": "🟨 CAMBIO",
        "🚨 Urgente": "🟥 CRÍTICO"
    }

    # Procesamos cada sistema
    aceite = semaforo.get(moto.get('estado_aceite'), "⬜ --")
    frenos = semaforo.get(moto.get('estado_frenos'), "⬜ --")
    elec = semaforo.get(moto.get('estado_electrico'), "⬜ --")
    kit = semaforo.get(moto.get('estado_kit'), "⬜ --")
    clutch = semaforo.get(moto.get('estado_clutch'), "⬜ --")
    barras = semaforo.get(moto.get('estado_barras'), "⬜ --")

    # Construcción del mensaje tipo "Ticket"
    texto = (
        f"🏁 *MOTOTECH - REPORTE TÉCNICO*\n"
        f"Placa: *{moto.get('placa')}*\n"
        f"------------------------------------------\n\n"
        f"Estimado(a) *{moto.get('dueño')}*,\n"
        f"Este es el diagnóstico de su vehículo:\n\n"
        f"🛢️ *ACEITE:* {aceite}\n"
        f"🛑 *FRENOS:* {frenos}\n"
        f"⚡ *ELECTRICO:* {elec}\n"
        f"⛓️ *KIT ARR:* {kit}\n"
        f"⚙️ *CLUTCH:* {clutch}\n"
        f"🍴 *BARRAS:* {barras}\n\n"
        f"------------------------------------------\n"
        f"📊 *KM ACTUAL:* {moto.get('km_actual')} km\n"
        f"🔧 *PRÓX. CITA:* {moto.get('km_proximo_mantenimiento')} km\n\n"
        f"_*Recuerde: Los puntos marcados con 🟥 requieren atención inmediata para su seguridad.*_\n\n"
        f"¡Gracias por confiar en MotoTech! 🛠️"
    )
    # El secreto técnico: urllib.parse.quote para evitar errores de UTF-8
    mensaje_codificado = urllib.parse.quote(texto)
    telefono = moto.get('telefono', '')
    
    # Quitamos espacios o caracteres raros del teléfono si los hay
    telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
    
    link_wa = f"https://wa.me/57{telefono_limpio}?text={mensaje_codificado}"
    
    return redirect(link_wa)




if __name__ == '__main__':
    app.run(debug=True)