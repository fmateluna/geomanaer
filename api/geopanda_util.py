from api.servel import DATABASE_SERVEL_URL
import geopandas as gpd
from shapely.geometry import Point
import os
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from contextlib import contextmanager

# Configuración de la conexión a la base de datos
DB_URI = "postgresql://usuario:contraseña@host:puerto/nombre_base_datos"


def esta_en_comuna(cut_com: str, lat: float, lon: float) -> dict:
    """
    Verifica si un punto (lat, lon) está dentro de la comuna especificada por cut_com.

    :param cut_com: Código único de la comuna.
    :param lat: Latitud del punto.
    :param lon: Longitud del punto.
    :return: True si el punto está en la comuna, False en caso contrario.
    """
    # Crear conexión a la base de datos
    engine = create_engine(DATABASE_SERVEL_URL, poolclass=NullPool)

    # Consulta para obtener la geometría de la comuna
    query = (
        f"SELECT  cut_com, comuna, geom FROM owd.comunas WHERE cut_com = '{cut_com}'"
    )

    # Cargar el resultado como un GeoDataFrame
    try:
        gdf = gpd.read_postgis(query, engine, geom_col="geom")
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        return False

    if gdf.empty:
        return {"error": f"No se encontró la comuna con cut_com: {cod_comuna}"}

    # Crear el punto a partir de latitud y longitud
    punto = Point(lon, lat)

    # Obtener la geometría de la comuna
    comuna_geom = gdf.iloc[0].geom
    comuna_nombre = gdf.iloc[0]["comuna"]

    # Determinar si está dentro, fuera o en el límite
    if comuna_geom.contains(punto):
        resultado = "Dentro"
    elif comuna_geom.touches(punto):
        resultado = "Limite"
    else:
        resultado = "Fuera"

    # Construir la salida
    return {
        "comuna": comuna_nombre,
        "cod_comuna": cut_com,
        "resultado": resultado,
    }
