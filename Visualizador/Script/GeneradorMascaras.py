import rasterio
import numpy as np
import matplotlib.pyplot as plt
import zipfile
import os
import tempfile
from tqdm import tqdm
import shutil


# Rutas a archivos
images_path = './Archivos/Subidos/'
bandas = './Archivos/Bandas/'
image_a_path = '../BAN - copia/data/LEVIR-CD/test/A/'
image_b_path = '../BAN - copia/data/LEVIR-CD/test/B/'
label_path = '../BAN - copia/data/LEVIR-CD/test/label/'

# Función para cargar las bandas 8, 4, 3 y 2 desde un directorio
def load_bands_from_dir(directory):
    band_8 = None
    band_4 = None
    band_3 = None
    band_2 = None
    for filename in os.listdir(directory):
        if 'B08' in filename and ('tif' in filename or 'tiff' in filename):
            with rasterio.open(os.path.join(directory, filename)) as src:
                band_8 = src.read(1)
        elif 'B04' in filename and ('tif' in filename or 'tiff' in filename):
            with rasterio.open(os.path.join(directory, filename)) as src:
                band_4 = src.read(1)
        elif 'B03' in filename and ('tif' in filename or 'tiff' in filename):
            with rasterio.open(os.path.join(directory, filename)) as src:
                band_3 = src.read(1)
        elif 'B02' in filename and ('tif' in filename or 'tiff' in filename):
            with rasterio.open(os.path.join(directory, filename)) as src:
                band_2 = src.read(1)
    return band_8, band_4, band_3, band_2

# Función para calcular el NDVI
def calculate_ndvi(band_8, band_4):
    ndvi = (band_8 - band_4) / (band_8 + band_4)
    return ndvi

# Obtener la lista de archivos ZIP en la carpeta de imágenes
zip_files = [f for f in os.listdir(images_path) if f.endswith('.zip')]

# Iterar sobre cada zona (carpeta dentro de images_path)
counter = 0
val=True
for zone_folder in os.listdir(images_path):
    zone_path = os.path.join(images_path, zone_folder)
    if not os.path.isdir(zone_path):  # Saltar si no es una carpeta
        continue
    zip_files = [f for f in os.listdir(zone_path) if f.endswith('.zip')]
    os.makedirs("./Archivos/Zonas RGB/"+zone_folder, exist_ok=True)
    os.makedirs("./Archivos/Label2/"+zone_folder, exist_ok=True)
    for i in tqdm(range(len(zip_files))):
        with tempfile.TemporaryDirectory() as temp_dir_a:
            with zipfile.ZipFile(os.path.join(zone_path, zip_files[i]), 'r') as zip_ref:
                zip_ref.extractall(temp_dir_a)
            band_8_a, band_4_a, _, _ = load_bands_from_dir(temp_dir_a)
            ndvi_a = calculate_ndvi(band_8_a, band_4_a)
            
            for j in range(i + 1, len(zip_files)):
                with tempfile.TemporaryDirectory() as temp_dir_b:
                    with zipfile.ZipFile(os.path.join(zone_path, zip_files[j]), 'r') as zip_ref:
                        zip_ref.extractall(temp_dir_b)
                    band_8_b, band_4_b, _, _ = load_bands_from_dir(temp_dir_b)
                    ndvi_b = calculate_ndvi(band_8_b, band_4_b)
                    diff = np.abs(ndvi_a - ndvi_b)
                    threshold = 0.2  # Ajusta este valor según tus necesidades
                    binary_diff = (diff > threshold).astype(np.uint8)

                    # Generar la etiqueta de cambio con los colores solicitados
                    label_class = np.zeros_like(binary_diff, dtype=np.uint8)
                    change_mask = ndvi_a > ndvi_b
                    label_class[binary_diff == 1] = change_mask[binary_diff == 1].astype(np.uint8) * 2
                    label_class[binary_diff == 1] += 1
                    label_class[binary_diff == 0] = 0  # Sin cambio (negro)

                    # Cargar y normalizar las bandas RGB para visualización
                    _, band_4_a, band_3_a, band_2_a = load_bands_from_dir(temp_dir_a)
                    _, band_4_b, band_3_b, band_2_b = load_bands_from_dir(temp_dir_b)

                    # Normalización y composición de las bandas RGB
                    image_a = np.dstack([np.interp(band, (band.min(), band.max()), (0, 1)) for band in [band_4_a, band_3_a, band_2_a]])
                    image_b = np.dstack([np.interp(band, (band.min(), band.max()), (0, 1)) for band in [band_4_b, band_3_b, band_2_b]])

                    # Guardar las imágenes A, B y la etiqueta (cambio)
                    plt.imsave(os.path.join(image_a_path, f'{counter}.png'), image_a)
                    plt.imsave(os.path.join(image_b_path, f'{counter}.png'), image_b)
                    plt.imsave(os.path.join(label_path, f'{counter}.png'), binary_diff, cmap='gray')
                    plt.imsave(os.path.join('./Archivos/Label2/'+zone_folder, f'{counter}.png'), label_class, cmap='viridis')
                    if val:
                        plt.imsave(os.path.join("./Archivos/Zonas RGB/"+zone_folder, zip_files[i].split(".")[0]+'.png'), image_a)
                        plt.imsave(os.path.join("./Archivos/Zonas RGB/"+zone_folder, zip_files[j].split(".")[0]+'.png'), image_b)
                        
                    counter += 1
            val=False

print("Ejecución correcta")