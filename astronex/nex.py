# -*- coding: utf-8 -*- 
import sys, os
import gettext
import atexit

# 1. Forzamos a Python a mirar en la carpeta actual para los imports locales
sys.path.append(os.path.dirname(__file__))

# 2. Imports básicos que ya hemos verificado
try:
    from . import countries 
    from .config import read_config
except ImportError as e:
    print(f"Error inicial de importación: {e}")

# 3. Preparación de GTK3 (Reemplaza al viejo PyGTK)
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf

# 4. Traducciones
locale_path = os.path.join(os.path.dirname(__file__), 'locale')
lang_es = gettext.translation('astronex', locale_path, languages=['es'], fallback=True)
lang_en = gettext.translation('astronex', locale_path, languages=['en'], fallback=True)
lang_ca = gettext.translation('astronex', locale_path, languages=['ca'], fallback=True)
lang_de = gettext.translation('astronex', locale_path, languages=['de'], fallback=True)
langs = { 'en': lang_en, 'es': lang_es, 'ca': lang_ca, 'de': lang_de }

def t(text):
    """Traducción dinámica basada en la configuración"""
    if not text: 
        return ""
    
    # Intentamos sacar el idioma de la configuración del Manager/Boss
    # Si no lo encuentra, por defecto usamos español 'es'
    try:
        from .boss import Manager
        current_lang = Manager.opts.get('language', 'es')
    except:
        current_lang = 'es'
        
    # Buscamos en el diccionario de lenguajes que ya tienes (langs)
    translation_engine = langs.get(current_lang, lang_es)
    return translation_engine.gettext(str(text))

from .extensions.path import path
version = "2.0 (Py3 Port)"

# 5. Ventana Splash (Se muestra mientras carga el resto)
class Splash(Gtk.Window):
    def __init__(self, appath):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.set_default_size(400, 250) 
        self.set_position(Gtk.WindowPosition.CENTER)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        img = Gtk.Image()
        # Intentamos buscar la imagen de carga
        splashimg = os.path.join(appath, "astronex/resources/splash.png")
        if os.path.exists(splashimg):
            img.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(splashimg))
        vbox.pack_start(img, True, True, 0)
        self.add(vbox)

# 6. Clase principal: Aquí es donde ocurrirán los fallos
class Application(object):
    def __init__(self, appath):
        # Guardamos la ruta base y la versión
        self.appath = path(appath)
        self.version = "2.0 (Py3 Port)"  # <--- AÑADE ESTA LÍNEA
        
        self.home_dir = path(os.path.expanduser('~')) / '.astronex'
        if not self.home_dir.exists():
            self.home_dir.mkdir()
        
        self.config_file = self.home_dir / 'astronex.conf'

    def run(self):
        self.splash = Splash(self.appath)
        self.splash.show_all()
        # En 1 segundo intentamos cargar la aplicación real
        GObject.timeout_add(1000, self.setup_app)
        Gtk.main()

    def setup_app(self):
        print("--- Iniciando carga de componentes ---")
        try:
            # A. Leer configuración
            opts = read_config(self.home_dir)
            opts.home_dir = self.home_dir
            
            # B. Idioma
            if opts.lang in langs:
                langs[opts.lang].install()
            
            # C. Países (Cuidado: esto puede fallar si countries.py no está migrado)
            # countries.install(opts.lang) 

            # D. CARGA CRÍTICA: Aquí fallará por sintaxis o por el archivo .so
            print("Cargando state y boss...")
            # Importación relativa para Python 3
            from .state import Current
            from .boss import Manager
            
            print("Instanciando el estado...")
            self.state = Current(self)
            
            print("Instanciando el Manager (Boss)...")
            self.boss = Manager(self, opts, self.state)
            
            # E. Intentar abrir la ventana principal
            print("Cargando interfaz gráfica...")
            from .gui.winnex import WinNex
            self.mainwin = WinNex(self.boss)
            self.boss.set_mainwin(self.mainwin)
            
            self.splash.hide()
            print("¡Carga completada con éxito!")

        except Exception as e:
            print(("\n" + "="*30))
            print(" FALLO DE EJECUCIÓN ")
            print(("="*30))
            import traceback
            traceback.print_exc() # Esto nos dirá el archivo y la línea exacta
            print(("="*30))
            Gtk.main_quit()
        
        return False

def main(appath, console=False):
    app = Application(appath)
    app.run()

