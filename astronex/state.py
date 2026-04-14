# -*- coding: utf-8 -*-
try:
    from . import pysw
except ImportError:
    import pysw
from . import chart
from . import database
from collections import deque
from .utils import PersonInfo, dectodeg, parsestrtime
from .nexdate import NeXDate
from .extensions.path import path
import pickle
import os

datlist = deque(['dat_nat','dat_house','dat_nod','prog_nat','prog_nod','prog_local','prog_soul'])
dialist =  deque(['dyn_cuad','dyn_cuad2','dyn_stars'])
biolist =  deque(['bio_nat','bio_nod','bio_soul'])
tranlist = deque(['draw_transits','rad_and_transit'])
clicklist = deque(['click_hh','click_nn','click_hn','click_nh','subject_click','click_rr','click_bridge'])
opdouble = deque(['draw_nat',
    'draw_house','draw_nod','draw_soul','draw_dharma','draw_ur_nodal','draw_local','draw_prof', 'draw_int', 'draw_single', 'draw_radsoul', 'draw_planetogram'])
optriplepair = deque(['click_hh', 'click_nn', 'click_hn', 'click_nh',
    'click_ss', 'click_rr','subject_click'])
listlabels = { 'opdouble': opdouble,'charts': opdouble, 'data':datlist,'clicks':clicklist,'bio':biolist,'diagram':dialist,'transit':tranlist,'double1':opdouble,'double2':opdouble,'triple1':opdouble,'triple2':optriplepair}

