
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from typing import Union
from typing import Dict, Any

from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ServelDireccionPersona(BaseModel):
    id: Optional[int] = None
    score: Optional[float] = None
    comuna: Optional[str] = ""
    provincia: Optional[str] = ""
    region: Optional[str] = ""
    cut_reg: Optional[str] = ""
    cut_com: Optional[str] = ""
    tipo_via: Optional[str] = ""
    nombre_via: Optional[str] = ""
    numero: Optional[str] = ""
    resto: Optional[str] = ""
    referencia: Optional[str] = ""
    localidad: Optional[str] = ""
    cut_region: Optional[str] = ""
    cut_provincia: Optional[str] = ""
    cut_comuna: Optional[str] = ""
    tipo_geo_id: Optional[int] = None
    revisado_id: Optional[int] = None
    obs_analista: Optional[str] = ""
    geo_id: Optional[int] = None
    tipo_padron_id: Optional[int] = None
    orden_edicion_id: Optional[int] = None
    prioridad_id: Optional[int] = None
    control_id: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    geom: Optional[str] = ""
    created_by: Optional[str] = ""
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = ""
    updated_at: Optional[datetime] = None
    deleted_by: Optional[str] = ""
    deleted_at: Optional[datetime] = None


class APTLocalidades(BaseModel):
    id_localid: Optional[int] = None
    cod_comuna: Optional[Union[str, int]] = ""
    comuna: Optional[Union[str, int]] = ""
    cod_r: Optional[str] = ""
    region: Optional[str] = ""
    nombre_localidad: Optional[str] = ""
    longitud: Optional[Union[str, float]] = None
    latitud: Optional[Union[str, float]] = None
    tipo: Optional[str] = ""
    estado: Optional[str] = ""
    circuns: Optional[str] = ""
    codigo_cir: Optional[str] = ""
    glosacircu: Optional[str] = ""
    principal: Optional[str] = ""
    revisado: Optional[str] = ""
    created_user: Optional[str] = None
    created_date: Optional[str] = None
    last_edited_user: Optional[str] = None
    last_edited_date: Optional[str] = None
    globalid: Optional[str] = ""



class APTDireccion(BaseModel):
    cod_direccion: Optional[str] = ""
    nombre_direcc: Optional[str] = ""
    numero: Optional[str] = "" 
    coordenada_x: str = ""
    coordenada_y: str = ""
    fecha_ingreso: Optional[str] = ""
    fecha_actualizacion: Optional[str] = ""
    fecha_georeferencia: Optional[str] = ""
    fecha_novigencia: Optional[str] = ""
    cod_vigencia: Optional[int] = None
    flag_normalizado: Optional[str] = ""
    cod_comuna_ine: Optional[int] = None
    cod_com_txt: Optional[str] = ""
    cod_calle: Optional[int] = None
    letnum: Optional[str] = ""
    sitio: Optional[str] = ""
    depto: Optional[str] = ""
    casa: Optional[str] = ""
    block: Optional[str] = ""
    cod_calle_old: Optional[str] = ""
    cod_via: Optional[str] = ""
    fuente: Optional[str] = ""
    cod_localidad: Optional[str] = ""
    cod_entidad: Optional[str] = ""
    cod_cpoblado: Optional[str] = ""
    referencia: Optional[str] = ""
    cod_uvecinal: Optional[str] = ""
    cod_ah: Optional[str] = ""
    localidad_rsh: Optional[str] = ""


class ServelLocalidades(BaseModel):
    score: float = 0.0
    localidad_nombre: str = ""
    localidad_comuna: Optional[str] = None
    localidad_region: Optional[int] = None
    id: int = 0
    geom: Optional[str] = None
    objectid: Optional[int] = None
    id_localid: Optional[int] = None
    cod_comuna: Optional[int] = None
    comuna_nombre: Optional[str] = None
    region_nombre: Optional[str] = None
    glosa_re: Optional[str] = None
    longitud: Optional[float] = None
    latitud: Optional[float] = None
    tipo: Optional[str] = None
    estado: Optional[str] = None
    circuns: Optional[str] = None
    codigo_cir: Optional[int] = None
    glosacircu: Optional[str] = None
    principal: Optional[str] = None
    revisado: Optional[str] = None
    created_user: Optional[str] = None
    last_edited_user: Optional[str] = None
    globalid: Optional[str] = None

# Clase que representa los datos callejeros
class DatosCallejeros(BaseModel):
    jerarquia: Optional[str] = ""
    cut: Optional[str] = ""
    cut_r: Optional[str] = ""
    cen_lat: Optional[str] = ""
    cen_lon: Optional[str] = ""

# Clase que representa la información geográfica de la dirección
class InfoGeoDireccion(BaseModel):
    origen: Optional[str] = ""
    apt_score: Optional[int]=0
    nombre_via: Optional[str] = ""
    numero: Optional[str] = ""
    provincia: Optional[str] = ""
    comuna: Optional[str] = ""
    region: Optional[str] = ""
    direccion_formateada: Optional[str] = ""
    jerarquia: Optional[str] = ""
    datos_callejeros: Optional[DatosCallejeros] = None
    apt: Optional[APTDireccion] = None
    apt_localidades: Optional[APTLocalidades] = None
    servel_direccion_persona :Optional[ServelDireccionPersona] =None
    servel_localidades : Optional[ServelLocalidades] =None
    google_maps : Optional[Dict[str, Any]] = None
    nominatim : Optional[Dict[str, Any]] = None
    
class InfoData(BaseModel):
    esquema: str = ""
    referencia: str = ""
    latitud: str = ""
    longitud: str = ""
    resto: str = ""
    codigo_postal: str = ""


class RequestGetGeo(BaseModel):
    nombre_via: str
    numero: str
    comuna: str
    region: str
    provincia: str = ""  
    info: InfoData = InfoData()
    show:str="coords"
