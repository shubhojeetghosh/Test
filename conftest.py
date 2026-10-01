"""
Root conftest.py
================
Sets USE_DB=false before any test module is imported so that
create_app() uses in-memory repositories instead of hitting
the Neon database. This keeps the test suite fast and isolated.
"""
import os
os.environ.setdefault("USE_DB", "false")
