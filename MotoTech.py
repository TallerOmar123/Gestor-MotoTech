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
    try:
        if os.path.exists(ARCHIVO_REGISTROS):
            with open(ARCHIVO_REGISTROS, 'r') as file:
                return json.load(file)
        return {}
    except Exception:
        # Retorna diccionario vacío si hay error o no existe el archivo
        return {}

def guardar_registros(registros: Dict[str, Any]) -> bool:
    """Guarda los registros en el archivo JSON."""
    try:
        with open(ARCHIVO_REGISTROS, 'w') as file:
            json.dump(registros, file, indent=4)
        return True
    except IOError:
        messagebox.showerror("Error de Guardado", "No se pudo guardar el archivo de registros.")
        return False
        
# -----------------------------------------------------------
# 2. CLASE PRINCIPAL DE LA APLICACIÓN (TallerAppProFinal)
# -----------------------------------------------------------
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue") 

class TallerAppProFinal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MotoTech Control PRO (Final)")
        self.geometry("1400x750+50+20") 
        
        # Base de Datos en Memoria
        self.registros_clientes = cargar_registros()

        # Configuración de Layout Adaptable (Grid)
        self.grid_rowconfigure(3, weight=1) 
        self.grid_columnconfigure(0, weight=1) 
        
        self.crear_widgets()
        self.actualizar_vista_registros()
        
    def crear_widgets(self):
        
        # 1. TÍTULO PRINCIPAL (Fila 0)
        self.titulo = ctk.CTkLabel(self, text="Gestor de Mantenimiento PRO", 
                                   font=ctk.CTkFont(size=30, weight="bold"))
        self.titulo.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="n")

        # 2. DASHBOARD / BÚSQUEDA (Fila 1)
        self.dashboard_frame = ctk.CTkFrame(self)
        self.dashboard_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.dashboard_frame.grid_columnconfigure((0, 2), weight=1)
        
        # BÚSQUEDA EN VIVO
        ctk.CTkLabel(self.dashboard_frame, text="🔍 Búsqueda Rápida:").grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        self.entry_busqueda = ctk.CTkEntry(self.dashboard_frame, placeholder_text="Filtrar por Placa, Dueño o Teléfono", width=350)
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_registros)
        self.entry_busqueda.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Botón de Guardar y Salir
        self.btn_guardar_salir = ctk.CTkButton(self.dashboard_frame, 
                                               text="💾 Guardar y Salir", 
                                               fg_color="red", hover_color="#8B0000",
                                               width=150, height=40,
                                               command=self.on_closing) 
        self.btn_guardar_salir.grid(row=0, column=2, padx=(10, 20), pady=10, sticky="e")
        
        # 3. MARCO CONTENEDOR DE BOTONES CRUD (Fila 2)
        self.frame_botones = ctk.CTkFrame(self)
        self.frame_botones.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.frame_botones.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_agregar = ctk.CTkButton(self.frame_botones)