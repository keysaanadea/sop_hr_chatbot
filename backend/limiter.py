"""
Shared rate limiter instance untuk seluruh aplikasi DENAI.
Diimport oleh main.py (setup) dan router files (dekorator).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
