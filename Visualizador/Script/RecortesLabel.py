import json
import os
from PIL import Image
import numpy as np
import cv2
import matplotlib.pyplot as plt
from keras.models import load_model

def proceso_imagen_redimensionada(anteriorA, posteriorB, etiqueta, ubi_rec_A, ubi_rec_B, ubi_rec_Eti, fecha_unida):
    # Cargar imágenes
    anterior = Image.open(anteriorA)
    posterior = Image.open(posteriorB)
    label_a = Image.open(etiqueta).convert('L')  # Convertir a blanco y negro

    # crear direcctorios no existentes
    os.makedirs(ubi_rec_A, exist_ok=True)
    os.makedirs(ubi_rec_B, exist_ok=True)
    os.makedirs(ubi_rec_Eti, exist_ok=True)

    # Convertir imagen de etiqueta a array de numpy y umbralizar
    label_array = np.array(label_a)
    _, thresholded = cv2.threshold(label_array, 127, 255, cv2.THRESH_BINARY)

    # Encontrar contornos
    contornos, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detalles_cortes = []
    # Recortar cada polígono detectado en todas las imágenes
    for j, contour in enumerate(contornos):
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50 and h > 50:
            rec_anterior = anterior.crop((x, y, x+w, y+h))
            rec_posterior = posterior.crop((x, y, x+w, y+h))
            rec_label = label_a.crop((x, y, x+w, y+h))

            # Redimensionar los recortes a 64x64 píxeles
            resize_anterior = rec_anterior.resize((64, 64))
            resize_posterior = rec_posterior.resize((64, 64))
            resize_label = rec_label.resize((64, 64))

            ant = os.path.join(ubi_rec_A, f'crop_{j}.png')
            post = os.path.join(ubi_rec_B, f'crop_{j}.png')
            etiq = os.path.join(ubi_rec_Eti, f'crop_{j}.png')

            # Guardar los recortes en las carpetas correspondientes
            resize_anterior.save(ant)
            resize_posterior.save(post)
            resize_label.save(etiq)

            eti_A = clasificar(ant)
            eti_B = clasificar(post)

            detalle = {
                "Rec_A": ant,
                "Rec_B": post,
                "Rec_L": etiq,
                "Eti_A": eti_A,
                "Eti_B": eti_B
            }
            detalles_cortes.append(detalle)
    return {
        fecha_unida : detalles_cortes
    }
        

# Diccionario de etiquetas
# etiquetas = {'AnnualCrop': 0, 'Forest': 1, 'HerbaceousVegetation': 2, 'Highway': 3, 'Industrial': 4, 'Pasture': 5, 'PermanentCrop': 6, 'Residential': 7, 'River': 8, 'SeaLake': 9}
etiquetas = {'Cultivo Anual': 0, 'Bosque': 1, 'Vegetación Herbácea': 2, 'Carretera': 3, 'Industrial': 4, 'Pastos': 5, 'Cultivo Permanente': 6, 'Residencial': 7 , 'Río': 8, 'Arboleda': 9}
# Función para obtener la etiqueta a partir de la predicción
def obtener_etiqueta(prediccion, etiquetas):
    clase_predicha = np.argmax(prediccion)
    for etiqueta, indice in etiquetas.items():
        if indice == clase_predicha:
            return etiqueta
    return None

def clasificar(ruta_imagen):
    # Cargar la imagen de tamaño 64x64 en modo RGB
    imagen = plt.imread(ruta_imagen)
    if imagen.shape[-1] == 4:  # Comprobar si la imagen tiene un cuarto canal
        imagen = imagen[:, :, :3]  # Eliminar el cuarto canal (canal alfa)

    # Hacer predicciones con ambos modelos
    pred_modelo_3 = modelo_1.predict(np.expand_dims(imagen, axis=0))
    etiqueta_predicha= obtener_etiqueta(pred_modelo_3, etiquetas)
    return etiqueta_predicha

def obtener_numero(archivo):
    return int(archivo.split('.')[0])

# Listar zonas y fechas de cada zona
def detalles_recortes_JSON(ruta_base):
    zonas = []
    
    # Listar todas las carpetas en el directorio base
    for subca in subcarpetas:
        ruta_carpeta = os.path.join(ruta_base, subca)
        ruta_label = os.path.join(ruta_Label, subca)

        if os.path.isdir(ruta_carpeta):
            fechas = []
            for archivo in os.listdir(ruta_carpeta):
                ruta_archivo = os.path.join(ruta_carpeta, archivo)
                if os.path.isfile(ruta_archivo):
                    fechas.append(archivo)
            arc_label = []
            for label in os.listdir(ruta_label):
                ruta_archivo = os.path.join(ruta_label, label)
                if os.path.isfile(ruta_archivo):
                    arc_label.append(label)
            
            recortes = []
            i = 1
            j = 0
            a_l = sorted(arc_label, key=obtener_numero)
           
            for fe in fechas:
                for x in fechas[i:]:
                    fechasJoin = fe.split(".")[0] + "_"+ x.split(".")[0]
                    # Generar recortes en Anterior
                    aux = proceso_imagen_redimensionada(ruta_carpeta+"/"+fe,ruta_carpeta+"/"+x,ruta_label+"/"+a_l[j],ruta_guardar+subca+"/"+fechasJoin+"/Rec_A/",ruta_guardar+subca+"/"+fechasJoin+"/Rec_B/",ruta_guardar+subca+"/"+fechasJoin+"/Rec_L/",fechasJoin)
                    recortes.append(aux)
                    j+=1
                i+=1
            zona = {
                "zona": subca,
                "recortes": recortes
            }
            zonas.append(zona)
    return zonas

ruta_base = "./Archivos/Zonas RGB/"
ruta_Label = "./Archivos/Label/"
ruta_guardar = "./Archivos/Recortes/"
ruta_modelo = './Modelos/ResNet152V2.h5'
directorio_origen = './Archivos/Subidos/'
modelo_1 = load_model(ruta_modelo)

# Cargar datos ya almacenados
archivo = "./Archivos/recortes.json"
with open(archivo, 'r') as f:
    recortes = json.load(f)

# Obtener todos los nombres de los elementos en el directorio de origen
elementos = os.listdir(directorio_origen)
# elementos = os.listdir(ruta_base)

# Filtrar solo los nombres de las carpetas
subcarpetas = [nombre.split(".")[0] for nombre in elementos if os.path.isdir(os.path.join(directorio_origen, nombre))]
# subcarpetas = [nombre.split(".")[0] for nombre in elementos if os.path.isdir(os.path.join(ruta_base, nombre))]

# procesamiento de recortes.
json_salida = detalles_recortes_JSON(ruta_base)

# with open('./Archivos/recortes.json', 'w') as json_file:
#     json.dump(json_salida, json_file, indent=4)


total_recortes = recortes + json_salida

with open('./Archivos/recortes.json', 'w') as json_file:
    json.dump(total_recortes, json_file, indent=4)
