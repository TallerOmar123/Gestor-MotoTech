import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from typing import Dict, Any, Optional





# -----------------------------------------------------------
# 1. LÓGICA DE NEGOCIO Y PERSISTENCIA
# -----------------------------------------------------------
MARGEN_ALERTA = 5000  # KM para notificar mantenimiento
MARGEN_URGENTE = 1000 # KM para alerta roja
ARCHIVO_REGISTROS = "registros.json" 





def cargar_registros() -> Dict[str, Any]:
    """Carga los registros desde el archivo JSON de forma robusta."""
    # --- SUB-BLOQUE: VERIFICACIÓN DE INTEGRIDAD ---
    # Intenta localizar el archivo en el sistema para evitar errores de "archivo no encontrado".
    try:
        if os.path.exists(ARCHIVO_REGISTROS):
            with open(ARCHIVO_REGISTROS, 'r') as file:
                # --- SUB-BLOQUE: DESERIALIZACIÓN ---
                # Convierte el texto del JSON en un diccionario de Python usable.
                return json.load(file)
        return {}
    except Exception:
        # --- SUB-BLOQUE: RESPALDO ---
        # Si el JSON está mal formado, devuelve un diccionario vacío para no bloquear el inicio.
        return {}





def guardar_registros(registros: Dict[str, Any]) -> bool:
    """Guarda los registros en el archivo JSON."""
    # --- SUB-BLOQUE: PERSISTENCIA FÍSICA ---
    # Abre el archivo en modo escritura ('w') para volcar los datos de la memoria al disco.
    try:
        with open(ARCHIVO_REGISTROS, 'w') as file:
            # --- SUB-BLOQUE: FORMATEO ---
            # Aplica un indent de 4 espacios para que el archivo sea fácil de leer por humanos.
            json.dump(registros, file, indent=4)
        return True
    except IOError:
        # --- SUB-BLOQUE: GESTIÓN DE ERRORES CRÍTICOS ---
        # Notifica al usuario si el sistema no tiene permisos o el disco está lleno.
        messagebox.showerror("Error de Guardado", "No se pudo guardar el archivo de registros.")
        return False
        




# -----------------------------------------------------------
# 2. CLASE PRINCIPAL DE LA APLICACIÓN (TallerAppProFinal)
# -----------------------------------------------------------
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue") 





class TallerAppProFinal(ctk.CTk):
    def __init__(self):
        # --- SUB-BLOQUE: INICIALIZACIÓN DE VENTANA ---
        # Configura las propiedades básicas como título, tamaño y posición en pantalla.
        super().__init__()
        self.title("MotoTech Control PRO (Final)")
        self.geometry("1400x750+50+20") 
        
        # --- SUB-BLOQUE: CARGA DE DATOS ---
        # Invoca la función de carga para tener la base de datos lista en memoria RAM.
        self.registros_clientes = cargar_registros()

        # --- SUB-BLOQUE: DISEÑO ELÁSTICO ---
        # Configura el comportamiento de las filas y columnas para que la app se adapte al estirar la ventana.
        self.grid_rowconfigure(3, weight=1) 
        self.grid_columnconfigure(0, weight=1) 
        
        self.crear_widgets()
        self.actualizar_vista_registros()
        




    def crear_widgets(self):
        
        # 1. TÍTULO PRINCIPAL (Fila 0)
        # --- SUB-BLOQUE: ELEMENTOS VISUALES ---
        # Creación de la etiqueta de encabezado con fuente personalizada.
        self.titulo = ctk.CTkLabel(self, text="Gestor de Mantenimiento PRO", 
                                   font=ctk.CTkFont(size=30, weight="bold"))
        self.titulo.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="n")


        # 2. DASHBOARD / BÚSQUEDA (Fila 1)
        # --- SUB-BLOQUE: PANEL DE CONTROL SUPERIOR ---
        # Contenedor para las herramientas de filtrado y el botón de salida segura.
        self.dashboard_frame = ctk.CTkFrame(self)
        self.dashboard_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.dashboard_frame.grid_columnconfigure((0, 2), weight=1)
        
        # BÚSQUEDA EN VIVO
        # --- SUB-BLOQUE: SISTEMA DE EVENTOS ---
        # Vincula la tecla "KeyRelease" a la función de filtrado para buscar mientras el usuario escribe.
        ctk.CTkLabel(self.dashboard_frame, text="🔍 Búsqueda Rápida:").grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        self.entry_busqueda = ctk.CTkEntry(self.dashboard_frame, placeholder_text="Filtrar por Placa, Dueño o Teléfono", width=350)
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_registros)
        self.entry_busqueda.grid(row=0, column=1, padx=5, pady=10, sticky="ew")


        # Botón de Guardar y Salir
        # --- SUB-BLOQUE: SALIDA SEGURA ---
        # Botón configurado en color rojo para advertir que cierra la sesión guardando cambios.
        self.btn_guardar_salir = ctk.CTkButton(self.dashboard_frame, 
                                               text="💾 Guardar y Salir", 
                                               fg_color="red", hover_color="#8B0000",
                                               width=150, height=40,
                                               command=self.on_closing) 
        self.btn_guardar_salir.grid(row=0, column=2, padx=(10, 20), pady=10, sticky="e")
        

        # 3. MARCO CONTENEDOR DE BOTONES CRUD (Fila 2)
        # --- SUB-BLOQUE: BOTONERA DE OPERACIONES ---
        # Organiza los botones de Agregar, Editar, Historial y Eliminar en una cuadrícula proporcional.
        self.frame_botones = ctk.CTkFrame(self)
        self.frame_botones.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.frame_botones.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_agregar = ctk.CTkButton(self.frame_botones)