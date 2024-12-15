import os
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from contextlib import contextmanager
from datetime import datetime
import time

from api.payloads import ServelDireccionPersona, ServelLocalidades

DB_CONFIG_SERVEL = {
    "dbname": os.getenv("DB_NAME_SERVEL", "prototipo_servel"),
    "user": os.getenv("DB_USER", "georoot"),
    "password": os.getenv("DB_PASSWORD", "Servel_IDDQD"),
    "host": os.getenv("DB_HOST", "10.247.119.90"),
    "port": os.getenv("DB_PORT", "5434"),
}


# Crear el motor de conexión
DATABASE_SERVEL_URL = f"postgresql://{DB_CONFIG_SERVEL['user']}:{DB_CONFIG_SERVEL['password']}@{DB_CONFIG_SERVEL['host']}:{DB_CONFIG_SERVEL['port']}/{DB_CONFIG_SERVEL['dbname']}"
engine = create_engine(DATABASE_SERVEL_URL, poolclass=NullPool)

# Crear una sesión de base de datos
SessionServel = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from contextlib import contextmanager

@contextmanager
def get_servel_session():
    """
    Provee una sesión para interactuar con la base de datos `prototipo_servel`.
    """
    session = SessionServel()
    try:
        yield session
    finally:
        session.close()
        
def servel_direccion_persona(nombre_via: str, numero: str, comuna: str, region: str, cut_comuna: str, cut_r: str):
    """
    Consulta para obtener información de una dirección en función de los parámetros especificados.

    Args:
        nombre_via (str): Nombre de la vía.
        numero (str): Número de la dirección.
        comuna (str): Nombre de la comuna.
        region (str): Nombre de la región.
        cut_comuna (str): Código único territorial de la comuna.
        cut_r (str): Código único territorial de la región.

    Returns:
        DireccionPersonaResponse | None: Resultado de la consulta como objeto o None si no hay coincidencias.
    """
    query = text(
        """
         SELECT
            dp.id,
            ((SIMILARITY(UPPER(dp.nombre_via), UPPER(:nombre_via)) +
            SIMILARITY(UPPER(c.comuna), UPPER(:comuna)) +
            SIMILARITY(UPPER(r.region), UPPER(:region))) / 3) * 100 AS score_total,
            SIMILARITY(UPPER(dp.nombre_via), UPPER(:nombre_via)) as score,
            c.comuna,
            c.provincia,
            r.region,
            r.cut_reg,
            c.cut_com,
            c.provincia,
            dp.tipo_via,
            dp.nombre_via,
            dp.numero,
            dp.resto,
            dp.referencia,
            dp.localidad,
            dp.cut_region,
            dp.cut_provincia,
            dp.cut_comuna,
            dp.tipo_geo_id,
            dp.revisado_id,
            dp.obs_analista,
            dp.geo_id,
            dp.tipo_padron_id,
            dp.orden_edicion_id,
            dp.prioridad_id,
            dp.control_id,
            dp.latitud,
            dp.longitud,
            dp.geom,
            dp.created_by,
            dp.created_at,
            dp.updated_by,
            dp.updated_at,
            dp.deleted_by,
            dp.deleted_at
        FROM
            direccion_persona dp
        INNER JOIN
            regiones AS r 
            ON ((r.cut_reg = dp.cut_region or r.cut_reg=:cut_reg) OR SIMILARITY(UPPER(r.region), UPPER(:region)) > 0.9)
        INNER JOIN
            comunas AS c 
            ON ((c.cut_com = dp.cut_comuna or c.cut_com=:cut_com) OR SIMILARITY(UPPER(c.comuna), UPPER(:comuna)) > 0.9)
        WHERE
            dp.numero = :numero 
            AND SIMILARITY(UPPER(dp.nombre_via), UPPER(:nombre_via))>0.6
        ORDER BY
            score DESC,
            dp.created_at DESC,
            dp.updated_at DESC
        LIMIT 1;



        """
    )

    try:
        # Ejecutar la consulta
        with get_servel_session() as session:  # Reemplaza con tu función para manejar sesiones
            try:
                result = session.execute(
                    query,
                    {
                        "nombre_via": nombre_via,
                        "numero": numero,
                        "comuna": comuna,
                        "region": region,
                        "cut_com": cut_comuna,
                        "cut_reg": cut_r,
                    },
                ).fetchone()
            except SQLAlchemyError as e:
                raise Exception(f"Error ejecutando la consulta SQL: {str(e)}")

        # Convertir el resultado a un objeto de respuesta si existe
        if result:
            try:
                return ServelDireccionPersona(**dict(result._asdict()))
            except AttributeError as e:
                raise Exception(f"Error al convertir el resultado a un objeto de respuesta: {str(e)}")
        else:
            return None

    except Exception as e:
        # Captura cualquier error general y lo muestra
        print(f"Error en 'servel_direccion_persona': {str(e)}")
        return None


