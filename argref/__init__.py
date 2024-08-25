import importlib.metadata

from argref.argref import AutolinkReference

__version__ = importlib.metadata.version("argref")

__all__ = ["AutolinkReference"]
