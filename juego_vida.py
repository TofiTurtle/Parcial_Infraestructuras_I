# JUEGO DE LA VIDA DE CONWAY
# Implementación secuencial + paralela (multiprocessing) + interfaz gráfica con Pygame

# ============================================================
# 1. CONFIGURACIÓN DEL PROGRAMA
DIMENSION_MATRIZ = 100       # Tamaño de la matriz: DIMENSION x DIMENSION
MODO = "paralelo"            # "secuencial" o "paralelo"
NUM_PROCESOS = 4             # Número de procesos (solo se usa en modo paralelo)
TAM_VENTANA = 700            # Tamaño de la ventana en píxeles
COLOR_MUERTA = (18, 18, 18)
COLOR_VIVA = (0, 230, 118)
RETARDO_REPETICION = 0.3     # Segundos antes de comenzar el avance continuo
INTERVALO_REPETICION = 0.05  # Tiempo mínimo entre generaciones
FPS = 60

# ============================================================
# 2. IMPORTACIONES
import random
import time
from multiprocessing import Pool
import numpy as np
import pygame

# ============================================================
# 3. CONFIGURACIÓN DEPENDIENTE DE PYGAME

TECLAS_AVANCE = (
    pygame.K_SPACE,
    pygame.K_PAUSE,
    pygame.K_RETURN,
    pygame.K_KP_ENTER
)

PALETA = np.array(
    [COLOR_MUERTA, COLOR_VIVA],
    dtype=np.uint8
)

# ============================================================
# 4. FUNCIONES GENERALES

def generar_matriz_aleatoria(dim):
    """
    Genera una matriz cuadrada de tamaño dim x dim.

    Cada posición contiene:
        0 -> célula muerta
        1 -> célula viva
    """

    matriz = [
        [
            random.randint(0, 1)
            for _ in range(dim)
        ]
        for _ in range(dim)
    ]

    return matriz


def imprimir_matriz(matriz):
    """
    Imprime una matriz en la terminal de forma legible.
    """

    for fila in matriz:
        print(" ".join(map(str, fila)))


def copiar_matriz(matriz):
    """
    Crea una copia independiente de una matriz.
    """

    return [fila[:] for fila in matriz]


# ============================================================
# 5. LÓGICA DEL JUEGO

def conteo_vecinos(m, i, j):
    """
    Cuenta cuántos vecinos vivos tiene la célula
    ubicada en la posición [i][j].

    Una célula puede tener como máximo 8 vecinos.
    """

    cont = 0

    # Recorremos las posiciones vecinas
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):

            # No contamos la propia célula
            if di == 0 and dj == 0:
                continue

            fila = i + di
            columna = j + dj

            # Verificamos que el vecino esté dentro de la matriz
            if (
                0 <= fila < len(m)
                and 0 <= columna < len(m)
            ):

                # Si el vecino está vivo, lo contamos
                if m[fila][columna] == 1:
                    cont += 1

    return cont


def calcular_filas(m, inicio, fin):
    """
    Calcula la siguiente generación SOLO de las filas
    [inicio, fin) y devuelve esas filas ya calculadas.

    Esta función es la que comparten la versión secuencial
    y la paralela, así la comparación de tiempos es justa.

    No modifica la matriz m: solo la lee. Por eso varios
    procesos pueden trabajar al tiempo sin condiciones de carrera.
    """

    filas_nuevas = []

    for i in range(inicio, fin):

        fila_nueva = []

        for j in range(len(m)):

            vecinos = conteo_vecinos(m, i, j)

            # Célula viva: sobrevive solo con 2 o 3 vecinos
            if m[i][j] == 1:
                if vecinos == 2 or vecinos == 3:
                    fila_nueva.append(1)
                else:
                    fila_nueva.append(0)

            # Célula muerta: revive solo con exactamente 3 vecinos
            else:
                if vecinos == 3:
                    fila_nueva.append(1)
                else:
                    fila_nueva.append(0)

        filas_nuevas.append(fila_nueva)

    return filas_nuevas


