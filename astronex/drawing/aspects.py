# -*- coding: utf-8 -*-
from operator import attrgetter 
import math
from math import pi as PI
RAD = PI /180

ten_colors = [
        (1.0, 0.5, 0.0), (0.9, 0.7, 0.0), (0.6, 0.0, 0.9), 
        (0.9, 0.7, 0.0), 
        (0.6, 0.0, 0.9), 
        (0.9, 0.0, 0.0), (0.6, 0.0, 0.9), 
        (0.9, 0.7, 0.0), 
        (0.6, 0.0, 0.9), 
        (0.9, 0.7, 0.0) ]

class ConjunctioAspect(object):
    def draw(self,cr,r,aspects,filter,extend=None):
        if extend:
            ex = extend
            fdivfac = 20
        else:
            ex = 1.105
            fdivfac = 10

            
        cr.save()
        for asp in aspects:
            asp.p1 %= 360.0
            asp.p2 %= 360.0
            x1 = r * math.cos(asp.p1 * RAD)
            y1 = r * math.sin(asp.p1 * RAD)
            x2 = r * math.cos(asp.p2 * RAD)
            y2 = r * math.sin(asp.p2 * RAD) 
            f1 = ex*0.99 if asp.f1 > 1 else 1 + asp.f1/fdivfac
            f2 = ex*0.99 if asp.f2 > 1 else 1 + asp.f2/fdivfac
            dis = abs(asp.p1 - asp.p2)
            dis = min(dis, 360-dis)
            if dis == 0.0 or filter: # zero div when same chart
                da = 3.0
            else:
                da = (((dis/asp.f1 + dis/asp.f2) / 2) - dis) / 2 
            if da < 0: da = -da
            a1 = min(asp.p1,asp.p2) - da
            a2 = max(asp.p1,asp.p2) + da
            if a1 < 0: a1 += 360.0
            if a2 < 0: a2 += 360.0
            a1 %= 360.0
            a2 %= 360.0 
            if min(asp.p1,asp.p2) != asp.p1:
                a1,a2 = a2,a1

            ebx1 = r * ex * math.cos(a1 * RAD)
            eby1 = r * ex * math.sin(a1 * RAD)
            ebx2 = r * ex * math.cos(a2 * RAD)
            eby2 = r * ex * math.sin(a2 * RAD) 
            
            cr.set_source_rgb(1,0.3,0) 
            cr.move_to(x1*f1,y1*f1)
            cr.line_to(ebx1,eby1)
            if (a1 < a2 and a2 - a1 < 180.0) or (a1 - a2) > 180.0:
                #print "arc",a1,a2,asp.p1,asp.p2
                cr.arc(0,0,r*ex,a1*RAD,a2*RAD)
            else:
                #print "neg",a1,a2,asp.p1,asp.p2
                cr.arc_negative(0,0,r*ex,a1*RAD,a2*RAD)
            cr.line_to(x2*f2,y2*f2)
            cr.close_path()
            cr.fill()

            cr.set_source_rgb(*asp.col)
            cr.move_to(x1*f1,y1*f1)
            cr.line_to(x1*ex,y1*ex)
            cr.line_to(x2*ex,y2*ex)
            cr.line_to(x2*f2,y2*f2)
            cr.close_path()
            cr.fill()
        cr.restore()

class UnilateralAspect(object):
    def __init__(self,baseline):
        self.lw = baseline
    
    def draw(self,cr,r,aspects):
        cr.save()
        cr.set_line_width(0.6*float(self.lw))
        for asp in aspects:
            x1 = r * math.cos(asp.p1 * RAD)
            y1 = r * math.sin(asp.p1 * RAD)
            x2 = r * math.cos(asp.p2 * RAD)
            y2 = r * math.sin(asp.p2 * RAD) 
            if asp.f1 < asp.f2:
                x2,x1 = x1,x2
                y2,y1 = y1,y2
            xx = (x2 + x1)/2; yy = (y2 + y1)/2
            cr.set_source_rgb(*asp.col)
            #cr.set_dash([12,6,24,6,36,6,48,6,60,6],0)
            cr.set_dash([4,3,12,4,18,5,24,6,30,6,36,6,48,6,60,6],0)
            #cr.set_dash([6,6,60,6,48,6,36,6,30,6,24,6,18,6,12,6,6,0],0)
            cr.move_to(x1,y1)
            cr.line_to(xx,yy)
            cr.stroke()
            cr.set_dash([1,0],0)
            cr.set_source_rgb(*asp.col)
            cr.move_to(xx,yy)
            cr.line_to(x2,y2) 
            cr.stroke()
        cr.restore()
    
