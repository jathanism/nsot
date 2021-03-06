"""
Emit the version using package metadata.

Please do not edit this file. The version should be managed using ``poetry
version``.
"""

try:
    from importlib import metadata
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata


__version__ = metadata.version(__package__)
