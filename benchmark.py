# ANÁLISIS DE RENDIMIENTO DEL JUEGO DE LA VIDA (versión MPI)
# Compara la versión secuencial con la paralela con MPI (sin interfaz gráfica)
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
import shutil
import subprocess
import sys
import tempfile
import time
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


def buscar_mpiexec():
    """
    Devuelve la ruta de mpiexec. Lo busca en el PATH y, si no está,
    en las carpetas donde MS-MPI se instala normalmente en Windows.
    """

    ruta = shutil.which("mpiexec")

    if ruta:
        return ruta

    candidatos = []

    if os.environ.get("MSMPI_BIN"):
        candidatos.append(os.path.join(os.environ["MSMPI_BIN"], "mpiexec.exe"))

    candidatos.append(r"C:\Program Files\Microsoft MPI\Bin\mpiexec.exe")
    candidatos.append(r"C:\Program Files (x86)\Microsoft MPI\Bin\mpiexec.exe")

    for candidato in candidatos:
        if os.path.isfile(candidato):
            return candidato

    raise SystemExit(
        "No se encontró mpiexec. Instala Microsoft MPI (msmpisetup.exe), "
        "cierra y vuelve a abrir VS Code/la terminal, y comprueba con: "
        "mpiexec -n 2 python -c \"from mpi4py import MPI; print(MPI.COMM_WORLD.Get_rank())\""
    )


def lanzar(num_procesos, *argumentos):
    """Lanza este script mediante MPI y muestra los errores completos."""

    comando = [
        buscar_mpiexec(),
        "-n", str(num_procesos),
        sys.executable,
        os.path.abspath(__file__),
        "--trabajo",
        *[str(a) for a in argumentos]
    ]

    print("\nEjecutando:", comando, flush=True)

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    if resultado.stdout:
        print("SALIDA DE MPI:")
        print(resultado.stdout)

    if resultado.stderr:
        print("ERRORES DE MPI:")
        print(resultado.stderr)

    if resultado.returncode != 0:
        raise RuntimeError(
            f"MPI terminó con código {resultado.returncode}"
        )



def leer_tiempo(modo, n, num_procesos, generaciones):
    """
    Lanza una medición y devuelve el tiempo que escribió el proceso 0.
    """

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, "tiempo.txt")
        lanzar(num_procesos, modo, n, generaciones, ruta)
        with open(ruta) as f:
            return float(f.read())


def medir_secuencial(n, generaciones):
    """
    Devuelve el tiempo promedio (segundos) por generación
    de la versión secuencial.
    """

    return leer_tiempo("seq", n, 1, generaciones)


def medir_paralelo(n, num_procesos, generaciones):
    """
    Devuelve el tiempo promedio (segundos) por generación
    de la versión paralela con num_procesos procesos MPI.
    """

    return leer_tiempo("mpi", n, num_procesos, generaciones)


def verificar_correctitud():
    """
    Comprueba que la versión paralela da EXACTAMENTE el mismo
    resultado que la secuencial después de varias generaciones.
    (La comparación la hace el proceso 0 dentro de mpiexec -n 4.)
    """

    lanzar(4, "verificar")


# ============================================================
# 4. TRABAJO DENTRO DE MPI (lo ejecutan los procesos lanzados con mpiexec)

def ejecutar_trabajo(argumentos):
    """
    Lo ejecutan TODOS los procesos MPI de un lanzamiento.
    argumentos: ["verificar"]  o  [modo, n, generaciones, ruta_resultado]
    con modo "seq" (secuencial) o "mpi" (paralelo).
    """

    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

    from juego_vida import (
        generar_matriz_aleatoria,
        siguiente_generacion_seq,
        siguiente_generacion_mpi,
        bucle_trabajador,
        comm,
        rank
    )

    modo = argumentos[0]

    # Los procesos que no son el 0 solo esperan trabajo y lo calculan
    if modo != "seq" and rank != 0:
        bucle_trabajador()
        return

    try:

        if modo == "verificar":

            random.seed(SEMILLA)
            base = generar_matriz_aleatoria(60)

            # Resultado secuencial
            m_seq = base
            for _ in range(10):
                m_seq = siguiente_generacion_seq(m_seq)

            # Resultado paralelo
            m_par = base
            for _ in range(10):
                m_par = siguiente_generacion_mpi(m_par)

            if m_seq == m_par:
                print("Verificación OK: secuencial y paralelo dan el mismo resultado.", flush=True)
            else:
                print("ERROR: los resultados son distintos.", flush=True)

        else:

            n = int(argumentos[1])
            generaciones = int(argumentos[2])
            ruta = argumentos[3]

            random.seed(SEMILLA)
            matriz = generar_matriz_aleatoria(n)

            if modo == "seq":

                m = matriz
                t0 = time.perf_counter()

                for _ in range(generaciones):
                    m = siguiente_generacion_seq(m)

                tiempo = (time.perf_counter() - t0) / generaciones

            else:

                # Generación de calentamiento (no se mide)
                siguiente_generacion_mpi(matriz)

                m = matriz
                t0 = time.perf_counter()

                for _ in range(generaciones):
                    m = siguiente_generacion_mpi(m)

                tiempo = (time.perf_counter() - t0) / generaciones

            with open(ruta, "w") as f:
                f.write(repr(tiempo))

    finally:
        # Orden de terminar para los demás procesos (siempre, incluso si hay error)
        if modo != "seq":
            comm.bcast(None, root=0)


# ============================================================
# 5. PROGRAMA PRINCIPAL

if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == "--trabajo":

        # Lanzado por mpiexec: este proceso es uno de los procesos MPI
        ejecutar_trabajo(sys.argv[2:])

    else:

        import matplotlib.pyplot as plt

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

            print(f"\nMatriz {n}x{n} ({generaciones} generaciones por prueba)")

            tiempos_seq[n] = medir_secuencial(n, generaciones)
            print(f"  Secuencial: {tiempos_seq[n]:.3f} s")

            tiempos_par[n] = {}

            for p in procesos:
                tiempos_par[n][p] = medir_paralelo(n, p, generaciones)
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