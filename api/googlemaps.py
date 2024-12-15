import os
import requests
from typing import Dict, Any

class GoogleMapsService:
    def __init__(self):
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.api_key = os.getenv("GOOGLE_API_KEY", "")

    def obtener_geolocalizacion(self, address: str) -> Dict[str, Any]:
        """
        Consulta la API de Google Maps para obtener las coordenadas geográficas de una dirección,
        filtrando resultados por location_type (ROOFTOP o RANGE_INTERPOLATED).

        :param address: Dirección a geolocalizar.
        :return: Respuesta procesada con los datos de latitud y longitud, o un mensaje de error.
        """
        try:
            params = {
                "address": address,
                "key": self.api_key
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Lanza una excepción si el estado HTTP indica error

            data = response.json()

            if data.get("status") == "OK":
                # Filtrar resultados por location_type  
                valid_results = [
                    result for result in data["results"]
                    if result["geometry"].get("location_type") in ["ROOFTOP", "RANGE_INTERPOLATED"]
                ]

                if valid_results:
                    # Retornar el primer resultado válido filtrado
                    result = valid_results[0]
                    return result
                else:
                    return {"error": "No se encontraron resultados con location_type válido (ROOFTOP o RANGE_INTERPOLATED)."}

            else:
                return {"error": f"No se pudo obtener la geolocalización: {data.get('status')}"}

        except requests.RequestException as e:
            print({"error": f"Error de conexión: {str(e)}"})
            return None
