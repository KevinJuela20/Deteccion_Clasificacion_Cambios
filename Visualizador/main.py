import streamlit as st
import requests
from streamlit_lottie import st_lottie
from PIL import Image
import os
import time
import shutil
import json

from Script.ContadorPixeles import contar_pixeles_por_color

# -------FUNCIONES -----------------------------------------------------------------------------------------------
# Animación de carga
def animacion(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def eliminar_archivos(directory_path):
    # Eliminar el directorio y su contenido
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)    
    # Volver a crear el directorio
    os.makedirs(directory_path)

def obtener_numero(archivo):
    return int(archivo.split('.')[0])

# Listar zonas y fechas de cada zona
def listar_carpetas_con_subcarpetas(ruta_base):
    zonas = []
    
    # Listar todas las carpetas en el directorio base
    for nombre in os.listdir(ruta_base):
        ruta_carpeta = os.path.join(ruta_base, nombre)
        ruta_label = os.path.join(ruta_Label, nombre)
        ruta_label2 = os.path.join(ruta_Label2, nombre)

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
            arc_label2 = []
            for label2 in os.listdir(ruta_label2):
                ruta_archivo = os.path.join(ruta_label2, label2)
                if os.path.isfile(ruta_archivo):
                    arc_label2.append(label2)
            unionFechas = []
            i = 1
            j = 0
            a_l = sorted(arc_label, key=obtener_numero)
            a_l2 = sorted(arc_label2, key=obtener_numero)

            for fe in fechas:
                for x in fechas[i:]:
                    fechasJoin = fe + ":"+ x
                    aux = {
                        "union": fechasJoin,
                        "Label": a_l[j],
                        "Label2": a_l2[j]
                    }
                    unionFechas.append(aux)
                    j+=1
                i+=1
            zona = {
                "zona": nombre,
                "fechas": fechas,
                "fechasUnidas": unionFechas
            }
            zonas.append(zona)
    return zonas

def obtener_zonas(JSON):
    lis_zonas = []
    for a in JSON:
        lis_zonas.append(a['zona'])
    return lis_zonas

def obtener_label_por_union(data, union_buscada, label):
    for fechas_unidas in data:
        if fechas_unidas["union"] == union_buscada:
            return fechas_unidas[label]
    return None

# Función para simular un proceso y actualizar la barra de progreso
def simulate_process(bar, percent_complete, text):
    for _ in range(percent_complete):
        time.sleep(0.01)
        bar.progress(_ + 1, text=text)

def resaltar_texto(mensaje, color):
    texto_resaltado = f'<span style="background-color: {color}; color:{color}">{mensaje}</span>'
    return texto_resaltado

def obtener_valores(detalle, zonaActual, fecha1, fecha2):
    # Recorre cada zona en el JSON
    for zona in detalle:
        # Comprueba si la zona actual es la misma que la zona que estamos buscando
        if zona['zona'] == zonaActual:
            # Recorre cada recorte en la zona
            for recorte in zona['recortes']:
                # Forma la clave a buscar en los recortes
                clave = f"{fecha1}_{fecha2}"
                # Comprueba si la clave existe en los recortes
                if clave in recorte:
                    # Devuelve los valores correspondientes a la clave
                    return recorte[clave]
    # Si no se encuentra, devuelve None
    return None

def guardar_archivo(archivo_subir, ruta):
    with open(ruta, "wb") as f:
        f.write(archivo_subir.getbuffer())
    st.success(f"Archivo guardado")
def carga_archivos(nombre, archivos):
    #ruta
    aux_ruta = "./Archivos/Subidos/"+nombre

    #Crear la nueva carpeta de zona
    os.makedirs(aux_ruta, exist_ok=True)

    for arc in archivos:

        # Crear la ruta completa de guardado
        guardar_path = os.path.join(aux_ruta, arc.name)
        
        # Guardar el archivo en la ruta especificada
        guardar_archivo(arc, guardar_path)
    
# -------RUTAS----------------------------------------------------------------------------------------------------

ruta_base = "./Archivos/Zonas RGB/"
url_animacion_carga = animacion("https://lottie.host/cfe6395a-9fee-4bda-88f3-72aa3cc89f52/tIa0jnMb0w.json")
url_amimacion = animacion("https://lottie.host/63b73ec3-692d-4853-b104-c9103015a83c/v0pb8y0YQ4.json")
ruta_Label = "./Archivos/Label/"
ruta_Label2 = "./Archivos/Label2/"