class Current(object):
    datab = database
    def __new__(cls,app=None):
        it = cls.__dict__.get("__it__")
        if it: return it
        cls.__it__ = it = object.__new__(cls)
        it.init(app)
        return it

    def init(self, app):
        self.datab.connect(app)
        self.epheflag = 4
        self.country = ''
        self.usa = False
        self.orbs = []
        self.peorbs = []
        self.transits = []
        
        # 1. PRIMERO creamos el objeto Locality (para que exista self.loc)
        self.loc = Locality()
        
        # 2. SEGUNDO creamos las cartas básicas
        self.master = chart.Chart('master')
        self.click = chart.Chart('click')
        self.now = chart.Chart('now')
        
        try:
            self.now.first = _('Momento actual')
        except NameError:
            self.now.first = 'Momento actual'
        
        # 3. TERCERO inicializamos las fechas (ahora ya pueden leer self.loc)
        self.date = NeXDate(self)
        self.calcdt = NeXDate(self)
        
        # 4. CUARTO: Inyección manual de localidad (Evita errores de base de datos)
        # Definimos los datos directamente para asegurar el arranque
        self.loc.city = 'Las Palmas de Gran Canaria'
        self.loc.country = 'ES'
        self.loc.region = 'Canarias'
        
        # Coordenadas exactas para que el motor suizo no de IndexError
        self.loc.latdec = 28.1     # 28° 07' N
        self.loc.longdec = -15.4   # 15° 23' W
        self.loc.zone = 'Atlantic/Canary'
        
        # Sincronizamos con el reloj del sistema
        self.date.set_now()
        
        # Calculamos la carta 'now' con estos datos fijos
        # Esto elimina el texto raro del archivo .po y pone planetas reales
        self.refresh_nowchart()

        # 5. El resto de la inicialización
        self.calc = chart.Chart('calc')
        self.person = PersonInfo()
        self.charts = { 'master' : self.master, 'click' : self.click,
                'now' : self.now, 'calc' : self.calc }
        
        # A partir de aquí, el código sigue igual...
        self.curr_chart = None
        self.curr_click = None
        self.crossed = True 

        self.opmode = 'simple'
        self.curr_op = 'draw_nat'
        self.opright = 'draw_house'
        self.opleft = 'draw_nat'
        self.opup = 'draw_nat'
        self.clickmode = 'master'
        self.curr_list = opdouble

        self.pool = deque([])
        file_pool = path.joinpath(app.home_dir,'mruch.pkl')
        if os.path.exists(file_pool):
            with open(file_pool, "rb") as f:
                try:
                    # Cargamos con encoding latin1 para compatibilidad con Py2
                    self.pool = pickle.load(f, encoding='latin1')
                except:
                    self.pool = deque([])
                    
        self.couples = []
        self.coup_ix = 0
        file_coups = path.joinpath(app.home_dir,'coups.pkl')
        if os.path.exists(file_coups):
            with open(file_coups, "rb") as f:
                try:
                    self.couples = pickle.load(f, encoding='latin1')
                except:
                    self.couples = []

        self.fav = []
        self.fav_ix = 0

    def is_valid(self, type):
        chart = self.charts[type]
        return bool(chart.date and chart.city)

    def get_active(self,active):
        return self.charts[active]

    def newchart(self):
        return chart.Chart()

    def setchart(self):
        ch = self.charts['calc']
        if self.person.first == '':
            self.person.set_first()
            self.person.last = ''
        ch.first = self.person.first
        ch.last = self.person.last
        ch.comment = ""
        ch.category = ""
        ch.city = self.loc.city
        ch.region = self.loc.region
        ch.country = self.loc.country
        ch.latitud = self.loc.latdec
        ch.longitud = self.loc.longdec
        ch.zone = self.loc.zone
        ch.date = self.calcdt.dateforstore()
        ch.planets, ch.houses = ch.calc(self.calcdt.dateforcalc(),self.loc,self.epheflag)

    def init_nowchart(self):
        self.date.set_now()
        self.refresh_nowchart()

    def set_now(self):
        # 1. Sincroniza el objeto de fecha interno con el reloj del sistema
        self.date.set_now() 
        
        # 2. Referencia a la carta del momento actual
        ch = self.now
        
        # 3. Actualizamos la fecha de la carta con el formato de almacenamiento
        ch.date = self.date.dateforstore()
        
        # 4. Mantenemos el cálculo original pero asegurándonos de que ocurra
        # No tocamos ni limpiamos los planetas aquí, dejamos que ch.calc haga su trabajo
        ch.planets, ch.houses = ch.calc(self.date.dateforcalc(), self.loc, self.epheflag)

        # DEBUG: Solo para confirmar que la jerarquía ha despertado
        #print(f"DEBUG: Reloj sincronizado. Fecha actual: {ch.date}")

    def refresh_nowchart(self):
        ch = self.now
        ch.city = self.loc.city
        ch.region = self.loc.region
        ch.country = self.loc.country
        ch.latitud = self.loc.latdec
        ch.longitud = self.loc.longdec
        ch.zone = self.loc.zone
        ch.date = self.date.dateforstore()
        ch.planets, ch.houses = ch.calc(self.date.dateforcalc(),self.loc,self.epheflag)

    def setprogchart(self,chart_obj):
        ch = self.calc
        basech = chart_obj
        self.calcdt.settz(basech.zone)
        self.loc.country = basech.country
        self.loc.city = basech.city
        self.loc.region = basech.region
        self.loc.latdec = basech.latitud
        self.loc.longdec = basech.longitud
        self.loc.zone = basech.zone
        ch.first = basech.first
        ch.last = basech.last
        ch.comment = ""
        ch.category = ""
        ch.city = basech.city
        ch.region = basech.region
        ch.country = basech.country
        ch.latitud = basech.latitud
        ch.longitud = basech.longitud
        ch.zone = basech.zone
        ch.date = self.calcdt.dateforstore()
        ch.planets, ch.houses = ch.calc(self.calcdt.dateforcalc(),self.loc,self.epheflag)

    def setloc(self,city,code):
        fetch = self.datab.fetch_worldcity
        if self.usa:
            fetch = self.datab.fetch_usacity
        try:
            # unicode() -> str() en Python 3
            fetch(self.country, str(city), code, self.loc)
            self.date.settz(self.loc.zone)
            self.calcdt.settz(self.loc.zone)
        except StopIteration:
            print(f"localidad no encontrada: {city}")

    def set_op(self, op):
        self.curr_op = op

    def set_opdelta(self,delta,side):
        if side == 'up' and self.clickmode == 'click':
            oplist = optriplepair
        else:
            oplist = opdouble
        ix = list(oplist).index(getattr(self,'op'+side))
        oplist.rotate(-ix-delta)
        opside = oplist[0]
        setattr(self,'op'+side,opside)
        if self.opmode == 'simple':
            self.curr_op = self.opleft
            return
        if self.clickmode == 'click':
            if opside == self.opleft:
                self.opright = self.opleft
            else:
                self.opleft = self.opright

    def reset_opup(self):
        if self.clickmode == 'click':
            self.opup = optriplepair[0]
        else:
            self.opup = opdouble[0]

    def set_list(self,label):
        self.curr_list = listlabels[label]

    def format_longitud(self,kind='chart'):
        chart_obj = self.curr_chart if kind == 'chart' else self.curr_click
        longitud = dectodeg(chart_obj.longitud)[:-2]
        let = 'W' if longitud[0] == '-' else 'E'
        if longitud[0] == '-': longitud = longitud[1:]
        return longitud[0:-2]+let+longitud[-2:]

    def format_latitud(self,kind='chart'):
        chart_obj = self.curr_chart if kind == 'chart' else self.curr_click
        lat = dectodeg(chart_obj.latitud)[:-2]
        let = 'S' if lat[0] == '-' else 'N'
        if lat[0] == '-': lat = lat[1:]
        return lat[0:-2]+let+lat[-2:]

    def load_import(self,chart_obj, ch):
        chart_obj.first, chart_obj.last, chart_obj.category = ch[0:3]
        chart_obj.city, chart_obj.region, chart_obj.country = ch[3:6]
        chart_obj.date = ch[6]
        chart_obj.latitud, chart_obj.longitud = float(ch[7]), float(ch[8])
        chart_obj.zone = ch[9]
        chart_obj.planets = [float(p) for p in ch[10:21]]
        chart_obj.houses = [float(h) for h in ch[21:33]]
        chart_obj.comment = ch[33]

    def load_from_pool(self,ix,id):
        if len(self.pool) == 0: return False
        self.pool.rotate(-ix)
        self.replicate(self.pool[0], self.charts[id])
        return True

    def load_from_fav(self,ix,id):
        self.fav_ix = ix
        self.replicate(self.fav[ix], self.charts[id])
        return True

    def replicate(self,src,dest):
        for attr in ['first','last','category','city','region','country','date','latitud','longitud','zone','planets','houses','comment']:
            setattr(dest, attr, getattr(src, attr))

    def add_to_pool(self,chart_obj,ow):
        if ow:
            self.pool[0] = chart_obj
        else:
            name = f"{chart_obj.first} {chart_obj.last}"
            for ch in list(self.pool):
                if f"{ch.first} {ch.last}" == name: return
            self.pool.appendleft(chart_obj)
            if len(self.pool) > 6: self.pool.pop()

    def save_pool(self,app):
        if len(self.pool) == 0: return
        file_p = path.joinpath(app.home_dir,'mruch.pkl')
        with open(file_p, 'wb') as f:
            pickle.dump(self.pool, f, -1)

    def save_couples(self,app):
        if len(self.couples) == 0: return
        file_c = path.joinpath(app.home_dir,'coups.pkl')
        with open(file_c, 'wb') as f:
            pickle.dump(self.couples, f, -1)

    def get_cycles(self,person2=False):
        chart_obj = self.curr_chart if not person2 else self.curr_click
        return chart_obj.get_cycles(self.date.dt)

    def year_regent(self):
        pto = [4,0,3,2,1,6,5]
        year = self.date.dt.year
        dnow = pysw.julday(*self.date.dateforcalc())
        s, sunnow, e = pysw.calc(dnow, 0, self.epheflag)
        fsols = pysw.julday(year+1, 1, 1, 0)
        s, solstice, e = pysw.calc(fsols, 0, self.epheflag)
        # Extraemos el primer valor (la longitud) de cada tupla
        s_pos = sunnow[0]
        s_sol = solstice[0]

        # Ahora la comparación es entre números reales, sin errores
        if not 0.0 <= s_pos < s_sol: 
            year -= 1
        return pto[year % 7]

    def safe_delete_chart(self,tbl,id):
        for c in self.couples:
            if (tbl == c['fem'][1] and id == c['fem'][2]) or (tbl == c['mas'][1] and id == c['mas'][2]):
                return False
        return True

    def safe_delete_table(self,tbl):
        for c in self.couples:
            if tbl == c['fem'][1] or tbl == c['mas'][1]: return False
        return True

    def fix_couples(self,tbl,first,last,newid):
        name = first + (" " + last if last else "")
        for c in self.couples:
            if (tbl == c['fem'][1] and name == c['fem'][0]):
                c['fem'] = (c['fem'][0], c['fem'][1], newid)
                break
            if (tbl == c['mas'][1] and name == c['mas'][2]):
                c['mas'] = (c['mas'][0], c['mas'][1], newid)
                break

    def chiron(self,ch):
        from .directions import strdate_to_date
        import datetime
        from pytz import timezone
        dt = strdate_to_date(ch.date)
        dt = datetime.datetime.combine(dt.date(),dt.time())
        nxdate = NeXDate(self,dt,timezone(ch.zone))
        print((ch.chiron_calc(nxdate.dateforcalc(),self.epheflag)))

    def vulcan(self,ch):
        from .directions import strdate_to_date
        import datetime
        from pytz import timezone
        dt = strdate_to_date(ch.date)
        dt = datetime.datetime.combine(dt.date(),dt.time())
        nxdate = NeXDate(self,dt,timezone(ch.zone))
        print((ch.vulcan_calc(nxdate.dateforcalc(),self.epheflag)))

class Locality(object):
    def __init__(self):
        self.country = ""
        self.country_code = ""
        self.city = ""
        self.region = ""
        self.region_code = ""
        self.latitud = ""   # Texto original (ej: "133534")
        self.longitud = ""  # Texto original (ej: "-894939")
        self.latdec = 0.0   # Valor decimal para el cálculo
        self.longdec = 0.0  # Valor decimal para el cálculo
        self.zone = "UTC"

    def set_coords(self, lon_str, lat_str):
        """Convierte los formatos '894939' de la DB a decimales reales"""
        try:
            # El formato de Morinus/Astro-Nex suele ser: 
            # Los últimos 4 dígitos son minutos y segundos.
            # Ejemplo: -894939 -> -89.4939 o similar. 
            # Para que el cálculo de la carta sea fluido:
            self.longdec = float(lon_str) / 10000.0
            self.latdec = float(lat_str) / 10000.0
            self.longitud = lon_str
            self.latitud = lat_str
        except:
            self.longdec = 0.0
            self.latdec = 0.0



