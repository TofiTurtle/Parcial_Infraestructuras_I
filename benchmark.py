# ANÁLISIS DE RENDIMIENTO DEL JUEGO DE LA VIDA
# Compara la versión secuencial con la paralela (sin interfaz gráfica)
# Requiere: matplotlib (pip install matplotlib)

# ============================================================
# 1. CONFIGURACIÓN DEL BENCHMARK
TAMANOS = [100, 500, 1000]       # Tamaños de matriz a probar
SEMILLA = 42                     # Semilla fija para repetir los mismos resultados

# Generaciones que se promedian según el tamaño.
# Las matrices pequeñas tardan muy poco, así que se repiten más veces
# para reducir el ruido de la medición.
GENERACIONES_POR_TAMANO = {100: 20, 500: 5, 1000: 3}

# Si es True, se prueba también con el doble de procesos que núcleos
# para ver qué pasa cuando hay más procesos que núcleos disponibles
PROBAR_MAS_QUE_NUCLEOS = True

# ============================================================
# 2. IMPORTACIONES
import os
import random
import time
from multiprocessing import Pool
import matplotlib.pyplot as plt

from juego_vida import (
    generar_matriz_aleatoria,
    siguiente_generacion_seq,
    siguiente_generacion_par
)

# ============================================================
# 3. FUNCIONES DE MEDICIÓN

def obtener_lista_procesos():
    """
    Arma la lista de números de procesos a probar según los
    núcleos del equipo (os.cpu_count()).

    Usa potencias de 2 menores que los núcleos, luego los núcleos
    exactos y, opcionalmente, el doble de núcleos.
    Ejemplo con 8 núcleos: [1, 2, 4, 8, 16]
    Ejemplo con 12 núcleos: [1, 2, 4, 8, 12, 24]
    """

    nucleos = os.cpu_count() or 1

    lista = []
    p = 1

    while p < nucleos:
        lista.append(p)
        p = p * 2

    lista.append(nucleos)

    if PROBAR_MAS_QUE_NUCLEOS:
        lista.append(nucleos * 2)

    return lista


def medir_secuencial(matriz, generaciones):
    """
    Devuelve el tiempo promedio (segundos) por generación
    de la versión secuencial.
    """

    m = matriz
    t0 = time.perf_counter()

    for _ in range(generaciones):
        m = siguiente_generacion_seq(m)

    return (time.perf_counter() - t0) / generaciones


def medir_paralelo(matriz, num_procesos, generaciones):
    """
    Devuelve el tiempo promedio (segundos) por generación
    de la versión paralela con num_procesos procesos.
    """

    pool = Pool(processes=num_procesos)

    # Generación de calentamiento: los procesos ya arrancan
    # antes de medir (no queremos medir su creación)
    siguiente_generacion_par(matriz, pool, num_procesos)

    m = matriz
    t0 = time.perf_counter()

    for _ in range(generaciones):
        m = siguiente_generacion_par(m, pool, num_procesos)

    tiempo = (time.perf_counter() - t0) / generaciones

    pool.close()
    pool.join()

    return tiempo


def verificar_correctitud():
    """
    Comprueba que la versión paralela da EXACTAMENTE el mismo
    resultado que la secuencial después de varias generaciones.
    """

    random.seed(SEMILLA)
    base = generar_matriz_aleatoria(60)

    # Resultado secuencial
    m_seq = base
    for _ in range(10):
        m_seq = siguiente_generacion_seq(m_seq)

    # Resultado paralelo
    pool = Pool(processes=4)
    m_par = base
    for _ in range(10):
        m_par = siguiente_generacion_par(m_par, pool, 4)
    pool.close()
    pool.join()

    if m_seq == m_par:
        print("Verificación OK: secuencial y paralelo dan el mismo resultado.")
    else:
        print("ERROR: los resultados son distintos.")


# ============================================================
# 4. PROGRAMA PRINCIPAL

if __name__ == '__main__':

    nucleos = os.cpu_count() or 1
    procesos = obtener_lista_procesos()

    print(f"Núcleos detectados (hilos lógicos): {nucleos}")
    print(f"Procesos a probar: {procesos}")

    verificar_correctitud()

    # tiempos_seq[n] -> tiempo secuencial para la matriz n x n
    # tiempos_par[n][p] -> tiempo paralelo con p procesos
    tiempos_seq = {}
    tiempos_par = {}

    for n in TAMANOS:

        generaciones = GENERACIONES_POR_TAMANO[n]

        random.seed(SEMILLA)
        matriz = generar_matriz_aleatoria(n)

        print(f"\nMatriz {n}x{n} ({generaciones} generaciones por prueba)")

        tiempos_seq[n] = medir_secuencial(matriz, generaciones)
        print(f"  Secuencial: {tiempos_seq[n]:.3f} s")

        tiempos_par[n] = {}

        for p in procesos:
            tiempos_par[n][p] = medir_paralelo(matriz, p, generaciones)
            speedup = tiempos_seq[n] / tiempos_par[n][p]
            print(f"  {p} procesos: {tiempos_par[n][p]:.3f} s  (speedup {speedup:.2f}x)")

    # --------------------------------------------------------
    # Gráfica 1: tiempo vs número de procesos (una línea por tamaño)

    plt.figure(figsize=(7, 5))
    for n in TAMANOS:
        plt.plot(procesos, [tiempos_par[n][p] for p in procesos],
                 marker="o", label=f"{n}x{n}")
    plt.axvline(nucleos, linestyle=":", color="gray", label=f"Núcleos ({nucleos})")
    plt.xlabel("Número de procesos")
    plt.ylabel("Tiempo por generación (s)")
    plt.title("Tiempo de ejecución vs número de procesos")
    plt.xticks(procesos)
    plt.yscale("log")
    plt.legend()
    plt.grid(True)
    plt.savefig("grafica_tiempo.png", dpi=150)

    # --------------------------------------------------------
    # Gráfica 2: speedup vs número de procesos

    plt.figure(figsize=(7, 5))
    for n in TAMANOS:
        plt.plot(procesos, [tiempos_seq[n] / tiempos_par[n][p] for p in procesos],
                 marker="o", label=f"{n}x{n}")
    plt.plot(procesos, procesos, "--", color="gray", label="Ideal")
    plt.axvline(nucleos, linestyle=":", color="gray", label=f"Núcleos ({nucleos})")
    plt.xlabel("Número de procesos")
    plt.ylabel("Speedup (T secuencial / T paralelo)")
    plt.title("Aceleración obtenida")
    plt.xticks(procesos)
    plt.legend()
    plt.grid(True)
    plt.savefig("grafica_speedup.png", dpi=150)

    # --------------------------------------------------------
    # Gráfica 3: tiempo vs tamaño de la matriz

    plt.figure(figsize=(7, 5))
    plt.plot(TAMANOS, [tiempos_seq[n] for n in TAMANOS],
             marker="o", label="Secuencial")
    for p in procesos:
        plt.plot(TAMANOS, [tiempos_par[n][p] for n in TAMANOS],
                 marker="o", label=f"{p} procesos")
    plt.xlabel("Tamaño de la matriz (n x n)")
    plt.ylabel("Tiempo por generación (s)")
    plt.title("Tiempo de ejecución vs tamaño de la matriz")
    plt.xticks(TAMANOS)
    plt.legend()
    plt.grid(True)
    plt.savefig("grafica_tamano.png", dpi=150)

    print("\nGráficas guardadas: grafica_tiempo.png, grafica_speedup.png, grafica_tamano.png")