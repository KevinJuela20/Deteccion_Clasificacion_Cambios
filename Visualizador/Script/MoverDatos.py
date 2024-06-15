import os
import json
import shutil

def contar_archivos(carpeta):
    return len([f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f))])

def calcular_combinaciones(n):
    return sum(range(n))

def crear_json_conteos_y_combinaciones(ruta_base, subcarpetas):
    datos = []
    for subcarpeta in subcarpetas:
        ruta_subcarpeta = os.path.join(ruta_base, subcarpeta)
        num_archivos = contar_archivos(ruta_subcarpeta)
        combinaciones = calcular_combinaciones(num_archivos)
        datos.append({"nomZona": subcarpeta, "combinaciones": combinaciones})
    return datos

def mover_archivos(json_datos, ruta_origen, ruta_destino_base):
    archivos_origen = sorted([f for f in os.listdir(ruta_origen) if f.endswith('.png')], key=lambda x: int(x.split('.')[0]))
    indice_archivo = 0
    for item in json_datos:
        nomZona = item["nomZona"]
        combinaciones = item["combinaciones"]
        ruta_destino = os.path.join(ruta_destino_base, nomZona)
        os.makedirs(ruta_destino, exist_ok=True)  # Crear la carpeta si no existe
        for _ in range(combinaciones):
            if indice_archivo < len(archivos_origen):
                archivo_a_mover = archivos_origen[indice_archivo]
                shutil.move(os.path.join(ruta_origen, archivo_a_mover), os.path.join(ruta_destino, archivo_a_mover))
                indice_archivo += 1

def eliminar_archivos(directory_path):
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)    
    os.makedirs(directory_path)

# Rutas y subcarpetas
directorio_origen = './Archivos/Subidos/'
ruta_base = './Archivos/Bandas/'
#subcarpetas = ['Zona 1', 'Zona 2', 'Zona 3', 'Zona 4', 'Zona 5', 'Zona 6']
ruta_origen = '../BAN - copia/resultados/vis_data/vis_image'
ruta_destino_base = './Archivos/Label/'

# Obtener todos los nombres de los elementos en el directorio de origen
elementos = os.listdir(directorio_origen)

# Filtrar solo los nombres de las carpetas
subcarpetas = [nombre.split(".")[0] for nombre in elementos if os.path.isdir(os.path.join(directorio_origen, nombre))]

# Iterar sobre todas las carpetas en el directorio de origen
for item in os.listdir(directorio_origen):
    # Construir la ruta completa del item
    ruta_item = os.path.join(directorio_origen, item)
    
    if os.path.isdir(ruta_item):
        destino = os.path.join(ruta_base, item)
        
        # Mover la carpetaç
        shutil.copytree(ruta_item, destino)

# Crear JSON con conteos y combinaciones
json_datos = crear_json_conteos_y_combinaciones(ruta_base, subcarpetas)

# print(json_datos)
# Guardar JSON en archivo
# with open('conteos_combinaciones.json', 'w') as f:
#     json.dump(json_datos, f, indent=4)

# # Mover archivos según las combinaciones calculadas
mover_archivos(json_datos, ruta_origen, ruta_destino_base)

print()
print("Todas las carpetas han sido movidas.")

#Limpiar los directorios A, B
ruta_a = '../BAN - copia/data/LEVIR-CD/test/A/'
ruta_b = '../BAN - copia/data/LEVIR-CD/test/B/'
ruta_label = '../BAN - copia/data/LEVIR-CD/test/label/'
eliminar_archivos(ruta_a)
eliminar_archivos(ruta_b)
eliminar_archivos(ruta_label)

