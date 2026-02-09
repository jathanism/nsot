"""Emit the version using package metadata."""

from importlib.metadata import version

__version__ = version("nsot")
