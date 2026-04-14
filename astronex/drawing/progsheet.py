# -*- coding: utf-8 -*-
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
from .. chart import zodnames,planames,aspnames
from .roundedcharts import NodalChart,SoulChart,LocalChart
from .. boss import boss
curr = boss.get_state()

aspcol = None

class ProgMixin(object):
    def __init__(self,zodiac):
        global aspcol
        aspcol = zodiac.get_aspcolors() 
        self.zod = zodiac.zod
        self.plan = zodiac.plan
    
    def prog_nat(self,cr,w,h,chartob):
        cr.set_source_rgb(1.0,1.0,1.0)
        cr.rectangle(0,0,w,h)
        
        cr.set_line_join(cairo.LINE_JOIN_ROUND) 
        cr.set_line_width(0.5)
        self.d_prog(cr,chartob)
    
    def prog_local(self,cr,w,h,chartob):
        cr.set_source_rgb(1.0,1.0,1.0)
        cr.rectangle(0,0,w,h)
        
        cr.set_line_join(cairo.LINE_JOIN_ROUND) 
        cr.set_line_width(0.5)
        chartob.__class__ = LocalChart
        self.d_prog(cr,chartob,kind='local')
    
    def prog_soul(self,cr,w,h,chartob):
        cr.set_source_rgb(1.0,1.0,1.0)
        cr.rectangle(0,0,w,h)
        
        cr.set_line_join(cairo.LINE_JOIN_ROUND) 
        cr.set_line_width(0.5)
        chartob.__class__ = SoulChart
        self.d_prog(cr,chartob,kind='soul')
    
    def prog_nod(self,cr,w,h,chartob):
        cr.set_source_rgb(1.0,1.0,1.0)
        cr.rectangle(0,0,w,h)
        
        cr.set_line_join(cairo.LINE_JOIN_ROUND) 
        cr.set_line_width(0.5)
        chartob.__class__ = NodalChart
        self.d_prog(cr,chartob,kind='nodal')
    
    def d_prog(self, cr, chartob, kind='radix'):
        # --- MARGEN SOLO PARA EL CUERPO DE LA TABLA ---
        # Ajusta este valor para mover las columnas de fechas a la derecha
        MARGIN_X = 275
        # ----------------------------------------------

        if kind == 'radix': 
            age = chartob.get_age_prog()
        elif kind == 'soul':
            age = chartob.get_age_prog()
        elif kind == 'local':
            age = chartob.get_age_prog()
        elif kind == 'nodal':
            age = chartob.get_age_prog()

        ho = 128; vo = 15
        hm = 50; vm = 110 # hm vuelve a su valor original de 50
        year = prev_y = ""
        
        layout = PangoCairo.create_layout(cr)
        font = Pango.FontDescription(self.opts.font)
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)

        # 1. CABECERA (Se queda donde estaba)
        self.main_labels(cr, font, kind)
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(50, 80)
        cr.line_to(540, 80)
        cr.stroke()
        if kind in ['radix', 'nodal']:
            self.cross_points(cr)
        else:
            vm = 90
        
        # 2. CUERPO DE LA TABLA
        cr.save()
        # Reset de matriz para evitar inclinación
        matrix = cairo.Matrix(1, 0, 0, 1, 0, 0)
        cr.set_matrix(matrix)

        for i in range(len(age)): 
            font = Pango.FontDescription(self.opts.font)
            font.set_size(9*Pango.SCALE)
            layout.set_font_description(font)
            cr.set_source_rgb(0, 0, 0.4)
            y_val = age[i]['year']
            if i == 0:
                year = prev_y = y_val
            else:
                if y_val != prev_y:
                    year = prev_y = y_val
                else:
                    if i % 48 == 0: year = y_val  
                    else: year = " "

            # AQUI aplicamos el MARGIN_X solo a las columnas
            x = int(hm + MARGIN_X + ho * (i // 48))
            y = int(vm + vo * (i % 48))
            
            cr.move_to(x, y)
            text = "%s.%s.%s" % (age[i]['day'], age[i]['mon'], str(year))
            layout.set_text(text)
            PangoCairo.show_layout(cr, layout)

            cl = age[i]['cl']
            text = age[i]['lab']
            
            if cl == "txt_cp":
                cr.set_source_rgb(0.6, 0, 0)
                layout.set_text(text)
                cr.move_to(x + 80, y)
                PangoCairo.show_layout(cr, layout)
            elif cl == "pr":
                cr.set_source_rgb(0, 0.4, 0)
                layout.set_text(text)
                cr.move_to(x + 80, y)
                PangoCairo.show_layout(cr, layout)
            elif cl == "pi":
                cr.set_source_rgb(0, 0, 0.6)
                layout.set_text(text)
                cr.move_to(x + 80, y)
                PangoCairo.show_layout(cr, layout)
            else:
                font_ast = Pango.FontDescription("Astro-Nex")
                font_ast.set_size(11*Pango.SCALE)
                layout.set_font_description(font_ast)
                if cl == 'asp':
                    tx = age[i]['lab'].split('/')
                    try:
                        idx = aspnames.index(tx[0])
                        asp = self.asplet[idx]
                        cr.move_to(x + 80, y)
                        cr.set_source_rgb(*aspcol[idx])
                        layout.set_text(asp)
                        PangoCairo.show_layout(cr, layout)
                        
                        idx_pl = planames.index(tx[1])
                        pl = self.plan[idx_pl].let
                        colp = self.plan[idx_pl].col
                        cr.set_source_rgb(*colp) 
                        cr.move_to(x + 100, y)
                        layout.set_text(pl)
                        PangoCairo.show_layout(cr, layout)
                    except ValueError: pass
                elif cl == 'sign':
                    try:
                        idx = zodnames.index(text)
                        colp = self.zod[idx%4].col
                        sign = self.zod[idx].let
                        cr.set_source_rgb(*colp) 
                        cr.move_to(x + 85, y)
                        layout.set_text(sign)
                        PangoCairo.show_layout(cr, layout)
                    except ValueError: pass
                elif cl == 'mid':
                    tx = age[i]['lab'].split('/')
                    try:
                        idx_pl1 = planames.index(tx[0])
                        pl1 = self.plan[idx_pl1].let
                        colp1 = self.plan[idx_pl1].col
                        cr.set_source_rgb(*colp1) 
                        cr.move_to(x + 80, y)
                        layout.set_text(pl1)
                        PangoCairo.show_layout(cr, layout)

                        idx_pl2 = planames.index(tx[1])
                        pl2 = self.plan[idx_pl2].let
                        colp2 = self.plan[idx_pl2].col
                        cr.set_source_rgb(*colp2) 
                        cr.move_to(x + 100, y)
                        layout.set_text(pl2)
                        PangoCairo.show_layout(cr, layout)
                    except (ValueError, IndexError): pass
            cr.new_path()
        cr.restore()
            
    def cross_points(self,cr):
        layout = PangoCairo.create_layout(cr)
        font = Pango.FontDescription(self.opts.font)
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        
        cp = curr.curr_chart.calc_cross_points(True)
        dat1 = cp['dat1']
        dat2 = cp['dat2']
        deg1 = cp['cp1']['deg']
        deg2 = cp['cp2']['deg']
        
        cr.set_source_rgb(0.5,0,0.5)
        cr.move_to(50,88)
        layout.set_text(_("Cruce PE - K1: %s  %s") % (dat1,deg1))
        PangoCairo.show_layout(cr, layout)
         
        cr.move_to(310,88)
        layout.set_text("K2: %s  %s" % (dat2,deg2))
        PangoCairo.show_layout(cr, layout)
        
        
        font = Pango.FontDescription("Astro-Nex")
        font.set_size(11*Pango.SCALE)
        layout.set_font_description(font)
        s1 = self.zod[cp['cp1']['name']].let
        s2 = self.zod[cp['cp2']['name']].let
        c1 = self.zod[cp['cp1']['col']%4].col
        c2 = self.zod[cp['cp2']['col']%4].col
        cr.move_to(274,86)
        cr.set_source_rgb(*c1)
        layout.set_text("%s" % (s1))
        PangoCairo.show_layout(cr, layout)
        
        cr.move_to(466,86)
        cr.set_source_rgb(*c2)
        layout.set_text("%s" % (s2))
        PangoCairo.show_layout(cr, layout)
        


    

