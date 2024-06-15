# Deteccion_Clasificacion_Cambios
Destección y clasificación de cambios en imágenes satelitales reutilizando la red BAN y ResNet152V2. 

Este sistema es parte del trabajo de titulación paper(url documento).

El sistema esta compuesto por una red profunda BAN, encargada para la detección de cambios en dos imágenes satelitales del mismo lugar pero en diferente tiempo. Además, se integrada un modelo preentrenado ResNet152V2 para realizar la clasificación de los cambios en 10 categorías.

## Conjunto de datos
El conjunto de datos almacenado en el sitio web Kaggle ([DCC-San-Juan-Bosco],https://kaggle.com/datasets/23c6ddb51029b5dc20c5291d958467f1524cf2abc782cbc8b1f4f965eed89dda)

## Directorio BAN 
Fue reentrenada con un dataset creado manualmente. El repositorio es el siguiente: ([BAN],https://github.com/likyoo/BAN?tab=readme-ov-file), allí se detalla la forma en como clonar el repositorio para su uso y como instalar el directorio open-cd.

### Agregar
Dentro del directorio BAN, es necesario crear una carpeta 'checkpoint' y colocar el modelo reentrenado 'iter_4000.pth'. El modelo se encuentra es el siguiente link: ([iter_4000.pth],https://drive.google.com/file/d/1D1aT5CGi5ZTaES0XjWbbCULFZvOQ_YAe/view?usp=drive_link) 

En resumen se debe crear:
```bash
-checkpoint
    --iter_4000.pth
-data  
    --LEVIR-CD
        ---test
            ----A
            ----B
            ----label
        ---label2
```
## Visualizador
Sitio web desarrollado por Streamlit.io. Toda la lógica está creada en lenguaje de Pyhton.

### Agregar
Crear el siguiente directorio:
```bash
-Modelos
    --ResNet152V2.h5
```
El modelo preentrenado lo puede descargar de: ([ResNet152V2],https://drive.google.com/file/d/1MkThCHmPvfXqnspdWFh64O1NSHqF5eDf/view?usp=drive_link)

# Red ResNet152V2
Es modelo preentrenado que se lo obtuvo del sitio de Kaggle. Su enlace es el siguiente: ([Modelo_preentrenado],https://www.kaggle.com/code/nilesh789/land-cover-classification-with-eurosat-dataset).