# ============================================================
# 6. IMPLEMENTACIÓN SECUENCIAL

def siguiente_generacion_seq(m):
    """
    Calcula una generación completa del Juego de la Vida
    con un solo proceso: procesa todas las filas de una vez.
    """

    return calcular_filas(m, 0, len(m))


# ============================================================
# 7. IMPLEMENTACIÓN PARALELA (multiprocessing)

def dividir_filas(n, num_procesos):
    """
    Divide n filas en num_procesos bloques de filas seguidas.

    Devuelve una lista de tuplas (inicio, fin). Si n no se
    reparte exacto, los primeros bloques reciben una fila extra.
    Ejemplo: dividir_filas(10, 3) -> [(0, 4), (4, 7), (7, 10)]
    """

    base = n // num_procesos
    sobrantes = n % num_procesos

    rangos = []
    inicio = 0

    for k in range(num_procesos):
        fin = inicio + base
        if k < sobrantes:
            fin += 1
        rangos.append((inicio, fin))
        inicio = fin

    return rangos


def trabajador(tarea):
    """
    Función que ejecuta cada proceso trabajador.

    Recibe una tupla (m, inicio, fin) y calcula su bloque de filas.
    """

    m, inicio, fin = tarea
    return calcular_filas(m, inicio, fin)


def siguiente_generacion_par(m, pool, num_procesos):
    """
    Calcula una generación completa repartiendo las filas
    entre varios procesos.

    Cada proceso recibe la generación actual (solo lectura) y
    calcula su bloque de filas. pool.map espera a que TODOS
    terminen antes de continuar (funciona como una barrera),
    y recién ahí se unen los bloques en la nueva matriz.
    """

    rangos = dividir_filas(len(m), num_procesos)

    # Una tarea por proceso: la matriz y su rango de filas
    tareas = [(m, inicio, fin) for inicio, fin in rangos]

    # Aquí se reparte el trabajo y se espera a todos (barrera)
    bloques = pool.map(trabajador, tareas)

    # Unimos los bloques en orden para formar la nueva matriz
    nueva = []
    for bloque in bloques:
        nueva.extend(bloque)

    return nueva


# ============================================================
# 8. FUNCIONES DE LA INTERFAZ GRÁFICA

def matriz_a_superficie(m):
    """
    Convierte una matriz de 0 y 1 en una superficie de Pygame.
    """

    # Convertimos la matriz de Python a NumPy
    arr = np.array(m, dtype=np.uint8)

    # Convertimos 0 y 1 en sus respectivos colores
    rgb = PALETA[arr]

    # Pygame espera las dimensiones en otro orden
    rgb = rgb.swapaxes(0, 1)

    # Convertimos el arreglo en una superficie de Pygame
    superficie = pygame.surfarray.make_surface(rgb)

    # Ajustamos la imagen al tamaño de la ventana
    superficie = pygame.transform.scale(
        superficie,
        (TAM_VENTANA, TAM_VENTANA)
    )

    return superficie


def crear_titulo(dim, generacion, modo, tiempo_calculo=None):
    """
    Crea el texto que aparecerá en el título de la ventana.
    """

    texto = (
        f"La vida {dim}x{dim} ({modo}) "
        f"- Generación {generacion}"
        f" | Espacio/Enter: avanzar"
        f" | Esc: salir"
    )

    if tiempo_calculo is not None:
        texto += f" | Último cálculo: {tiempo_calculo:.2f}s"

    return texto


# ============================================================
# 9. EJECUCIÓN DEL JUEGO

