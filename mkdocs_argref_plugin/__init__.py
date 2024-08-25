import importlib.metadata

from argref.argref import AutolinkReference

__version__ = importlib.metadata.version("mkdocs_argref_plugin")

__all__ = ["AutolinkReference"]
