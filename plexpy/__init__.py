from importlib import import_module as _import_module


_pkg_name = __name__
_pkg_spec = __spec__
_pkg_path = __path__
_pkg_file = __file__
_pkg_loader = __loader__

_bootstrap = _import_module('plexpy.app.bootstrap')

_globals = globals()
for _key, _value in _bootstrap.__dict__.items():
    if _key in ('__dict__', '__weakref__'):
        continue
    _globals[_key] = _value

__name__ = _pkg_name
__package__ = _pkg_name
__spec__ = _pkg_spec
__path__ = _pkg_path
__file__ = _pkg_file
__loader__ = _pkg_loader
