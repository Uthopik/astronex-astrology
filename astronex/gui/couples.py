# -*- coding: utf-8 -*-
from gi.repository import Gtk, Gdk
import sys,os,re
import pickle 
from .datewidget import DateEntry, set_background
from pytz import timezone
from datetime import datetime
from .. extensions.validation import MaskEntry,ValidationError
from .. extensions.path import path

curr = None
boss = None
regex = re.compile("[A-Za-z][_A-Za-z0-9]*$")

class CouplesPanel(Gtk.Box):
    
    def __init__(self,parent):
        global curr,boss
        boss = parent.boss
        curr = boss.get_state()
        Gtk.Box.__init__(self)
        self.data = {'ftab':'','mtab':'','fname':'','mname':'','fid':None,'mid':None}
        self.changes = False
        self.coup_ix = 0

        hbox = Gtk.Box()
        vbox = Gtk.Box() 
        vbox.set_border_width(3) 
        vbox.set_size_request(400,-1)
        
        button = Gtk.Button(_('Crear pareja'))
        button.connect('clicked',self.on_createcouple_clicked)
        vbox.pack_start(button,False,False,0)

        coupmodel = Gtk.ListStore(str,str,int,str,str,int)
        coupview = Gtk.TreeView(coupmodel)
        for c in curr.couples:
            coupmodel.append([c['fem'][0],c['fem'][1],c['fem'][2],
                c['mas'][0],c['mas'][1], c['mas'][2]])
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None,cell,text=0)
        coupview.append_column(column) 
        column = Gtk.TreeViewColumn(None,cell,text=3)
        coupview.append_column(column) 
        sel = coupview.get_selection()
        sel.set_mode(Gtk.SelectionMode.SINGLE)
        sel.connect('changed',self.on_sel_changed)
        sel.select_path(0,)
        menu = Gtk.Menu()
        menu_item = Gtk.MenuItem(_('Eliminar'))
        menu.append(menu_item)
        menu_item.op = 'delete'
        menu_item.connect("activate", self.on_menuitem_activate)
        coupview.connect("button_press_event", self.on_view_clicked,menu)
        menu_item.show()
        vbox.pack_start(coupview,False,False,0)
        
        hbox.pack_start(vbox,True,True,0)
        hbox.pack_start(Gtk.VSeparator(),False,False,0)
        
        vbox = Gtk.Box() 
        vbox.set_border_width(3) 
        vbox.set_size_request(400,-1)
        datewid = CoupleDates(self,boss)
        dt = datetime.now()
        tz = timezone('UTC')
        ld = tz.localize(dt)
        datewid.set_date(ld.date())
        bbox = Gtk.Alignment()
        bbox.set_property("xalign", 0.5)
        bbox.set_property("yalign", 0.0)
        bbox.set_property("xscale", 0.0)
        bbox.set_property("yscale", 0.0)
        bbox.add(datewid)
        vbox.pack_start(bbox,False,False,0)
        but = Gtk.Button()
        img = Gtk.Image()
        appath = boss.app.appath
        imgfile = path.joinpath(appath,"astronex/resources/gtk-go-down.png")
        img.set_from_file(str(imgfile))
        but.set_image(img)
        but.connect('clicked',self.on_add_date_clicked)
        bbox = Gtk.Alignment()
        bbox.set_property("xalign", 0.5)
        bbox.set_property("yalign", 0.0)
        bbox.set_property("xscale", 0.0)
        bbox.set_property("yscale", 0.0)
        bbox.add(but) 
        vbox.pack_start(bbox,False,False,0)
        
        datemodel = Gtk.ListStore(str,str)
        dateview = Gtk.TreeView(datemodel)
        dateview.set_headers_visible(False)
        dateview.set_size_request(-1,300)
        if curr.couples:
            for d in curr.couples[0]['dates']:
                datemodel.append([d[0],d[1]])
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None,cell,text=0)
        dateview.append_column(column) 
        cell = Gtk.CellRendererText()
        cell.set_property('editable',True)
        cell.connect('edited', self.on_cell_edited)
        column = Gtk.TreeViewColumn(None,cell,text=1)
        dateview.append_column(column) 
        sel = dateview.get_selection()
        sel.set_mode(Gtk.SelectionMode.SINGLE)
        sel.select_path(0,)
        menu = Gtk.Menu()
        menu_item = Gtk.MenuItem(_('Eliminar'))
        menu.append(menu_item)
        menu_item.connect("activate", self.on_menudate_activate)
        dateview.connect("button_press_event", self.on_dateview_clicked,menu)
        menu_item.show()
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(dateview)
        vbox.pack_start(sw,False,False,0)
        
        hbox.pack_start(vbox,True,True,0)
        frame = Gtk.Frame()
        frame.add(hbox)
        frame.set_border_width(6)
        self.pack_start(frame,False,False,0)
        
        self.coupview = coupview
        self.datewid = datewid
        self.dateview = dateview
        datewid.view = dateview

    def on_createcouple_clicked(self, button): 
        # En GTK3, los botones se definen preferiblemente con tuplas de (Texto, Respuesta)
        dialog = Gtk.Dialog(
            title=_("Crear pareja"), 
            parent=None,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        # Añadimos los botones manualmente para evitar el uso de STOCK items obsoletos
        dialog.add_button("_Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Aceptar", Gtk.ResponseType.OK)

        # En GTK3 usamos Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Empaquetamos los selectores
        hbox.pack_start(self.make_tables_selector('f'), True, True, 0)
        hbox.pack_end(self.make_tables_selector('m'), True, True, 0)
        
        # IMPORTANTE: En GTK3 se usa get_content_area() en lugar de .vbox
        dialog.get_content_area().pack_start(hbox, True, True, 0)
        
        dialog.connect("response", self.create_response)
        dialog.show_all()

    def make_tables_selector(self, key): 
        # En GTK3 se recomienda especificar la orientación
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)        
        liststore = Gtk.ListStore(str)
        
        tables = Gtk.ComboBox.new_with_model_and_entry(liststore)
        tables.set_entry_text_column(0)
        tables.set_size_request(182, -1)
        
        # En GTK3, para acceder al Entry de un ComboBox con Entry:
        tables.get_child().set_editable(False)
        
        # Si usas set_entry_text_column, no necesitas CellRenderer manual, 
        # pero si lo dejas, debe tener los argumentos correctos:
        cell = Gtk.CellRendererText()
        tables.pack_start(cell, True)
        tables.add_attribute(cell, 'text', 0)
        
        tablelist = curr.datab.get_databases()
        
        for c in tablelist:
            liststore.append([c])
            
        index = 0
        for i, r in enumerate(liststore):
            if r[0] == boss.opts.database:
                index = i
                break 
        
        tables.set_active(index) 
        
        # --- CORRECCIÓN CRÍTICA AQUÍ ---
        active_iter = tables.get_active_iter()
        table_name = liststore[active_iter][0] if active_iter else ""
        self.data["%stab" % key] = table_name
        
        vbox.pack_start(tables, False, False, 0)

        chartmodel = Gtk.ListStore(str, int)
        personae = Gtk.ComboBox.new_with_model_and_entry(chartmodel)
        personae.set_entry_text_column(0)
        
        # Usamos la variable table_name que acabamos de extraer
        chartlist = curr.datab.get_chartlist(table_name)

        for c in chartlist:
            glue = ", "
            if c[2] == '': glue = ''
            chartmodel.append([c[2] + glue + c[1], int(c[0])])
        
        # Configuración de personae
        personae.set_size_request(100, 28)
        personae.set_active(0)
        personae.connect('changed', self.on_persona_changed, key)
        
        vbox.pack_start(personae, True, True, 0) 
        vbox.set_size_request(210, -1)
        
        tables.connect('changed', self.on_tables_changed, personae, key)
        
        # --- CONFIGURACIÓN DEL AUTOCOMPLETADO ---
        compl = Gtk.EntryCompletion()
        compl.set_text_column(0)
        compl.set_model(personae.get_model())
        
        # En GTK3, el Entry es el "child" del ComboBox
        entry = personae.get_child()
        entry.set_completion(compl)
        compl.connect('match_selected', self.on_person_match, personae)
        
        # Emitir el cambio inicial para sincronizar datos
        personae.emit('changed')
        
        return vbox
    
    def on_person_match(self,compl,model,iter,personae):
        sel = str(model.get_value(iter,0),"utf-8")
        for r in personae.get_model():
            if r[0] == sel:
                personae.set_active_iter(r.iter)
                break
    
    def on_persona_changed(self,combo,key):
        if combo.get_active() == -1: return
        model = combo.get_model()
        iter =  combo.get_active_iter()
        name = model.get_value(iter,0)
        try:
            last,first = name.split(',')
            name = first[1:]+" "+last
        except ValueError:
            pass
        id = model.get_value(iter,1)
        self.data["%sname" % key] = name
        self.data["%sid" % key] = id

    def on_tables_changed(self,combo,personae,key): 
        if combo.get_active() == -1: 
            return
        if personae:
            chartmodel = Gtk.ListStore(str,int)
            t_iter = combo.get_active_iter()
            if t_iter is not None:
                table = combo.get_model()[t_iter][0]
            else:
                table = ""
            chartlist = curr.datab.get_chartlist(table) 
            for c in chartlist:
                glue = ", "
                if not c[2]:  glue = ''
                chartmodel.append([c[2]+glue+c[1] , int(c[0]) ])
            personae.set_model(chartmodel)
            personae.set_active(0)
            self.data["%stab" % key] = table
    
    def create_response(self,dialog,rid):
        if rid == Gtk.ResponseType.NONE or rid == Gtk.ResponseType.DELETE_EVENT:
            self.changes = False
            dialog.destroy()
            return
        couple = { 'fem': (self.data['fname'],self.data['ftab'],self.data['fid']),
                'mas': (self.data['mname'],self.data['mtab'],self.data['mid']),
                'dates': [] }
        curr.couples.append(couple)
        coupmodel = Gtk.ListStore(str,str,int,str,str,int)
        for c in curr.couples:
            coupmodel.append([c['fem'][0],c['fem'][1],c['fem'][2],
                c['mas'][0],c['mas'][1], c['mas'][2]])
        self.coupview.set_model(coupmodel)
        self.coupview.get_selection().select_path(len(coupmodel)-1,) 
        self.changes = True
        dialog.destroy()

    def save_couples(self):
        if self.changes:
            curr.save_couples(boss.app)

    def on_view_clicked(self,view, event,menu):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pthinfo = view.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                view.grab_focus()
                view.set_cursor(path,col,0)
                menu.popup(None, None, None, event.button, event.time)
            return True

    def on_sel_changed(self,sel):
        model, iter = sel.get_selected()
        if not iter:
            return
        self.coup_ix = model.get_path(iter)[0]
        datemodel = Gtk.ListStore(str,str)
        for d in curr.couples[self.coup_ix]['dates']:
            datemodel.append([d[0],d[1]])
        try:
            self.dateview.set_model(datemodel)
        except AttributeError:
            pass

    def on_menuitem_activate(self,menuitem): 
        model,iter = self.coupview.get_selection().get_selected()
        i =  model.get_path(iter)[0]
        del curr.couples[i]
        model.remove(iter)
        if i >= 1:
            self.coupview.get_selection().select_path(i-1,) 
        elif len(model) == 1:
            self.coupview.get_selection().select_path(0,) 
        else:
            datemodel = Gtk.ListStore(str,str)
            self.dateview.set_model(datemodel) 
        self.changes = True

    def on_menudate_activate(self,menuitem): 
        model,iter = self.dateview.get_selection().get_selected()
        i =  model.get_path(iter)[0]
        model.remove(iter)
        del curr.couples[self.coup_ix]['dates'][i]
        self.changes = True

    def on_dateview_clicked(self,view, event,menu):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pthinfo = view.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                view.grab_focus()
                view.set_cursor(path,col,0)
                menu.popup(None, None, None, event.button, event.time)
            return True

    def on_cell_edited(self,cell,path_string,newtext):
        model = self.dateview.get_model()
        iter = model.get_iter_from_string(path_string)
        path = model.get_path(iter)[0] 
        date = model.get_value(iter, 0)
        curr.couples[self.coup_ix]['dates'][path] = (date,newtext)
        ntxt = curr.couples[self.coup_ix]['dates'][path][1]
        model.set_value(iter, 1, ntxt)
        self.changes = True 

    def on_add_date_clicked(self,but):
        if  len(self.coupview.get_model()) < 1:
            return
        date = self.datewid.date
        dtstring = str(date.day) + "/" + str(date.month) + "/" + str(date.year)
        model = self.dateview.get_model()
        iter = model.append()
        desc = _('Acontecimiento')
        model.set(iter,0,dtstring,1,desc)
        curr.couples[self.coup_ix]['dates'].append((dtstring,desc))
        self.changes = True
        

class CoupleDates(DateEntry):
    def __init__(self,parent,boss):
        self.parent_container = parent
        DateEntry.__init__(self,boss,fullpanel=False)
        self.view = None

    def calc_and_set(self,entry):
        try:
            self.date = self.get_date()
            set_background(entry, "#ffffff") 
        except ValidationError as e:
            self.date = None
            set_background(entry, "#ff699a")
        if self.date is None: 
            return
        try:
            model, iter = self.view.get_selection().get_selected()
            if iter:
                date = self.date
                dtstring = str(date.day) + "/" + str(date.month) + "/" + str(date.year)
                model.set(iter, 0, dtstring)
                path = model.get_path(iter)[0] 
                desc = model.get_value(iter, 1)
                coup = self.container.coup_ix
                curr.couples[coup]['dates'][path] = (dtstring,desc)
                self.container.changes = True
        except AttributeError:
            pass