class GoodwillAspect(object):
    def __init__(self,baseline):
        self.lw = baseline

    def draw(self,cr,r,aspects):
        cr.save()
        cr.set_dash([12,6],2)
        cr.set_line_width(0.7*float(self.lw))
        for asp in aspects:
            x1 = r * math.cos(asp.p1 * RAD)
            y1 = r * math.sin(asp.p1 * RAD)
            x2 = r * math.cos(asp.p2 * RAD)
            y2 = r * math.sin(asp.p2 * RAD) 
            cr.set_source_rgb(*asp.col)
            cr.move_to(x1,y1) 
            cr.line_to(x2,y2) 
            cr.stroke()
        cr.restore()
    
class AgePointAspect(object):
    def draw(self,cr,r,aspects,pe):
        cr.save()
        cr.set_dash([3,3],2)
        for asp in aspects:
            x1 = r * math.cos(asp.p1 * RAD)
            y1 = r * math.sin(asp.p1 * RAD)
            x2 = r * math.cos(pe * RAD)
            y2 = r * math.sin(pe * RAD) 
            awidth = 1.2 -asp.f
            if awidth < 0.3: awidth = 0.3
            cr.set_line_width(awidth) 
            cr.set_source_rgb(*asp.col)
            cr.move_to(x1,y1) 
            cr.line_to(x2,y2) 
            cr.stroke()
        cr.restore()

class FususAspect(object):
    '''Normal aspect (fusus form)'''
    def draw(self,cr,r,aspects):
        cr.save()
        scl = r * 0.00065
        for asp in aspects:
            f = 3*((5-5*asp.f1)+(5-5*asp.f2)) * scl #/10 
            x1 = r * math.cos(asp.p1 * RAD)
            y1 = r * math.sin(asp.p1 * RAD)
            x2 = r * math.cos(asp.p2 * RAD)
            y2 = r * math.sin(asp.p2 * RAD) 
            xx = (x2 + x1)/2; yy = (y2 + y1)/2
            cr.set_source_rgb(*asp.col)
            angle = math.atan((y2-y1)/(x2-x1)) / RAD 
            dx = math.cos((90+angle)*RAD)* f
            dy = math.sin((90+angle)*RAD)* f
            cr.move_to(x1,y1)
            cr.curve_to((xx+dx),(yy+dy),(xx+dx),(yy+dy),x2,y2)
            cr.curve_to((xx-dx),(yy-dy),(xx-dx),(yy-dy),x1,y1)
            cr.fill_preserve()
            cr.set_line_width(0.425)
            cr.stroke()
        cr.restore()

