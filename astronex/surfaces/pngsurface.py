# -*- coding: utf-8 -*-
import os
from ..nex import t
import sys
from gi.repository import Gtk
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
import PIL.Image
import PIL.ImageOps
from .. drawing.dispatcher import DrawMixin
from .. utils import parsestrtime
from .. boss import boss
curr = boss.get_state()
opts = None
minim = None
MAGICK_SCALE = 0.002

suffixes = boss.suffixes

class ImageExportDialog(Gtk.Dialog):
    '''Save image config dialog'''

    def __init__(self, pg=False):
        Gtk.Dialog.__init__(self, 
            title=_("Exportar como imagen"), 
            parent=None, 
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            buttons=(
                "_Cancelar", Gtk.ResponseType.CANCEL,
                "_Guardar", Gtk.ResponseType.OK
            )
        )

        # En GTK3 usamos el área de contenido del diálogo
        content_area = self.get_content_area()
        content_area.set_border_width(3)
        content_area.set_spacing(6)
        
        # Añadir controles personalizados (make_control debe estar actualizado a GTK3)
        content_area.pack_start(self.make_control(), False, False, 0)
        
        # Separador horizontal moderno
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_area.pack_start(separator, False, False, 0)
        
        # Widget del selector de archivos
        chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SAVE)
        content_area.pack_start(chooser, True, True, 0)
        self.chooser = chooser
        self.chooser.set_size_request(600, 400)
        
        self.set_default_response(Gtk.ResponseType.OK)
        
        # Configuración del filtro de imagen
        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("Imagen"))
        file_filter.add_mime_type("image/png")
        file_filter.add_mime_type("image/jpeg")
        self.chooser.add_filter(file_filter)
        
        # Generación del nombre del archivo usando f-strings de Python 3
        if pg:
            name = f"{curr.curr_chart.first}_{curr.curr_chart.last}_pg"
        else:
            name = f"{curr.curr_chart.first}_{suffixes[curr.curr_op]}"

        # Obtener extensión y establecer nombre por defecto
        tree_iter = self.typefile_chooser.get_active_iter()
        # Sacamos el texto de la primera columna (índice 0)
        ext = self.typefile_chooser.get_model().get_value(tree_iter, 0)
        self.chooser.set_current_name(f"{name}.{ext}")
        
        # Definición de carpeta inicial por plataforma
        if sys.platform == 'win32':
            import winshell
            self.chooser.set_current_folder(winshell.my_documents())
        else: 
            self.chooser.set_current_folder(os.path.expanduser("~"))
            
        self.chooser.set_do_overwrite_confirmation(True)
        self.show_all()

    def make_control(self):
        # En GTK3 usamos Gtk.Grid en lugar de Gtk.Table
        tab = Gtk.Grid()
        tab.set_row_spacing(6)
        tab.set_column_spacing(12)
        tab.set_row_homogeneous(False)
        tab.set_border_width(6)
        
        # --- Lado Izquierdo (Anchura) ---
        # HButtonBox -> ButtonBox con orientación horizontal
        buttbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        buttbox.set_layout(Gtk.ButtonBoxStyle.EDGE) 
        label = Gtk.Label(label=_("Anchura"))
        buttbox.pack_start(label, False, False, 0)
        
        # boss debe ser accesible (usualmente self.boss)
        adj = Gtk.Adjustment(value=int(boss.opts.hsize), lower=1, upper=10000, 
                             step_increment=1, page_increment=1, page_size=1)
        hdim = Gtk.SpinButton(adjustment=adj)
        hdim.set_alignment(1.0)
        hdim.set_numeric(True)
        lbl = 'hsize'
        adj.connect('value-changed', self.spin_imgsize, hdim, lbl)
        hdim.connect('changed', self.entry_imgsize, lbl)
        buttbox.pack_start(hdim, False, False, 0)
        # Grid.attach(widget, columna, fila, ancho_celdas, alto_celdas)
        tab.attach(buttbox, 0, 0, 1, 1)
        
        # --- Lado Izquierdo (Altura) ---
        buttbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        buttbox.set_layout(Gtk.ButtonBoxStyle.EDGE) 
        label = Gtk.Label(label=_("Altura"))
        buttbox.pack_start(label, False, False, 0)
        adj = Gtk.Adjustment(value=int(boss.opts.vsize), lower=1, upper=10000, 
                             step_increment=1, page_increment=1, page_size=1)
        vdim = Gtk.SpinButton(adjustment=adj)
        vdim.set_alignment(1.0)
        vdim.set_numeric(True)
        lbl = 'vsize'
        adj.connect('value-changed', self.spin_imgsize, vdim, lbl)
        vdim.connect('changed', self.entry_imgsize, lbl)
        buttbox.pack_start(vdim, False, False, 0)
        tab.attach(buttbox, 0, 1, 1, 1)
        
        # --- Lado Derecho (Resolución) ---
        buttbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        buttbox.set_layout(Gtk.ButtonBoxStyle.EDGE) 
        label = Gtk.Label(label=_("Resolucion"))
        buttbox.pack_start(label, False, False, 0)
        adj = Gtk.Adjustment(value=int(boss.opts.resolution), lower=1, upper=600, 
                             step_increment=1, page_increment=1, page_size=1)
        res = Gtk.SpinButton(adjustment=adj)
        res.set_alignment(1.0)
        res.set_numeric(True)
        adj.connect('value-changed', self.spin_change_res, res)
        res.connect('changed', self.entry_change_res)
        buttbox.pack_start(res, False, False, 0)
        tab.attach(buttbox, 1, 0, 1, 1)
    
        # --- Lado Derecho (Tipo de archivo) ---
        buttbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        buttbox.set_layout(Gtk.ButtonBoxStyle.EDGE) 
        label = Gtk.Label(label=_("Tipo"))
        buttbox.pack_start(label, False, False, 0)
        
        store = Gtk.ListStore(str)
        store.append([_('png')])
        store.append([_('jpg')])
        
        # En GTK3 es mejor usar ComboBoxText si solo es texto, 
        # pero mantenemos ComboBox con ListStore por compatibilidad con tu código
        combo = Gtk.ComboBox(model=store)
        cell = Gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 0)
        combo.set_active(0)
        combo.connect("changed", self.typefile_changed)
        self.typefile_chooser = combo
        
        buttbox.pack_start(combo, False, False, 0)
        tab.attach(buttbox, 1, 1, 1, 1)
        
        tab.show_all()
        return tab
    
    def typefile_changed(self, combo):
        # Obtenemos el iterador de la fila seleccionada
        tree_iter = combo.get_active_iter()
        
        if tree_iter is not None:
            # Extraemos el texto ('png' o 'jpg') del modelo
            model = combo.get_model()
            ext = model.get_value(tree_iter, 0)
            
            # Obtenemos el nombre actual que haya en el selector
            filename = self.chooser.get_filename()
            if filename:
                base = os.path.basename(filename)
                root, oldext = os.path.splitext(base)
                # Actualizamos el nombre con la nueva extensión
                self.chooser.set_current_name(root + "." + ext)

    def spin_imgsize(self,adj,spin,lbl):
        opt = spin.get_value_as_int() 
        setattr(boss.opts,lbl,opt)

    def entry_imgsize(self,spin,lbl):
        try:
            opt = int(spin.get_text())
        except ValueError:
            return
        setattr(boss.opts,lbl,opt)

    def spin_change_res(self,adj,spin):
        opt = spin.get_value_as_int() 
        boss.opts.resolution = opt
    
    def entry_change_res(self,spin):
        try:
            opt = int(spin.get_text())
        except ValueError:
            return
        boss.opts.resolution = opt

