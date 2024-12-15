import json

# Variable global para almacenar la configuración
_config = None

def cargar_configuracion(archivo_config="./mapeador/config/config.json"):
    """Carga la configuración desde un archivo JSON, solo si no se ha cargado antes."""
    global _config
    if _config is None:
        with open(archivo_config, "r", encoding="utf-8") as f:
            _config = json.load(f)
    return _config

def obtener_ruta_maestro_calles():
    """Obtiene la ruta del archivo MAESTROCALLES desde la configuración"""
    config = cargar_configuracion()
    return config.get("MAESTROCALLES", "")

def obtener_ruta_apt_chile():
    """Obtiene la ruta del archivo APT desde la configuración"""
    config = cargar_configuracion()
    return config.get("APT", "")

def obtener_ruta_apt_localidades():
    """Obtiene la ruta del archivo APT desde la configuración"""
    config = cargar_configuracion()
    return config.get("LOCALIDADES", "")

def obtener_config():
    """Devuelve la configuración cargada"""
    return cargar_configuracion()
