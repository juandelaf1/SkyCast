import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def parse_aemet_coordinate(coord_str: str | None) -> float | None:
    """
    Convierte coordenadas de AEMET en formato DDMMSS + direccion a grados decimales.

    Formato AEMET:
        - Latitud:  DDMMSS + N/S  (ej. "394924N"  -> 39.8233)
        - Longitud: DDMMSS + E/W  (ej. "025309E"  ->  2.8858)

    Retorna None si el formato no es valido.
    """
    if not coord_str or len(coord_str) < 7:
        return None

    direccion = coord_str[-1].upper()
    numerico = coord_str[:-1]

    try:
        grados = int(numerico[0:2])
        minutos = int(numerico[2:4])
        segundos = int(numerico[4:6])
    except (ValueError, IndexError):
        return None

    decimal = grados + minutos / 60.0 + segundos / 3600.0

    if direccion in ("S", "W"):
        decimal = -decimal

    return round(decimal, 6)
