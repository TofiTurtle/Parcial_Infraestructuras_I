"""
Cómo ejecutarlo:
    python vida_secuencial.py              -> abre la interfaz gráfica
    python vida_secuencial.py benchmark    -> mide tiempos (sin interfaz)
"""

import random
import sys
import time
import tkinter as tk

# 1. CONFIGURACIÓN 

FILAS = 40              # Número de filas de la matriz (para la interfaz)
COLUMNAS = 40           # Número de columnas de la matriz (para la interfaz)
TAM_CELDA = 15          # Tamaño en píxeles de cada celda 
VELOCIDAD_MS = 100      # Milisegundos entre generaciones en la interfaz
PROB_VIVA = 0.25        # Probabilidad de que una celda nazca viva al azar

COLOR_VIVA = "black"
COLOR_MUERTA = "white"

VIVA = 1                # Representamos una célula viva con 1
MUERTA = 0              # Representamos una célula muerta con 0

# 2. LÓGICA DEL JUEGO 

def crear_matriz_vacia(filas, columnas):
    """Crea una matriz de filas x columnas con todas las células muertas."""
    return [[MUERTA] * columnas for _ in range(filas)]


def crear_matriz_aleatoria(filas, columnas, prob_viva=PROB_VIVA):
    """Crea una matriz donde cada célula está viva con probabilidad prob_viva."""
    matriz = crear_matriz_vacia(filas, columnas)
    for f in range(filas):
        for c in range(columnas):
            if random.random() < prob_viva:
                matriz[f][c] = VIVA
    return matriz


def contar_vecinos_vivos(matriz, fila, col):
    """
    Cuenta cuántos de los 8 vecinos de la celda (fila, col) están vivos.

    Los vecinos son las celdas que rodean a la celda actual:

        (-1,-1) (-1, 0) (-1,+1)
        ( 0,-1)  CELDA  ( 0,+1)
        (+1,-1) (+1, 0) (+1,+1)

    """
    filas = len(matriz)
    columnas = len(matriz[0])
    vecinos_vivos = 0

    # Recorremos el desplazamiento en las filas (-1, 0, +1)
    for df in (-1, 0, 1):
        # Y el desplazamiento en las columnas (-1, 0, +1)
        for dc in (-1, 0, 1):

            # (0, 0) es la propia celda, no es su vecina: la saltamos
            if df == 0 and dc == 0:
                continue

            f_vecino = fila + df
            c_vecino = col + dc

            # Solo contamos si el vecino está dentro de la matriz
            if 0 <= f_vecino < filas and 0 <= c_vecino < columnas:
                vecinos_vivos += matriz[f_vecino][c_vecino]

    return vecinos_vivos


def siguiente_generacion(matriz):
    """
    Calcula la siguiente generación aplicando las reglas de Conway.

    Reglas:
      Célula viva:
        - menos de 2 vecinos vivos  -> muere (soledad)
        - 2 o 3 vecinos vivos       -> sobrevive
        - más de 3 vecinos vivos    -> muere (sobrepoblación)
      Célula muerta:
        - exactamente 3 vecinos     -> nace
    """
    filas = len(matriz)
    columnas = len(matriz[0])
    nueva = crear_matriz_vacia(filas, columnas)

    # Este doble ciclo es lo que se repartirá entre hilos/procesos
    # en la versión paralela (por ejemplo, dando bloques de filas a cada uno).
    for f in range(filas):
        for c in range(columnas):
            vecinos = contar_vecinos_vivos(matriz, f, c)

            if matriz[f][c] == VIVA:
                # Regla de la célula viva: sobrevive con 2 o 3 vecinos
                if vecinos == 2 or vecinos == 3:
                    nueva[f][c] = VIVA
                # En cualquier otro caso queda en MUERTA (ya es 0 por defecto)
            else:
                # Regla de la célula muerta: nace con exactamente 3 vecinos
                if vecinos == 3:
                    nueva[f][c] = VIVA

    return nueva


# ======================================================================
# 3. BENCHMARK (medición de tiempos para el análisis de rendimiento)
# ======================================================================

def medir_tiempo(tamano, generaciones):
    """
    Ejecuta `generaciones` pasos sobre una matriz de tamano x tamano
    y devuelve el tiempo total en segundos.
    """
    random.seed(67)  # Semilla fija: así todas las versiones parten del mismo tablero
    matriz = crear_matriz_aleatoria(tamano, tamano)

    inicio = time.perf_counter()          
    for _ in range(generaciones):
        matriz = siguiente_generacion(matriz)
    fin = time.perf_counter()

    return fin - inicio


def ejecutar_benchmark():
    """Mide el tiempo secuencial para varios tamaños de matriz."""
    tamanos = [100, 500, 1000]   # Tamaños pedidos en el enunciado
    generaciones = 5             # Pocas generaciones: 1000x1000 en Python es lento

    print(f"Benchmark secuencial ({generaciones} generaciones por tamaño)")
    print("-" * 52)
    print(f"{'Tamaño':>12} | {'Tiempo total (s)':>18} | {'Por generación (s)':>18}")
    print("-" * 52)

    for n in tamanos:
        total = medir_tiempo(n, generaciones)
        print(f"{n:>5}x{n:<6} | {total:>18.4f} | {total / generaciones:>18.4f}")


# ======================================================================
# 4. INTERFAZ GRÁFICA (tkinter)
# ======================================================================

