import random
# importaciones necesarias para graficacion
import numpy as np
import time
import pygame
# importaciones de threading


# 1. CONFIGURACIÓN 

# *************** Funciones generales del programa, que ambas versiones utilizan para su ejecucion ***************

# Funcion de generar matriz aleatoria, se genera de manera tradicional
# Esta recibe una dimension predeterminada, y genera la matriz con los valores 1 o 0
def generar_matriz_aleatoria(dim):
    m = [[random.randint(0,1) 
          for _ in range(dim)] 
          for _ in range(dim)]
    return m

# Funcion imprimir matriz, usada para hacer diversos testeos de correctitud desde la terminal.
# Recibe una matriz y la imprime de una forma legible.
def imprimir_matriz(matriz):
    for fila in matriz:
        # Convierte cada número a texto y los une con un espacio
        print(" ".join(map(str, fila)))

# 2. LÓGICA DEL JUEGO 

#****************************** ImplementacionInterfaz grafica con pygame ******************************
TAM_VENTANA = 800  # lado en píxeles de la ventana, sin importar el tamaño de la matriz
COLOR_MUERTA = (18, 18, 18)
COLOR_VIVA = (0, 230, 118)
PALETA = np.array([COLOR_MUERTA, COLOR_VIVA], dtype=np.uint8)
 
# Teclas que avanzan al siguiente estado
TECLAS_AVANCE = (pygame.K_SPACE, pygame.K_PAUSE, pygame.K_RETURN, pygame.K_KP_ENTER)
RETARDO_REPETICION = 0.3   # segundos que hay que mantener la tecla antes de que avance solo
INTERVALO_REPETICION = 0.05  # segundos mínimos entre generaciones mientras se mantiene
 
 
def matriz_a_superficie(m):
    """Convierte la matriz (lista de listas de 0/1) en una superficie de pygame."""
    arr = np.array(m, dtype=np.uint8)
    rgb = PALETA[arr]                      # (filas, columnas, 3)
    rgb = rgb.swapaxes(0, 1)               # pygame espera (x, y, 3)
    superficie = pygame.surfarray.make_surface(rgb)
    # scale (vecino más cercano) mantiene los colores puros, sin mezclar celdas
    return pygame.transform.scale(superficie, (TAM_VENTANA, TAM_VENTANA))
 
 
def titulo(n, generacion, tiempo_calculo=None):
    texto = (f"Juego de la vida {n}x{n} - Generación {generacion}"
             f" | Espacio/Enter/Pausa: avanzar (mantener = continuo), Esc: salir")
    if tiempo_calculo is not None:
        texto += f" | último cálculo: {tiempo_calculo:.2f}s"
    return texto
 
 
def ejecutar(dim):
    print(f"Generando matriz {dim}x{dim}...")
    m1 = generar_matriz_aleatoria(dim)
    # copiamos la matriz base a la matriz auxiliar
    m_aux = [fila[:] for fila in m1]
    generacion = 1
 
    pygame.init()
    pantalla = pygame.display.set_mode((TAM_VENTANA, TAM_VENTANA))
    reloj = pygame.time.Clock()
 
    imagen = matriz_a_superficie(m1)
    pygame.display.set_caption(titulo(dim, generacion))
 
    t_inicio_pulsacion = 0.0
    t_ultimo_paso = 0.0
 
    corriendo = True
    while corriendo:
        ahora = time.perf_counter()
        avanzar = False
 
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif evento.key in TECLAS_AVANCE:
                    avanzar = True
                    t_inicio_pulsacion = ahora
 
        # Si se mantiene presionada una tecla de avance, sigue avanzando solo.
        # Se consulta el estado de la tecla (no se encolan eventos), así que en
        # matrices grandes no se acumulan pasos pendientes.
        if not avanzar:
            teclas = pygame.key.get_pressed()
            if (any(teclas[k] for k in TECLAS_AVANCE)
                    and ahora - t_inicio_pulsacion >= RETARDO_REPETICION
                    and ahora - t_ultimo_paso >= INTERVALO_REPETICION):
                avanzar = True
 
        if avanzar and corriendo:
            pygame.display.set_caption(f"Calculando generación {generacion + 1}...")
            pygame.event.pump()
 
            t0 = time.perf_counter()
            survives_seq(m1, m_aux)
            revives_seq(m1, m_aux)
            m1 = [fila[:] for fila in m_aux]
            t = time.perf_counter() - t0
 
            generacion += 1
            imagen = matriz_a_superficie(m1)
            pygame.display.set_caption(titulo(dim, generacion, t))
            t_ultimo_paso = time.perf_counter()
 
        pantalla.blit(imagen, (0, 0))
        pygame.display.flip()
        reloj.tick(30)
 
    pygame.quit() 


