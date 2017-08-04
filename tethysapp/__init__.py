# -*- coding: utf-8 -*-
"""__init__.py
    The app parent directory.
"""
# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
