import importlib.metadata

from mkdocs_argref_plugin.argref import AutolinkReference

__version__ = importlib.metadata.version("mkdocs_argref_plugin")

__all__ = ["AutolinkReference"]