class SimpleAspectManager(object):
    # Esta es la tabla de tu imagen (5 columnas: Semisextil, Sextil/Quin, Cuad, Trig, Conj/Opos)
    orbs = [
        [3.0, 5.0, 6.0, 8.0, 9.0], # Fila 0: Sol y Luna
        [2.0, 4.0, 5.0, 6.0, 7.0], # Fila 1: Merc, Ven, Jup
        [1.5, 3.0, 4.0, 5.0, 6.0], # Fila 2: Mar, Sat
        [1.0, 2.0, 3.0, 4.0, 5.0]  # Fila 3: Urano, Nep, Plu, Nodo
    ]

    # Mapeo de planetas a las filas de arriba (según la imagen)
    # Sol=0, Luna=0, Merc=1, Ven=1, Mar=2, Jup=1, Sat=2, Ura=3, Nep=3, Plu=3, Nodo=3
    planclass = [0, 0, 1, 1, 2, 1, 2, 3, 3, 3, 3]

    # Esta lista ya la tienes, pero asegúrate de que sea así:
    # Mapea el aspecto (distancia) a la COLUMNA de la matriz 'orbs'
    aspclass = [4, 0, 1, 2, 3, 1, 4, 1, 3, 2, 1, 0] 
    
    # El resto los dejamos planos o como prefieras
    peorbs = [8, 1, 3, 6, 6, 1, 8, 1, 6, 6, 3, 1]
    trorbs = [1.0] * 12
    ten_orbs = [[3.0,5.0,6.0,8.0,9.0],[2.0,4.0,5.0,6.0,7.0],[1.5,3.0,4.0,5.0,6.0],
                [1.0,2.0,3.0,4.0,5.0],[1.0,2.0,2.0,3.0,4.0]]
    ten_aspclass = [4,0,3,2,1,4,1,2,3,0]

    def filtgw_asp(self,asp):
        aspects = set(asp)
        gw = set(a for a in aspects if a.f1 > 1 and a.f2 > 1)
        aspects.difference_update(gw)
        return list(aspects)
    
    def filtcj_asp(self,asp):
        aspects = set(asp)
        conj = set(a for a in aspects if a.a == 0)
        aspects.difference_update(conj)
        return list(aspects)
    
    def sort_aspects(self,aspects):
        asp = [ (a.p1,a.p2,a) for a in aspects]
        asp.sort()
        return [ a[2] for a in asp ]

    def dictify(self,aspects):
        return [a.__dict__ for a in aspects]

    def strong_chain(self,pl):
        #a = self.filtcj_asp(self.filtgw_asp(self.aspects(pl)))
        a = self.filtcj_asp(self.filtgw_asp(self.asp_fun(pl)))
        #return self.dictify(self.sort_aspects(a))
        return self.sort_aspects(a)

    
 
    def twelve_aspects(self, pl, click=None, filter=None):
        aspects = []
        class asp_obj(object): 
            def __init__(self, **kargs): self.__dict__ = kargs
        
        # 1. Tablas de Orbes
        huber_matrix = [
            [3.0, 5.0, 6.0, 8.0, 9.0], # Clase 0: Sol, Luna
            [2.0, 4.0, 5.0, 6.0, 7.0], # Clase 1: Merc, Ven, Jup
            [1.5, 3.0, 4.0, 5.0, 6.0], # Clase 2: Mar, Sat
            [1.0, 2.0, 3.0, 4.0, 5.0]  # Clase 3: Lentos y Nodo
        ]
        # Orbes fijos para tránsitos
        trorbs = [1.0, 1.0, 1.0, 1.1, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0]
        #trorbs = [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0]

        lencl = len(pl)
        pairpl = pl
        if click:
            lencl = len(click)
            pairpl = click

        def get_p_group(p_idx):
            if p_idx in [0, 1]: return 0
            if p_idx in [2, 3, 5]: return 1
            if p_idx in [4, 6]: return 2
            return 3

        for i in range(len(pl)):
            for j in range(not click and i+1 or 0, lencl):
                dis = abs(pl[i] - pairpl[j])
                nsig, orb = divmod(dis, 30)
                if orb > 20.0:  
                    nsig += 1; orb = 30.0 - orb
                nsig_idx = int(nsig % 12)

                # --- ASIGNACIÓN DE COLUMNA (acl) ---
                if nsig_idx in [0, 6]:           acl = 4
                elif nsig_idx in [4, 8]:         acl = 3
                elif nsig_idx in [3, 9]:         acl = 2
                elif nsig_idx in [2, 10, 5, 7]:  acl = 1
                elif nsig_idx in [1, 11]:        acl = 0
                else: continue 

                pc1 = get_p_group(i)
                pc2 = get_p_group(j)

                # Orbes base de la matriz para cálculos de intensidad (f1, f2)
                orb1 = huber_matrix[pc1][acl]
                orb2 = huber_matrix[pc2][acl]

                # --- LÓGICA DE FILTRADO ---
                if filter == 'transit':
                    # AJUSTE MANUAL: Cambia este 1.0 para abrir o cerrar orbes de tránsito
                    f_tr = 1.0
                    
                    tr_limit = (trorbs[j] if j < len(trorbs) else 1.0) * f_tr
                    
                    if orb <= tr_limit:
                        # Usamos max(0.1...) para evitar errores de división
                        aspects.append(asp_obj(p1=i, p2=j, a=nsig_idx, f1=orb/max(0.1, orb1), f2=orb/max(0.1, tr_limit)))
                else:
                    # NATAL: Regla del Nodo y orbes Huber (OR)
                    if not click:
                        if j == 10: orb2 = orb1
                        elif i == 10: orb1 = orb2
                    
                    if orb <= orb1 * 1.1 or orb <= orb2 * 1.1:
                        aspects.append(asp_obj(p1=i, p2=j, a=nsig_idx, f1=orb/max(0.1, orb1), f2=orb/max(0.1, orb2)))
                        
        return aspects
    
    asp_fun = twelve_aspects

    def ten_aspects(self,pl,click=None,filter=None):
        aspects = []
        class asp_obj(object): 
            def __init__(self,**kargs): self.__dict__ = kargs
        lencl = len(pl)
        pairpl = pl 
        for i in range(len(pl)):
            for j in range(i+1 ,lencl):
                dis = abs(pl[i] - pairpl[j])
                nsig,orb = divmod(dis,36)
                if orb > 26.0:  nsig += 1; orb = 36.0 - orb
                nsig = int(nsig%10)
                pc1 = self.planclass[i]
                if j != 10:
                    pc2 = self.planclass[j]
                else: 
                    pc2 = self.planclass[i]
                acl = self.ten_aspclass[nsig]
                orb1,orb2 = self.ten_orbs[pc1][acl],self.ten_orbs[pc2][acl] 
                if orb <= orb1 or orb <= orb2:
                    aspects.append(asp_obj(p1=i,p2=j,a=nsig,f1=orb/orb1,f2=orb/orb2)) 
        return aspects

