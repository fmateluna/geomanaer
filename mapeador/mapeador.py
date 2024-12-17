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
    try:
        ruta_maestro_calles = obtener_ruta_maestro_calles()

        # Crear la conexión a DuckDB
        conn = duckdb.connect(ruta_maestro_calles)

        # Función para escapar comillas simples
        def escapar_comillas(valor):
            return valor.replace("'", "''") if valor else ""

        # Asegurarse de que las variables no sean None, limpiar espacios y escapar comillas
        nombre_via = escapar_comillas(direccion_procesada.nombre_via.strip().upper()) if direccion_procesada.nombre_via else ""
        comuna = escapar_comillas(direccion_procesada.comuna.strip().upper()) if direccion_procesada.comuna else ""
        region = escapar_comillas(direccion_procesada.region.strip().upper()) if direccion_procesada.region else ""
        jerarquia = escapar_comillas(direccion_procesada.jerarquia.strip().upper()) if direccion_procesada.jerarquia else ""

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
            
            return direccion_procesada   

    except Exception as e:
        # Manejo de errores de la base de datos
        print(f"Error al procesar la dirección en el maestro de calles: {e}")
        return None
    finally:
        # Asegurar que la conexión se cierra
        if 'conn' in locals() and conn:
            conn.close()

    return None  # En caso de que no se encuentre una calle adecuada

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
        if similitud > mejor_similitud and similitud >= 80:  # 80% de similitud mínima
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
    # Cargar mapeos de jerarquías y abreviaciones
    jerarquias = cargar_traductores("mapeador/jerarquias.json")
    abreviaciones = cargar_traductores("mapeador/abreviaciones.json")

    # Dividir el nombre de la vía en partes
    partes_nombre_via = direccion.nombre_via.split()
    partes_corregidas = []

    for palabra in partes_nombre_via:
        # Intentar corregir la palabra usando el glosario de jerarquías
        palabra_corregida = corregir_glosario(palabra, jerarquias)

        # Verificar si la palabra corregida coincide con alguna clave (key) en jerarquías
        jerarquia_normalizada = None
        for key in jerarquias:
            if palabra_corregida == key:  # Comparar directamente con la clave
                jerarquia_normalizada = key
                break  

        if jerarquia_normalizada:
            if direccion.jerarquia == "":
                direccion.jerarquia = jerarquia_normalizada
        else:
            # Si no es una jerarquía, intentar corregir con abreviaciones
            palabra_corregida = corregir_glosario(palabra_corregida, abreviaciones)

        # Agregar la palabra corregida a la lista
        partes_corregidas.append(palabra_corregida)

    # Reconstruir la dirección formateada
    direccion.direccion_formateada = " ".join(partes_corregidas)

    return direccion