archivo = "./Archivos/recortes.json"

# -------VARIABLES BASES------------------------------------------------------------------------------------------
carpetas = listar_carpetas_con_subcarpetas(ruta_base)
with open(archivo, 'r') as f:
    recortes = json.load(f)


# Título fijo
st.markdown("""
    <style>
    .fixed-title {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: white;
        padding: 20px 0 0 0;
        text-align: center;
        z-index: 10;
        border-bottom: 2px solid #f0f0f0;
    }
    .content {
        padding-top: 50px;
    }
    .st-emotion-cache-13ln4jf{
        max-width: 75rem;
    }
    .stTabs [role="tablist"] {
        display: flex;
        justify-content: space-around;
    }
    .stTabs [role="tab"] {
        flex: 1;
        text-align: center;
        font-size: 1.2em;
        padding: 10px;
    }
    .stToast{
        z-index: 2000 !important;
    }
            
    [data-testid="stHorizontalBlock"] {
        overflow: auto;
        height: 50vh; /* Ajusta la altura según sea necesario */
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="fixed-title"><h1>Visualizador</h1><h4> Detección de cambios con imágenes satelitales</h4> </div> ', unsafe_allow_html=True)
#st.markdown('<div class="fixed-title"><h1>Visualizador</h1></div> ', unsafe_allow_html=True)
# with st.container():
#     st.title("Vualizador")
#     st.subheader("Detección de cambios con imágenes satelitales")

with st.sidebar:
    st.header("Seleccione la zona")
    zonas = obtener_zonas(carpetas)
    zona_seleccionada = st.selectbox("", zonas)
    
    indice = zonas.index(zona_seleccionada)
    fechas = carpetas[indice]['fechas']
    st.header(f"Fechas disponibles en {zona_seleccionada}")
    
    selected_rows = st.multiselect("", fechas, placeholder="Seleccione dos fechas", key="fechas_multiselect")
    
    if len(selected_rows) == 2:
        st.toast(':green[¡Perfecto!]', icon='👌')
    elif len(selected_rows) > 2:
        st.toast(':blue[¡Por favor, seleccione solo dos fechas!]', icon='🤨')
    elif len(selected_rows) < 2:
        st.toast(":red[Seleccione dos fechas de la lista]", icon="😁")

    
    with st.container(border=True):
        st.subheader("Cargar nueva zona")
        nom = st.text_input("Ingrese nombre de la Zona",value="")
        num = st.text_input("Ingrese el número de zip a subir", value="")
        
        if nom != "" and num != "":
            st.write("Los archivos (mímino 2) deben ser de tipo .zip y contener las bandas 2,3,4,8. El nombre del archivo debe ser 'Zona #-yyyy-mm-dd.zip' ")
            # Usar el cargador de archivos para subir un archivo de tipo zip
            archivos = st.file_uploader("", type="zip", accept_multiple_files=True)
            num_ent = int(num)
            if len(archivos) == num_ent and num_ent > 1:
                st.success("Genial")
                carga_archivos(nom, archivos)

            elif (len(archivos) > 0) and (len(archivos) < num_ent): 
                st.error("Faltan archivos")
            elif len(archivos)==0:
                st.error("Archivos aún no seleccionados")
            else:
                st.error("Número de archivos excedidos")


st.markdown('<div class="content">', unsafe_allow_html=True)

# General container
with st.container():

    tabs = st.tabs(["IA", "Basado en píxeles"])
    selected_rows.sort()
    # IA tab
    with tabs[0]:
        
        if len(selected_rows) == 2:
            
            with st.container():
                c1, c2, c3 = st.columns(3)
                with c1: 
                    st.subheader("Imagen anterior")
                    img1 = Image.open(ruta_base+zona_seleccionada+"/"+selected_rows[0])
                    st.image(img1.resize((350, 350)),caption=selected_rows[0].split(".")[0])
                with c2:
                    st.subheader("Imagen posterior")
                    img2 = Image.open(ruta_base+zona_seleccionada+"/"+selected_rows[1])
                    st.image(img2.resize((350, 350)), caption=selected_rows[1].split(".")[0])

                with c3:
                    label = carpetas[indice]['fechasUnidas']
                    f_join = selected_rows[0]+":"+selected_rows[1]
                    aux = obtener_label_por_union(label,f_join,"Label")
                    st.subheader(":red[_Cambios Detectados_]")
                    rutaEti = ruta_Label+zona_seleccionada+"/"+aux
                    img3L = Image.open(rutaEti)
                    st.image(img3L.resize((350, 350)), caption=aux)
            
            with st.container():
                # Recortar las imágenes.
                temp = obtener_valores(recortes,zona_seleccionada,selected_rows[0].split(".")[0],selected_rows[1].split(".")[0])

                cols = st.columns(3)

                cols[0].header("Recorte")
                cols[1].header("Anterior")
                cols[2].header("Posterior")
                
                for detalle in temp:
                    with cols[0]:
                        imgR1 = Image.open(detalle["Rec_L"])
                        st.image(imgR1.resize((120,120)), caption="Polígono")
                    with cols[1]:
                        imgR2 = Image.open(detalle["Rec_A"])
                        st.image(imgR2.resize((120,120)), caption=detalle["Eti_A"])
                    with cols[2]:
                        imgR3 = Image.open(detalle["Rec_B"])
                        st.image(imgR3.resize((120,120)), caption=detalle["Eti_B"])

        else :
            st.info("Elegir dos fechas",icon="📆")
            st_lottie(url_amimacion, height=300)

    # Pixels tab
    with tabs[1]:
        if len(selected_rows) == 2:
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Imagen pasada")
                #img1 = Image.open(ruta_base+zona_seleccionada+"/"+selected_rows[0])
                st.image(img1.resize((350, 350)),caption=selected_rows[0].split(".")[0])
            with col2:
                st.subheader("Imagen posterior")
                #img2 = Image.open(ruta_base+zona_seleccionada+"/"+selected_rows[1])
                st.image(img2.resize((350, 350)), caption=selected_rows[1].split(".")[0])
            with col3:
                label2 = carpetas[indice]['fechasUnidas']
                f_join = selected_rows[0]+":"+selected_rows[1]
                aux = obtener_label_por_union(label2,f_join,"Label2")
                st.subheader(":red[_Cambios Detectados_]")
                img3L2 = Image.open(ruta_Label2+zona_seleccionada+"/"+aux)
                st.image(img3L2.resize((350, 350)))
                

            with st.container():
                with st.spinner('Realizando calculos...'):
                    x = contar_pixeles_por_color(ruta_Label2+zona_seleccionada+"/"+aux)

                    mensaje_resaltado = resaltar_texto("----", "#440154")
                    st.markdown(mensaje_resaltado +  '<span style="font-weight: bold;"> ⫸ SIN CAMBIOS</span>', unsafe_allow_html=True)
                    bar1 = st.progress(0, text="")
                    bar1.empty()
                    simulate_process(bar1, int(round(x[3],2)), "{}% ➡️ Metros cuadrados: {}".format(round(x[3],2), x[0]))
                    mensaje_resaltado = resaltar_texto("----", "#FDE724")
                    st.markdown(mensaje_resaltado+'<span style="font-weight: bold;"> ⫸ VEGETACIÓN a NO VEGETACIÓN</span>', unsafe_allow_html=True)
                    bar2 = st.progress(0, text="")
                    bar2.empty()
                    simulate_process(bar2, int(round(x[4],2)), "{}% ➡️ Metros cuadrados: {}".format(round(x[4],2), x[1]))

                    mensaje_resaltado = resaltar_texto("----", "#30678D")
                    st.markdown(mensaje_resaltado+'<span style="font-weight: bold;"> ⫸ NO VEGETACIÓN a VEGETACIÓN</span>', unsafe_allow_html=True)

                    bar3 = st.progress(0, text="")
                    bar3.empty()
                    simulate_process(bar3, int(round(x[5],2)), " {}% ➡️ Metros cuadrados: {}".format(round(x[5],2), x[2]))

        else: 
            st.info("Elegir dos fechas",icon="📆")
            st_lottie(url_amimacion, height=300)

st.markdown('</div>', unsafe_allow_html=True)