# Funcion conteo vecinos, esta dada una matriz m, y unas coordinadas i,j. recorre todos los vecinos proximos a la celda m[i][j]
# esta realiza un conteo de que numero de vecinos se encuentran vivos al momento de llamarla.
def conteo_vecinos(m, i, j):
    #Establecemos un conteo en 0 para poder tener el acumulado de vecinos
    cont = 0

    # Ciclos para recorrer los vecinos proximos de caada celula
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            # ignoramos la posicion actual (la misma celula no se cuenta)
            if di == 0 and dj == 0:
                continue  

            # establecemos la coordenada de cada vecino proximo en base a las posiciones dadas i,j
            fila = i + di
            columna = j + dj

            # Hacemos validacion para que NO accedamos a posiciones fuera de rango de la matriz
            if 0 <= fila < len(m) and 0 <= columna < len(m):
                if m[fila][columna] == 1: #contamos solo los elementos vivos
                    cont += 1

    return cont #devolvemos el conteo que tengamos de vecinos vivos




#****************************** Implementacion secuencial del Problema ******************************

# funcion que revisa para cada elemento de la matriz, si sobrevive o muere en cada iteracion que se llama en base al numero
# de vecinos a su alrededor, usando conteo_vecinos. Esta recibe una matriz sobre la cual aplica esta logica, y ademas una matriz auxiliar
# m_aux para ir almacenando el nuevo estado de la partida sin modificar la logica de la iteracion actual.
def survives_seq(m,m_aux):
    # Recorremos la matriz
    for i in range(len(m)):
        for j in range(len(m)):
            # Conteo de vecinos vivos, llamamos a conteo_vecinos
            if m[i][j] == 1: #primero verificamos que estemos en una celula viva
                vecinos = conteo_vecinos(m,i,j) # contamos sus vecinos vivos
                if vecinos != 2 and vecinos != 3: # si no son ni 2 ni 3 se muere.
                    m_aux[i][j] = 0 #almacenamos este nuevo estado de celda en la matriz auxiliar
            
# Funcion revivir. Esta revisa para cada celula muerta si cuenta con la cantidad exacta de vecinos necesarios para revivir en la proxima 
# iteracion. Esta recibe una matriz sobre la cual aplica esta logica, y ademas una matriz auxiliar m_aux para ir almacenando el nuevo
# estado de la partida sin modificar la logica de la iteracion actual.
def revives_seq(m,m_aux):
    # Recorremos la matriz
    for i in range(len(m)):
        for j in range(len(m)):
            # Conteo de vecinos vivos, llamamos a conteo_vecinos
            if m[i][j] == 0: # primero verificamos que estemos en una celula muerta
                vecinos = conteo_vecinos(m,i,j) # contamos sus vecinos vivos
                if vecinos == 3: # comprobamos que tenga EXACTAMENTE 3 vecinos vivos
                    m_aux[i][j] = 1 #almacenamos este nuevo estado de la celda en la matriz auxiliar
                        


# Desarrollo Paralelo del programa =============================================================00



#****************************** Archivo de ejecucion principal Main ******************************
if __name__ == '__main__':

    # Ejecutamos la aplicacion de dimension M x M
    # Ejecutar ( M )
    ejecutar(10)


    """ 
    # Apartado de egecuciones genericas en la termianl para testeos
    m1 = generar_matriz_aleatoria(60)
    # copiamos la matriz base a la matriz auxiliar
    m_aux = [fila[:] for fila in m1]

    #iteracion 1:
    imprimir_matriz(m1)


    #Ejecucion RAPIDA mediante ciclo for
    for i in range(1000):
        print( f"ITERACION ", i)
        survives_seq(m1, m_aux)
        revives_seq(m1, m_aux)
        m1 = [fila[:] for fila in m_aux]
        imprimir_matriz(m1)
            
        
        print("flip")

    #Ejecucion CONTROLADA mediante ciclo while
    iterador = 0
    while iterador < 1000:
        pregunta = input("presione espacio para la siguiente ejecucion")
        

        if not pregunta:
            print(f"ITERACION ", {iterador})
            survives_seq(m1, m_aux)
            revives_seq(m1, m_aux)
            m1 = [fila[:] for fila in m_aux]
            mostrar_matriz(m1)
        else:
            break
    """