class DrawPng(object):
    @staticmethod
    def clicked(boss):
        global opts, minim
        opts = boss.opts

        dialog = ImageExportDialog()

        filename = None
        response = dialog.run()
    
        if response == Gtk.ResponseType.OK:
            filename = dialog.chooser.get_filename()
            dialog.destroy()
            # No hace falta llamar a save_to_png porque el código sigue aquí abajo
    
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        
        else:
            dialog.destroy()
            return

        if filename is None or filename == '': 
            return

        w = int(opts.hsize)
        h = int(opts.vsize)
    
        if curr.curr_op in ['compo_one', 'compo_two']:
            w = 800
            h = 1100
        
        minim = min(w, h)
    
        # Crear la superficie de Cairo
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surface) 
    
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()
    
        # En GTK3 los Enums cambian de nombre
        cr.set_line_join(cairo.LineJoin.ROUND) 
        cr.set_line_width(float(opts.base))
    
        # Dibujar la carta
        dr = DrawMixin(opts, DrawPng())
        dr.dispatch_pres(cr, w, h)
    
        if opts.labels == 'true' or curr.curr_op in ['compo_one', 'compo_two']:
            draw_label(cr, w, h)
    
        # --- PROCESAMIENTO DE IMAGEN PARA PYTHON 3 ---
        # Convertimos el buffer de la superficie a bytes
        d = bytes(surface.get_data())
    
        # Cargamos en PIL. Usamos "BGRA" porque es el formato nativo de Cairo
        im = PIL.Image.frombuffer("RGBA", (surface.get_width(), surface.get_height()), d, "raw", "BGRA", 0, 1)
    
        res = int(opts.resolution)
    
        # Si es JPEG, quitamos el canal Alfa (transparencia) para evitar errores
        if filename.lower().endswith(('.jpg', '.jpeg')):
            im = im.convert("RGB")
        
        im.save(filename, dpi=(res, res))

        # Abrir el visor
        if sys.platform == 'win32':
            os.startfile(filename) 
        else: 
            # Asegúrate de que 'pngviewer' esté configurado (ej: 'xdg-open' o 'eog')
            os.system("%s '%s' &" % (opts.pngviewer, filename))

    @staticmethod
    def simple_batch(table="plagram"):
        global opts
        opts = boss.opts
        w = 1280 
        h = 1020
        if sys.platform == 'win32':
            import winshell
            folder = winshell.my_documents()
        else: 
            folder = os.path.expanduser("~")
        curr.curr_op = "draw_planetogram"
        chlist = curr.datab.get_chartlist(table)
        chart = curr.curr_chart
        
        for id, name,sur in chlist:
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h)
            cr = PangoCairo.CairoContext(cairo.Context(surface))
            cr.set_source_rgb(1.0,1.0,1.0)
            cr.rectangle(0,0,w,h)
            cr.fill()
            cr.set_line_join(cairo.LINE_JOIN_ROUND) 
            cr.set_line_width(float(opts.base))
            dr = DrawMixin(opts,DrawPng())
            curr.datab.load_chart(table,id,chart)
            dr.dispatch_pres(cr,w,h)
            wname = "_".join([name,sur,"pg"])
            filename = ".".join([wname,'png'])
            filename = os.path.join(folder,filename)
            #d_name(cr,w,h)
            surface.write_to_png(filename) 

