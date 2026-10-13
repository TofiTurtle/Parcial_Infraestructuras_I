
# JUEGO DE LA VIDA DE CONWAY

# ============================================================
# 1. CONFIGURACIÓN DEL PROGRAMA
DIMENSION_MATRIZ = 100       # Tamaño de la matriz: DIMENSION x DIMENSION
TAM_VENTANA = 700        # Tamaño de la ventana en píxeles
COLOR_MUERTA = (18, 18, 18)
COLOR_VIVA = (0, 230, 118) 
RETARDO_REPETICION = 0.3    # Segundos antes de comenzar el avance continuo
INTERVALO_REPETICION = 0.05 # Tiempo mínimo entre generaciones
FPS =60
# ============================================================
# 2. IMPORTACIONES
import random
import time
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


# ============================================================
# 6. IMPLEMENTACIÓN SECUENCIAL


def survives_seq(m, m_aux):
    """
    Revisa las células actualmente vivas.

    Regla del Juego de la Vida:
    Una célula viva sobrevive si tiene 2 o 3 vecinos vivos.
    """

    for i in range(len(m)):
        for j in range(len(m)):

            # Comprobamos si la célula está viva
            if m[i][j] == 1:

                vecinos = conteo_vecinos(m, i, j)

                # Si no tiene 2 ni 3 vecinos, muere
                if vecinos != 2 and vecinos != 3:
                    m_aux[i][j] = 0


def revives_seq(m, m_aux):
    """
    Revisa las células actualmente muertas.

    Regla del Juego de la Vida:
    Una célula muerta revive si tiene exactamente 3
    vecinos vivos.
    """

    for i in range(len(m)):
        for j in range(len(m)):

            # Comprobamos si la célula está muerta
            if m[i][j] == 0:

                vecinos = conteo_vecinos(m, i, j)

                # Si tiene exactamente 3 vecinos, revive
                if vecinos == 3:
                    m_aux[i][j] = 1


def siguiente_generacion(m, m_aux):
    """
    Calcula una generación completa del Juego de la Vida.

    Primero se procesan las células vivas y después
    las células muertas.
    """

    survives_seq(m, m_aux)
    revives_seq(m, m_aux)

    # La matriz auxiliar pasa a ser la nueva generación
    return copiar_matriz(m_aux)


# ============================================================
# 7. FUNCIONES DE LA INTERFAZ GRÁFICA
# ============================================================

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


def crear_titulo(dim, generacion, tiempo_calculo=None):
    """
    Crea el texto que aparecerá en el título de la ventana.
    """

    texto = (
        f"La vida {dim}x{dim} "
        f"- Generación {generacion}"
        f" | Espacio/Enter: avanzar"
        f" | Esc: salir"
    )

    if tiempo_calculo is not None:
        texto += f" | Último cálculo: {tiempo_calculo:.2f}s"

    return texto


# ============================================================
# 8. EJECUCIÓN DEL JUEGO

def ejecutar(dim):
    """
    Ejecuta el Juego de la Vida utilizando Pygame.
    """

    print(f"Generando matriz {dim}x{dim}...")

    # --------------------------------------------------------
    # Crear matriz inicial

    matriz_actual = generar_matriz_aleatoria(dim)

    # Matriz auxiliar para almacenar la siguiente generación
    matriz_auxiliar = copiar_matriz(matriz_actual)

    generacion = 1


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
        crear_titulo(dim, generacion)
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

            # Calcular siguiente generación
            matriz_actual = siguiente_generacion(
                matriz_actual,
                matriz_auxiliar
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
# 9. PROGRAMA PRINCIPAL

if __name__ == '__main__':

    ejecutar(DIMENSION_MATRIZ)
