# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib
from gi.repository import GObject as gobject
from gi.repository import Gtk, Gdk, Pango, PangoCairo
import cairo
import math
from .. nex import t
from .. drawing.dispatcher import DrawMixin
from .. gui.plselector_dlg import PlanSelector
from .. gui.popup import PlanPopup, TextPopup
from .. gui.cycle_dlg import CycleSelector
from .. gui.aux_dlg import AuxWindow
from .. gui.bridgewin import BridgePEWindow
from .. extensions.path import path
from .. countries import cata_reg
from .. utils import parsestrtime
from .sdasurface import DrawDiagram, HouseSelector
from datetime import datetime, timedelta
from .. boss import boss
curr = boss.get_state()

MAGICK_COL = 65535.0
initmenu = (_('Ayuda'),_('Acercar'),_('Solo EA'),_('Ver zonas PE'),
        _('Ver zonas de casa'),_('Ver EA'),_('Activar goodwill'),
        _('Ocultar unilaterales'),_('Ego-clics'),_('Ver todos los aspectos'))
bios = ['bio_nat','bio_nod','bio_soul','bio_dharma']
peops = ['draw_nat','draw_nod','draw_soul','draw_local']
sheetops = ['dat_nat', 'dat_nod', 'dat_house', 'prog_nat', 'prog_nod', 'prog_local', 'prog_soul' ]
extended = ['prog_nat','prog_nod','prog_soul','prog_local','compo_one','compo_two']