def formatear_direccion(direccion: ServelDireccionPersona) -> str:
    """
    Formatea la dirección en un formato legible: 
    nombre_via + numero + provincia + comuna + region.
    
    Args:
        direccion (DireccionPersonaResponse): Objeto con los detalles de la dirección.
        
    Returns:
        str: Dirección formateada.
    """
    # Verificar si los campos requeridos están presentes y formatear la dirección
    try:
        direccion_formateada = f"{direccion.nombre_via} {direccion.numero}, {direccion.provincia}, {direccion.comuna}, {direccion.region}"
        return direccion_formateada
    except AttributeError as e:
        raise Exception(f"Error al formatear la dirección: {str(e)}")



def servel_localidades(nombre_via: str, cut_r: Optional[int] = None, region: Optional[str] = None, 
                         cut_comuna: Optional[int] = None, comuna: Optional[str] = None) -> Optional[ServelLocalidades]:
    query = text(
        """
        SELECT
            SIMILARITY(UPPER(l.nombre), UPPER(:nombre_via)) AS score,
            l.nombre AS localidad_nombre,
            l.comuna AS localidad_comuna,
            l.region AS localidad_region,
            l.id,
            l.geom,
            l.objectid,
            l.id_localid,
            l.cod_comuna,
            c.comuna AS comuna_nombre,
            r.region AS region_nombre,
            l.glosa_re,
            l.longitud,
            l.latitud,
            l.tipo,
            l.estado,
            l.circuns,
            l.codigo_cir,
            l.glosacircu,
            l.principal,
            l.revisado,
            l.created_user,
            l.last_edited_user,
            l.globalid 
        FROM
            localidades l
        INNER JOIN
            regiones r 
            ON (CAST(r.cut_reg AS INTEGER) = l.region OR CAST(:cut_reg AS INTEGER) = l.region OR SIMILARITY(UPPER(r.region), UPPER(:region)) > 0.9)
        INNER JOIN
            comunas c 
            ON (CAST(c.cut_com AS INTEGER) = l.cod_comuna OR CAST(:cut_com AS INTEGER) = l.cod_comuna OR SIMILARITY(UPPER(c.comuna), UPPER(:comuna)) > 0.9)
        where
        	SIMILARITY(UPPER(l.nombre), UPPER(:nombre_via))>0.9
        ORDER BY
            l.created_date
        LIMIT 1
        """
    )

    try:
        # Ejecutar la consulta
        with get_servel_session() as session:
            try:
                result = session.execute(
                    query, {
                        "nombre_via": nombre_via, 
                        "cut_reg": cut_r, 
                        "region": region, 
                        "cut_com": cut_comuna, 
                        "comuna": comuna
                    }
                ).fetchone()
            except SQLAlchemyError as e:
                raise Exception(f"Error ejecutando la consulta SQL: {str(e)}")

        # Convertir el resultado a la clase ServelLocalidades
        if result:
            return ServelLocalidades(**dict(result._mapping))
        else:
            return None

    except Exception as e:
        # Captura cualquier error general y lo muestra
        print(f"Error en 'servel_localidades': {str(e)}")
        return None