def ejecutar(dim, modo, num_procesos):
    """
    Ejecuta el Juego de la Vida utilizando Pygame.

    modo puede ser "secuencial" o "paralelo".
    """

    print(f"Generando matriz {dim}x{dim} en modo {modo}...")

    # --------------------------------------------------------
    # Crear matriz inicial

    matriz_actual = generar_matriz_aleatoria(dim)

    generacion = 1

    # --------------------------------------------------------
    # Crear los procesos trabajadores (solo en modo paralelo)
    # Se crean una sola vez y se reutilizan en cada generación

    pool = None

    if modo == "paralelo":
        pool = Pool(processes=num_procesos)

    # --------------------------------------------------------
    # Inicializar Pygame

    pygame.init()

    pantalla = pygame.display.set_mode(
        (TAM_VENTANA, TAM_VENTANA)
    )

    reloj = pygame.time.Clock()

    # --------------------------------------------------------
    # Preparar primera imagen
    # --------------------------------------------------------

    imagen = matriz_a_superficie(matriz_actual)

    pygame.display.set_caption(
        crear_titulo(dim, generacion, modo)
    )

    # --------------------------------------------------------
    # Variables para controlar las teclas

    t_inicio_pulsacion = 0.0
    t_ultimo_paso = 0.0

    corriendo = True

    # ========================================================
    # BUCLE PRINCIPAL

    while corriendo:

        ahora = time.perf_counter()

        avanzar = False

        # ----------------------------------------------------
        # Revisar eventos de Pygame

        for evento in pygame.event.get():

            # Cerrar la ventana
            if evento.type == pygame.QUIT:
                corriendo = False

            # Detectar teclas
            elif evento.type == pygame.KEYDOWN:

                # ESC -> salir
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False

                # Tecla de avance
                elif evento.key in TECLAS_AVANCE:

                    avanzar = True

                    t_inicio_pulsacion = ahora

        # ----------------------------------------------------
        # Detectar si la tecla sigue presionada

        if not avanzar:

            teclas = pygame.key.get_pressed()

            tecla_presionada = any(
                teclas[k]
                for k in TECLAS_AVANCE
            )

            tiempo_presionado = (
                ahora - t_inicio_pulsacion
            )

            tiempo_desde_ultimo_paso = (
                ahora - t_ultimo_paso
            )

            if (
                tecla_presionada
                and tiempo_presionado >= RETARDO_REPETICION
                and tiempo_desde_ultimo_paso >= INTERVALO_REPETICION
            ):
                avanzar = True

        # ----------------------------------------------------
        # Calcular siguiente generación

        if avanzar and corriendo:

            pygame.display.set_caption(
                f"Calculando generación {generacion + 1}..."
            )

            pygame.event.pump()

            # Medir tiempo del cálculo
            t0 = time.perf_counter()

            # Calcular siguiente generación según el modo elegido
            if modo == "paralelo":
                matriz_actual = siguiente_generacion_par(
                    matriz_actual,
                    pool,
                    num_procesos
                )
            else:
                matriz_actual = siguiente_generacion_seq(
                    matriz_actual
                )

            # Tiempo empleado
            tiempo_calculo = (
                time.perf_counter() - t0
            )

            # Actualizar número de generación
            generacion += 1

            # Crear nueva imagen
            imagen = matriz_a_superficie(
                matriz_actual
            )

            # Actualizar título
            pygame.display.set_caption(
                crear_titulo(
                    dim,
                    generacion,
                    modo,
                    tiempo_calculo
                )
            )

            # Registrar momento del último cálculo
            t_ultimo_paso = time.perf_counter()

        # ----------------------------------------------------
        # Dibujar imagen

        pantalla.blit(
            imagen,
            (0, 0)
        )

        pygame.display.flip()

        # Controlar FPS
        reloj.tick(FPS)

    # --------------------------------------------------------
    # Cerrar procesos y Pygame

    if pool is not None:
        pool.close()
        pool.join()

    pygame.quit()


# ============================================================
# 10. PROGRAMA PRINCIPAL

if __name__ == '__main__':

    ejecutar(DIMENSION_MATRIZ, MODO, NUM_PROCESOS)