class DrawMaster(Gtk.Layout):
    fullscreen = False
    panning = False
    zoom_in = False
    panelvisible = False
    diadavisible = False
    hselvisible = False
    pepending = [False,None,None]
    rulinepending = None
    bridge = None
    sec_alltimes = False
    overlay = False

    def __init__(self,boss):
        self.boss = boss
        self.opts = boss.opts
        Gtk.Layout.__init__(self)
        self.menu = Gtk.Menu()
        self.hidden_op = {}
        for buf in initmenu:
            menu_item = Gtk.MenuItem(buf)
            self.menu.append(menu_item)
            menu_item.connect("activate", self.on_menuitem_activate)
            if buf in [_('Ayuda'),_('Ver EA')]:
                sep_item = Gtk.SeparatorMenuItem()
                self.menu.append(sep_item)
                sep_item.show()
            if buf not in [_('Ver EA'),_('Ver zonas PE'),_('Ver zonas de casa'),
                    _('Ver todos los aspectos'),_('Ego-clics')]:
                menu_item.show()
            elif buf == _('Ver EA'):
                self.hidden_op['ea'] = menu_item
            elif buf == _('Ver zonas PE'):
                self.hidden_op['pez'] = menu_item
            elif buf == _('Ver zonas de casa'):
                self.hidden_op['hz'] = menu_item
            elif buf == _('Ver todos los aspectos'):
                self.hidden_op['acl'] = menu_item 
            elif buf == _('Ego-clics'):
                self.hidden_op['ego'] = menu_item 
        
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("draw", self.dispatch)
        self.connect("button_press_event", self.on_da_clicked)
        self.connect("button_release_event", self.on_da_clicked)
        self.connect("motion_notify_event", self.on_da_clicked)
        self.connect("scroll-event", self.on_scroll)
        self.panel = ChangeDatePanel(self)
        self.put(self.panel,-200,-200)

        self.create_special_area()
        self.create_hselector()
        self.drawer = DrawMixin(boss.opts,self) 
        self.plselector = None
        self.cycleselector = None
        self.planpopup = None
        self.textspopup = None
        self.where_diada = 0
        self.where_hsel = 0
        self.auxwins = []

        self.ha = None
        self.va = None
        self.m_x = 0
        self.m_y = 0
    
    def create_special_area(self):
        frame = Gtk.Frame()
        diada = DrawDiagram(self.boss)
        diada.set_size_request(275,275) 
        frame.add(diada)
        self.put(frame,-280,0)
        self.diada = frame

    def create_hselector(self):
        frame = Gtk.Frame()
        hsel = HouseSelector(self.boss)
        hsel.set_size_request(120,120) 
        frame.add(hsel)
        self.put(frame,-160,612)
        self.hsel = frame

    def on_da_clicked(self,da,event):
        showAP = DrawMixin.get_showAP()
        x, y = event.x,event.y
        info = getattr(self, "move_info", None)
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.menu.popup(None, None, None, None, event.button, event.time)
            return True
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            if showAP or curr.curr_chart == curr.now or curr.curr_op in ['draw_transits','rad_and_transit']:
                self.panel.nowbut.emit('clicked')
                info['button'] = 100; #now
                if self.cycleselector:
                    cycles = curr.curr_chart.get_cycles()
                    self.cycleselector.adj.set_value(cycles+1) 
            elif curr.curr_op == 'sec_prog':
                self.sec_alltimes = not(self.sec_alltimes)
            return True
        elif event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            if curr.curr_op in bios and curr.opmode == 'simple':
                return False
            if event.button != 1: return False
            if info['button'] < 0:
                info['button'] = event.button
                if self.panning:
                        fleur = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.FLEUR)
                        mask = (Gdk.EventMask.POINTER_MOTION_MASK | 
                                Gdk.EventMask.BUTTON_RELEASE_MASK | 
                                Gdk.EventMask.POINTER_MOTION_HINT_MASK)
                        
                        # En GTK3 el grab se hace a través del dispositivo del evento
                        device = event.get_device()
                        device.grab(self.get_window(), 
                                    Gdk.GrabOwnership.APPLICATION, 
                                    True, 
                                    mask, 
                                    fleur, 
                                    event.time)
                                    
                        info['click_x'] = event.x
                        info['click_y'] = event.y
            elif info['button'] == 100:
                info['button'] = -1
            if showAP is None:
                return True 
            alloc = da.get_allocation()
            w = alloc.width / 2
            h = alloc.height / 2
            if curr.opmode == 'simple' and curr.curr_op in peops:
                pass
                #if event.state & Gtk.gdk.CONTROL_MASK:
                #    self.drawer.set_op_AP(curr.curr_op,event.state )
                #    dt = curr.date.dt
                #    dt = datetime.combine(dt.date(),dt.time())
                #    self.hsel.child.set_house_from_date(dt)
                #    self.redraw()
                #    self.redraw_auxwins()
                #    return
            elif curr.opmode == 'double' or curr.curr_op == 'rad_and_transit':
                deg = math.degrees(math.atan2(y-h, (x%w)-(w/2) )) 
                for_op = [curr.opleft,curr.opright][x > w]
                if curr.clickmode == 'click':
                    for_ch = ['chart','click'][x > w]
                else:
                    for_ch = 'chart'
                if deg == 0.0: deg = 0.0001
                self.drawer.set_AP(deg,for_op,for_ch)
                self.redraw()
                dt = curr.date.dt
                dt = datetime.combine(dt.date(),dt.time())
                self.hsel.child.set_house_from_date(dt)
                self.redraw_auxwins()
                info['button'] = -1
            else:
                return False
            return True
        elif event.type == Gdk.EventType.BUTTON_PRESS and event.button == 2:
            if curr.clickmode == 'click' and curr.opmode != 'simple':
                return
            if curr.opmode == 'double':
                boss.mpanel.chooser.swap_ops() 
                boss.da.redraw_auxwins(True)
            elif curr.opmode == 'triple':
                x, y = event.x,event.y 
                w, h = da.allocation.width, da.allocation.height
                side = ['up',None][y > (h/2)] 
                if not side:
                    side = ['left','right'][x > (w/2)] 
                boss.mpanel.chooser.swap_ops(side) 
            elif curr.opmode == 'simple':
                if self.zoom_in:
                    self.panning = not self.panning
                elif not showAP:
                    nb = boss.mpanel.chooser.notebook
                    page = nb.get_current_page()
                    sel = nb.get_nth_page(page).get_selection()
                    m,i = sel.get_selected()
                    ix = m.get_path(i)[0]
                    if ix == 0 and not self.planpopup:
                        self.planpopup = PlanPopup(boss)
                    elif page == 3 and ix in [2,3,4]:
                        if not self.textspopup:
                            self.textspopup = TextPopup(ix)
                    #else:
                    #    sel.select_path(0)
                    #    sel.emit('changed') 
                else:
                    self.drawer.set_op_AP(curr.curr_op,event.state )
                    dt = curr.date.dt
                    dt = datetime.combine(dt.date(),dt.time())
                    self.hsel.child.set_house_from_date(dt)
                    self.redraw()
                    self.redraw_auxwins()
        elif event.type == Gdk.EventType.BUTTON_RELEASE:
            if self.planpopup:
                self.planpopup.destroy()
                self.planpopup = None 
            if curr.curr_op in bios or curr.opmode != 'simple':
                return False
            if info['button'] < 0 or info['button'] == 100:
                return True
            if info['button'] == event.button:
                info['button'] = -1; 
                if self.panning:
                    device = event.get_device()
                    device.ungrab(event.time)
                else: 
                    self.drawer.ruline = None
                    self.rulinepending = None
                    if showAP:
                        alloc = da.get_allocation()
                        w = alloc.width / 2
                        h = alloc.height / 2
                        deg = math.degrees(math.atan2(y-h,x-w))
                        for_op = curr.curr_op
                        for_ch = 'chart'
                        self.drawer.set_AP(deg,for_op,for_ch)
                        dt = curr.date.dt
                        dt = datetime.combine(dt.date(),dt.time())
                        hsel_child = self.hsel.get_child()
                        if hsel_child:
                            hsel_child.set_house_from_date(dt)
                    self.redraw()
                    boss.redraw(both=False)
                    self.redraw_auxwins()
        elif event.type == Gdk.EventType.MOTION_NOTIFY:
            if curr.curr_op in bios or curr.opmode != 'simple':
                return False
            window = event.get_window()
            device = event.get_device()
            _, x, y, state = window.get_device_position(device)
            if DrawMaster.overlay:
                self.m_x = x
                self.m_y = y
                self.queue_draw()
            if info['button'] < 0 or info['button'] == 100:
                info['button'] = -1
                return False
            alloc = da.get_allocation()
            w = alloc.width / 2
            h = alloc.height / 2
            if self.panning:
                x = info['click_x'] - x
                y = info['click_y'] - y
                w = self.allocation.width
                h = self.allocation.height
                wrange = w - self.ha.page_size
                hrange = h - self.va.page_size
                #dx = float(x) / w * wrange
                #dy = float(y) / h * hrange
                if x + self.ha.value < 0:
                    self.ha.value = 0
                elif x + self.ha.value > wrange: 
                    self.ha.value = wrange
                else:
                    self.ha.value += x
                if y + self.va.value < 0:
                    self.va.value = 0
                elif y + self.va.value > hrange: 
                    self.va.value = hrange
                else:
                    self.va.value += y
            else:
                self.drawer.ruline = (x-w,y-h)
                self.queue_draw()
            #self.queue_draw()

    def toggle_overlay(self):
        DrawMaster.overlay = not DrawMaster.overlay 
        # En GTK3 usamos get_window() en lugar de .window
        window = self.get_window()
        
        if DrawMaster.overlay:
            # Forma moderna de crear un cursor invisible en GTK3
            cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.BLANK_CURSOR)
            if window:
                window.set_cursor(cursor)
        else:
            if window:
                window.set_cursor(None)
        self.queue_draw()

    def on_scroll(self,da,event):
        x, y = event.x,event.y 
        alloc = da.get_allocation()
        w, h = alloc.width, alloc.height
        side = None
        
        if event.direction == Gdk.ScrollDirection.UP:
            delta = -1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            delta = 1
        else:
            # En GTK3 a veces existen desplazamientos laterales (LEFT/RIGHT) 
            # o SMOOTH. Si no es arriba/abajo, ignoramos el delta.
            delta = 0

        if self.textspopup:
            self.textspopup.destroy()
            self.textspopup = None 
            nb = boss.mpanel.chooser.notebook
            page = nb.get_current_page()
            m,i = nb.get_nth_page(page).get_selection().get_selected()
            ix = m.get_path(i)[0] + delta 
            if page == 3 and ix in [2,3,4]:
                self.textspopup = TextPopup(ix)
        
        if  curr.opmode == 'simple':
            boss.mpanel.chooser.delta_select(delta) 
        elif  curr.opmode == 'triple':
            side = ['up',None][y > (h/2)] 
            if not side:
                side = ['left','right'][x > (w/2)] 
            curr.set_opdelta(delta,side)
            boss.mpanel.chooser.delta_triple_select(delta,side) 
        elif  curr.opmode == 'double':
            side = ['left','right'][x > (w/2)] 
            curr.set_opdelta(delta,side)
            boss.mpanel.chooser.delta_double_select(delta,side) 
        
        self.redraw()
        return True

    def on_menuitem_activate(self,menuitem): 
        if menuitem.get_label() == _('Acercar'):
            scrw, scrh = self.get_size_request()
            #self.set_size_request(720*2,720*2)
            self.set_size_request(scrw*2,scrh*2)
            self.zoom_in = True
            self.panning = True
            menuitem.set_label(_('Alejar'))
        elif menuitem.get_label() == _('Alejar'):
            scrw, scrh = self.get_size_request()
            #self.set_size_request(720,720)
            self.set_size_request(scrw/2,scrh/2)
            self.zoom_in = False
            self.panning = False
            menuitem.set_label(_('Acercar'))
        elif menuitem.get_label() == _('Ayuda'):
            boss.mainwin.show_help()
        elif menuitem.get_label() == _('Ver zonas PE'):
            self.drawer.pe_zones = True
            self.redraw_auxwins(True)
            menuitem.set_label(_('Ocultar zonas PE'))
        elif menuitem.get_label() == _('Ocultar zonas PE'):
            self.drawer.pe_zones = False
            self.redraw_auxwins(True)
            menuitem.set_label(_('Ver zonas PE')) 
        elif menuitem.get_label() == _('Ver zonas de casa'):
            self.drawer.hzones = True
            menuitem.set_label(_('Ocultar zonas de casa'))
        elif menuitem.get_label() == _('Ocultar zonas de casa'):
            self.drawer.hzones = False
            menuitem.set_label(_('Ver zonas de casa'))
        elif menuitem.get_label() == _('Solo EA'):
            DrawMixin.set_onlyEA(True)
            menuitem.set_label(_('Mostrar todo')) 
        elif menuitem.get_label() == _('Mostrar todo'):
            DrawMixin.set_onlyEA(False)
            menuitem.set_label(_('Solo EA'))
        elif menuitem.get_label() == _('Activar goodwill'):
            self.drawer.goodwill = True
            menuitem.set_label(_('Desactivar goodwill'))
        elif menuitem.get_label() == _('Desactivar goodwill'):
            self.drawer.goodwill = False
            menuitem.set_label(_('Activar goodwill'))
        elif menuitem.get_label() == _('Ocultar unilaterales'):
            self.drawer.uniaspect = False
            menuitem.set_label(_('Mostrar unilaterales'))
        elif menuitem.get_label() == _('Mostrar unilaterales'):
            self.drawer.uniaspect = True
            menuitem.set_label(_('Ocultar unilaterales'))
        elif menuitem.get_label() == _('Ver EA'):
            DrawMixin.set_showEA(True)
            menuitem.set_label(_('Ocultar EA'))
        elif menuitem.get_label() == _('Ocultar EA'):
            DrawMixin.set_showEA(False)
            menuitem.set_label(_('Ver EA'))
        elif menuitem.get_label() == _('Ver todos los aspectos'):
            self.drawer.allclick = True
            menuitem.set_label(_('Ver solo clics'))
        elif menuitem.get_label() == _('Ver solo clics'):
            self.drawer.allclick = False
            menuitem.set_label(_('Ver todos los aspectos'))
        elif menuitem.get_label() == _('Ego-clics'):
            self.drawer.egoclick = True
            menuitem.set_label(_('Clics sin ego'))
        elif menuitem.get_label() == _('Clics sin ego'):
            self.drawer.egoclick = False
            menuitem.set_label(_('Ego-clics'))

        self.redraw()

    def toggle_menulist(self,men,dothing):
        if dothing == 'add':
            self.hidden_op[men].show()
        elif dothing == 'remove':
            self.hidden_op[men].hide() 
    
    def popup_menu(self):
        event = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
        self.menu.popup(None, None, None, 1, event.time)

    def redraw(self): 
        # Usamos métodos get_ en lugar de acceso directo a propiedades
        w = int(self.ha.get_upper() - self.ha.get_lower())
        h = int(self.va.get_upper() - self.va.get_lower())
        x = int(self.ha.get_lower())
        y = int(self.va.get_lower())
    
        # En GTK 3, Rectangle se maneja a través de Gdk (no Gtk.gdk)
        # y invalidate_rect suele llamarse desde el objeto window
        from gi.repository import Gdk
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = x, y, w, h
    
        if self.get_window():
            self.get_window().invalidate_rect(rect, False) 

        if self.diadavisible:
            # Usamos get_allocation() en lugar de .allocation
            alloc = self.diada.get_child().get_allocation()
            w = alloc.width
            h = alloc.height
        
            child_window = self.diada.get_child().get_window()
            if child_window:
                rect_diada = Gdk.Rectangle()
                rect_diada.x, rect_diada.y, rect_diada.width, rect_diada.height = 0, 0, w, h
                child_window.invalidate_rect(rect_diada, False)
            
        if boss.da.hselvisible:
            boss.da.hsel.get_child().queue_draw()

    def redraw_auxwins(self,onlybridge=False):
        if self.bridge:
            self.bridge.sda.redraw()
        if onlybridge:
            return
        for aux in self.auxwins:
            aux.sda.redraw()

    def show_panel(self,menuitem=None):
        self.move(self.panel,0,0)
        self.panelvisible = True
        #boss.mpanel.stop_timeout()

    def hide_panel(self,menuitem=None):
        self.move(self.panel,-200,-200)
        self.panelvisible = False
        if curr.curr_chart == curr.now:
            self.panel.nowbut.emit('clicked')
            #boss.mpanel.start_timeout()

    def show_pe(self,menuitem=None):
        if curr.curr_chart == curr.now:
            boss.mpanel.toolbar.get_nth_item(1).set_active(False)
            return
        DrawMixin.set_showAP('now')
        #self.panel.nowbut.emit('clicked')
        self.redraw()
        self.redraw_auxwins()
        
    def hide_pe(self,menuitem=None):
        DrawMixin.set_showAP(None)
        self.redraw()
        self.redraw_auxwins()
    
    def show_diada(self,menuitem=None):
        where = self.get_allocation().width - self.diada.get_allocation().width
        self.move(self.diada,where,0) 
        self.diadavisible = True 
        self.redraw()
    
    def hide_diada(self,menuitem=None):
        self.move(self.diada,-280,0) 
        self.diadavisible = False
        self.redraw()
    
    def make_auxwin(self):
        self.auxwins.append(AuxWindow(boss.mainwin)) 
        sda = self.auxwins[-1].sda
        sda.drawer.hoff = sda.get_allocation().width * 0.125
        sda.drawer.gridw = sda.drawer.hoff * 6

    def make_pebridge(self):
        if not self.bridge:
            self.bridge = BridgePEWindow(boss.mainwin)
    
    def hide_pebridge(self):
        self.bridge.exit()
        self.bridge = None


    def make_plsel(self):
        if not self.plselector:
            self.plselector = PlanSelector(self.boss.mainwin)
            self.plselector.move(0,0)

    def make_cycleswin(self): 
        if not self.cycleselector:
            self.cycleselector = CycleSelector(self.boss.mainwin)
            wx,wy = self.boss.mainwin.pos_x,self.boss.mainwin.pos_y
            ww,wh =self.boss.mainwin.get_size()
            alloc = self.cycleselector.get_allocation()
            w, h = alloc.width, alloc.height
            self.cycleselector.move(wx+ww-w-10,wh+wy-h-24)

    def dispatch(self, da, cr):
        # Actualizamos variables de dimensiones compatibles con GTK 3
        alloc = self.get_allocation()
        curr_w = alloc.width
        curr_h = alloc.height

        if self.diadavisible:
            diada_alloc = self.diada.get_allocation()
            where = curr_w - diada_alloc.width
            if self.where_diada != where:
                self.move(self.diada, where, 0) 
                self.where_diada = where
        
        op = curr.curr_op
        if self.fullscreen:
            DrawMixin.extended_canvas = False
        elif op in extended and curr.opmode == 'simple':
            if not DrawMixin.extended_canvas:
                DrawMixin.extended_canvas = True
                pad = 160 
                if op in ['compo_one', 'compo_two']: 
                    if boss.mainwin.scr_width <= 1024:
                        pad = curr_w * 0.4
                    else:
                        pad = curr_w * 0.55
                self.set_size_request(720, int(720 + pad))
        else:
            if DrawMixin.extended_canvas:
                DrawMixin.extended_canvas = False
                self.set_size_request(720, 720)
    
        if op in bios and not self.hselvisible and curr.opmode == 'simple':
            hsel_h = self.hsel.get_allocation().height
            where = curr_h - hsel_h
            self.move(self.hsel, 0, where) 
            self.hselvisible = True
        elif self.hselvisible and curr.opmode != 'simple' or op not in bios:
            self.move(self.hsel, -160, 650) 
            self.hselvisible = False

        if self.hselvisible:
            hsel_h = self.hsel.get_allocation().height
            where = curr_h - hsel_h
            if self.where_hsel != where:
                self.move(self.hsel, 0, where) 
                self.where_hsel = where
        
        window = self.get_window()
        if not window: return
        
        import cairo
        from gi.repository import Gdk, Gtk
        cr = Gdk.cairo_create(window)

        # --- LÓGICA DE COLORES DEL SISTEMA ---
        context = self.get_style_context()
        # Obtenemos color de fondo y de texto (foreground) del tema actual
        bg_color = context.get_background_color(Gtk.StateFlags.NORMAL)
        fg_color = context.get_color(Gtk.StateFlags.NORMAL)

        # 1. Pintamos el fondo dinámico
        cr.set_source_rgba(bg_color.red, bg_color.green, bg_color.blue, bg_color.alpha)
        cr.rectangle(0, 0, curr_w, curr_h)
        cr.fill()

        # 2. Preparamos el color de las líneas para que contraste (texto del tema)
        cr.set_source_rgba(fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha)

        # Lógica de Escala y Proporción
        original_base = 720.0
        min_allowed = original_base * 0.38
        side = min(curr_w, curr_h)
        
        if side < min_allowed:
            side = min_allowed
            
        off_x = (curr_w - side) / 2.0
        off_y = (curr_h - side) / 2.0

        cr.save()
        cr.translate(off_x, off_y)
        cr.set_line_join(cairo.LINE_JOIN_ROUND) 
        cr.set_line_width(float(self.opts.base))
        
        draw_w, draw_h = side, side
        
        if self.diadavisible:
            cr.translate(0, draw_h * 0.15)
            draw_w *= 0.85
            draw_h *= 0.85
            
        self.drawer.dispatch_pres(cr, draw_w, draw_h)
        cr.restore()
        
        # Volvemos a asegurar el color de primer plano para etiquetas
        cr.set_source_rgba(fg_color.red, fg_color.green, fg_color.blue, fg_color.alpha)
        cr.identity_matrix()

        if self.pepending[0]:
            self.draw_pelabel(cr, curr_w, curr_h)
            self.pepending = [False, None, None]
        elif curr.curr_chart == curr.now or curr.curr_op in ['draw_transits', 'solar_rev']:
            self.d_now_date(cr, curr_w, curr_h)
            
        if self.rulinepending:
            self.d_ruldegree(cr, curr_w, curr_h)
            
        self.draw_label(cr, curr_w, curr_h) 
        if self.check_local_label():
            self.d_loclbl(cr, curr_w, curr_h)

    def check_local_label(self):
        if curr.opmode == 'simple' and curr.curr_op == 'draw_local': 
            return True
        labelyes = curr.opleft == 'draw_local' or curr.opright == 'draw_local'
        if curr.opmode == 'double' and labelyes:
            return True 
        if curr.opmode == 'triple' and labelyes or curr.opup == 'draw_local':
            return True 
        return False 

    def d_ruldegree(self,cr,w,h):
        if self.diadavisible:
            return
        sign,deg = divmod(self.rulinepending,30)
        mint = int((deg - int(deg)) * 60)
        sign = int(sign)
        deg = int(deg)
        let = self.drawer.zodlet[sign]
        col = boss.opts.zodiac.zod[sign].col
        signs = "%s\u00b0 %s\u00b4" % (deg,mint)
        layout = self.create_pango_layout("")
        cr.set_source_rgb(0,0,0.6) 
        font = Pango.FontDescription(self.opts.font)
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        layout.set_text(signs)
        ink,logical = layout.get_extents()
        xpos = logical.width / Pango.SCALE
        cr.move_to(w-xpos-20,20)
        PangoCairo.show_layout(cr, layout)
        
        font = Pango.FontDescription("Astro-Nex")
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        cr.set_source_rgb(*col)
        layout.set_text(let)
        ink,logical = layout.get_extents()
        xpos = logical.width / Pango.SCALE
        cr.move_to(w-xpos-5,20)
        PangoCairo.show_layout(cr, layout)

    def draw_pelabel(self,cr,w,h):
        if self.diadavisible:
            return

        date = curr.date.ld
        date = date.__str__().split(' ')[0].split('-')
        date.reverse()
        date = "/".join(date) 
        layout = PangoCairo.create_layout(cr)
        
        signs = ['','']
        collet = [0,0]
        for i in [1,2]:
            pe = self.pepending[i]
            if not pe: break
            sign,deg = divmod(pe,30)
            mint = int((deg - int(deg)) * 60)
            sign = int(sign)
            deg = int(deg)
            let = self.drawer.zodlet[sign]
            col = boss.opts.zodiac.zod[sign].col
            collet[i-1] = (col,let,i%2)
            signs[i-1] = "%s\u00b0 %s\u00b4" % (deg,mint)
        if signs[1]:
            signs[0],signs[1] = signs[1],signs[0]

        cr.set_source_rgb(0,0,0.6) 
        font = Pango.FontDescription(self.opts.font)
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        layout.set_text(signs[1]+" "+date+" "+signs[0])
        ink,logical = layout.get_extents()
        xpos = logical.width / Pango.SCALE
        cr.move_to(w-xpos-20,5)
        PangoCairo.show_layout(cr, layout)

        font = Pango.FontDescription("Astro-Nex")
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        if collet[1]: 
            off = xpos+22
            for col,let,f in collet:
                cr.set_source_rgb(*col)
                layout.set_text(let)
                ink,logical = layout.get_extents()
                xpos = logical.width / Pango.SCALE
                cr.move_to(w-xpos-5-f*off,5)
                PangoCairo.show_layout(cr, layout)
        else:
            cr.set_source_rgb(*col)
            layout.set_text(let)
            ink,logical = layout.get_extents()
            xpos = logical.width / Pango.SCALE
            cr.move_to(w-xpos-5,5)
            PangoCairo.show_layout(cr, layout)
        
    def d_now_date(self,cr,w,h):
        if self.diadavisible:
            return
        strdate = curr.charts['now'].date
        date,time = parsestrtime(strdate)
        date = date + " " + time.split(" ")[0]
        layout = PangoCairo.create_layout(cr)
        cr.set_source_rgb(0,0,0.6)
        font = Pango.FontDescription(self.opts.font)
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        layout.set_text(date)
        ink,logical = layout.get_extents()
        xpos = logical.width / Pango.SCALE
        cr.move_to(w-xpos-18,5) 
        PangoCairo.show_layout(cr, layout)
    
        font = Pango.FontDescription("Astro-Nex")
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        regent = curr.year_regent()
        pl = boss.opts.zodiac.plan[regent]
        cr.set_source_rgb(*pl.col)
        layout.set_text(pl.let)
        ink,logical = layout.get_extents()
        xpos = logical.width / Pango.SCALE
        cr.move_to(w-xpos-5,5)
        PangoCairo.show_layout(cr, layout)


    def d_loclbl(self,cr,w,h):
        layout = PangoCairo.create_layout(cr)
        cr.set_source_rgb(0,0.5,0.3) 
        font = Pango.FontDescription(self.opts.font)
        font.set_size(8*Pango.SCALE)
        layout.set_font_description(font)
        region = curr.loc.region
        if boss.opts.lang == 'ca' and curr.loc.country == 'España':
            region = cata_reg[region]
        layout.set_text(curr.loc.city+' ('+region+'-'+t(curr.loc.country)[0]+')')
        ink,logical = layout.get_extents()
        xpos = logical.width / Pango.SCALE
        cr.move_to(w/2-xpos/2,h-15)
        PangoCairo.show_layout(cr, layout)

    def draw_label(self,cr,w,h): 
        if curr.curr_op in sheetops:
            return
        layout = PangoCairo.create_layout(cr)
        font = Pango.FontDescription(self.opts.font)
        font.set_size(9*Pango.SCALE)
        layout.set_font_description(font)
        h -= 20 if self.fullscreen else 15

        cols = [(0,0,0.4),(0.8,0,0.1)]
        ix = [0,1][curr.clickmode == 'click']
        charts = (curr.curr_chart,curr.curr_click) 
        for i in range(ix+1):
            name = "%s %s" % (charts[i].first,charts[i].last) 
            layout.set_text(name)
            ink,logical = layout.get_extents()
            xpos = logical.width / Pango.SCALE
            if ix and not i:
                pos = 0 + 5
            else:
                pos = w - xpos - 5 
            cr.set_source_rgb(*cols[i]) 
            cr.move_to(pos,h)
            PangoCairo.show_layout(cr, layout)
        if self.diadavisible and curr.clickmode == 'click':
            where = self.allocation.width - self.diada.allocation.width
            name = "%s %s" % (charts[0].first,charts[0].last) 
            layout.set_text(name)
            ink,logical = layout.get_extents()
            xpos = logical.width / Pango.SCALE
            cr.move_to(where-20,5+xpos)
            cr.rotate(-90*math.pi/180)
            cr.set_source_rgb(*cols[0]) 
            PangoCairo.show_layout(cr, layout)


