import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox, simpledialog, ttk
import json
import os
import sys
import webbrowser
import urllib.parse

# **************************************************************
# BLOQUE 1: CONFIGURACIONES Y PERSISTENCIA DE DATOS
# TRABAJO QUE HACE: Carga y guarda la información en el archivo JSON
# y define las constantes de mantenimiento.
# **************************************************************
MARGEN_ALERTA = 5000 

def cargar_registros():
    """Carga los registros desde el archivo JSON de forma robusta."""
    try:
        if os.path.exists("registros.json"):
            with open("registros.json", 'r') as file:
                return json.load(file)
        else:
            return {}
    except Exception:
        return {}

def guardar_registros(registros):
    """Guarda los registros en el archivo JSON."""
    try:
        with open("registros.json", 'w') as file:
            json.dump(registros, file, indent=4)
        return True
    except IOError:
        messagebox.showerror("Error de Guardado", "No se pudo guardar el archivo de registros.")
        return False

# **************************************************************
# BLOQUE 2: CONFIGURACIÓN VISUAL INICIAL
# TRABAJO QUE HACE: Establece el tema oscuro y los colores de la App.
# **************************************************************
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("dark-blue") 


# **************************************************************
# BLOQUE 3: CLASE FORMULARIO CLIENTE (NUEVO REGISTRO)
# TRABAJO QUE HACE: Ventana modal para capturar datos de clientes nuevos.
# **************************************************************
class FormularioCliente(ctk.CTkToplevel):
    """
    Ventana modal dedicada para capturar todos los datos de un nuevo cliente.
    """
    def __init__(self, master, callback_guardar):
        super().__init__(master)
        self.title("➕ Agregar Cliente Nuevo")
        self.master = master
        self.callback_guardar = callback_guardar
        self.transient(master)  
        self.grab_set()         
        self.resizable(False, False)
        
        self.placa_var = ctk.StringVar()
        self.dueno_var = ctk.StringVar()
        self.telefono_var = ctk.StringVar()
        self.email_var = ctk.StringVar()
        self.km_actual_var = ctk.StringVar()
        self.km_prox_var = ctk.StringVar() 
        
        self.crear_widgets_formulario()
        self.lift()
        self.attributes("-topmost", True)

    def crear_widgets_formulario(self):
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(padx=20, pady=20, fill="x")

        campos = [
            ("Placa (Clave Única):", self.placa_var, "Escriba la placa"),
            ("Dueño:", self.dueno_var, "Nombre completo"),
            ("Teléfono:", self.telefono_var, "Número de contacto"),
            ("Email:", self.email_var, "Opcional"),
            ("Kilometraje Actual:", self.km_actual_var, "Solo números (KM)"),
            ("KM Próximo Mantenimiento:", self.km_prox_var, "Sugerido: KM Actual + 5000") 
        ]

        for i, (label_text, var, placeholder) in enumerate(campos):
            ctk.CTkLabel(self.frame_inputs, text=label_text).grid(row=i, column=0, padx=10, pady=(10, 0), sticky="w")
            entry = ctk.CTkEntry(self.frame_inputs, textvariable=var, placeholder_text=placeholder, width=300)
            entry.grid(row=i, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkButton(self, text="💾 Guardar Cliente", command=self.validar_y_guardar, fg_color="green").pack(pady=(0, 20))

    def validar_y_guardar(self):
        placa = self.placa_var.get().upper().strip()
        dueno = self.dueno_var.get().strip()
        telefono = self.telefono_var.get().strip()
        email = self.email_var.get().strip()
        km_actual_str = self.km_actual_var.get().strip()
        km_prox_str = self.km_prox_var.get().strip()
        
        if not placa or not dueno or not km_actual_str or not km_prox_str: 
            messagebox.showwarning("Datos Incompletos", "Placa, Dueño y AMBOS Kilometrajes son obligatorios.")
            return
        
        try:
            km_actual = int(km_actual_str)
            km_proximo = int(km_prox_str)
            if km_actual < 0 or km_proximo < 0: raise ValueError
            if km_proximo <= km_actual: 
                 messagebox.showerror("Error de Lógica", "El KM Próximo debe ser mayor al KM Actual.")
                 return
        except ValueError:
            messagebox.showerror("Error de Dato", "Los kilometrajes deben ser números enteros positivos.")
            return

        self.callback_guardar(placa, dueno, telefono, email, km_actual, km_proximo) 
        self.destroy()


# **************************************************************
# BLOQUE 4: CLASE FORMULARIO EDICIÓN (MODIFICAR DATOS)
# TRABAJO QUE HACE: Ventana modal para editar información de clientes existentes.
# **************************************************************
class FormularioEdicion(ctk.CTkToplevel):
    """
    Ventana modal dedicada para cargar y editar todos los datos de un cliente existente.
    """
    def __init__(self, master, placa, datos_cliente, callback_guardar_edicion):
        super().__init__(master)
        self.title(f"✏️ Modificar Cliente: {placa}")
        self.placa = placa
        self.datos_cliente = datos_cliente
        self.callback_guardar_edicion = callback_guardar_edicion
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)

        self.placa_var = ctk.StringVar(value=placa)
        self.dueno_var = ctk.StringVar(value=datos_cliente.get('dueño', ''))
        self.telefono_var = ctk.StringVar(value=datos_cliente.get('telefono', ''))
        self.email_var = ctk.StringVar(value=datos_cliente.get('email', 'N/A')) 
        self.km_actual_var = ctk.StringVar(value=str(datos_cliente.get('kilometraje_actual', 0)))
        self.km_prox_var = ctk.StringVar(value=str(datos_cliente.get('prox_mantenimiento', 0)))

        self.crear_widgets_formulario()
        self.lift()
        self.attributes("-topmost", True)

    def crear_widgets_formulario(self):
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(self.frame_inputs, text="Placa:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        entry_placa = ctk.CTkEntry(self.frame_inputs, textvariable=self.placa_var, width=300, state="readonly")
        entry_placa.grid(row=0, column=1, padx=10, pady=(0, 10), sticky="ew")

        campos = [
            ("Dueño:", self.dueno_var, "Nombre completo"),
            ("Teléfono:", self.telefono_var, "Número de contacto"),
            ("Email:", self.email_var, "Correo electrónico"), 
            ("Kilometraje Actual:", self.km_actual_var, "Solo números (KM)"),
            ("KM Próximo Mantenimiento:", self.km_prox_var, "Próximo servicio KM")
        ]

        for i, (label_text, var, placeholder) in enumerate(campos):
            row_index = i + 1 
            ctk.CTkLabel(self.frame_inputs, text=label_text).grid(row=row_index, column=0, padx=10, pady=(10, 0), sticky="w")
            entry = ctk.CTkEntry(self.frame_inputs, textvariable=var, placeholder_text=placeholder, width=300)
            entry.grid(row=row_index, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkButton(self, text="💾 Guardar Cambios", command=self.validar_y_guardar, fg_color="blue").pack(pady=(0, 20))

    def validar_y_guardar(self):
        dueno = self.dueno_var.get().strip()
        telefono = self.telefono_var.get().strip()
        email = self.email_var.get().strip()
        km_actual_str = self.km_actual_var.get().strip()
        km_prox_str = self.km_prox_var.get().strip()

        if not dueno or not km_actual_str or not km_prox_str:
            messagebox.showwarning("Datos Incompletos", "Dueño, Kilometraje Actual y Próximo son obligatorios.")
            return

        try:
            km_actual = int(km_actual_str)
            km_proximo = int(km_prox_str)
            if km_actual < 0 or km_proximo < 0: raise ValueError
            if km_proximo < km_actual:
                 messagebox.showerror("Error de Lógica", "El KM Próximo no puede ser menor al KM Actual.")
                 return
        except ValueError:
            messagebox.showerror("Error de Dato", "Los kilometrajes deben ser números enteros positivos.")
            return

        self.callback_guardar_edicion(self.placa, dueno, telefono, email, km_actual, km_proximo)
        self.destroy()

# **************************************************************
# BLOQUE 5: CLASE PRINCIPAL TALLERAPP (INTERFAZ)
# TRABAJO QUE HACE: Controla la ventana principal, botones y tabla.
# **************************************************************
class TallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MotoTech Control")
        self.geometry("1500x600+50+20") 
        self.grid_rowconfigure(3, weight=1) 
        self.grid_columnconfigure(0, weight=1)
        self.registros_clientes = cargar_registros()
        self.crear_widgets()
        self.revisar_mantenimientos_gui()

    def crear_widgets(self):
        self.titulo = ctk.CTkLabel(self, text="Control MotoTech", 
                                    font=ctk.CTkFont(size=25, weight="bold"))
        self.titulo.grid(row=0, column=0, pady=25, padx=20, sticky="n") 

        self.frame_botones = ctk.CTkFrame(self)
        self.frame_botones.grid(row=1, column=0, pady=10, padx=40, sticky="ew") 
        
        self.btn_agregar = ctk.CTkButton(self.frame_botones, 
                                  text="➕  Agregar Cliente",
                                  width=140, height=50, 
                                  command=self.agregar_cliente_gui)
        self.btn_agregar.pack(side='left', padx=50)

        self.btn_modificar = ctk.CTkButton(self.frame_botones, 
                                         text="✏️  Modificar Cliente",
                                         width=140, height=50,
                                         command=self.modificar_cliente_gui)
        self.btn_modificar.pack(side='left', padx=50) 
                                          
        self.btn_eliminar = ctk.CTkButton(self.frame_botones, 
                                         text="🗑️  Eliminar Cliente",
                                         width=140, height=50,
                                         command=self.eliminar_cliente_gui)
        self.btn_eliminar.pack(side='left', padx=80)

        self.btn_mantenimiento = ctk.CTkButton(self.frame_botones, 
                                             text="⚙️ Revisar Mantenimiento", 
                                             width=100, height=50, 
                                             command=self.revisar_mantenimientos_gui)
        self.btn_mantenimiento.pack(side='left', padx=30)
        
        self.btn_whatsapp = ctk.CTkButton(self.frame_botones, 
                                          text="💬 Notificar WhatsApp", 
                                          fg_color="green", 
                                          width=100, 
                                          height=50, 
                                          command=self.notificar_cliente_seleccionado)
        self.btn_whatsapp.pack(side='left', padx=(30, 80)) 
        
        self.espaciador = ctk.CTkLabel(self.frame_botones, text="") 
        self.espaciador.pack(side='left', fill='x', expand=True)
        
        self.btn_guardar_salir = ctk.CTkButton(self.frame_botones, 
                                             text="💾 Guardar y Salir", 
                                             width=180, height=60, 
                                             command=self.on_closing) 
        self.btn_guardar_salir.pack(side='right', padx=10)

        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.grid(row=3, column=0, pady=10, padx=40, sticky="nsew") 

        self.tree = ttk.Treeview(self.frame_tabla, 
                                     columns=("dueño", "telefono", "km_actual", "km_prox"), 
                                     show='headings')
        
        s = ttk.Style()
        s.configure('Treeview.Heading', 
                    font=('Times New Roman', 12, 'bold italic')) 
        
        self.tree.heading("#0", text="Placa", anchor="w")
        self.tree.heading("dueño", text="Dueño de la moto", anchor="w")
        self.tree.heading("telefono", text="Teléfono del cliente", anchor="w")
        self.tree.heading("km_actual", text="KM Actual de la moto", anchor="w")
        self.tree.heading("km_prox", text="KM Próximo Mantenimiento de la moto", anchor="w")

        self.tree.column("#0", width=300, anchor="w", stretch=False)
        self.tree.column("dueño", width= 300, anchor="w")
        self.tree.column("telefono", width= 280, anchor="w")
        self.tree.column("km_actual", width=300, anchor="w")
        self.tree.column("km_prox", width=500, anchor="w")
        
        self.tree.pack(fill="both", expand=True)
        self.actualizar_vista_registros()

# **************************************************************
# BLOQUE 6: MÉTODOS CRUD (LÓGICA DE NEGOCIO)
# TRABAJO QUE HACE: Funciones para agregar, editar y borrar datos.
# **************************************************************
    def agregar_cliente_gui(self):
        FormularioCliente(self, self.guardar_registro_nuevo)

    def guardar_registro_nuevo(self, placa, dueno, telefono, email, km_actual, km_proximo): 
        if placa in self.registros_clientes:
            messagebox.showerror("Error", f"La placa {placa} ya está registrada.")
            return 
        
        self.registros_clientes[placa] = {
            "dueño": dueno,
            "telefono": telefono,
            "email": email,
            "kilometraje_actual": km_actual,
            "prox_mantenimiento": km_proximo 
        }
        
        guardar_registros(self.registros_clientes)
        messagebox.showinfo("Éxito", f"¡Vehículo {placa} agregado con éxito! Próximo servicio a {km_proximo} KM.")
        self.actualizar_vista_registros()

    def modificar_cliente_gui(self):
        item_seleccionado = self.tree.focus() 
        if not item_seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo de la lista para modificar.")
            return
        placa_a_modificar = self.tree.item(item_seleccionado, "text")
        datos_actuales = self.registros_clientes[placa_a_modificar]
        FormularioEdicion(self, placa_a_modificar, datos_actuales, self.guardar_edicion)

    def guardar_edicion(self, placa, dueno, telefono, email, km_actual, km_proximo):
        self.registros_clientes[placa] = {
            "dueño": dueno,
            "telefono": telefono,
            "email": email, 
            "kilometraje_actual": km_actual,
            "prox_mantenimiento": km_proximo
        }
        guardar_registros(self.registros_clientes)
        messagebox.showinfo("Éxito", f"Registro de {placa} actualizado correctamente.")
        self.actualizar_vista_registros()

    def eliminar_cliente_gui(self):
        item_seleccionado = self.tree.focus()
        if not item_seleccionado:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un vehículo de la lista para eliminar.")
            return
        placa_a_eliminar = self.tree.item(item_seleccionado, "text")
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro?"):
            if placa_a_eliminar in self.registros_clientes:
                del self.registros_clientes[placa_a_eliminar]
                messagebox.showinfo("Éxito", f"Vehículo {placa_a_eliminar} ELIMINADO.")
                self.actualizar_vista_registros() 

# **************************************************************
# BLOQUE 7: MANTENIMIENTO Y NOTIFICACIONES
# TRABAJO QUE HACE: Revisa alertas de KM y envía mensajes por WhatsApp.
# **************************************************************
    def revisar_mantenimientos_gui(self):
        if not self.registros_clientes:
            messagebox.showinfo("Revisión", "La base de datos está vacía.")
            return
        reporte = ""
        clientes_a_notificar = 0
        for placa, datos in self.registros_clientes.items():
            km_actual = datos.get('kilometraje_actual', 0)
            km_proximo = datos.get('prox_mantenimiento', 0)
            km_faltantes = km_proximo - km_actual
            if km_faltantes <= MARGEN_ALERTA: 
                estado = "🚨 URGENTE" if km_faltantes <= 0 else "🔔 PRÓXIMO"
                reporte += f"{estado} - Placa: {placa}\n"
                reporte += f"   Dueño: {datos['dueño']}. Tel: {datos['telefono']}\n"
                reporte += f"   Mantenimiento a {km_proximo} KM. Faltan {km_faltantes} KM.\n\n"
                clientes_a_notificar += 1
        if clientes_a_notificar > 0:
            messagebox.showinfo("Reporte", f"Se encontraron {clientes_a_notificar} vehículos en alerta:\n\n" + reporte)
        else:
            messagebox.showinfo("Reporte", "¡Todo al día!")

    def actualizar_vista_registros(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for placa, datos in self.registros_clientes.items():
            self.tree.insert("", "end", text=placa, 
                             values=(datos['dueño'], datos['telefono'], 
                                     datos['kilometraje_actual'], datos['prox_mantenimiento']))

    def enviar_notificacion_whatsapp(self, placa):
        if placa not in self.registros_clientes:
            messagebox.showerror("Error", f"Placa no registrada.")
            return
        datos = self.registros_clientes[placa]
        telefono = datos.get('telefono', '').strip()
        km_prox = datos.get('prox_mantenimiento', 0)
        dueno = datos.get('dueño', 'Estimado cliente')
        if not telefono or not telefono.isdigit():
            messagebox.showwarning("Advertencia", f"Teléfono no válido.")
            return
        mensaje_base = (f"Hola {dueno.split()[0]}, somos MotoTech Control. "
                        f"Mantenimiento para placa {placa} a los {km_prox} KM.")
        mensaje_codificado = urllib.parse.quote(mensaje_base) 
        url = f"https://wa.me/{telefono}?text={mensaje_codificado}"
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir navegador: {e}")

    def notificar_cliente_seleccionado(self):
        item_seleccionado = self.tree.focus() 
        if not item_seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo.")
            return
        placa_a_notificar = self.tree.item(item_seleccionado, "text")
        self.enviar_notificacion_whatsapp(placa_a_notificar)

    def on_closing(self):
        guardar_registros(self.registros_clientes)
        self.destroy() 

# **************************************************************
# BLOQUE 8: INICIO DE LA APLICACIÓN
# TRABAJO QUE HACE: Lanza el bucle principal (MainLoop) del programa.
# **************************************************************
if __name__ == "__main__":
    try:
        app = TallerApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing) 
        app.mainloop()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        messagebox.showerror("Error Crítico", f"Detalle: {e}")