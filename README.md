# Parcial_Infraestructuras_I
Repositorio para almacenar el codigo de la implementacion del juego para parcial I de infra

## Juan Jose Rodriguez Lozano - 202419084
## Steven Fernando Aragon Alvarez - 202418804
## Yoel Steven Montoya - 202416571

### Guia cortica para la ejecucion del programa:
Si se ejecuta el archivo de ***juego_vida.py*** de manera comun, se ejecuta el programa con un proceso (asi tengamos configurada la version "mpi").
Entonces para hacer la ejecución con distintos numeros procesos.
1. En una terminal, dirigirse hasta el directorio donde se encuentra situado el archivo de juego_vida.py. 
(ej: en mi caso es:   cd C:\Users\HP\Desktop\infra_parcial\Parcial_Infraestructuras_I )
2. Verificar que la version a usar es `MODO = mpi` es el archivo de juego_vida.py, despues **GUARDE EL ARCHIVO**
3. Ejecutar el siguiente comando: `mpiexec -n [NUM PROCESOS] python juego_vida.py`
   Reemplazando [NUM PROCESOS] por el numero deseado de procesos a usar en la ejecucion.
