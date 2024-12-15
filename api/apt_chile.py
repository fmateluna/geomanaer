import datetime
from api.payloads import APTDireccion, APTLocalidades
import duckdb
from typing import List, Optional
from mapeador.config.PathConfig import obtener_ruta_apt_chile, obtener_ruta_apt_localidades


class AptChile:
    def __init__(self):
        self.database_apt_chile_path = obtener_ruta_apt_chile()
        self.database_apt_localidades_path = obtener_ruta_apt_localidades()
        
        
    def buscar_direccion_sin_numero(self, cod_comuna: str, nombre_localidad: str) -> APTLocalidades:
        """
        Busca una localidad en la base de datos localidades.duckdb.

        Args:
            cod_comuna (str): Código de la comuna a buscar.
            nombre_localidad (str): Nombre exacto de la localidad.

        Returns:
            Optional[LocalidadesResponse]: Resultado de la consulta o None si no se encuentra.
        """
        # Conectar a DuckDB
        conn = duckdb.connect(self.database_apt_localidades_path)
        
                # Ajustar el formato de la dirección
        direccion_like = '%'.join(nombre_localidad.split())  # Reemplaza espacios con %

        # Query parametrizada
        query = """
        SELECT 
            id_localid,
            cod_comuna,
            comuna,
            cod_r,
            region,
            nombre_localidad,
            longitud,
            latitud,
            tipo,
            estado,
            circuns,
            codigo_cir,
            glosacircu,
            principal,
            revisado,
            created_user,
            created_date,
            last_edited_user,
            last_edited_date,
            globalid
        FROM localidades
        WHERE 
            cod_comuna = ?
            AND nombre_localidad ILIKE ? 
        LIMIT 1
        """

        # Ejecutar la consulta
        resultado = conn.execute(query, (cod_comuna, f"%{direccion_like}%")).fetchone()

        # Cerrar la conexión
        conn.close()

        # Retornar el resultado mapeado si existe
        if resultado:
            return APTLocalidades(
                id_localid=int(resultado[0]) if resultado[0] is not None else None,
                cod_comuna=str(resultado[1]) if resultado[1] is not None else "",
                comuna=str(resultado[2]) if resultado[2] is not None else "",
                cod_r=str(resultado[3]) if resultado[3] is not None else "",
                region=str(resultado[4]) if resultado[4] is not None else "",
                nombre_localidad=str(resultado[5]) if resultado[5] is not None else "",
                longitud=float(resultado[6]) if resultado[6] is not None else None,
                latitud=float(resultado[7]) if resultado[7] is not None else None,
                tipo=str(resultado[8]) if resultado[8] is not None else "",
                estado=str(resultado[9]) if resultado[9] is not None else "",
                circuns=str(resultado[10]) if resultado[10] is not None else "",
                codigo_cir=str(resultado[11]) if resultado[11] is not None else "",
                glosacircu=str(resultado[12]) if resultado[12] is not None else "",
                principal=str(resultado[13]) if resultado[13] is not None else "",
                revisado=str(resultado[14]) if resultado[14] is not None else "",
                created_user=str(resultado[15]) if resultado[15] is not None else None,
                created_date=datetime.fromisoformat(resultado[16]) if resultado[16] is not None else None,
                last_edited_user=str(resultado[17]) if resultado[17] is not None else None,
                last_edited_date=datetime.fromisoformat(resultado[18]) if resultado[18] is not None else None,
                globalid=str(resultado[19]) if resultado[19] is not None else "",
            )
        return None        

    def buscar_direccion_con_numero(self, cut: int , direccion: str, numero: str) -> APTDireccion:
        """
        Busca una dirección en la base de datos apt_chile.duckdb.

        Args:
            cut (int): Código de comuna (CUT) para filtrar.
            direccion (str): Dirección parcial a buscar.
            numero (str): Número exacto de la dirección.

        Returns:
            AptChileResponse: Resultado de la consulta con todos los campos de la tabla apt_chile.
        """
        # Conectar a DuckDB
        conn = duckdb.connect(self.database_apt_chile_path)

        # Ajustar el formato de la dirección
        direccion_like = '%'.join(direccion.split())  # Reemplaza espacios con %
        
        # Query parametrizada con todos los atributos
        query = """
        SELECT
            COD_DIRECCION,
            NOMBRE_DIRECC,
            NUMERO,
            COORDENADA_X,
            COORDENADA_Y,
            FECHA_INGRESO,
            FECHA_ACTUALIZACION,
            FECHA_GEOREFERENCIA,
            FECHA_NOVIGENCIA,
            COD_VIGENCIA,
            FLAG_NORMALIZADO,
            COD_COMUNA_INE,
            COD_COM_TXT,
            COD_CALLE,
            LETNUM,
            SITIO,
            DEPTO,
            CASA,
            BLOCK,
            COD_CALLE_OLD,
            COD_VIA,
            FUENTE,
            COD_LOCALIDAD,
            COD_ENTIDAD,
            COD_CPOBLADO,
            REFERENCIA,
            COD_UVECINAL,
            COD_AH,
            LOCALIDAD_RSH
        FROM apt_chile
        WHERE 
            COD_COMUNA_INE = ? 
            AND NOMBRE_DIRECC ILIKE ? 
            AND NUMERO = ?
        LIMIT 1
        """

        # Ejecutar la consulta
        resultado = conn.execute(query, (cut, f"%{direccion_like}%", numero)).fetchone()

        # Cerrar la conexión
        conn.close()

        if resultado is not None:
            # Mapear los resultados a AptChileResponse
            apt_chile_responses = APTDireccion(
                cod_direccion=resultado[0],
                nombre_direcc=resultado[1],
                numero=str(resultado[2]),  # Convierte a str
                coordenada_x=str(resultado[3]),  # Convierte a str
                coordenada_y=str(resultado[4]),  # Convierte a str
                fecha_ingreso=resultado[5],
                fecha_actualizacion=resultado[6],
                fecha_georeferencia=resultado[7],
                fecha_novigencia=resultado[8],
                cod_vigencia=resultado[9],
                flag_normalizado=resultado[10],
                cod_comuna_ine=resultado[11],
                cod_com_txt=resultado[12],
                cod_calle=resultado[13],
                letnum=resultado[14],
                sitio=resultado[15],
                depto=resultado[16],
                casa=resultado[17],
                block=resultado[18],
                cod_calle_old=resultado[19],
                cod_via=resultado[20],
                fuente=resultado[21],
                cod_localidad=resultado[22],
                cod_entidad=resultado[23],
                cod_cpoblado=resultado[24],
                referencia=resultado[25],
                cod_uvecinal=resultado[26],
                cod_ah=resultado[27],
                localidad_rsh=resultado[28]
            )        
            return apt_chile_responses
        return None
