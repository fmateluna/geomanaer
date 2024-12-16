import requests
from typing import Dict, Any

class NominatimService:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {"User-Agent": "MiApp/1.0 (contacto@miapp.com)"}

    def obtener_geolocalizacion(self, address: str) -> Dict[str, Any]:
        """
        Consulta la API de Nominatim para obtener las coordenadas geográficas de una dirección.

        :param address: Dirección a geolocalizar.
        :return: Respuesta procesada con los datos de latitud y longitud, o un mensaje de error.
        """
        try:
            params = {
                "q": address + ", Chile",
                "format": "json",
                "limit": 1
            }

            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()  # Lanza una excepción si el estado HTTP indica error

            data = response.json()

            if not data:
                #{"error": "No se encontraron resultados para la dirección proporcionada."}
                return None

            result = data[0]
            # Retornar el primer resultado encontrado
            return result

        except requests.RequestException as e:            
            print (f"Error de conexión: {str(e)}")
            return None
        except ValueError as e:
            print (f"Error de conexión: {str(e)}")
            return None
