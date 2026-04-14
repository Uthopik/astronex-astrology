# -*- coding: utf-8 -*-
from gi.repository import Gtk
from .. countries import cata_reg
from .. boss import boss
from .searchview import SearchView
curr = boss.get_state()

def filter_region(model,iter,code):
    value = model.get_value(iter,1)
    return value == code 

class LocWidget(Gtk.Box):
    def __init__(self, default=False):
        # CAMBIO CLAVE: En Python 3 usamos super() o Gtk.Box.__init__() SIN argumentos extra
        super().__init__() 
        self.set_orientation(Gtk.Orientation.VERTICAL) # Gtk3 necesita saber la orientación
        self.set_homogeneous(False)
        self.set_spacing(5)

        if not default:
            if curr.usa:
                x,c = curr.loc.region.split('(')
                c = curr.datab.get_usacode_from_name(c[:-1])
                country_code = c
            else:
                country_code = curr.loc.country_code
            region = curr.loc.region_code
            city = curr.loc.city 
        else:
            curr.usa = {'false':False,'true':True}[boss.opts.usa]
            country_code = boss.opts.country
            region = boss.opts.region
            city = boss.opts.locality
            curr.country = country_code

        self.countries = curr.datab.get_states_tuple(curr.usa)
        self.sortlist = sorted(self.countries) 

        compl = Gtk.EntryCompletion()
        # country label and check btns 
        hbox = Gtk.Box()
        l = [_('Pais'),_('Estado')][curr.usa]
        label = Gtk.Label(l)
        hbox.pack_start(label,False,False,0)
        self.check = Gtk.CheckButton(_("Usa"))
        self.check.set_active(curr.usa)
        self.check.connect('toggled',self.on_usa_toggled,compl,label)
        hbox.pack_start(self.check,True,False,0)
        
        self.filtcheck = Gtk.CheckButton(_("Filtro"))
        self.filtcheck.connect('toggled',self.on_filter_toggled)
        hbox.pack_start(self.filtcheck,True,False,0) 
        label = Gtk.Label(_('Region'))
        hbox.pack_end(label,True,False,0)
        hbox.set_border_width(3) 
        hbox.set_homogeneous(True) 
        self.pack_start(hbox,False,False,0)

        # country combo
        hbox = Gtk.Box()
        liststore = Gtk.ListStore(str,str)
        self.country_combo = Gtk.ComboBox.new_with_model_and_entry(liststore)
        self.country_combo.set_entry_text_column(0)
        cell = Gtk.CellRendererText()
        self.country_combo.pack_start(cell, True)
        
        for n,c in self.sortlist:
            liststore.append([n,c])

        for r in self.country_combo.get_model():
            if r[1] == country_code:
                self.country_combo.set_active_iter(r.iter)
                break
        
        compl.set_text_column(0)
        compl.set_model(self.country_combo.get_model())
        entry = self.country_combo.get_child()
        if entry:
            entry.set_completion(compl)
        compl.connect('match_selected', self.on_count_match)

        self.country_combo.set_wrap_width(4)
        self.country_combo.connect('changed',self.on_count_selected) 
        hbox.pack_start(self.country_combo,False,False,0)

        
        # region combo
        liststore = Gtk.ListStore(str,str)
        self.reg_combo = Gtk.ComboBox.new_with_model_and_entry(liststore)
        self.reg_combo.set_entry_text_column(0)
        cell = Gtk.CellRendererText()
        self.reg_combo.pack_start(cell, True)
        self.reg_combo.connect('changed',self.on_reg_selected)
        rlist = curr.datab.list_regions(country_code,curr.usa)
        if country_code == "SP" and boss.opts.lang == 'ca':
            temp = []
            for r in rlist:
                temp.append((cata_reg[r[0]],r[1]))
            rlist = temp

        i = 0
        for n,r in enumerate(rlist):
            liststore.append(r)
            if region == r[1]:
                i = n

        self.reg_combo.set_active(i)
        hbox.pack_end(self.reg_combo,False,False,0)
        self.pack_start(hbox,False,False,0)
        
        
        
        

        # locality view
        self.locmodel = Gtk.ListStore(str,str,str)
        
        loclist = curr.datab.fetch_all_from_country(country_code,curr.usa)
        print("\n" + "*"*40)
        print("   INSPECCIÓN EN LA INTERFAZ (GTK)")
        print("*"*40)
        if loclist:
            item = loclist[0]
            print(f"Elementos en la fila a insertar: {len(item)}")
            print(f"Fila completa recibida: {item}")
            # Verificamos si los tipos coinciden con el ListStore(str, str, str)
            for i, v in enumerate(item):
                print(f"Dato {i}: {v} | ¿Es String?: {isinstance(v, str)}")
        else:
            print("AVISO: loclist llegó vacío al Widget.")
        print("*"*40 + "\n")

        # El bucle que suele fallar
        # Este es el bucle que recorre la lista de ciudades
        for n, c in enumerate(loclist):
            # c[0] es la ciudad, c[1] es la región, c[2] es la coordenada fecha
            # Creamos una fila nueva con la coordenada "bonita"
            fila_bonita = [c[0], c[1], self.formatear_coordenada_visual(c[2])]
            
            self.locmodel.append(fila_bonita)
            
            if city == c[0]:
                i = n
        
        
        
        #self.locview = Gtk.TreeView(self.locmodel)
        self.locview = SearchView(self.locmodel)
        selection = self.locview.get_selection()
        selection.connect('changed',self.on_sel_changed)
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        i = 0
        for n,c in enumerate(loclist):
            self.locmodel.append(c)
            if city == c[0]:
                i = n

        cell = Gtk.CellRendererText()
        cell.set_property('width-chars',38)
        cell.set_property('foreground','blue')
        cellgeo = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None)
        column.pack_start(cell,False)
        column.pack_start(cellgeo,False)
        column.set_attributes(cell,text=0)
        column.set_attributes(cellgeo,text=2)
        column.set_widget(Gtk.HSeparator())
        self.locview.append_column(column) 
        self.locview.set_headers_visible(False)
        #self.locview.set_enable_search(True)
        self.locview.set_cursor(i,column)
        self.locview.scroll_to_cell(i)
        self.locview.connect('row-activated',self.on_row_activate)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.locview) 
        self.pack_start(sw, True, True, 0)
        
    def formatear_coordenada_visual(self, texto_original):
        try:
            # Separamos la longitud y la latitud (ej: "-152330;280720")
            lon_raw, lat_raw = texto_original.split(';')
            
            def convertir(valor_str, es_latitud):
                val = int(valor_str)
                # Determinamos la letra (N/S para latitud, E/W para longitud)
                if es_latitud:
                    letra = "N" if val >= 0 else "S"
                else:
                    letra = "E" if val >= 0 else "W"
                
                val_abs = abs(val)
                grados = val_abs // 10000
                minutos = (val_abs % 10000) // 100
                return f"{grados}{letra}{minutos:02d}"

            return f"{convertir(lon_raw, False)} {convertir(lat_raw, True)}"
        except:
            # Si algo falla (dato vacío, etc), devolvemos el original para no colgar el programa
            return texto_original


    def on_reg_selected(self,combo):
        model = combo.get_model()
        active = combo.get_active()
        if active < 0: 
            return
        self.reg_code = model[active][1]
        if self.filtcheck.get_active():
            filtmodel = self.locmodel.filter_new()
            filtmodel.set_visible_func(filter_region, self.reg_code)
            self.locview.set_model(filtmodel)

    def on_count_selected(self, combo):
        iter = combo.get_active_iter()
        if not iter: return
        model = combo.get_model()
        code = model.get_value(iter, 1)
        
        # 1. Actualización de regiones (se queda igual)
        liststore_reg = Gtk.ListStore(str, str)
        rlist = curr.datab.list_regions(code, curr.usa)
        for r in rlist:
            liststore_reg.append(r)
        self.reg_combo.set_model(liststore_reg)
        self.reg_combo.set_active(0) 

        # 2. Actualización de localidades (AQUÍ ESTÁ EL CAMBIO)
        liststore_loc = Gtk.ListStore(str, str, str)
        loclist = curr.datab.fetch_all_from_country(code, curr.usa)
        
        for c in loclist:
            # c[0]: Ciudad, c[1]: Región, c[2]: Coordenada Original
            # Creamos la fila con la coordenada ya formateada visualmente
            fila_visual = [c[0], c[1], self.formatear_coordenada_visual(c[2])]
            liststore_loc.append(fila_visual)
            
        self.locview.set_model(liststore_loc)
        self.locmodel = liststore_loc
        self.set_country_code(code)

    def set_country_code(self,code):
        curr.country = code 

    def on_count_match(self,compl,model,iter):
        sel = str(model.get_value(iter,0),"utf-8")
        for r in self.country_combo.get_model():
            if r[0] == sel:
                self.country_combo.set_active_iter(r.iter)
                break

    def on_usa_toggled(self,check,cpl,lbl):
        if check.get_active():
            curr.usa = True
            lbl.set_text(_("Estado"))
        else:
            curr.usa = False
            lbl.set_text(_("Pais"))
        self.countries = curr.datab.get_states_tuple(curr.usa)
        self.sortlist = sorted(self.countries)
        model = Gtk.ListStore(str,str)
        for n,c in self.sortlist:
            model.append([n,c])
        self.country_combo.set_model(model)
        cpl.set_model(model)
        for r in model:
            if r[1] == boss.opts.country:
                self.country_combo.set_active_iter(r.iter)
                break
        else:
            self.country_combo.set_active(0)

    def on_filter_toggled(self,check):
        if check.get_active():
            filtmodel = self.locmodel.filter_new()
            filtmodel.set_visible_func(filter_region, self.reg_code)
            self.locview.set_model(filtmodel)
        else:
            self.locview.set_model(self.locmodel)
        self.locview.get_selection().select_path("0")

    def on_row_activate(self,tree,path,col):
        model,iter = tree.get_selection().get_selected()
        city,code= model.get(iter,0,1)
        self.actualize_if_needed(city,code)

    def on_sel_changed(self,sel):
        model,iter = sel.get_selected()
        if not iter: return
        city,code= model.get(iter,0,1)
        for r in self.reg_combo.get_model():
            if code== r[1]:
                self.reg_combo.set_active_iter(r.iter)
                break
        self.actualize_if_needed(city,code)
        
    def actualize_if_needed(self,city,code):
        curr.setloc(city,code)
        if curr.curr_chart == curr.now:
            curr.set_now()
        if curr.curr_op == 'draw_local' or boss.mainwin.locselflag: 
            boss.da.redraw()
        else:
            active = boss.mpanel.active_slot
            curr.setchart()
            curr.act_pool(active,curr.calc)

    def set_default_local(self): 
        usa = boss.opts.usa
        usa = {'false':False,'true':True}[boss.opts.usa]
        if usa != self.check.get_active():
            self.check.set_active(usa)
            return
        self.countries = curr.datab.get_states_tuple(usa)
        self.sortlist = sorted(self.countries)
        model = Gtk.ListStore(str,str)
        for n,c in self.sortlist:
            model.append([n,c])
        self.country_combo.set_model(model)
        
        for r in model:
            if r[1] == boss.opts.country:
                self.country_combo.set_active_iter(r.iter)
                break
        else:
            self.country_combo.set_active(0)
        
        liststore = Gtk.ListStore(str,str,str)
        loclist = curr.datab.fetch_all_from_country(boss.opts.country,usa)
        i = 0
        for n,c in enumerate(loclist):
            liststore.append(c)
            if boss.opts.locality == c[0]:
                i = n
        self.locview.set_model(liststore)
        self.locmodel = liststore
        self.locview.set_cursor(i)
        self.locview.scroll_to_cell(i)
