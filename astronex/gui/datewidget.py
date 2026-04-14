from gi.repository import GObject as gobject
from gi.repository import Pango as pango
from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

# Definimos el alias para que el resto del código no falle
keysyms = Gdk
import datetime
from pytz import timezone
from .. extensions.validation import MaskEntry,ValidationError
import time
from .. boss import boss
curr = boss.get_state()

def set_background(widget, color, state=Gtk.StateFlags.NORMAL):
    widget.modify_base(state, Gdk.color_parse(color))

class _DateEntryPopup(Gtk.Window):
    __gsignals__ = {
            'date-selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,(object,)),
            }

    def __init__(self, dateentry):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('key-press-event', self._on__key_press_event)
        self.connect('button-press-event', self._on__button_press_event)
        self._dateentry = dateentry

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.add(frame)
        frame.show()

        vbox = Gtk.Box()
        vbox.set_border_width(6)
        frame.add(vbox)
        vbox.show()
        self._vbox = vbox

        self.calendar = Gtk.Calendar()
        self.calendar.connect('day-selected-double-click',
                               self._on_calendar__day_selected_double_click)
        vbox.pack_start(self.calendar, False, False,0)
        self.calendar.show()

        buttonbox = Gtk.HButtonBox()
        buttonbox.set_border_width(6)
        buttonbox.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        vbox.pack_start(buttonbox, False, False,0)
        buttonbox.show()

        for label, callback in [(_('_Hoy'), self._on_today__clicked),
                                (_('_Cancelar'), self._on_cancel__clicked),
                                (_('_Aceptar'), self._on_select__clicked)]:
            button = Gtk.Button(label, use_underline=True)
            button.connect('clicked', callback)
            buttonbox.pack_start(button, True, True, 0)
            button.show()

        self.set_resizable(False)
        self.set_screen(dateentry.get_screen())

        self.realize()
        self.height = self._vbox.get_preferred_size()[0].height

    def _on_calendar__day_selected_double_click(self, calendar):
        self.emit('date-selected', self.get_date())

    def _on__button_press_event(self, window, event):
        # If we're clicking outside of the window close the popup
        hide = False

        # Also if the intersection of self and the event is empty, hide
        # the calendar
        if (tuple(self.get_allocation().intersect(
              Gdk.Rectangle(x=int(event.x), y=int(event.y),
                           width=1, height=1))) == (0, 0, 0, 0)):
            hide = True

        # Toplevel is the window that received the event, and parent is the
        # calendar window. If they are not the same, means the popup should
        # be hidden. This is necessary for when the event happens on another
        # widget
        toplevel = event.window.get_toplevel()
        parent = self.calendar.get_parent_window()
        if toplevel != parent:
            hide = True

        if hide:
            self.popdown()

    def _on__key_press_event(self, window, event):
        keyval = event.keyval
        # En GTK3 usamos Gdk.ModifierType para la máscara
        state = event.state & Gtk.accelerator_get_default_mod_mask()
        
        # Combinación Escape o Alt+Arriba para cerrar
        if (keyval == Gdk.KEY_Escape or
            ((keyval == Gdk.KEY_Up or keyval == Gdk.KEY_KP_Up) and
             state == Gdk.ModifierType.MOD1_MASK)):
            self.popdown()
            return True
            
        # Cerrar con Tabulador
        elif keyval == Gdk.KEY_Tab:
            self.popdown()
            return True
            
        # Seleccionar fecha con Enter o Espacio
        elif (keyval == Gdk.KEY_Return or
              keyval == Gdk.KEY_space or
              keyval == Gdk.KEY_KP_Enter or
              keyval == Gdk.KEY_KP_Space):
            self.emit('date-selected', self.get_date())
            return True

        return False

    def _on_select__clicked(self, button):
        self.emit('date-selected', self.get_date())

    def _on_cancel__clicked(self, button):
        self.popdown()

    def _on_today__clicked(self, button):
        self.set_date(datetime.date.today())

    def _popup_grab_window(self):
        activate_time = 0
        # Obtenemos la ventana GDK una sola vez
        window = self.get_window()
        
        if not window:
            return False

        # Intentamos el grab del puntero (ratón)
        if Gdk.pointer_grab(window, True,
                            (Gdk.EventMask.BUTTON_PRESS_MASK |
                             Gdk.EventMask.BUTTON_RELEASE_MASK |
                             Gdk.EventMask.POINTER_MOTION_MASK),
                             None, None, activate_time) == Gdk.GrabStatus.SUCCESS:
            
            # Intentamos el grab del teclado
            if Gdk.keyboard_grab(window, True, activate_time) == Gdk.GrabStatus.SUCCESS:
                return True
            else:
                # Si falla el teclado, soltamos el puntero
                display = window.get_display()
                display.get_default_seat().ungrab() # Forma moderna de soltar en GTK3
                return False
        return False

    def _get_position(self):
        self.realize()
        calendar = self
        sample = self._dateentry

        # 1. Obtenemos origen de la ventana (Ignorando el éxito con _)
        _, x, y = sample.dateentry.get_window().get_origin()
        
        # 2. Obtenemos tamaño pedido (Requisition en GTK3)
        requisition = calendar.get_preferred_size()[1]
        width = requisition.width
        # Usamos la altura definida en la clase o la natural del calendario
        height = getattr(self, 'height', requisition.height)

        # 3. Datos del monitor (Geometría)
        screen = sample.get_screen()
        monitor_num = screen.get_monitor_at_window(sample.dateentry.get_window())
        monitor = screen.get_monitor_geometry(monitor_num)
        
        # 4. Obtener el 'allocation' (rectángulo de dimensiones)
        alloc = sample.get_allocation()

        # --- Lógica de posicionamiento ---
        
        # Ajuste horizontal (evitar que se salga por los lados)
        if x < monitor.x:
            x = monitor.x
        elif x + width > monitor.x + monitor.width:
            x = monitor.x + monitor.width - width

        # Ajuste vertical (¿Cabe abajo o lo ponemos arriba?)
        if y + alloc.height + height <= monitor.y + monitor.height:
            y += alloc.height
        elif y - height >= monitor.y:
            y -= height
        elif (monitor.y + monitor.height - (y + alloc.height) > y - monitor.y):
            y += alloc.height
            height = monitor.y + monitor.height - y
        else:
            height = y - monitor.y
            y = monitor.y

        return x, y, width, height

    def popup(self, date):
        """
        Shows the list of options. And optionally selects an item
        @param date: date to select
        """
        combo = self._dateentry
        if not combo.get_realized():
            return

        treeview = self.calendar
        if treeview.get_mapped():
            return
        toplevel = combo.get_toplevel()
        if isinstance(toplevel, Gtk.Window):
            group = toplevel.get_group()  # Obtenemos el objeto grupo
            if group:
                group.add_window(self)

        x, y, width, height = self._get_position()
        self.set_size_request(width, height)
        self.move(x, y)
        self.show_all()

        if date:
            self.set_date(date)
        self.grab_focus()

        if not self.calendar.has_focus():
            self.calendar.grab_focus()

        if not self._popup_grab_window():
            self.hide()
            return

        self.grab_add()

    def popdown(self):
        combo = self._dateentry
        if not combo.get_realized():
            return

        self.grab_remove()
        self.hide()

    def get_date(self):
        y, m, d = self.calendar.get_date()
        return datetime.date(y, m + 1, d)

    def set_date(self, date):
        self.calendar.select_month(date.month - 1, date.year)
        self.calendar.select_day(date.day)
        # FIXME: Only mark the day in the curr month?
        self.calendar.clear_marks()
        self.calendar.mark_day(date.day)