#im.save("itest.jpg", dpi=im.info['dpi'])
#im.save("itest.tiff", dpi=im.info['dpi'])


def draw_label(cr,w,h): 
    cr.identity_matrix() 
    clickops = ['click_hh','click_nn','click_bridge','click_nh','click_rr',
            'click_ss','click_rs','click_sn','ascent_star','wundersensi_star',
            'polar_star','paarwabe_plot','crown_comp',
            'dyn_cuad2','click_hn','subject_click'] 
    sheetopts = ['dat_nat', 'dat_nod', 'dat_house', 'prog_nat', 'prog_nod', 
            'prog_local', 'prog_soul' ]

    if curr.curr_op in clickops or (curr.clickmode == 'click' and curr.opmode != 'simple'): 
        d_name(cr,w,h,kind='click')
    elif curr.curr_op in ['compo_one','compo_two']:
        compo_name(cr,w,h)
    elif curr.curr_op not in sheetopts:
        d_name(cr,w,h)

def compo_name(cr, w, h):
    # En GTK3/Python3 el contexto de Cairo ya no crea layouts directamente
    layout = PangoCairo.create_layout(cr)
    
    font = Pango.FontDescription(opts.font)
    # Pango.SCALE y MAGICK_SCALE deben estar definidos globalmente
    font.set_size(int(7 * Pango.SCALE * minim * 0.9 * MAGICK_SCALE))
    layout.set_font_description(font)
    
    h *= 0.995
    mastcol = (0.8, 0, 0.1)
    clickcol = (0, 0, 0.4)    
    
    # Usamos f-strings (opcional pero recomendado en Py3)
    mastname = f"{curr.curr_chart.first} {curr.curr_chart.last}"
    clickname = f"{curr.curr_click.first} {curr.curr_click.last}"
    
    # --- Dibujar Nombre Secundario (Click) ---
    cr.set_source_rgb(*mastcol)
    layout.set_alignment(Pango.Alignment.RIGHT) # Corregido Enum
    layout.set_text(clickname, -1)
    
    ink, logical = layout.get_extents()
    # Usamos .width y .height en lugar de índices [2] y [3]
    xpos = logical.width / Pango.SCALE
    ypos = logical.height / Pango.SCALE
    
    cr.move_to(w - xpos - 30, h - ypos)
    PangoCairo.show_layout(cr, layout) # Corregido método de dibujo
    
    # --- Dibujar Nombre Principal (Master) ---
    cr.set_source_rgb(*clickcol)
    layout.set_alignment(Pango.Alignment.LEFT) # Corregido Enum
    layout.set_text(mastname, -1) 
    
    # Recalculamos extents para el nuevo texto
    ink, logical = layout.get_extents()
    ypos = logical.height / Pango.SCALE
    
    cr.move_to(30, h - ypos)
    PangoCairo.show_layout(cr, layout)

