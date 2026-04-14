# -*- coding: utf-8 -*-
import math
from datetime import datetime, timedelta, date, time
from pytz import timezone
RAD = math.pi / 180

class PersonInfo(object):
    count = 1
    def __init__(self):
        self.first = _("sin_nombre%d") % self.count
        self.last = ""

    def set_first(self,noname=False):
        if noname:
            self.first = ''
        else:
            self.first = _("sin_nombre%d") % self.count
            PersonInfo.count += 1


def degtodec(d):
    sign = 1
    if d.startswith('-'):
        sign = -sign
        d = d[1:]
    sec, rest = d[-2:], d[:-2]
    mint, deg = rest[-2:], rest[:-2]
    mint = int(mint) + int(sec)/60.0
    if not deg: deg = '0'
    deg = int(deg) + mint/60
    deg *= sign
    return deg

def dectodeg(d):
    # Si d es None, el programa no encontró la lat/long preestablecida.
    # Le damos 0.0 para que pueda seguir arrancando.
    if d is None:
        print("DEBUG: Se ha recibido una coordenada None. Revisar configuración de localidad.")
        d = 0.0
    
    if d < 0: 
        sign = '-'
    else:
        sign = '+' # O vacío, según el código original
    import math
    sign = ''
    if d < 0 :  sign = '-'
    absd = abs(d)
    deg = int(math.floor(absd))
    rest = (absd - deg) * 60
    mint = int(math.floor(rest))
    sec = int(math.floor((rest - mint) * 60))
    return (sign+str(deg)+str(mint).zfill(2)+str(sec).zfill(2))

def parsestrtime(strdate):
    # 1. Validación inicial: Si no hay datos o es muy corta, devolvemos valores seguros
    if not strdate or 'T' not in strdate:
        return "01/01/2000", "00:00 +00"

    date, _, time_part = strdate.partition('T')
    
    # Invertir fecha (de YYYY-MM-DD a DD/MM/YYYY)
    date_parts = date.split('-')
    date = "/".join(reversed(date_parts)) 
    
    # Extraer zona y hora base
    # Usamos rebanado seguro para evitar errores si la cadena es corta
    zone = time_part[8:] if len(time_part) > 8 else ""
    time = time_part[:5] if len(time_part) >= 5 else "00:00"
    
    delta = "+00" # Valor por defecto por si falla el procesamiento de zona
    
    try:
        if zone:
            if ':' in zone:
                delta, zone = zone[:6], zone[6:]
            else:
                # El bloque que fallaba: solo operamos si delta tiene longitud suficiente
                temp_delta = zone[:5]
                if len(temp_delta) >= 5:
                    d1, d2 = temp_delta[1:3], temp_delta[3:5]
                    # Solo intentamos sumar si son dígitos numéricos
                    if d1.isdigit() and d2.isdigit():
                        delta = temp_delta[0] + str(int(d1) + int(d2)).rjust(2, '0')
                    else:
                        delta = temp_delta[:3]
                zone = zone[5:]
    except (ValueError, IndexError):
        # Si algo sale mal internamente, delta se queda como "+00"
        pass

    time += ' ' + delta + zone
    return (date, time)

        

def format_longitud(long):
    if long is None: long = 0.0  # Valor por defecto
    longitud = dectodeg(long)[:-2]
    
    if longitud.startswith('-'):
        let = 'W'
        longitud = longitud[1:]
    else:
        let = 'E'
    
    # Aseguramos que tenga al menos 3 caracteres para que el rebanado [-2:] no falle
    longitud = longitud.zfill(3) 
    return longitud[0:-2] + let + longitud[-2:]

def format_latitud(lat):
    if lat is None: lat = 0.0   # Valor por defecto
    latitud = dectodeg(lat)[:-2]
    
    # Determinamos el hemisferio
    if latitud.startswith('-'):
        let = 'S'
        latitud = latitud[1:]
    else:
        let = 'N'
    
    # Rellenamos con ceros a la izquierda para que siempre tenga 
    # al menos 3 dígitos (ej: '5' pasa a '005') antes de separar grados/minutos
    latitud = latitud.zfill(3)
    
    # Retornamos Grados + Letra (N/S) + Minutos
    return latitud[0:-2] + let + latitud[-2:]

def points_from_angle(angles):
    points = []
    for a in angles:
        points.append((math.cos(a*RAD),math.sin(a*RAD)))
    return points

def strdate_to_date(strdate):
    date,_,time = strdate.partition('T')
    try:
        y,mo,d = [ int(x) for x in date.split('-')]
    except ValueError:
        print(date)
    zone, time  = time[8:], time[:5]
    try:
        zone.index(':')
        delta, zone = zone[:6], zone[6:]
        d1, d2 = delta[1:3], delta[4:6]
        tot = int(d1)+int(d2)/60.0
    except ValueError:
        delta, zone = zone[:5], zone[5:]
        d1, d2 = delta[1:3], delta[3:5]
        tot = int(d1)+int(d2)
    sign = {'+': 1, '-': -1}[delta[0]]
    delta = tot*sign
    h,m = [int(x) for x in time.split(':')]
    #h = (h + m/60.0) - delta
    #m = int((h - int(h))*60)
    dt = datetime(y,mo,d,int(h),m,0,tzinfo=timezone('UTC'))
    dt = datetime.combine(dt.date(),dt.time())
    return dt
