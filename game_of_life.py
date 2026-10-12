# importaciones
import random

#Funciones generales del programa, que ambas versiones utilizan para su ejecucion.s

def generar_matriz_aleatoria(dim):
    m = [[random.randint(0,1) # generada con numeros aleatorios entre 1 y 100
          for _ in range(dim)] 
          for _ in range(dim)]
    return m

def imprimir_matriz(matriz):
    for fila in matriz:
        # Convierte cada número a texto y los une con un espacio
        print(" ".join(map(str, fila)))

def conteo_vecinos(m, i, j):
    cont = 0

    # Ciclos para recorrer los vecinos proximos de caada celula
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            # ignoramos la posicion actual (la misma celula no se cuenta)
            if di == 0 and dj == 0:
                continue  
            
            fila = i + di
            columna = j + dj

            # Hacemos validacion para que NO accedamos a posiciones fuera de rango de la matriz
            if 0 <= fila < len(m) and 0 <= columna < len(m):
                if m[fila][columna] == 1:   
                    cont += 1

    return cont
# implementacion secuencial
def survives_seq(m,m_aux):
    # Recorremos la matriz
    for i in range(len(m)):
        for j in range(len(m)):
            # Conteo de vecinos vivos, llamamos a conteo_vecinos
            if m[i][j] == 1:
                vecinos = conteo_vecinos(m,i,j)
                if vecinos != 2 and vecinos != 3:
                    m_aux[i][j] = 0
            

def revives_seq(m,m_aux):
    for i in range(len(m)):
        for j in range(len(m)):
            # Conteo de vecinos vivos, llamamos a conteo_vecinos
            if m[i][j] == 0:
                vecinos = conteo_vecinos(m,i,j)
                if vecinos == 3:
                    m_aux[i][j] = 1
                        


# Desarrollo Paralelo del programa =============================================================00




# Archivo de ejecucion principal Main
if __name__ == '__main__':

    m1 = generar_matriz_aleatoria(20)
    # copiamos la matriz base a la matriz auxiliar
    m_aux = [fila[:] for fila in m1]

    #iteracin 1:
    imprimir_matriz(m1)
"""
    #iteracion 2:
    print("ITERACION 2")
    survives_seq(m1, m_aux)
    revives_seq(m1, m_aux)
    m1 = [fila[:] for fila in m_aux]
    imprimir_matriz(m1)

    #iteracion 3:
    print("ITERACION 3")
    survives_seq(m1, m_aux)
    revives_seq(m1, m_aux)
    m1 = [fila[:] for fila in m_aux]
    imprimir_matriz(m1)
    
    #iteracion 4:
    print("ITERACION 2")
    survives_seq(m1, m_aux)
    revives_seq(m1, m_aux)
    m1 = [fila[:] for fila in m_aux]
    imprimir_matriz(m1)

"""
"""
PROGRAMA DE EJECUCION RAPIDA
for i in range(1000):
    print( f"ITERACION ", i)
    survives_seq(m1, m_aux)
    revives_seq(m1, m_aux)
    m1 = [fila[:] for fila in m_aux]
    imprimir_matriz(m1)
        
     
    print("flip")
"""
iterador = 0
while iterador < 1000:
    pregunta = input("presione espacio para la siguiente ejecucion")
    

    if not pregunta:
        print(f"ITERACION ", {iterador})
        survives_seq(m1, m_aux)
        revives_seq(m1, m_aux)
        m1 = [fila[:] for fila in m_aux]
        imprimir_matriz(m1)
    else:
        break
