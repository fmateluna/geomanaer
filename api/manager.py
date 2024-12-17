import re
from api.apt_chile import AptChile
from api.geopanda_util import esta_en_comuna
from api.googlemaps import GoogleMapsService
from api.nominatim import NominatimService
from api.payloads import APTLocalidades, DatosCallejeros, RequestGetGeo, APTDireccion
from api.servel import (
    formatear_direccion,
    servel_direccion_persona,
    servel_localidades,
)
from mapeador.mapeador import (
    InfoGeoDireccion,
    procesa_direccion_maestro_calle,
    procesar_direccion,
)
from fuzzywuzzy import fuzz

def convertir_a_float(valor, nombre_campo):
    try:
        return float(valor)
    except (TypeError, ValueError):
        print(f"Error: El valor de {nombre_campo} no se pudo convertir a float. Valor actual: {valor}")
        return None


def procesar_numero(numero: str) -> str:
    """
    Procesa el valor de 'numero' para devolver un número válido o una cadena vacía si no es válido.
    """
    if not numero or numero.strip().upper() in {
        "SIN NUMERO",
        "SIN NRO",
        "S/N",
        "SN",
        "SINNUMERO",
        "NAN",
        "NULL",
    }:
        return ""

    # Intentar extraer números directos de la cadena
    match = re.search(r"\b\d+\b", numero)
    if match:
        return match.group()  # Retorna el número encontrado

    # Si no se encuentra un número válido, retorna vacío
    return ""




def formatea_direcciones(direccion_original: InfoGeoDireccion):
    nombre_via_sin_procesar = direccion_original.nombre_via

    # Medir tiempo para formatear la dirección original

    if not es_clasificacion_rural(nombre_via_sin_procesar):
        direccion_procesada = procesar_direccion(direccion_original)
        mejor_resultado = procesa_direccion_maestro_calle(direccion_procesada)
    else:
        mejor_resultado = procesa_direccion_maestro_calle(direccion_original)
        direccion_procesada = direccion_original

    # RUTINA DE VALIDACION DE DIRECCION PROCESADA

    # Asegurarse de que mejor_resultado no sea None, si lo es, asignar un valor predeterminado.
    if mejor_resultado is not None:
        mejor_resultado = (
            direccion_procesada.copy()
        )  # Copiar los datos de direccion_procesada, dado que no encontro datos en procesa_direccion_maestro_calle
        mejor_resultado.apt_score = 0  # Inicializar apt_score a 0 si no existe

        # Comparar nombre_via con un umbral de similitud (usando fuzz.ratio)
        comparativa = fuzz.ratio(nombre_via_sin_procesar, mejor_resultado.nombre_via)

        # Comparar nombre_via
        if (
            direccion_procesada.nombre_via == mejor_resultado.nombre_via
            and comparativa > 50
        ):
            mejor_resultado.apt_score += (
                34  # Asignar 34 puntos por coincidencia en nombre_via
            )
        else:
            direccion_procesada.nombre_via = nombre_via_sin_procesar 

        # Comparar comuna
        if direccion_procesada.comuna == mejor_resultado.comuna:
            mejor_resultado.apt_score += (
                33  # Asignar 33 puntos por coincidencia en comuna
            )

        # Comparar región
        if direccion_procesada.region == mejor_resultado.region:
            mejor_resultado.apt_score += (
                33  # Asignar 33 puntos por coincidencia en región
            )

        # Si la puntuación total es menor a 100, actualizar nombre_via
        if mejor_resultado.apt_score < 100:
            mejor_resultado.nombre_via = nombre_via_sin_procesar

        # Retornar el mejor resultado con las actualizaciones
        return mejor_resultado

    else:
        direccion_procesada.apt_score = 0
        return direccion_procesada

def es_clasificacion_rural(nombre_via_original: str) -> bool:
    """
    Verifica si el nombre de la vía original contiene algún término asociado a ruralidad.
    
    :param nombre_via_original: String que representa el nombre original de la vía.
    :return: True si contiene un término de la lista de ruralidad, False en caso contrario.
    """
    # Lista de términos asociados a ruralidad
    terminos_ruralidad = [
        "RUTA", "KILOMETRO", "KM", "HACIENDA", "HAC", 
        "FUNDO", "FDO", "PARCELA", "PARCELACION", "PARC", 
        "PC", "SECTOR", "SITIO", "ST", "HIJUELA", 
        "ASENTAMIENTO", "LOTE", "LT"
    ]
    
    
    nombre_via_original_upper = nombre_via_original.upper()
    
    return any(termino in nombre_via_original_upper for termino in terminos_ruralidad)