class JuegoDeLaVidaGUI:
    """Ventana que dibuja la matriz y permite simular el juego."""

    def __init__(self, ventana, filas, columnas):
        self.ventana = ventana
        self.ventana.title("Juego de la Vida - Versión Secuencial")
        self.filas = filas
        self.columnas = columnas

        # Estado del juego
        self.matriz = crear_matriz_aleatoria(filas, columnas)
        self.generacion = 0
        self.corriendo = False       # True mientras la simulación está activa

        # --- Lienzo donde se dibujan las celdas ---
        self.canvas = tk.Canvas(
            ventana,
            width=columnas * TAM_CELDA,
            height=filas * TAM_CELDA,
            bg=COLOR_MUERTA,
        )
        self.canvas.pack()

        # Creamos un rectángulo por celda UNA sola vez y guardamos su id.
        # Después solo le cambiamos el color (es más rápido que redibujar).
        self.rectangulos = []
        for f in range(filas):
            fila_rects = []
            for c in range(columnas):
                x1 = c * TAM_CELDA
                y1 = f * TAM_CELDA
                x2 = x1 + TAM_CELDA
                y2 = y1 + TAM_CELDA
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=COLOR_MUERTA, outline="lightgray"
                )
                fila_rects.append(rect)
            self.rectangulos.append(fila_rects)

        # Clic sobre una celda -> cambia su estado (viva/muerta)
        self.canvas.bind("<Button-1>", self.al_hacer_clic)

        # --- Etiqueta de información ---
        self.etiqueta = tk.Label(ventana, text="", font=("Arial", 11))
        self.etiqueta.pack(pady=4)

        # --- Botones ---
        panel = tk.Frame(ventana)
        panel.pack(pady=4)

        self.btn_iniciar = tk.Button(panel, text="Iniciar", width=10,
                                     command=self.alternar_simulacion)
        self.btn_iniciar.grid(row=0, column=0, padx=3)

        tk.Button(panel, text="Paso", width=10,
                  command=self.avanzar_un_paso).grid(row=0, column=1, padx=3)

        tk.Button(panel, text="Aleatorio", width=10,
                  command=self.reiniciar_aleatorio).grid(row=0, column=2, padx=3)

        tk.Button(panel, text="Limpiar", width=10,
                  command=self.limpiar).grid(row=0, column=3, padx=3)

        self.dibujar()

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def dibujar(self, tiempo_calculo=None):
        """Pinta cada celda según su estado actual."""
        for f in range(self.filas):
            for c in range(self.columnas):
                color = COLOR_VIVA if self.matriz[f][c] == VIVA else COLOR_MUERTA
                self.canvas.itemconfig(self.rectangulos[f][c], fill=color)

        # Contamos las células vivas sumando todas las filas
        vivas = sum(sum(fila) for fila in self.matriz)
        texto = f"Generación: {self.generacion}   |   Células vivas: {vivas}"
        if tiempo_calculo is not None:
            texto += f"   |   Cálculo: {tiempo_calculo * 1000:.2f} ms"
        self.etiqueta.config(text=texto)

    # ------------------------------------------------------------------
    # Acciones de los botones
    # ------------------------------------------------------------------
    def avanzar_un_paso(self):
        """Calcula y muestra UNA generación (midiendo cuánto tarda)."""
        inicio = time.perf_counter()
        self.matriz = siguiente_generacion(self.matriz)
        tiempo = time.perf_counter() - inicio

        self.generacion += 1
        self.dibujar(tiempo)

    def alternar_simulacion(self):
        """Botón Iniciar/Pausar."""
        self.corriendo = not self.corriendo
        if self.corriendo:
            self.btn_iniciar.config(text="Pausar")
            self.bucle_simulacion()
        else:
            self.btn_iniciar.config(text="Iniciar")

    def bucle_simulacion(self):
        """Avanza una generación y se vuelve a programar mientras esté corriendo."""
        if self.corriendo:
            self.avanzar_un_paso()
            # after() llama a esta misma función dentro de VELOCIDAD_MS milisegundos
            self.ventana.after(VELOCIDAD_MS, self.bucle_simulacion)

    def reiniciar_aleatorio(self):
        """Genera un tablero nuevo con células al azar."""
        self.matriz = crear_matriz_aleatoria(self.filas, self.columnas)
        self.generacion = 0
        self.dibujar()

    def limpiar(self):
        """Deja todas las células muertas (útil para dibujar tus propios patrones)."""
        self.matriz = crear_matriz_vacia(self.filas, self.columnas)
        self.generacion = 0
        self.dibujar()

    def al_hacer_clic(self, evento):
        """Invierte el estado de la celda donde el usuario hizo clic."""
        c = evento.x // TAM_CELDA     # Columna = posición x dividida por el tamaño
        f = evento.y // TAM_CELDA     # Fila = posición y dividida por el tamaño
        if 0 <= f < self.filas and 0 <= c < self.columnas:
            self.matriz[f][c] = MUERTA if self.matriz[f][c] == VIVA else VIVA
            self.dibujar()


def iniciar_interfaz():
    """Crea la ventana principal y arranca la aplicación."""
    if tk is None:
        print("tkinter no está disponible en este equipo.")
        print("Usa el modo benchmark: python vida_secuencial.py benchmark")
        return
    ventana = tk.Tk()
    JuegoDeLaVidaGUI(ventana, FILAS, COLUMNAS)
    ventana.mainloop()


# ======================================================================
# 5. PUNTO DE ENTRADA
# ======================================================================

if __name__ == "__main__":
    # Si se ejecuta con el argumento "benchmark" -> mide tiempos
    # En cualquier otro caso -> abre la interfaz gráfica
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        ejecutar_benchmark()
    else:
        iniciar_interfaz()