#¿Qué funciones cumplen estas librerías?
#customtkinter (ctk): Es la evolución moderna de Tkinter. Permite que tu aplicación tenga un 
#aspecto actual (Modo Oscuro/Claro, bordes redondeados, botones estilizados) similar a una 
#app de Windows 11 o macOS.

#tkinter (ttk, messagebox, simpledialog): Proporciona los componentes base de la interfaz, 
#como ventanas de alerta para mensajes de error y cuadros para entrada de datos simples.

#json y os: Se encargan de la "memoria" del programa. Permiten guardar y leer la información 
#de tus clientes en archivos físicos en el computador.

#typing (Dict, Any, Optional): Se utiliza para el Tipado de Datos, lo que hace que tu código 
#sea más profesional y fácil de depurar al definir exactamente qué tipo de información entra 
#y sale de cada función.

import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from typing import Dict, Any, Optional




#🔍 Configuración del Núcleo Operativo
#Este bloque establece las "reglas del juego" para el funcionamiento automático de tu 
#aplicación:

#MARGEN_ALERTA (5000 km): Define el ciclo de vida estándar para el mantenimiento preventivo. 
#El sistema usará este valor como punto de referencia para notificar al cliente que su 
#servicio está próximo.

#MARGEN_URGENTE (1000 km): Establece el umbral de riesgo. Cuando la diferencia de kilometraje 
#cae por debajo de este número, el sistema prioriza el registro con alertas visuales 
#(normalmente resaltado en rojo) debido al riesgo de falla mecánica.

#ARCHIVO_REGISTROS: Centraliza el almacenamiento. Al definirlo como una constante, 
#facilitas que todo el programa sepa exactamente dónde guardar y leer la base de datos 
#de clientes, evitando duplicidad de archivos.

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
        




#🔍 Configuración de Identidad y Entorno
#set_appearance_mode("System"): Esta instrucción permite que la aplicación sea "consciente" 
#del entorno del usuario. Si el sistema operativo cambia a Modo Oscuro, la interfaz se 
#adaptará automáticamente sin necesidad de reiniciar el programa, mejorando la ergonomía visual.

#set_default_color_theme("blue"): Define el ADN visual de la herramienta. El tema azul 
#establece una jerarquía de colores profesional para botones, interruptores y barras 
#de progreso, asegurando que la interfaz se sienta moderna y confiable.

# -----------------------------------------------------------
# 2. CLASE PRINCIPAL DE LA APLICACIÓN (TallerAppProFinal)
# -----------------------------------------------------------
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue") 







#🔍 Arquitectura del Constructor (__init__)
#Este bloque de código es el punto de partida que ensambla toda la aplicación:

#Inicialización de Ventana: Define un espacio de trabajo amplio (1400x750 píxeles) 
#diseñado para visualizar tablas de datos complejas. El uso de super().__init__() asegura 
#que todas las herramientas modernas de CTk estén disponibles.

#Gestión de Datos en Memoria: Almacena la base de datos en self.registros_clientes 
#inmediatamente al abrir el programa. Esto garantiza que la navegación sea instantánea, 
#ya que los datos están listos en la RAM.

#Diseño Elástico (Layout Manager): Configura el sistema de rejilla (grid_rowconfigure) 
#para que, si el usuario maximiza la ventana, los componentes (como la tabla de clientes) 
#se estiren proporcionalmente, evitando espacios vacíos o cortes en la interfaz.


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
        








#🔍 Construcción de la Interfaz Operativa
#Este bloque define cómo interactúa el usuario con el software:

#Encabezado Corporativo: Utiliza CTkLabel con tipografía escalada para establecer la 
#identidad visual de la herramienta desde el primer contacto.

#Dashboard de Búsqueda Reactiva: * El uso de self.entry_busqueda.bind("<KeyRelease>", ...) 
#es clave, ya que activa el filtrado en tiempo real. Cada vez que el usuario suelta una 
#tecla, la interfaz se actualiza sin necesidad de presionar "Enter".

#El diseño usa un CTkFrame con expansión horizontal (sticky="ew") para que las 
#herramientas de búsqueda se vean uniformes en cualquier tamaño de pantalla.

#Módulo de Salida Segura: El botón de "Guardar y Salir" está diferenciado cromáticamente 
#en rojo (fg_color="red"). Esto es una convención de diseño para indicar una acción d
#definitiva que invoca el método on_closing, garantizando que ningún dato se pierda al 
#cerrar el programa.

#Matriz de Gestión (CRUD): Prepara un contenedor especializado (frame_botones) 
#con un sistema de pesos equitativos (weight=1), lo que permite que los botones de 
#administración se distribuyan perfectamente de forma simétrica.




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