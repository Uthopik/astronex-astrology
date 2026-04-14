# -*- coding: utf-8 -*-
from gi.repository import Gtk, Gdk
import cairo
from gi.repository import Pango
from copy import copy
from .. drawing.coredraw import CoreMixin
from .. drawing.dispatcher import DrawMixin, AspectManager
from .. drawing.roundedcharts import RadixChart 
from .mainnb import Slot
from .. utils import parsestrtime
from .mixer import MixerPanel
from .import_dlg import ImportPanel
from .couples import CouplesPanel
from .. extensions.path import path
from .searchview import SearchView

boss = None
curr = None
chart =  None
MainPanel = None

class ChartBrowserWindow(Gtk.Window):
    def __init__(self,parent):
        global boss, curr, chart, MainPanel
        boss = parent.boss
        curr = parent.boss.get_state()
        chart = curr.newchart()
        MainPanel = parent.mpanel.__class__
        Gtk.Window.__init__(self)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_transient_for(parent)
        #self.set_modal(True)
        self.set_destroy_with_parent(True)
        self.set_title(_("Explorador"))
        self.connect('destroy', self.cb_exit,parent)
        self.connect('focus-out-event', self.on_state)
        self.connect('configure-event', self.on_configure_event) 

        accel_group = Gtk.AccelGroup()
        accel_group.connect(Gdk.KEY_Escape, 0, Gtk.AccelFlags.LOCKED, self.escape)
        self.add_accel_group(accel_group) 
        
        self.nb = Gtk.Notebook()
        self.nb.set_tab_pos(Gtk.PositionType.LEFT)
        self.nb.connect('switch-page', self.page_select)

        label = Gtk.Label(_("Explorador"))
        label.set_angle(90)
        self.nb.append_page(BrowserPanel(parent), label)
        
        label = Gtk.Label(_("Mezclador"))
        label.set_angle(90)
        self.nb.append_page(MixerPanel(parent),label)

        label = Gtk.Label(_("Importacion AAF"))
        label.set_angle(90)
        self.nb.append_page(ImportPanel(parent),label)

        label = Gtk.Label(_("Parejas"))
        label.set_angle(90)
        self.nb.append_page(CouplesPanel(parent),label)
        
        self.add(self.nb)
        self.set_default_size(650,400)
        self.show_all()
        self.pos_x, self.pos_y = self.get_position()

    def on_configure_event(self,widget,event):
        self.pos_x = event.x
        self.pos_y = event.y

    def page_select(self,nb,page,pnum): 
        page = nb.get_nth_page(pnum)
        try:
            if pnum == 0 and nb.get_nth_page(1).changes:
                page.relist()
        except AttributeError:
            pass 
        if page.__class__ == CouplesPanel:
            page.save_couples()
        title = nb.get_tab_label(page).get_text()
        self.set_title(title)

    def escape(self,a,b,c,d):
        self.destroy() 

    def on_state(self, e, event):
        # Eliminamos el parche. Si self.nb no existe o la página 1 es None, 
        # el Traceback saltará y sabremos por qué.
        page_mezclador = self.nb.get_nth_page(1)
        if page_mezclador.changes:
            boss.mpanel.browser.tables.emit('changed')
            boss.mpanel.browser.relist('')

    def cb_exit(self,e,parent):
        parent.browser = None
        if self.nb.get_nth_page(1).changes:
            boss.mpanel.browser.tables.emit('changed')
            boss.mpanel.browser.relist('')
        self.nb.get_nth_page(3).save_couples()
        return False