############################################
############################################

class ChangeDatePanel(Gtk.VBox):
    changes = ['minutes','hours','days']
    def __init__(self,parent):
        Gtk.VBox.__init__(self)
        
        frame = Gtk.Frame()
        self.time = curr.date.ld.time()
        self.internal_signal = True
        self.needsredrawing = True
        self.calendar = Gtk.Calendar()
        self.calendar.set_display_options(Gtk.CalendarDisplayOptions.SHOW_HEADING | 
                                          Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES)
        self.calendar.connect('day-selected', self.on_calendar_day_selected,parent)
        self.mth_hid = self.calendar.connect('month-changed',self.on_calendar_day_selected,parent)
        frame.add(self.calendar)
        self.pack_start(frame, False, False,0)
        
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button_press_event", lambda s,but: True)
        
        butbox = Gtk.HBox()
        
        adj = Gtk.Adjustment(value=1, lower=1, upper=10, step_increment=1, page_increment=5, page_size=0)
        self.spin = Gtk.SpinButton()
        self.spin.set_adjustment(adj)
        self.spin.set_wrap(True)
        self.spin.set_alignment(1.0)
        self.spin.set_size_request(40,-1)
        butbox.pack_start(self.spin,False,False,0)

        button = Gtk.Button() 
        button.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        arrow = Gtk.Arrow(arrow_type=Gtk.ArrowType.LEFT, shadow_type=Gtk.ShadowType.NONE)
        button.add(arrow)
        button.dir = '<'
        button.connect("button_press_event",self.on_panel_clicked,parent)
        button.connect("button_release_event",self.on_panel_clicked,parent)
        butbox.pack_start(button,False,False,0)
        
        self.combo = Gtk.ComboBoxText()
        self.combo.append_text(_("minutos"))
        self.combo.append_text(_("horas"))
        self.combo.append_text(_("dias"))
        self.combo.set_active(2)
        self.combo.set_size_request(70,-1)
        butbox.pack_start(self.combo,False,False,0) 
        
        button = Gtk.Button()
        button.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        arrow = Gtk.Arrow(arrow_type=Gtk.ArrowType.RIGHT, shadow_type=Gtk.ShadowType.NONE)
        button.add(arrow)
        button.dir = '>'
        button.connect("button_press_event",self.on_panel_clicked,parent)
        button.connect("button_release_event",self.on_panel_clicked,parent)
        butbox.pack_start(button,False,False,0)

        but = Gtk.Button()
        img = Gtk.Image()
        appath = boss.app.appath
        imgfile = path.joinpath(appath,"astronex/resources/refresh-18.png")
        img.set_from_file(str(imgfile))
        but.set_image(img)
        butbox.pack_start(but,False,False,0)
        but.connect('clicked',self.on_now_clicked)
        self.nowbut = but
        self.pack_start(butbox,False,False,0)
        # --- FORZAR ACTUALIZACIÓN AL INICIO ---
        from gi.repository import GLib
        # Esperamos 500ms para que el resto del programa cargue y luego "pulsamos" el botón
        GLib.timeout_add(500, lambda: self.on_now_clicked(None) or False)
    
    def on_calendar_day_selected(self,cal,parent):
        y,m,d = cal.get_date()
        time = self.time
        try:
            date = datetime.combine(datetime(y,m+1,d),time)
        except ValueError:
            try:
                date = datetime.combine(datetime(y,m+1,d-1),time) 
            except ValueError:
                date = datetime.combine(datetime(y,m+1,d-3),time) 
        curr.date.setdt(date) 
        curr.refresh_nowchart()
        boss.mpanel.act_now(curr.now)
        if parent.cycleselector:
            cycles = curr.curr_chart.get_cycles(date)
            parent.cycleselector.adj.set_value(cycles+1) 
        if self.internal_signal:
            boss.da.hsel.get_child().set_house_from_date(date)
        if self.needsredrawing:
            parent.redraw()
            parent = self.get_parent()
            if parent and hasattr(parent, 'redraw_auxwins'):
                parent.redraw_auxwins()
            else:
                # Si get_parent() no llega, intentamos acceder vía el objeto 'boss' 
                # si está disponible en ese ámbito
                try:
                    boss.redraw_auxwins()
                except:
                    pass
        else:
            self.needsredrawing = True
        self.internal_signal = True

    def on_panel_clicked(self,but,event,parent):
        delta = self.spin.get_value_as_int()        
        if getattr(but, 'dir', None) == '<':
            delta = -delta
        change = self.changes[self.combo.get_active()] 
        if event.type == Gdk.EventType.BUTTON_PRESS:
            self.timeout_sid = gobject.timeout_add(80,self.start_spining,delta,change)
        elif event.type == Gdk.EventType.BUTTON_RELEASE:
            GLib.source_remove(self.timeout_sid)

    def start_spining(self,delta,change):
        dt = self.set_delta((delta,change))
        self.set_date(dt,True)
        return True

    def on_now_clicked(self,but):
        self.set_date(datetime.now(),True)

    def update_cycles(self,delta):
        y,m,d = self.calendar.get_date()
        y = y + 72*delta
        self.set_date(datetime(y,m+1,d))

    def set_date(self,date,timechanged=False):
        if timechanged:
            self.time = date.time()
            self.internal_signal = True
        else:
            self.time = curr.date.ld.time() 
            self.internal_signal = False
        self.set_cal(date)

    def set_cal(self,date):
        self.calendar.handler_block(self.mth_hid)
        self.calendar.select_month(date.month - 1, date.year)
        self.calendar.handler_unblock(self.mth_hid)
        self.calendar.select_day(date.day)
        self.calendar.clear_marks()
        self.calendar.mark_day(date.day)
    
    def set_date_only(self,date):
        self.time = date.time()
        self.internal_signal = True
        self.set_cal(date)
        self.needsredrawing = False

    def set_delta(self,delta):
        amount = delta[0]
        what = delta[1]
        dt = datetime.combine(curr.date.ld.date(),curr.date.ld.time())
        if what == 'minutes':
            dt = dt + timedelta(minutes=amount)
        elif what == 'hours':
            dt = dt + timedelta(hours=amount)
        elif what == 'days':
            dt = dt + timedelta(days=amount)
        return dt