def d_name(cr, w, h, kind='radix'):
    # En GTK3 usamos PangoCairo para crear el layout
    layout = PangoCairo.create_layout(cr)
    font = Pango.FontDescription(opts.font)
    font.set_size(int(6 * Pango.SCALE * minim * MAGICK_SCALE))
    layout.set_font_description(font)
    h *= 0.995
    
    mastcol = (0, 0, 0.4)
    clickcol = (0.8, 0, 0.1)
    mastname = f"{curr.curr_chart.first} {curr.curr_chart.last}"
    clickname = f"{curr.curr_click.first} {curr.curr_click.last}"
    
    if kind == "click":
        mastcol, clickcol = clickcol, mastcol
        mastname, clickname = clickname, mastname
        date, time = parsestrtime(curr.curr_click.date)
        date = date + " " + time.split(" ")[0]
        geodat = curr.format_longitud(kind='click') + " " + curr.format_latitud(kind='click')
        # Corregido el acceso a la traducción t()
        loc = curr.curr_click.city + " (" + t(curr.curr_chart.country)[0] + ") "
        text = "\n" + date + "\n" + loc + geodat
    else:
        date, time = parsestrtime(curr.curr_chart.date)
        date = date + " " + time.split(" ")[0]
        geodat = curr.format_longitud() + " " + curr.format_latitud()
        loc = curr.curr_chart.city + " (" + t(curr.curr_chart.country)[0] + ") "
        text = "\n" + date + "\n" + loc + geodat

    cr.set_source_rgb(*mastcol)
    
    # Ajustes de Pango para GTK3
    layout.set_alignment(Pango.Alignment.RIGHT) 
    layout.set_text(mastname + text, -1)
    
    ink, logical = layout.get_extents()
    # Cambio de índices [2], [3] por atributos .width, .height
    xpos = logical.width / Pango.SCALE
    ypos = logical.height / Pango.SCALE
    
    cr.move_to(w - xpos - 5, h - ypos)
    PangoCairo.show_layout(cr, layout)

    if kind == 'click':
        cr.set_source_rgb(*clickcol)
        layout.set_alignment(Pango.Alignment.LEFT) 
        date, time = parsestrtime(curr.curr_chart.date)
        date = date + " " + time.split(" ")[0]
        geodat = curr.format_longitud() + " " + curr.format_latitud()
        loc = curr.curr_chart.city + " (" + t(curr.curr_chart.country)[0] + ") "
        text = "\n" + date + "\n" + loc + geodat
        layout.set_text(clickname + text, -1)
        
        # Recalculamos el alto para el segundo bloque de texto
        ink, logical = layout.get_extents()
        ypos = logical.height / Pango.SCALE
        cr.move_to(0 + 5, h - ypos)
        PangoCairo.show_layout(cr, layout)