class BrowserPanel(Gtk.Box): 
    def __init__(self,parent):
        # Aseguramos orientación horizontal para el Box principal
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        self.chartview = None
        # Quitamos hbox innecesario, self ya es un Box
        
        # --- COLUMNA IZQUIERDA (Selectores y Lista) ---
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Selector de Tablas (HBox superior)
        liststore = Gtk.ListStore(str)
        self.tables = Gtk.ComboBox.new_with_model_and_entry(liststore)
        self.tables.set_entry_text_column(0)
        
        # Limitamos el ancho pero dejamos que la altura sea la mínima necesaria
        self.tables.set_size_request(200, -1)
        self.tables.get_child().set_editable(False)
        
        self.tables.connect('changed', self.on_tables_changed)
        tablelist = curr.datab.get_databases()
        for c in tablelist:
            liststore.append([c])
        
        # Lógica de selección de índice
        index = 0
        try:
            target_table = curr.datab.table
            for i, r in enumerate(liststore):
                if r[0] == target_table:
                    index = i
                    break
        except:
            index = 0
        self.tables.set_active(index)

        # Botón Refresh
        but = Gtk.Button()
        img = Gtk.Image()
        appath = boss.app.appath
        imgfile = path.joinpath(appath, "astronex/resources/refresh-18.png")
        img.set_from_file(str(imgfile))
        but.set_image(img)
        but.connect('clicked', self.on_refresh_clicked, self.tables)

        # Empaquetamos el combo y el botón en un HBox
        hhbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        hhbox.pack_start(self.tables, True, True, 0) # El combo se expande horizontalmente
        hhbox.pack_start(but, False, False, 0)
        
        # IMPORTANTE: El hhbox NO debe expandirse verticalmente (False)
        vbox.pack_start(hhbox, False, False, 5)
        
        # 2. Lista de Cartas (TreeView + ScrolledWindow)
        self.chartmodel = Gtk.ListStore(str, int)
        self.chartview = SearchView(self.chartmodel)
        
        # ... (restante configuración del chartview igual) ...
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, cell, text=0)
        self.chartview.append_column(column) 
        self.chartview.set_headers_visible(False)
        self.chartview.connect('row_activated', self.on_chart_activated)
        sel = self.chartview.get_selection()
        sel.set_mode(Gtk.SelectionMode.SINGLE)
        sel.connect('changed', self.on_sel_changed)
        
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC) # Evitamos scroll horizontal
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.add(self.chartview) 
        
        # CLAVE: El sw SI debe expandirse verticalmente (True, True)
        vbox.pack_start(sw, True, True, 0)
        
        # --- COLUMNA DERECHA (Dibujo) ---
        self.chsnap = ChartSnapshot(parent.boss)
        self.chsnap.set_size_request(400, 400) 

        # Empaquetamos todo en el self (que es el Box principal)
        self.pack_start(vbox, False, False, 5) # La lista tiene ancho fijo (vbox)
        self.pack_start(Gtk.VSeparator(), False, False, 0)
        self.pack_start(self.chsnap, True, True, 0) # El dibujo ocupa el resto
        
        self.show_all()

    def on_refresh_clicked(self,but,combo):
        combo.emit('changed')
    
    def findchart(self,first,last):
        model = self.chartview.get_model()
        iter = model.get_iter_root()
        while iter:
            tfirst,__,tlast = model.get_value(iter,0).partition(',')
            if first == tfirst and last == tlast:
                self.chartview.get_selection().select_path(model.get_path(iter)) 
                break
            iter = model.iter_next(iter)

    def on_tables_changed(self,combo): 
        if combo.get_active() == -1: return
        if not self.chartview is None:
            chartmodel = Gtk.ListStore(str,int)
            tree_iter = combo.get_active_iter()
            if tree_iter is not None:
                model = combo.get_model()
                # Obtenemos el valor de la columna 0 (donde está el nombre de la tabla)
                table_name = model[tree_iter][0]
                chartlist = curr.datab.get_chartlist(table_name)
            for c in chartlist:
                glue = ", "
                if c[2] == '':  glue = ''
                chartmodel.append([c[2]+glue+c[1] , int(c[0]) ])
            self.chartview.set_model(chartmodel)
            self.chartview.get_selection().select_path(0,)
    
    def on_sel_changed(self,sel):
        model, iter = sel.get_selected()
        if not iter:
            sel.select_path(0,)
            model, iter = sel.get_selected()
        id = model.get_value(iter,1)
        table = self.tables.get_child().get_text()
        curr.datab.load_chart(table,id,chart)
        try:
            self.chsnap.redraw()
        except AttributeError:
            pass

    def on_chart_activated(self,view,path,col):
        model,iter = view.get_selection().get_selected()
        id = model.get_value(iter,1)
        chart = curr.charts[Slot.storage]
        table = self.tables.get_active_text()
        curr.datab.load_chart(table,id,chart)
        curr.add_to_pool(copy(chart),Slot.overwrite)
        MainPanel.actualize_pool(Slot.storage,chart) 

    def relist(self):
        liststore = Gtk.ListStore(str)
        tablelist = curr.datab.get_databases() 
        for c in tablelist:
            liststore.append([c])
        self.tables.set_model(liststore)


