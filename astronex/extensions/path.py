import sys, warnings, os, fnmatch, glob, shutil, codecs
from hashlib import md5

__version__ = '2.2_py3_port'
__all__ = ['path']

# En Python 3, str ya es unicode
_base = str
_getcwd = os.getcwd

class path(_base):
    def __repr__(self):
        return 'path(%s)' % _base.__repr__(self)

    def __add__(self, more):
        resultStr = _base.__add__(self, more)
        return self.__class__(resultStr)

    def __radd__(self, other):
        return self.__class__(other.__add__(self))

    # El operador / para unir rutas en Python 3
    def __truediv__(self, rel):
        return self.__class__(os.path.join(self, rel))
    
    # Para compatibilidad con código viejo que use /
    __div__ = __truediv__

    @classmethod
    def getcwd(cls):
        return cls(_getcwd())

    # --- Operaciones de os.path ---
    def abspath(self):       return self.__class__(os.path.abspath(self))
    def normcase(self):      return self.__class__(os.path.normcase(self))
    def normpath(self):      return self.__class__(os.path.normpath(self))
    def realpath(self):      return self.__class__(os.path.realpath(self))
    def expanduser(self):    return self.__class__(os.path.expanduser(self))
    def expandvars(self):    return self.__class__(os.path.expandvars(self))
    def dirname(self):       return self.__class__(os.path.dirname(self))
    
    @property
    def name(self):          return os.path.basename(self)

    @property
    def parent(self):        return self.dirname()

    @property
    def ext(self):
        return os.path.splitext(self)[1]

    def joinpath(self, *args):
        return self.__class__(os.path.join(self, *args))

    def isdir(self):  return os.path.isdir(self)
    def isfile(self): return os.path.isfile(self)
    def exists(self): return os.path.exists(self)

    # Corregido: Permisos octales para Python 3
    def mkdir(self, mode=0o777):
        os.mkdir(self, mode)

    def makedirs(self, mode=0o777):
        os.makedirs(self, mode)

    def listdir(self, pattern=None):
        names = os.listdir(self)
        if pattern is not None:
            names = fnmatch.filter(names, pattern)
        return [self / child for child in names]

    def glob(self, pattern):
        return [self.__class__(s) for s in glob.glob(str(self / pattern))]

    def copy(self, dest):
        shutil.copy(self, dest)
