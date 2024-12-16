# Librerías estándar
import json
import re
import time
from api.payloads import DatosCallejeros, InfoGeoDireccion
import duckdb
from fuzzywuzzy import fuzz

# Librerías de terceros
from difflib import get_close_matches
import pandas as pd

from mapeador.config.PathConfig import obtener_ruta_maestro_calles

# Función para cargar el CSV de MAESTROCALLES
def cargar_maestro_calles(archivo):
    """Carga el archivo CSV asegurando la codificación UTF-8"""
    return pd.read_csv(archivo, encoding="utf-8")


def procesa_direccion_maestro_calle(direccion_procesada: InfoGeoDireccion):
    ruta_maestro_calles = obtener_ruta_maestro_calles()

    # Crear la conexión a DuckDB
    conn = duckdb.connect(ruta_maestro_calles)

    # Asegurarse de que las variables no sean None y asignarles un valor por defecto vacío si lo son
    nombre_via = direccion_procesada.nombre_via.strip().upper() if direccion_procesada.nombre_via else ""
    comuna = direccion_procesada.comuna.strip().upper() if direccion_procesada.comuna else ""
    region = direccion_procesada.region.strip().upper() if direccion_procesada.region else ""
    jerarquia = direccion_procesada.jerarquia.strip().upper() if direccion_procesada.jerarquia else ""

    # Optimización: Consultar solo las filas potencialmente relevantes
    query = f"""
    SELECT * 
    FROM maestro_calles
    WHERE 
        upper(COMUNA) LIKE '%{comuna}%' 
        OR upper(REGION) LIKE '%{region}%'
        OR upper(NOMBRE_VIA) ILIKE '%{nombre_via}%'
    """
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]

    mejor_similitud = 0
    mejor_fila = None  # Solo una fila de mejor resultado

    for fila in rows:
        # Acceder a las columnas por índice a través de sus nombres
        jerarquia_similitud = fuzz.ratio(fila[column_names.index("JERARQUIA")].upper(), jerarquia) if fila[column_names.index("JERARQUIA")] else 0
        comuna_similitud = fuzz.ratio(fila[column_names.index("COMUNA")].upper(), comuna) if fila[column_names.index("COMUNA")] else 0
        region_similitud = fuzz.ratio(fila[column_names.index("REGION")].upper(), region) if fila[column_names.index("REGION")] else 0
        nombre_via_similitud = fuzz.ratio(fila[column_names.index("NOMBRE_VIA")].upper(), nombre_via) if fila[column_names.index("NOMBRE_VIA")] else 0

        puntaje_total = (
            ((jerarquia_similitud > 70) * jerarquia_similitud)
            + (comuna_similitud >= 70) * comuna_similitud
            + (region_similitud >= 70) * region_similitud
            + (nombre_via_similitud >= 50) * nombre_via_similitud
        )

        if puntaje_total > mejor_similitud:
            mejor_similitud = puntaje_total
            mejor_fila = fila  # Actualizamos con la nueva mejor fila

    # Cerrar la conexión
    conn.close()

    # Devolver mejor fila como diccionario (opcional, para facilitar el uso posterior)
    if mejor_fila:
        mejor_resultado_callejero = {column_names[idx]: value for idx, value in enumerate(mejor_fila)}
        
        datos_callejeros = DatosCallejeros()
        direccion_procesada.nombre_via = mejor_resultado_callejero["NOMBRE_VIA"]
        datos_callejeros.jerarquia = mejor_resultado_callejero["JERARQUIA"]
        datos_callejeros.cen_lat = mejor_resultado_callejero["CEN_LAT"]
        datos_callejeros.cut = str(mejor_resultado_callejero["CUT"])
        datos_callejeros.cut_r = str(mejor_resultado_callejero["CUT_R"])
        datos_callejeros.cen_lat = mejor_resultado_callejero["CEN_LAT"]
        datos_callejeros.cen_lon = mejor_resultado_callejero["CEN_LON"]
        
        direccion_procesada.datos_callejeros = datos_callejeros
        
        direccion_procesada.direccion_formateada = (
            mejor_resultado_callejero["JERARQUIA"]
            + " "
            + mejor_resultado_callejero["NOMBRE_VIA"]
            + " "
            + direccion_procesada.numero
            + ", "
            + mejor_resultado_callejero["COMUNA"]
            + ", "
            + mejor_resultado_callejero["PROVINCIA"]
            + ", "
            + mejor_resultado_callejero["REGION"]
        )
        
        return  direccion_procesada   
    return None #Te falta calle..



# Cargar glosario de jerarquías desde un archivo JSON
def cargar_traductores(archivo):
    """Carga las jerarquías desde un JSON asegurando UTF-8"""
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


# Normalizar texto: eliminar puntos y convertir a mayúsculas
def normalizar_texto(texto):
    return re.sub(r"\.", "", texto).strip().upper()


def corregir_glosario(texto, diccionario):
    """
    Corrige errores de escritura en jerarquías basándose en las claves del glosario.
    Permite un máximo de 3 errores de escritura según distancia de Levenshtein.
    """
    texto = normalizar_texto(texto)  # Normalizar entrada
    palabras = list(diccionario.keys())  # Consideramos solo las claves del glosario
    
    mejor_match = None
    mejor_similitud = 0

    for palabra in palabras:
        similitud = fuzz.ratio(texto, palabra)
        if similitud > mejor_similitud and similitud >= 60:  # 80% de similitud mínima
            mejor_match = palabra
            mejor_similitud = similitud
    return mejor_match if mejor_match else texto


# Traducir jerarquías usando el glosario
def traducir_jerarquia(texto, jerarquias):
    texto = normalizar_texto(texto)
    for jerarquia, variaciones in jerarquias.items():
        if texto == jerarquia or texto in variaciones:
            return jerarquia
    return texto


# Procesar dirección completa, corrigiendo y traduciendo todas las palabras
def procesar_direccion(direccion: InfoGeoDireccion):
    jerarquias = cargar_traductores("mapeador/jerarquias.json")
    abreviaciones = cargar_traductores("mapeador/abreviaciones.json")
    partes_nombre_via = direccion.nombre_via.split()
    partes_corregidas = []

    for palabra in partes_nombre_via:
        palabra_corregida = corregir_glosario(palabra, jerarquias)
        palabra_corregida = corregir_glosario(palabra_corregida, abreviaciones)
        jerarquia_normalizada = traducir_jerarquia(palabra_corregida, jerarquias)
        if direccion.jerarquia == "":
            direccion.jerarquia = jerarquia_normalizada
              
            
        partes_corregidas.append(palabra_corregida)

    direccion.direccion_formateada = " ".join(partes_corregidas)

    return direccion


# Procesar texto simple (comuna, region, provincia)
def procesar_texto_simple(texto, jerarquias):
    if not texto:
        return texto  # Devuelve texto vacío si no hay nada que procesar

    palabras = texto.split()
    palabras_corregidas = []

    for palabra in palabras:
        palabra_corregida = corregir_glosario(palabra, jerarquias)
        jerarquia_normalizada = traducir_jerarquia(palabra_corregida, jerarquias)
        palabras_corregidas.append(jerarquia_normalizada)

    return " ".join(palabras_corregidas)



