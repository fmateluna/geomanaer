# GeoCoords

**GeoCoords** es un sistema avanzado para la geocodificación de direcciones, diseñado específicamente para el contexto geográfico de Chile. Combina múltiples fuentes de datos y tecnologías para proporcionar resultados precisos, priorizando la validación y la limpieza de las direcciones ingresadas.

## Descripción General

GeoCoords permite procesar y validar direcciones utilizando geocodificadores como Servel, Google Maps, Nominatim, y Street Map Premium de Esri. Además, incorpora validaciones espaciales con geometrías y utiliza un maestro de calles nacional para estandarizar los nombres y mejorar la precisión.

El proyecto está optimizado para manejar grandes volúmenes de datos con rapidez y confiabilidad, empleando DuckDB para la gestión eficiente de las consultas.

---

## Características Principales

### 1. **Fuentes de Geocodificación**
- **Servel:** Geocodificador principal con diversas capas (Dirección Persona, APT Servel, IDE Chile).
- **Google Maps:** Ofrece coordenadas rooftop e interpoladas.
- **Nominatim:** Resultados filtrados para direcciones de tipo "building".
- **Street Map Premium de Esri:** Geocoder adicional en evaluación.
- **APT Chile:** Geocoder basado en un archivo CSV con coordenadas rooftop predefinidas.

### 2. **Validaciones Geográficas**
- Utiliza **GeoPandas** para verificar que las coordenadas generadas pertenezcan a áreas geográficas específicas (comuna, región, país).

### 3. **Limpieza y Normalización de Direcciones**
- Emplea el **Maestro de Calles del INE 2024** como referencia principal para estandarizar nombres.
- Implementa reglas para corregir abreviaturas comunes y términos alternativos (e.g., STA → SANTA, PROF → PROFESOR).

### 4. **Eficiencia en Procesamiento**
- Archivos CSV preprocesados y convertidos a formato **DuckDB** para mejorar el rendimiento.
- Soporte para grandes volúmenes de datos con consultas rápidas y estructuradas.

### 5. **Procesamiento Prioritario**
- Orden lógico en el uso de geocodificadores: comienza con Servel y recurre a otras fuentes solo cuando sea necesario.

---

## Requisitos Técnicos

### Dependencias
- Python 3.10+
- DuckDB
- GeoPandas
- SQLAlchemy
- Google Maps API Key

### Archivos de Entrada
Los siguientes archivos deben estar disponibles en el directorio `data/`:
- `LOCALIDADES_UR_RU.csv`: Listado de localidades rurales y urbanas.
- `MAESTROCALLES_CHILE_INE2024.csv`: Base de datos de calles organizada por comuna.
- `APT_CHILE.csv`: Geocoder predefinido con coordenadas rooftop.

---
ejecutar 

###En modo desarrollador
python -m venv venv
pip freeze > requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000


