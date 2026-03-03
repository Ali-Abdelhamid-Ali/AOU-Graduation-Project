"""Backend package bootstrap helpers."""

from importlib import import_module
import sys


# Preserve existing ``src.*`` imports when the app is imported as ``backend.main``.
sys.modules.setdefault("src", import_module(".src", __name__))
