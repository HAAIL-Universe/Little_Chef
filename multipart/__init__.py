"""Compatibility shim so starlette finds python-multipart instead of the old multipart package."""
from python_multipart import *
from python_multipart import __all__, __author__, __copyright__, __license__, __version__
