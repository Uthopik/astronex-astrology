# -*- coding: utf-8 -*-
import sys,os
from .. extensions.path import path
from gi.repository import Gtk, Gdk, GObject, GdkPixbuf
from .. surfaces.layoutsurface import DrawMaster
from .. surfaces.pngsurface import DrawPng
from .. surfaces.pdfsurface import DrawPdf
#from .. surfaces import printsurface
from .mainnb import MainPanel
from .config_dlg import ConfigDlg
from .customloc_dlg import CustomLocDlg
from .chartbrowser import ChartBrowserWindow
from .plagram_dlg import PlagramWindow
from .entry_dlg import EntryDlg
from .localsel import LocSelector
from .aux_dlg import AuxWindow
from .shell_dlg import ShellDialog
from .quickhelp import HelpWindow
from .inieditor import IniEditor

class WinNex(Gtk.Window):

    def __init__(self,manager):
        Gtk.Window.__init__(self)
        self.boss = manager
        appath = self.boss.app.appath
        appath = path.joinpath(appath,"astronex")
        self.entry = None
        self.locsel = None
        self.locselflag = False
        self.browser = None
        self.plagram = None
        self.set_title("Astro-Nex")
        self.connect('destroy', self.cb_exit)
        self.connect('key-press-event', self.on_key_press_event)
        self.connect('scroll-event', self.on_mouse_scroll)
        #self.da.add_events(Gdk.EventMask.SCROLL_MASK)
        #self.da.connect('scroll-event', self.on_mouse_scroll)
        self.connect('configure-event', self.on_configure_event) 

        accel_group = Gtk.AccelGroup()
        #accel_group.connect_group(ord('u'),Gtk.gdk.CONTROL_MASK,Gtk.ACCEL_LOCKED,self.printpage_cb)
        accel_group.connect(ord('j'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE, self.swap_to_ten)
        accel_group.connect(ord('u'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE, self.swap_to_twelve)
        accel_group.connect(ord('e'), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE, self.entry_calc)
        accel_group.connect(ord('n'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.locselector)
        accel_group.connect(ord('l'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.customloc_cb)
        accel_group.connect(ord('b'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_chartbrowser)
        accel_group.connect(ord('w'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_aux)
        accel_group.connect(ord('e'), Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE, self.launch_plagram) 
        accel_group.connect(ord('r'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_pebridge)
        accel_group.connect(ord('k'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_shell)
        accel_group.connect(ord('i'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_editor)
        accel_group.connect(ord('o'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.toggle_overlay)
        accel_group.connect(ord('c'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_calendar)
        accel_group.connect(ord('a'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.show_pe)
        accel_group.connect(ord('h'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_selector)
        accel_group.connect(ord('y'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.launch_cycles)
        accel_group.connect(ord('d'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.show_diada)
        accel_group.connect(ord('x'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.swap_slot)
        accel_group.connect(ord('z'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.swap_storage)
        accel_group.connect(ord('u'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.load_couple)
        accel_group.connect(ord('1'), Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE, self.load_one_fav)

        # Atajos con teclas de Función (F2, F3...) y especiales
        accel_group.connect(Gdk.KEY_F2, 0, Gtk.AccelFlags.VISIBLE, self.fake_modify_chart)
        accel_group.connect(Gdk.KEY_F3, 0, Gtk.AccelFlags.VISIBLE, self.fake_click_clock)
        accel_group.connect(Gdk.KEY_F4, 0, Gtk.AccelFlags.VISIBLE, self.launch_calendar)
        accel_group.connect(Gdk.KEY_F5, 0, Gtk.AccelFlags.VISIBLE, self.set_now)
        accel_group.connect(Gdk.KEY_F6, 0, Gtk.AccelFlags.VISIBLE, self.show_pe)
        accel_group.connect(Gdk.KEY_plus, 0, Gtk.AccelFlags.VISIBLE, self.house_change)
        accel_group.connect(Gdk.KEY_minus, 0, Gtk.AccelFlags.VISIBLE, self.house_change)
        accel_group.connect(Gdk.KEY_Left, Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE, self.view_change)
        accel_group.connect(Gdk.KEY_Right, Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE, self.view_change)
        accel_group.connect(Gdk.KEY_Page_Up, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.fake_scroll_up)
        accel_group.connect(Gdk.KEY_Page_Down, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.fake_scroll_down)
        accel_group.connect(Gdk.KEY_Menu, 0, Gtk.AccelFlags.VISIBLE, self.popup_menu)
        #accel_group.connect(Gdk.KEY_Up, 0, Gtk.AccelFlags.VISIBLE, self.view_change)
        #accel_group.connect(Gdk.KEY_Down, 0, Gtk.AccelFlags.VISIBLE, self.view_change)

        # Bucles para el teclado numérico (KP)
        for i in range(0, 10):
            ksym = getattr(Gdk, "KEY_KP_%s" % str(i))
            accel_group.connect(ksym, 0, Gtk.AccelFlags.VISIBLE, self.page_select)
            accel_group.connect(ksym, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, self.op_select)

        for i in ('Add', 'Subtract'):
            ksym = getattr(Gdk, "KEY_KP_%s" % str(i))
            accel_group.connect(ksym, 0, Gtk.AccelFlags.VISIBLE, self.scroll_pool)

        self.add_accel_group(accel_group)

        # El contenedor principal sigue después
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.add(hbox)
        
        ### toolbar
        self.tb = Gtk.Toolbar()
        self.tb.set_size_request(300,-1)
        #self.tb.set_tooltips(True)
        self.tb.set_style(Gtk.ToolbarStyle.ICONS)
        
        ti = Gtk.ToolButton()
        ti.connect('clicked',self.cb_exit)
        img = Gtk.Image()
        imgfile = path.joinpath(appath,"resources/gtk-quit-32.png")
        img.set_from_file(str(imgfile))
        ti.set_icon_widget(img)
        ti.add_accelerator('clicked', accel_group, ord('q'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        ti.set_tooltip_text(_("Salir"))
        self.tb.insert(ti,0)
        
        #if 'DEBUG_NEX' in os.environ and sys.platform != 'win32': 
        #    tkon = Gtk.ToolButton()
        #    img = Gtk.Image()
        #    imgfile = os.path.join(appath,"resources/konsole-24.png")
        #    img.set_from_file(imgfile)
        #    tkon.set_icon_widget(img)
        #    tkon.connect('clicked',self.on_kon_clicked)
        #    tkon.set_tooltip_text(_("Terminal"))
        #    self.tb.insert(tkon,-1) 

        tfull = Gtk.ToolButton()
        img = Gtk.Image()
        imgfile = os.path.join(appath,"resources/fullscreen-32.png")
        img.set_from_file(imgfile)
        tfull.set_icon_widget(img)
        tfull.connect('clicked',self.on_fullscreen_clicked)
        tfull.toggled = True
        tfull.set_tooltip_text(_("Pantalla completa"))
        self.tb.insert(tfull,-1) 
        self.add_mnemonic(Gdk.KEY_F11, tfull)

        timg = Gtk.ToolButton()
        img = Gtk.Image()
        imgfile = os.path.join(appath,"resources/gnome-image-32.png")
        img.set_from_file(imgfile)
        timg.set_icon_widget(img)
        timg.connect('clicked',self.on_png_clicked)
        timg.add_accelerator('clicked', accel_group, ord('g'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        timg.set_tooltip_text(_("Exportar a imagen"))
        self.tb.insert(timg,-1) 

        tpdf = Gtk.ToolButton()
        img = Gtk.Image()
        imgfile = os.path.join(appath,"resources/x-pdf-32.png")
        img.set_from_file(imgfile)
        tpdf.set_icon_widget(img)
        tpdf.connect('clicked',self.on_pdf_clicked)
        tpdf.add_accelerator('clicked', accel_group, ord('p'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        tpdf.set_tooltip_text(_("Exportar a PDF/Imprimir"))
        self.tb.insert(tpdf,-1) 

        tentry = Gtk.ToolButton()
        img = Gtk.Image()
        imgfile = os.path.join(appath,"resources/gtk-compose-32.png")
        img.set_from_file(imgfile)
        tentry.set_icon_widget(img)
        tentry.connect('clicked',self.on_entry_clicked)
        tentry.add_accelerator('clicked', accel_group, ord('e'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        tentry.set_tooltip_text(_("TEntradas"))
        self.tentry = tentry
        self.tb.insert(tentry,-1) 
        
        thelp = Gtk.ToolButton()
        img = Gtk.Image()
        imgfile = os.path.join(appath,"resources/gtk-properties-32.png")
        img.set_from_file(imgfile)
        thelp.set_icon_widget(img)
        thelp.connect('clicked',self.on_props_clicked)
        thelp.add_accelerator('clicked', accel_group, ord('s'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        thelp.set_tooltip_text(_("TConfiguracion"))
        self.tb.insert(thelp,-1) 
        
        tabout = Gtk.ToolButton()
        img = Gtk.Image()
        imgfile = os.path.join(appath,"resources/stock_about.png")
        img.set_from_file(imgfile)
        tabout.set_icon_widget(img)
        tabout.connect('clicked',self.on_about_clicked,appath)
        tabout.set_tooltip_text(_("Acerca de Astro-Nex"))
        self.tb.insert(tabout,-1) 

        self.mpanel = MainPanel(self.boss)

        vbox = Gtk.VBox()
        vbox.pack_start(self.tb,False,False, 0)
        vbox.pack_start(self.mpanel,True,True, 0)

        hbox.pack_start(vbox,False,False, 0)
        self.da = DrawMaster(self.boss)
        self.da.add_events(Gdk.EventMask.SCROLL_MASK)
        self.da.connect('scroll-event', self.on_mouse_scroll)
        self.da.set_can_focus(True)
        screen = Gdk.Screen.get_default()
        scr_width = screen.get_width()
        scr_height = screen.get_height()
        if scr_width >= 1280:
            self.da.set_size_request(660,660)
        else:
            self.da.set_size_request(500,500)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add_with_viewport(self.da)
        scrolled.set_shadow_type(Gtk.ShadowType.NONE)
        hbox.pack_start(scrolled, True, True, 0)
        self.da.ha = scrolled.get_hadjustment()
        self.da.va = scrolled.get_vadjustment()

        imgfile = path.joinpath(appath,"resources/iconex-22.png")
        self.set_icon_from_file(str(imgfile))
        screen = Gdk.Screen.get_default()
        scr_width = screen.get_width()
        scr_height = screen.get_height()
        #if scr_width >= 1280:
        #    scr_width *= 0.9
        #if scr_height >= 768:
        #    scr_height *= 0.79
        self.set_default_size(int(scr_width), int(scr_height))
        self.scr_width = scr_width
        self.show_all()
        wpos = self.get_position()
        self.pos_x = wpos[0]
        self.pos_y = wpos[1]

    def on_configure_event(self,widget,event):
        self.pos_x = event.x
        self.pos_y = event.y

    def on_key_press_event(self,window,event): 
        if event.keyval == Gdk.KEY_F11 or (event.keyval == Gdk.KEY_Escape and self.da.__class__.fullscreen):
            self.tb.get_nth_item(1).emit('clicked')
        elif event.keyval == Gdk.KEY_F1:
            self.show_help()
        return False
    
    def activate_entry(self):
        self.tentry.emit('clicked')
    
    def cb_exit(self,e):
        Gtk.main_quit()

    def on_pdf_clicked(self,but):
        DrawPdf.clicked(self.boss)
    
    def on_png_clicked(self,but):
        DrawPng.clicked(self.boss)
    
    def on_props_clicked(self,but):
        ConfigDlg(self)
    
    def on_entry_clicked(self,but):
        if not self.entry:
            self.entry = EntryDlg(self) 

    def entry_calc(self,a,b,c,d):
        if not self.entry:
            self.entry = EntryDlg(self) 
            self.entry.modify_entries(self.boss.state.calc)
    
    def locselector(self,a,b,c,d):
        self.locselflag = True
        if not self.locsel:
            self.locsel = LocSelector(self) 
    
    def on_fullscreen_clicked(self,full):
        if full.toggled:
            full.toggled = False
            self.mpanel.hide()
            self.tb.hide()
            self.boss.set_fullscreen_state(True)
            self.fullscreen()
        else:
            full.toggled = True
            self.tb.show()
            self.mpanel.show()
            self.boss.set_fullscreen_state(False) 
            self.unfullscreen()

    def on_kon_clicked(self,but):
        self.boss.ipshell()

    def on_about_clicked(self,but,appath):
        about = Gtk.AboutDialog()
        about.connect("response", self.on_about_response)
        about.connect("close", self.on_about_close)
        #about.connect("delete_event", self.on_about_close)
        about.set_name("Astro-Nex")
        about.set_version(self.boss.app.version)
        about.set_comments(_("Programa de calculo y dibujo de cartas astrologicas segun el metodo API"))
        file = path.joinpath(appath,"resources/COPYING")
        about.set_license(open(file).read())
        about.set_copyright("Copyright © 2006")
        about.set_website("http://astro-nex.net")
        about.set_authors(["Jose Antonio Rodríguez <jar@eideia.net>"])
        imgfile = path.joinpath(appath,"resources/splash.png")
        logo = GdkPixbuf.Pixbuf.new_from_file(imgfile)
        about.set_logo(logo)
        about.show_all()

    def on_about_response(self,dialog,response):
        if response < 0:
            dialog.destroy()
            dialog.emit_stop_by_name('response')
    
    def on_about_close(self,widget,event=None):
        widget.destroy()
        return True

    #def printpage_cb(self,acgroup,actable,keyval,mod):
    #    printsurface.printpage(self.boss)
    
    def customloc_cb(self,acgroup,actable,keyval,mod):
        CustomLocDlg(self.boss)
    
    def launch_chartbrowser(self,acgroup,actable,keyval,mod):
        if not self.browser:
            self.browser = ChartBrowserWindow(self)
    
    def launch_chartbrowser_from_mpanel(self):
        if not self.browser:
            self.browser = ChartBrowserWindow(self)
    
    def launch_plagram(self,acgroup,actable,keyval,mod):
        if not self.plagram:
            self.plagram = PlagramWindow(self)

    def launch_aux(self,acgroup,actable,keyval,mod):
        self.da.auxwins.append(AuxWindow(self))
    
    def launch_aux_from_browser(self,chart):
        self.da.auxwins.append(AuxWindow(self,chart=chart))
    
    def launch_pebridge(self,acgroup,actable,keyval,mod):
        item = self.mpanel.toolbar.get_nth_item(6)
        item.set_active(not item.get_active())
    
    def launch_shell(self,acgroup,actable,keyval,mod):
        ShellDialog(self.boss)
    
    def launch_editor(self,acgroup,actable,keyval,mod):
        IniEditor(self)
    
    def launch_calendar(self,acgroup,actable,keyval,mod):
        item = self.mpanel.toolbar.get_nth_item(0)
        item.set_active(not item.get_active())

    def show_pe(self,acgroup,actable,keyval,mod):
        item = self.mpanel.toolbar.get_nth_item(1)
        item.set_active(not item.get_active())

    def launch_selector(self,acgroup,actable,keyval,mod):
        item = self.mpanel.toolbar.get_nth_item(3)
        item.set_active(not item.get_active())

    def launch_cycles(self,acgroup,actable,keyval,mod):
        item = self.mpanel.toolbar.get_nth_item(4)
        item.set_active(not item.get_active())

    def show_diada(self,acgroup,actable,keyval,mod):
        item = self.mpanel.toolbar.get_nth_item(5)
        item.set_active(not item.get_active())

    def swap_slot(self,acgroup,actable,keyval,mod):
        self.mpanel.slot_act_inactive()
    
    def swap_storage(self,acgroup,actable,keyval,mod):
        self.mpanel.swap_storage() 

    def load_one_fav(self,acgroup,actable,keyval,mod):
        self.boss.load_one_fav()
    
    def load_couple(self,acgroup,actable,keyval,mod):
        self.boss.load_couple()
    
    def show_help(self):
        HelpWindow(self)
        
    def swap_to_ten(self,acgroup,actable,keyval,mod):
        self.boss.da.drawer.aspmanager.swap_to_ten()
        self.boss.da.redraw()

    def swap_to_twelve(self,acgroup,actable,keyval,mod):
        self.boss.da.drawer.aspmanager.swap_to_twelve()
        self.boss.da.redraw()
    
    def page_select(self, acgroup, actable, keyval, mod):
        # En GTK3/Python3 usamos Gdk para los códigos de teclado
        # s = Gdk  (Asegúrate de tener 'from gi.repository import Gdk' al inicio)
        
        kcodes = {
            Gdk.KEY_KP_0: 'transit', 
            Gdk.KEY_KP_1: 'charts', 
            Gdk.KEY_KP_2: 'clicks', 
            Gdk.KEY_KP_3: 'bio', 
            Gdk.KEY_KP_4: 'double1',
            Gdk.KEY_KP_5: 'triple1', 
            Gdk.KEY_KP_6: 'data', 
            Gdk.KEY_KP_7: 'diagram', 
            Gdk.KEY_KP_8: 'double2', 
            Gdk.KEY_KP_9: 'triple2' 
        }

        # Verificamos si la tecla pulsada está en nuestro diccionario
        if keyval in kcodes:
            thisname = kcodes[keyval]
            for but in self.mpanel.chooser.groups_table.get_children():
                if but.get_data('name') == thisname:
                    but.set_active(True)
                    break

    def op_select(self, acgroup, actable, keyval, mod):
        # Lista de teclas usando Gdk
        kcodes = [
            Gdk.KEY_KP_0, Gdk.KEY_KP_1, Gdk.KEY_KP_2, Gdk.KEY_KP_3, Gdk.KEY_KP_4,
            Gdk.KEY_KP_5, Gdk.KEY_KP_6, Gdk.KEY_KP_7, Gdk.KEY_KP_8, Gdk.KEY_KP_9
        ]
        
        # Verificamos que la tecla pulsada sea una de las del teclado numérico
        if keyval in kcodes:
            n = kcodes.index(keyval)
            nb = self.boss.mpanel.chooser.notebook
            
            # Obtenemos la página actual del notebook (el panel de opciones)
            v = nb.get_nth_page(nb.get_current_page())
            
            # Verificamos que la página (v) tenga un modelo (sea un TreeView/Lista)
            model = v.get_model()
            if model:
                # Calculamos el índice (n) y seleccionamos la fila
                # El % len(model) evita que falle si pulsas un número mayor a las filas que hay
                v.get_selection().select_path(n % len(model))

    def scroll_pool(self, acgroup, actable, keyval, mod):
        # En GTK3, las constantes de teclado están en Gdk y empiezan por KEY_
        if keyval == Gdk.KEY_KP_Add:
            delta = 1
        elif keyval == Gdk.KEY_KP_Subtract:
            delta = -1
        else:
            return # Evitamos errores si se pulsa otra tecla

        self.mpanel.scroll_pool(delta)

    def house_change(self, acgroup, actable, keyval, mod):
        if self.da.hselvisible:
            # Usamos Gdk.KEY_plus para el símbolo +
            if keyval == Gdk.KEY_plus:
                self.da.hsel.get_child().house_updown(1)
            # Usamos Gdk.KEY_minus para el símbolo -
            elif keyval == Gdk.KEY_minus:
                self.da.hsel.get_child().house_updown(-1)

    def view_change(self, acgroup, actable, keyval, mod):
        # 1. Definimos nb (notebook) para que no de NameError
        # Ajusta esta ruta según sea exactamente en tu estructura, 
        # normalmente en Astro-Nex es:
        try:
            nb = self.boss.mpanel.chooser.notebook
        except AttributeError:
            # Si la ruta anterior falla, intentamos esta otra común:
            nb = self.mpanel.chooser.notebook

        page_idx = nb.get_current_page()
        
        # Saltamos las primeras pestañas como hace el original
        if page_idx < 6: 
            return

        # Determinamos la dirección del salto
        if keyval in (Gdk.KEY_Right, Gdk.KEY_Up):
            val = 2
        elif keyval in (Gdk.KEY_Left, Gdk.KEY_Down):
            val = -2
        else:
            return

        page = nb.get_nth_page(page_idx)
        # Obtenemos los hijos (las tablas/vistas)
        views = page.get_children()
        n = len(views)
        if n == 0: return
        
        found = False
        for v in range(n):
            if views[v].has_focus():
                next_idx = (v + val) % n
                views[next_idx].grab_focus()
                found = True
                break
        
        # Si nada tiene el foco (clásico al usar el ratón), se lo damos al primero
        if not found:
            views[0].grab_focus()

    def popup_menu(self,acgroup,actable,keyval,mod):
        self.da.popup_menu()
    
    def on_mouse_scroll(self, widget, event):
        success, direction = event.get_scroll_direction()
        if not success:
            return False

        try:
            # En MainPanel, el objeto OpPanel se llama 'chooser'
            # Esta es la ruta real en tu memoria:
            opp = self.boss.mpanel.chooser
            
            if direction == Gdk.ScrollDirection.UP:
                # delta_select(-1) sube en la lista (Radix <- Casas)
                opp.delta_select(-1)
                
            elif direction == Gdk.ScrollDirection.DOWN:
                # delta_select(1) baja en la lista (Radix -> Casas)
                opp.delta_select(1)
                
            return True
        except Exception as e:
            # Si esto falla, intentamos la ruta sin .boss por si acaso
            try:
                self.mpanel.chooser.delta_select(1 if direction == Gdk.ScrollDirection.DOWN else -1)
                return True
            except:
                print(f"Error final en scroll: {e}")
                return False

    def fake_scroll_up(self, acgroup, actable, keyval, mod):
        # En lugar de fabricar un evento, llamamos a la lógica directamente
        # Si da.on_scroll espera un objeto con .direction:
        class FakeEvent:
            direction = Gdk.ScrollDirection.UP
        self.da.on_scroll(self.da, FakeEvent())
    
    def fake_scroll_down(self, acgroup, actable, keyval, mod):
        class FakeEvent:
            direction = Gdk.ScrollDirection.DOWN
        self.da.on_scroll(self.da, FakeEvent())

    def set_now(self,acgroup,actable,keyval,mod):
        self.da.panel.nowbut.emit('clicked')

    def fake_click_clock(self,acgroup,actable,keyval,mod):
        slot = self.mpanel.pool[self.mpanel.active_slot]
        slot.clock.emit('clicked')

    def fake_modify_chart(self,acgroup,actable,keyval,mod):
        slot = self.mpanel.pool[self.mpanel.active_slot]
        slot.mod.emit('clicked')

    def toggle_overlay(self,acgroup,actable,keyval,mod):
        self.da.toggle_overlay()
    
    def on_key_press_event(self, window, event): 
        if event.keyval == Gdk.KEY_F11 or (event.keyval == Gdk.KEY_Escape and self.da.__class__.fullscreen): 
            self.tb.get_nth_item(1).emit('clicked')
        elif event.keyval == Gdk.KEY_F1:
            self.show_help()
            
        # Nueva lógica para la tecla 'g' en Python 3
        elif event.keyval == Gdk.KEY_g:
            da = self.da
            if hasattr(da, 'planpopup') and da.planpopup:
                da.planpopup.destroy()
                da.planpopup = None
            else:
                # Intentamos la importación desde aux_dlg, que es donde suele estar en U20
                try:
                    from .aux_dlg import PlanPopup
                except ImportError:
                    # Si falla, es que está en el mismo nivel de las superficies
                    from ..surfaces.layoutsurface import PlanPopup
                
                da.planpopup = PlanPopup(self.boss)
            
            da.queue_draw()
            return True
        
        

