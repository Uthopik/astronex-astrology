# -*- coding: utf-8 -*-
import sys, os

# Esto permite que el archivo encuentre a sus vecinos sin importar el punto '.'
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from .extensions.path import path
except ImportError:
    from .extensions.path import path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from configobj import ConfigObj
from . import locale

MAGICK_COL = 65535.0

default_colors = {'pers': 'ff5600', 'tool': '0000ff',
        'trans': '0000ff', 'node': '0000ff',
        'fire': 'dd0000', 'earth': '00bb00', 'air': 'ffb600',
        'water': '0000ff', 'orange': 'ff8000',
        'green': '00cc00', 'blue': '0000f7', 
        'red': 'ee0000', 'click1': '3300e6', 
        'click2': 'cc001a', 'inv': '7f7f99', 'low': '7f997f',
        'transcol': '7f7f99', 'overlay': '803480' ,'clicksoul': 'c227ff' }
COLORS = default_colors
PNG = {'hsize': 600, 'vsize': 600, 'labels': 'true' , 'pngviewer':'display', 'resolution': 300 }
PDF = {'pdfviewer': 'xdg-open'}
LANG = { 'lang': 'es' }
FONT = { 'font': 'Sans 11' , 'transtyle':  'huber'} #'classic' 
LINES = { 'base': 0.85 }
ORBS = { 'transits': [1.0,1.0,1.0,1.0,1.0,2.0,2.0,2.0,2.0,2.0,1.0],
        'lum' :[3.0,5.0,6.0,8.0,9.0],
        'normal': [2.0,4.0,5.0,6.0,7.0],
        'short': [1.5,3.0,4.0,5.0,6.0],
        'far' : [1.0,2.0,3.0,4.0,5.0],
        'useless' : [1.0,2.0,2.0,3.0,4.0], 
        'pelum' :[3.0,5.0,6.0,8.0,9.0],
        'penormal': [2.0,4.0,5.0,6.0,7.0],
        'peshort': [1.5,3.0,4.0,5.0,6.0],
        'pefar' : [1.0,2.0,3.0,4.0,5.0],
        'peuseless' : [1.0,2.0,2.0,3.0,4.0], 
        'discard': []  }
DEFAULT = { 'usa': 'false', 'favourites': '', 'nfav': 3, 'aux_size': 800,
        'database' : 'personal', 'ephepath': 'ephe',
        'country' : 'SP', 'region': 53,
        'locality' :'Las Palmas de Gran Canaria' }

class NexConf(object):
    sections = { 'DEFAULT': DEFAULT, 'ORBS': ORBS,
            'COLORS': COLORS, 'LINES': LINES,
            'FONT': FONT, 'PNG': PNG, 'LANG': LANG , 'PDF': PDF}

    def __init__(self):
        for sec in list(self.sections.values()):
            self.__dict__.update(sec)
        
        try:
            lang = locale.getdefaultlocale()[0]
        except:
            lang = 'es'
            
        if lang:
            lang = lang.split('_')[0]
            if lang not in ['es','de','ca']:
                lang = 'en'
        else:
            lang = 'es'
        self.lang = lang

    def opts_to_config(self, config):
        for sec, val in list(self.sections.items()):
            config[sec] = {}
            for s in list(val.keys()):
                config[sec][s] = getattr(self, s)

cfgcols = {}

def read_config(homedir):
    global cfgcols
    cfgfile = path.joinpath(homedir, 'cfg.ini')
    conf = ConfigObj(cfgfile)
    popts = {}
    for k in list(conf.keys()):
        popts.update(conf[k])

    if 'transits' in popts and not isinstance(popts['transits'], list):
        del popts['transits']

    opts = NexConf()
    opts.__dict__.update(popts)

    for keyc in list(default_colors.keys()):
        val = getattr(opts, keyc)
        cfgcols[keyc] = ''.join(['#', val])

    if not path.exists(cfgfile) or len(opts.__dict__) != len(popts):
        opts.opts_to_config(conf)
        conf.write()

    return opts

# Función auxiliar para convertir colores HEX a formato decimal (0.0 - 1.0)
def _parse_color(hex_str):
    rgba = Gdk.RGBA()
    rgba.parse(hex_str)
    return (rgba.red, rgba.green, rgba.blue)

def parse_aux_colors():
    auxcol = {}
    for cl in ['click1', 'click2', 'clicksoul', 'inv', 'low', 'transcol']:
        auxcol[cl] = _parse_color(cfgcols[cl])
    return auxcol
    
def parse_zod_colors():
    zodcol = [] 
    for cl in ['fire', 'earth', 'air', 'water']:
        zodcol.append(_parse_color(cfgcols[cl])) 
    return zodcol

def parse_plan_colors():
    plancol = {}
    for cl in ['pers', 'tool', 'trans', 'node']:
        plancol[cl] = _parse_color(cfgcols[cl])
    return plancol

def parse_asp_colors():
    aspcol = {}
    for cl in ['orange', 'green', 'blue', 'red']:
        aspcol[cl] = _parse_color(cfgcols[cl])
    return aspcol

def reset_colors(opts):
    global cfgcols
    for keyc, val in list(default_colors.items()):
        setattr(opts, keyc, val)
        cfgcols[keyc] = ''.join(['#', val])

def reload_config():
    """Recarga la configuración global del programa."""
    # Aquí deberías llamar a la lógica que lee el archivo .ini de nuevo
    # Por ahora, para que el programa no explote al importar:
    pass
