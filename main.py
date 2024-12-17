import os
import json
from pathlib import Path
from api.manager import retorna_geolocalizacion
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from api.payloads import RequestGetGeo

# Crear el router
router = APIRouter()

# Usar pathlib para obtener una ruta relativa
FRONTEND_PATH = Path(__file__).resolve().parent / "../front"

# Modelo para la respuesta de error
class ErrorResponse(BaseModel):
    detail: str
    code: int = 500

# Endpoint para recibir y procesar la geolocalización de una dirección
@router.post("/getgeo/")
async def get_geo_endpoint(request: RequestGetGeo):
    try:
        # Extraer los datos recibidos como un diccionario
        data = request.dict()

        # Validación: asegurarse de que los atributos principales estén presentes
        required_fields = ["nombre_via", "comuna", "region"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "message": "Petición recibida con advertencias",
                "warnings": f"Faltan los siguientes campos requeridos: {', '.join(missing_fields)}",
                "data": data,
            }

        # Llamar a retornaGeolocalizacion con los datos del diccionario
        return retorna_geolocalizacion(request)        

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al procesar la solicitud: {str(e)}"
        )


# Configurar la aplicación principal
app = FastAPI()
app.include_router(router)

# Iniciar el servidor si se ejecuta como un script
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