class DateEntry(Gtk.Box):
    __gsignals__ = {
            'changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,()),
            }

    def __init__(self,manager,fullpanel=True):
        self.boss = manager
        Gtk.Box.__init__(self)
        self._popping_down = False
        dt = datetime.datetime.now()
        self.date = dt.date()
        self.time = dt.time()
        self.dateformat = "%d/%m/%Y"
        self.timeformat = "%H:%M:%S"

        vbox = Gtk.Box()
        self.dateentry = MaskEntry()
        self.dateentry.set_mask('00/00/0000')
        self.dateentry.connect('changed',self.on_entry_changed)
        self.dateentry.connect('focus_out_event',self.on_entry_focus_out)
        mask = self.dateentry.get_mask()
        self.dateentry.set_width_chars(len(mask))
        hbox1 = Gtk.Box()
        if fullpanel:
            label = Gtk.Label("    "+_("Fecha:")+"    ")
            hbox1.pack_start(label,False,False,0)
            sg = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
            sg.add_widget(label)
        hbox1.pack_start(self.dateentry,False,False,0)

        self._button = Gtk.ToggleButton()
        self._button.connect('scroll-event', self.on_entry_scroll_event)
        self._button.connect('toggled', self.on_button_toggled)
        self._button.set_focus_on_click(False)
        hbox1.pack_start(self._button, False, False,0)
        self._button.show()

        arrow = Gtk.Arrow(arrow_type=Gtk.ArrowType.DOWN, shadow_type=Gtk.ShadowType.NONE)
        self._button.add(arrow)
        arrow.show()

        self._popup = _DateEntryPopup(self)
        self._popup.connect('date-selected', self._on_popup__date_selected)
        self._popup.connect('hide', self._on_popup__hide)
        self._popup.set_size_request(-1, 24)

        vbox.pack_start(hbox1,False,False,0)
        if fullpanel:
            label = Gtk.Label(_("Hora:"))
            self.timeentry = MaskEntry()
            self.timeentry.set_mask('00:00:00')
            self.timeentry.connect('changed',self.on_entry_changed)
            self.timeentry.connect('focus_out_event',self.on_entry_focus_out)
            mask = self.timeentry.get_mask()
            self.timeentry.set_width_chars(len(mask))
            hbox2 = Gtk.Box()
            hbox2.pack_start(label,False,False,0)
            hbox2.pack_start(self.timeentry,False,False,0)
            sg.add_widget(label)
            vbox.pack_start(hbox2,False,False,0)
            self.pack_end(self.create_delta_panel(), False, False, 0)

        self.pack_start(vbox,False,False,0)

    def create_delta_panel(self):
        vbox = Gtk.Box()
        adj = Gtk.Adjustment(1,1,15,1,5)
        spin = Gtk.SpinButton(adjustment=adj)
        spin.set_wrap(True)
        spin.set_alignment(1.0)
        self.spin = spin
        vbox.pack_start(spin,False,False,0)

        hbox = Gtk.Box()
        button = Gtk.Button()
        arrow = Gtk.Arrow(arrow_type=Gtk.ArrowType.LEFT, shadow_type=Gtk.ShadowType.NONE)
        button.add(arrow)
        button.dir = '<'
        button.set_size_request(26,-1)
        button.connect('clicked',self.on_panel_arrow_clicked)
        hbox.pack_start(button,False,False,0)

        button = Gtk.ToggleButton(_('minutos'))
        button.set_size_request(60,-1)
        button.connect('toggled',self.on_delta_toggled)
        button.connect('scroll-event', self.on_delta_scroll_event)
        self.hintbut = button
        hbox.pack_start(button,False,False,0)

        button = Gtk.Button()
        arrow = Gtk.Arrow(arrow_type=Gtk.ArrowType.RIGHT, shadow_type=Gtk.ShadowType.NONE)
        button.add(arrow)
        button.dir = '>'
        button.set_size_request(26,-1)
        button.connect('clicked',self.on_panel_arrow_clicked)
        hbox.pack_start(button,False,False,0)
        vbox.pack_start(hbox,False,False,0)
        return vbox

    def do_grab_focus():
        self.dateentry.grab_focus()

    def on_entry_changed(self,entry):
        self.calc_and_set(entry)

    def on_entry_focus_out(self,entry,event):
        self.calc_and_set(entry)

    def calc_and_set(self,entry):
        if entry is self.dateentry:
            try:
                self.date = self.get_date()
                set_background(entry, "#ffffff")
            except ValidationError as e:
                self.date = None
                set_background(entry, "#ff699a")
        elif entry is self.timeentry:
            try:
                self.time = self.get_time()
                set_background(entry, "#ffffff")
            except ValidationError as e:
                self.time = None
                set_background(entry, "#ff699a")
        if self.date is not None and self.time is not None:
            curr.calcdt.setdt(datetime.datetime.combine(self.date,self.time))
        active = self.boss.mpanel.active_slot
        curr.setchart()
        curr.act_pool(active,curr.calc)

    def set_date(self,date):
        if not isinstance(date,datetime.date):
            raise TypeError("date must be a datetime.date instance")
        if date.year < 1900:
            year = date.year
            month = str(date.month).rjust(2,'0')
            day = str(date.day).rjust(2,'0')
            strdate = "%s/%s/%s" % (day,month,year)
            self.dateentry.set_text(strdate)
        else:
            texto_fecha = str(date.strftime(self.dateformat))
            self.dateentry.set_text(texto_fecha)

    def get_date(self):
        text = self.dateentry.get_text()
        if text == "":
            return None
        try:
            dateinfo = time.strptime(text, self.dateformat)
            return datetime.date(*dateinfo[:3])
        except ValueError:
            raise ValidationError('value error: %s' % text)
        return None

    def set_time(self,time):
        if not isinstance(time,datetime.time):
            raise TypeError("date must be a datetime.time instance")
        self.timeentry.set_text(time.strftime(self.timeformat))

    def get_time(self):
        text = self.timeentry.get_text()
        if text == "":
            return None
        try:
            dateinfo = time.strptime(text, self.timeformat)
            return datetime.time(*dateinfo[3:6])
        except ValueError:
            raise ValidationError('value error: %s' % text)

    def on_entry_scroll_event(self,entry,event):
        if event.direction == Gdk.SCROLL_UP:
            amount = 1
        elif event.direction == Gdk.SCROLL_DOWN:
            amount = -1
        else:
            return
        try:
            date = self.get_date()
            newdate = date + datetime.timedelta(days=amount)
        except ValidationError:
            newdate = datetime.date.today()
        self.set_date(newdate)

    def on_button_toggled(self,button):
        if self._popping_down:
            return
        try:
            date = self.get_date()
        except ValidationError:
            date = None
        self._popup.popup(date)

    def _on_popup__hide(self, popup):
        self._popping_down = True
        self._button.set_active(False)
        self._popping_down = False

    def _on_popup__date_selected(self, popup, date):
        self.set_date(date)
        popup.popdown() # <--- CORRECTO: Llama al método que cierra la ventana flotante
        self.dateentry.grab_focus()
        # En GTK3, para que set_position funcione, asegúrate de que el texto ya esté puesto
        self.dateentry.set_position(-1) # -1 es un truco para ir al final automáticamente

    def on_panel_arrow_clicked(self,but):
        delta = self.spin.get_value_as_int()
        if getattr(but, 'dir', None) == '<':
            delta = -delta
        self.change_on_delta(delta)

    def on_delta_toggled(self,but):
        hint = [_('minutos'),_('horas')]
        lbl = hint[but.get_active()]
        but.set_label(lbl)

    def on_delta_scroll_event(self,entry,event):
        delta = self.spin.get_value_as_int()
        if event.direction == Gdk.SCROLL_UP:
            amount = 1 * delta
        elif event.direction == Gdk.SCROLL_DOWN:
            amount = -1 * delta
        else:
            return
        self.change_on_delta(amount)

    def change_on_delta(self,delta):
        changes = {_('minutos'):'minutes',_('horas'):'hours'}
        hof = None
        change = changes[self.hintbut.get_label()]
        try:
            time = self.get_time()
        except ValidationError:
            time = None
        if not time:
            time = datetime.time.min
        h = time.hour
        m = time.minute
        s = time.second
        if change == 'minutes':
            mof,m = divmod(m+delta,60)
            if mof:
                hof,h = divmod(h+mof,24)
        else:
            hof,h = divmod(h+delta,24)
        newtime = datetime.time(h,m,s)
        self.set_time(newtime)
        if hof:
            try:
                date = self.get_date()
                newdate = date + datetime.timedelta(days=hof)
            except ValidationError:
                newdate = datetime.date.today()
            self.set_date(newdate)