def retorna_geolocalizacion(request: RequestGetGeo):

    resumen = {}  # <-- El resumen
    direccion_original = InfoGeoDireccion()

    encontre_en_servel = False
    encontre_en_apt = False
    encontre_en_google = False
    encontre_en_nominatim = False

    nombre_via_original = request.nombre_via

    # Representacion de NO NUMEROS = "SN" o numeros escritor como once o casos como calle 13,
    request.numero = procesar_numero(request.numero)
    direccion_original.numero = request.numero

    direccion_original.comuna = request.comuna
    direccion_original.region = request.region
    direccion_original.nombre_via = request.nombre_via
    direccion_original.provincia = request.provincia

    direccion_no_procesada = direccion_original.copy()

    direccion_procesada = direccion_no_procesada
    direccion_procesada.apt_score = 0
    
    
    direccion_procesada = formatea_direcciones(direccion_original)
        
    exactitud_nombre_via = fuzz.ratio(
        # Este es el caso cuando no hay forma de encontrar en el meastro de calles un formato adecuado
        direccion_procesada.nombre_via.upper(),
        nombre_via_original,
    )

    datos_callejeros = direccion_procesada.datos_callejeros

    if datos_callejeros is None:
        datos_callejeros = DatosCallejeros()
        datos_callejeros.cut_r = ""
        datos_callejeros.cut = ""

    # Cuando nos va mal con el Callejero
    if exactitud_nombre_via < 50:
        direccion_procesada = direccion_no_procesada.copy()

    # Guardo datos callejeros
    direccion_procesada.datos_callejeros = datos_callejeros

    apt_chile = AptChile()

    if request.numero != "":
        apt_chile_response = apt_chile.buscar_direccion_con_numero(
            int(direccion_procesada.datos_callejeros.cut or "0"),
            direccion_procesada.nombre_via,
            direccion_procesada.numero,
        )
        if apt_chile_response is not None:
            encontre_en_apt = True
            direccion_procesada.origen = "APT CHILE"
            direccion_procesada.apt = apt_chile_response
    else:
        apt_localidades_response = apt_chile.buscar_direccion_sin_numero(
            int(direccion_procesada.datos_callejeros.cut or "0"),
            direccion_procesada.nombre_via,
        )
        if apt_localidades_response is not None:
            encontre_en_apt = True
            direccion_procesada.origen = "APT LOCALIDADES"
            direccion_procesada.apt_localidades = apt_localidades_response

    # Si tienen un puntaje igual a 100, son la respuesta correcta si no les falta calle
    if direccion_procesada.apt_score == 100 and encontre_en_apt:
        if direccion_procesada.origen == "APT CHILE":
            resumen = {
                "origen": direccion_procesada.origen,
                "direccion": direccion_procesada.direccion_formateada,
                "latitud": direccion_procesada.apt.coordenada_y,
                "longitud": direccion_procesada.apt.coordenada_x,
            }
        if direccion_procesada.origen == "APT LOCALIDADES":
            resumen = {
                "origen": direccion_procesada.origen,
                "direccion": direccion_procesada.direccion_formateada,
                "latitud": direccion_procesada.apt_localidades.latitud,
                "longitud": direccion_procesada.apt_localidades.longitud,
            }
    else:

        # continuamos la busqueda de la direccion
        if request.numero != "":
            # nombre_via: str, numero: str, comuna: str, region: str, cut_comuna: str, cut_r: str
            direccion_persona = servel_direccion_persona(
                nombre_via=direccion_procesada.nombre_via,
                numero=direccion_procesada.numero,
                comuna=direccion_procesada.comuna,
                region=direccion_procesada.region,
                cut_comuna=(
                    str(direccion_procesada.datos_callejeros.cut or "0")
                    if direccion_procesada.datos_callejeros
                    else None
                ),
                cut_r=(
                    str(direccion_procesada.datos_callejeros.cut_r or "0")
                    if direccion_procesada.datos_callejeros
                    else None
                ),
            )

            if direccion_persona is not None:
                encontre_en_servel = True
                direccion_formateada = formatear_direccion(direccion_persona)
                direccion_procesada.servel_direccion_persona = direccion_persona
                resumen = {
                    "origen": "SERVEL_DIRECCION_PERSONA",
                    "direccion": direccion_formateada,
                    "latitud": direccion_persona.latitud,
                    "longitud": direccion_persona.longitud,
                }

        else:
            localidades = servel_localidades(
                nombre_via=direccion_procesada.nombre_via,
                comuna=direccion_procesada.comuna,
                region=direccion_procesada.region,
                cut_comuna=(
                    str(direccion_procesada.datos_callejeros.cut or "0")
                    if direccion_procesada.datos_callejeros
                    else None
                ),
                cut_r=(
                    str(direccion_procesada.datos_callejeros.cut_r or "0")
                    if direccion_procesada.datos_callejeros
                    else None
                ),
            )
            if localidades is not None:
                encontre_en_servel = True
                direccion_formateada = localidades.localidad_nombre
                direccion_procesada.servel_localidades = localidades
                resumen = {
                    "origen": "SERVEL_LOCALIDADES",
                    "direccion": direccion_formateada,
                    "latitud": localidades.latitud,
                    "longitud": localidades.longitud,
                }

    if not encontre_en_servel and not encontre_en_apt:
        direccion_para_apis_externas = (
            direccion_procesada.nombre_via
            + " "
            + direccion_procesada.numero
            + " , "
            + direccion_procesada.comuna
            + " ,"
            + direccion_procesada.region
        )

        is_rural = (direccion_procesada.numero == "" or  es_clasificacion_rural(direccion_para_apis_externas))

        nominatim_service = NominatimService()
        nominatim_response = nominatim_service.obtener_geolocalizacion(
            direccion_para_apis_externas
        )
        if nominatim_response is not None:
            direccion_procesada.nominatim = nominatim_response
            
            #Consultar si tiene el numero en su display_name  ()  gi
            if nominatim_response is not None:
                display_name = nominatim_response.get("display_name", "")
                direccion_procesada.nominatim = nominatim_response                    
                if direccion_procesada.numero in display_name or is_rural:
                    resumen = {
                        "direccion": display_name,
                        "latitud": nominatim_response.get("lat"),
                        "longitud": nominatim_response.get("lon"),
                        "origen": "Nominatim",
                    }
                    encontre_en_nominatim = True

        if not encontre_en_nominatim:
            google_maps_service = GoogleMapsService()
            response_api_google_maps = google_maps_service.obtener_geolocalizacion(
                direccion_para_apis_externas, is_rural
            )
            if response_api_google_maps is not None:
                direccion_procesada.google_maps = response_api_google_maps
                direccion_google = response_api_google_maps["formatted_address"]

                validando_google = fuzz.ratio(
                    direccion_google.lower(), direccion_para_apis_externas.lower()
                )

                palabras_original = set(direccion_para_apis_externas.lower().split())
                palabras_google = set(direccion_google.lower().split())
                palabras_comunes = palabras_original & palabras_google
                porcentaje_palabras_comunes = (
                    len(palabras_comunes) / len(palabras_original) * 100
                )

                # Validar si es aceptable por cualquiera de los criterios
                if (
                 (validando_google > 50 or porcentaje_palabras_comunes > 75) 
                ):  # Ajusta el porcentaje según necesidad
                    location = response_api_google_maps["geometry"]["location"]
                    resumen = {
                        "direccion": direccion_google,
                        "latitud": location["lat"],
                        "longitud": location["lng"],
                        "origen": "Google Maps",
                    }
                    encontre_en_google = True

        if not encontre_en_google and not encontre_en_nominatim:
            if datos_callejeros is not None:
                lat = datos_callejeros.cen_lat
                lon = datos_callejeros.cen_lon

            resumen = {
                "direccion": "",
                "latitud": lat,
                "longitud": lon,
                "origen": "DIRECCION NO ENCONTRADA",
            }

    # inicia como si no tuviera lat y lon, dado que eso se calcula despues
    comuna = {"Error": "no existe lat y lon a calcular"}
    try:
        latitud_geo_panda = convertir_a_float(resumen["latitud"], "latitud")
        longitud_geo_panda = convertir_a_float(resumen["longitud"], "longitud")

        resumen["latitud"] = latitud_geo_panda
        resumen["longitud"] = longitud_geo_panda

        if latitud_geo_panda is not None and longitud_geo_panda is not None:
            comuna = esta_en_comuna(
                direccion_procesada.comuna, datos_callejeros.cut, latitud_geo_panda, longitud_geo_panda
            )

    except Exception as e:
        comuna = {"Error": e}
    if request.show == "coords":
        resumen["geopanda"] = comuna
        return resumen

    return {"coords": resumen, "geopanda": comuna, "traza": direccion_procesada}
