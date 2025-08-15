from math import radians, cos, sin, sqrt, atan2
from datetime import datetime, timedelta, date

# Coordenadas fixas da empresa (exemplo). Substitua pelas coordenadas reais.
EMPRESA_LAT = -8.062780
EMPRESA_LNG = -34.871100

def calcular_distancia_em_metros(lat1, lon1, lat2, lon2):
    R = 6371000  # raio da Terra em metros
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def to_datetime_today(t):
    if not t:
        return None
    return datetime.combine(date.today(), t)

def calcular_banco_horas(entrada, saida_almoco, retorno_almoco, saida_final):
    e = to_datetime_today(entrada)
    s_alm = to_datetime_today(saida_almoco)
    r_alm = to_datetime_today(retorno_almoco)
    s_final = to_datetime_today(saida_final)
    if not all([e, s_alm, r_alm, s_final]):
        return None
    periodo_manha = s_alm - e
    periodo_tarde = s_final - r_alm
    total_trabalhado = periodo_manha + periodo_tarde
    carga = timedelta(hours=8)
    banco = total_trabalhado - carga
    return round(banco.total_seconds() / 3600, 2)
