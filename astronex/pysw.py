# -*- coding: utf-8 -*-
import os
import swisseph as swe

# 'os.path.dirname(__file__)' es la carpeta 'astronex'
# '..' sube un nivel a la raíz donde está 'ext/Ephem'
BASE_DIR = os.path.dirname(__file__)
EPHE_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'ext', 'Ephem'))

if os.path.exists(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)
    print(f"✅ Motor activo. Efemérides cargadas desde: {EPHE_PATH}")
else:
    # Intento de rescate si lo lanzas desde la propia raíz
    if os.path.exists("./ext/Ephem"):
        swe.set_ephe_path(os.path.abspath("./ext/Ephem"))
        print("✅ Motor activo (Ruta relativa local)")
    else:
        print(f"❌ ERROR: No se encuentran las efemérides en {EPHE_PATH}")

# --- FUNCIONES QUE ASTRO-NEX ESPERA ---

def setpath(path):
    if os.path.exists(path):
        swe.set_ephe_path(path)

def julday(year, month, day, hour=0.0):
    # Aseguramos que la hora sea float
    return swe.julday(year, month, day, float(hour))

def calc(jd, planet_no, flag):
    # Astro-Nex espera: (status, [6 posiciones], error)
    try:
        res = swe.calc_ut(jd, planet_no, flag)
        # res es (posiciones, flag)
        return 0, res[0], None
    except Exception as e:
        return -1, [0.0]*6, str(e)

def revjul(jd):
    return swe.revjul(jd)

def houses_ex(jd, lat, lon, hsys):
    # hsys suele ser 'P'. En Py3 la lib C necesita bytes.
    if isinstance(hsys, str):
        hsys = hsys.encode('ascii')
    elif isinstance(hsys, int):
        hsys = chr(hsys).encode('ascii')
    
    # swe.houses_ex devuelve (cusps, asmc)
    res = swe.houses_ex(jd, lat, lon, hsys)
    return res[0], res[1]

def calc_ut_with_speed(jd, planet_no, flag):
    """
    Función puente que espera Astro-Nex para calcular posiciones y velocidad (retrogradación).
    Retorna: (status, longitud, velocidad, error_msg)
    """
    try:
        # Forzamos el flag de velocidad para saber si es retrógrado
        import swisseph as swe
        flag |= swe.FLG_SPEED
        
        # swe.calc_ut devuelve ((lon, lat, dist, lon_vel, lat_vel, dist_vel), ret_flag)
        res, ret_flag = swe.calc_ut(jd, planet_no, flag)
        
        # Astro-Nex espera: 0 (ok), longitud (res[0]), velocidad (res[3]), None (sin error)
        return 0, res[0], res[3], None
    except Exception as e:
        return -1, 0.0, 0.0, str(e)

def local_houses(jd, lon, lat, flag):
    """
    Calcula las casas locales (generalmente sistema Placidus 'P').
    Astro-Nex espera recibir las cúspides de las casas.
    """
    try:
        import swisseph as swe
        # Astro-Nex suele usar Placidus por defecto ('P')
        # swe.houses_ex devuelve (cusps, asmc)
        cusps, asmc = swe.houses_ex(jd, lat, lon, b'P')
        return cusps
    except Exception as e:
        print(f"Error en local_houses: {e}")
        # Devolvemos una lista de 13 ceros (índice 0 no se usa, 1-12 son las casas)
        return [0.0] * 13


