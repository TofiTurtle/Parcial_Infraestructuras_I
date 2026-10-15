# JUEGO DE LA VIDA DE CONWAY
# Implementación secuencial + paralela con MPI (mpi4py) + interfaz gráfica con Pygame

# ============================================================
# 1. CONFIGURACIÓN DEL PROGRAMA
DIMENSION_MATRIZ = 100       # Tamaño de la matriz: DIMENSION x DIMENSION
MODO = "mpi"                 # "secuencial" o "mpi"  (el número de procesos lo da mpiexec -n)
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
import numpy as np
import pygame
from mpi4py import MPI # Implementacion escogida de las alternativas dadas: MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()       # identificador de este proceso (0 .. size-1)
size = comm.Get_size()       # número total de procesos MPI

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
# 5. LOGICA DEL JUEGO

def conteo_vecinos(m, i, j):
    """
    Cuenta cuántos vecinos vivos tiene la célula
    ubicada en la posición [i][j].

    Una célula puede tener como máximo 8 vecinos.
    """

    #inicializamo el contador en 0
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
# 7. IMPLEMENTACIÓN PARALELA (MPI*** ojo vivisimo)

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


def calcular_y_reunir(m):
    """
    Parte que ejecutan TODOS los procesos (rank 0 incluido):
    cada uno calcula su bloque de filas y lo envía al rank 0.

    comm.gather funciona como barrera hacia el rank 0: no devuelve
    hasta que llegaron los bloques de todos los procesos, y los
    entrega ordenados por rank (así quedan en su posición correcta).
    Devuelve la lista de bloques en rank 0 y None en los demás.
    """
    inicio, fin = dividir_filas(len(m), size)[rank]
    bloque = calcular_filas(m, inicio, fin)
    return comm.gather(bloque, root=0)


def siguiente_generacion_mpi(m):
    """
    Una generación completa. SOLO la llama el rank 0.

    1. bcast: el rank 0 envía la matriz actual a todos los procesos
       (los demás están esperando en bucle_trabajador).
    2. Todos calculan su bloque y lo reúnen con gather.
    3. El rank 0 une los bloques en orden.
    """
    comm.bcast(m, root=0)

    bloques = calcular_y_reunir(m)

    nueva = []
    for bloque in bloques:
        nueva.extend(bloque)

    return nueva


def bucle_trabajador():
    """
    Lo ejecutan los procesos con rank > 0 mientras el rank 0
    maneja la interfaz. Esperan una matriz, calculan su bloque
    y lo devuelven. Una matriz None es la orden de terminar.
    """
    while True:
        m = comm.bcast(None, root=0)

        if m is None:
            break

        calcular_y_reunir(m)


# ============================================================
# 8. FUNCIONES DE LA INTERFAZ GRÁFICA (solo rank 0)

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
    # Ahora decimos con cuantos procesos tamos ejecutandolo desde la terminal siuuuu
    detalle = f"mpi, {size} procesos" if modo == "mpi" else modo

    texto = (
        f"La vida {dim}x{dim} ({detalle}) "
        f"- Generación {generacion}"
        f" | Espacio/Enter: avanzar"
        f" | Esc: salir"
    )

    if tiempo_calculo is not None:
        texto += f" | Último cálculo: {tiempo_calculo:.2f}s"

    return texto


# ============================================================
# 9. EJECUCIÓN DEL JUEGO (solo rank 0, es decir interfaz jeje)

def ejecutar(dim, modo):
    """
    Ejecuta el Juego de la Vida utilizando Pygame.

    modo puede ser "secuencial" o "mpi".
    """

    print(f"Generando matriz {dim}x{dim} en modo {modo} ({size} procesos)...")

    # --------------------------------------------------------
    # Crear matriz inicial

    matriz_actual = generar_matriz_aleatoria(dim)

    generacion = 1


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

            if modo == "mpi":
                matriz_actual = siguiente_generacion_mpi(matriz_actual)
            else:
                matriz_actual = siguiente_generacion_seq(matriz_actual)

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
    # Cerrar Pygame
    pygame.quit()


# ============================================================
# 10. PROGRAMA PRINCIPAL

if __name__ == '__main__':

    if rank == 0:
        try:
            ejecutar(DIMENSION_MATRIZ, MODO)
        finally:
            # Orden de terminar para los demás procesos (siempre, incluso si hay error)
            comm.bcast(None, root=0)
    else:
        bucle_trabajador()