class AspectManager(SimpleAspectManager):
    def __init__(self,boss,get_gw,get_uni,get_nw,plmanager,colors,baseline,chartob=None):
        self.boss = boss
        self.orbs = SimpleAspectManager.orbs 
        self.peorbs = SimpleAspectManager.peorbs
        self.trorbs = SimpleAspectManager.trorbs
        self.plmanager = plmanager
        self.colhues = colors
        self.fusus = FususAspect()
        self.unilat = UnilateralAspect(baseline)
        self.conjunctio = ConjunctioAspect()
        self.gwill = GoodwillAspect(baseline)
        self.get_gw = get_gw
        self.get_nw = get_nw
        self.get_uni = get_uni
        self.ten_colors = ten_colors

    def swap_to_ten(self):
        if self.asp_fun == self.twelve_aspects:
            self.asp_fun = self.ten_aspects
            self.ten_colors,self.colhues = self.colhues,self.ten_colors 
    
    def swap_to_twelve(self):
        if self.asp_fun == self.ten_aspects:
            self.asp_fun = self.twelve_aspects
            self.colhues,self.ten_colors = self.ten_colors,self.colhues 

    def filter_int(self,aspects):
        pint = [0,1,6,10]
        return set(a for a in aspects if a.p1 in pint and a.p2 in pint)

    def filter_pers(self,aspects):
        pint = [0,1,6]
        return set(a for a in aspects if a.p1 in pint and a.p2 in pint)
    
    def filter_nw(self,aspects,nw,filter):
        if not filter:
            return set(a for a in aspects if a.p1 not in nw and a.p2 not in nw)
        else:
            return set(a for a in aspects if a.p2 not in nw)

    def manage_now_aspects(self,cr,r,planets,pe,pedraw):
        aspects = set(self.now_aspects(planets,pe))
        ap = AgePointAspect()
        deg = attrgetter('degree')
        plots1 = [deg(p) for p in self.plmanager.plot1 ]
        for a in aspects:
            a.p1 = plots1[a.p1]
            a.col = self.colhues[a.a]
            delattr(a,'a')
        ap.draw(cr,r,aspects,pedraw)
    
    def manage_aspects(self,cr,r,planets,clickplan=None,filter=None,extend=None):
        aspects = set(self.asp_fun(planets,clickplan,filter))
        notwanted = self.get_nw(filter)
        if notwanted:
            aspects = self.filter_nw(aspects,notwanted,filter)
        elif filter == 'int':
            aspects = self.filter_int(aspects)
        elif filter == 'pers':
            aspects = self.filter_pers(aspects)

        gw = set(a for a in aspects if a.f1 > 1 and a.f2 > 1)
        aspects.difference_update(gw)

        if self.get_gw():
            self.arrange_for_draw(gw,click=clickplan)
            self.gwill.draw(cr,r,gw)

        conj = set(a for a in aspects if a.a == 0)
        aspects.difference_update(conj)
        if not self.get_uni():
            uni = set(a for a in conj if a.f1 > 1 or a.f2 > 1)
            conj.difference_update(uni)
        self.arrange_for_draw(conj,click=clickplan)
        self.conjunctio.draw(cr,r,conj,filter,extend)

        if filter == 'click': 
            noopos = set(a for a in aspects if a.a != 6)
            aspects.difference_update(noopos) 
        try:
            ea = self.boss.get_showEA()
        except AttributeError:
            ea = None
        uni = set(a for a in aspects if a.f1 > 1 or a.f2 > 1)
        aspects.difference_update(uni)
        if self.get_uni():
            self.arrange_for_draw(uni,click=clickplan)
            if ea and filter == 'transit':
                self.gwill.draw(cr,r,uni) 
            else:
                self.unilat.draw(cr,r,uni)
        self.arrange_for_draw(aspects,click=clickplan)
        if ea and filter == 'transit':
            self.gwill.draw(cr,r,aspects) 
        else:
            self.fusus.draw(cr,r,aspects) 

    def arrange_for_draw(self,ascoll,click=None):
        deg = attrgetter('degree')
        plots1 = [deg(p) for p in self.plmanager.plot1 ]
        if click:
            plots2 = [deg(p) for p in self.plmanager.plot2 ]
        else:
            plots2 = plots1

        for a in ascoll:
            a.p1 = plots1[a.p1]
            a.p2 = plots2[a.p2]
            a.col = self.colhues[a.a]
            delattr(a,'a')
    
    def now_aspects(self,pl,pe):
        aspects = []
        class asp_obj(object): 
            def __init__(self,**kargs): self.__dict__ = kargs
        lencl = len(pl)

        for i in range(len(pl)):
            dis = abs(pl[i] - pe)
            nsig,orb = divmod(dis,30)
            if orb > 20.0:  nsig += 1; orb = 30.0 - orb
            nsig = int(nsig%12)
            dpi = pl[i] - int(pl[i]/30)*30
            dpe = pe - int(pe/30)*30            
            pci = self.planclass[i]
            acl = self.aspclass[nsig]
            if orb > 9.0:
                continue
            try:#Error
                orb1 = self.peorbs[pci][acl] if i != 10 else 1.0
            except (IndexError, KeyError):
                # Si el aspecto (acl) no está definido en la tabla de orbes, 
                # usamos un orbe por defecto (por ejemplo, 1.0 grado)
                orb1 = 1.0
            if orb <= orb1:
                if i in [4,7]:
                    if dpe < dpi: f = 0.5 - orb/(orb1*2) 
                    else: f = 0.5 + orb/(orb1*2) 
                elif i in [3,9]:
                    if dpe < dpi: f = 0.5 + orb/(orb1*2) 
                    else: f = 0.5 - orb/(orb1*2) 
                elif i == 8:
                    f = 1 - orb/(orb1*2) 
                else:
                    f = orb / orb1
                aspects.append(asp_obj(p1=i,a=nsig,f=f)) 
        return aspects
