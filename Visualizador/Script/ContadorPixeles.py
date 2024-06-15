from PIL import Image

def contar_pixeles_por_color(imagen):
    # Abre la imagen
    img = Image.open(imagen)

    # Convierte la imagen a modo RGB (si no lo está ya)
    img = img.convert('RGB')

    # Inicializa contadores de píxeles por color
    morado = 0
    amarillo = 0
    turquesa = 0

    # Obtiene las dimensiones de la imagen
    width, height = img.size

    # Itera sobre cada píxel de la imagen y cuenta los píxeles por color
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            if r == 68 and g == 1 and b == 84:  # Píxel morado (RGB: 128, 0, 128)
                morado += 1
            elif r == 253 and g == 231 and b == 36:  # Píxel amarillo (RGB: 255, 255, 0)
                amarillo += 1
            elif r == 48 and g == 103 and b == 141:  # Píxel turquesa (RGB: 0, 255, 255)
                turquesa += 1

    # Calcula los porcentajes de píxeles por color
    total_pixeles = width * height
    porcentaje_morado = (morado / total_pixeles) * 100
    porcentaje_amarillo = (amarillo / total_pixeles) * 100
    porcentaje_turquesa = (turquesa / total_pixeles) * 100

    resultados = [morado, amarillo, turquesa, porcentaje_morado, porcentaje_amarillo, porcentaje_turquesa]
    return resultados