class ChartSnapshot(Gtk.DrawingArea):
    def __init__(self, boss):
        self.boss = boss
        self.opts = boss.opts
        Gtk.DrawingArea.__init__(self)
        # GTK3 usa 'draw' en lugar de 'expose_event'
        self.connect("draw", self.dispatch)
        self.drawer = SnapMixin(boss.opts, self) 

    def dispatch(self, da, cr):
        # En GTK3, 'cr' ya es el contexto Cairo. No hace falta cairo_create()
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        
        # Fondo
        cr.set_source_rgb(1.0, 1.0, 0.95)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        
        cr.set_line_join(cairo.LINE_JOIN_ROUND) 
        cr.set_line_width(float(self.opts.base))
        
        chartobject = RadixChart(chart, None)
        self.drawer.draw_nat(cr, w, h, chartobject)
        self.d_label(cr, w, h, chart)
        return True

    def redraw(self): 
        # En GTK3 se usa queue_draw() para refrescar el área de dibujo
        self.queue_draw()

    def d_label(self, cr, w, h, chart):
        cr.identity_matrix()
        # Pango en GTK3 se usa mediante PangoCairo
        import gi
        gi.require_version('PangoCairo', '1.0')
        from gi.repository import PangoCairo
        
        font = Pango.FontDescription(self.opts.font)
        font.set_size(7 * Pango.SCALE)
        
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(font)
        
        date, time = parsestrtime(chart.date)
        date = date + " - " + time.split(" ")[0]
        name = chart.first + " " + chart.last
        layout.set_text('%s  (%s)' % (name, date), -1)
        
        logical = layout.get_pixel_extents()[1]
        xpos = logical.width
        cr.set_source_rgb(0.0, 0, 0.5)
        cr.move_to(w - xpos - 5, h - 12)
        PangoCairo.show_layout(cr, layout)

R_ASP = 0.435
class SnapMixin(CoreMixin):
    def __init__(self,opts,surface):
        self.opts = opts
        self.surface = surface
        self.aspmanager = AspectManager(boss,self.get_gw,self.get_uni,self.get_nw, DrawMixin.planetmanager,opts.zodiac.aspcolors,opts.base)
        CoreMixin.__init__(self,opts.zodiac,surface)
    
    def draw_nat(self,cr,width,height,chartob):
        cx,cy = width/2,height/2
        radius = min(cx,cy)
        cr.translate(cx,cy)

        self.d_radial_lines(cr,radius,chartob)
        self.make_all_rulers(cr,radius,chartob)
        self.draw_signs(cr,radius,chartob)
        self.draw_planets(cr,radius,chartob)
        self.make_plines(cr,radius,chartob,'EXT')
        self.draw_cusps(cr,radius,chartob)
        self.d_year_lines(cr,radius,chartob)
        self.d_golden_points(cr,radius,chartob)
        self.d_cross_points(cr,radius,chartob)
        self.aspmanager.manage_aspects(cr,radius*R_ASP,chartob.get_planets())
        self.make_plines(cr,radius,chartob,'INN')
        self.d_inner_circles(cr,radius)

    def get_gw(self):
        return False

    def get_uni(self):
        return True

    def get_nw(self,f=None):
        return []
