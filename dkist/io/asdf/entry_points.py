"""
This file contains the entry points for asdf.
"""
import sys

from asdf.extension import ManifestExtension
from asdf.resource import DirectoryResourceMapping

if sys.version_info < (3, 9):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

from dkist.io.asdf.converters import DatasetConverter, FileManagerConverter, TiledDatasetConverter


def get_resource_mappings():
    """
    Get the resource mapping instances for myschemas
    and manifests.  This method is registered with the
    asdf.resource_mappings entry point.

    Returns
    -------
    list of collections.abc.Mapping
    """
    from . import resources
    resources_root = importlib_resources.files(resources)

    return [
        DirectoryResourceMapping(
            resources_root / "schemas", "asdf://dkist.nso.edu/schemas/"),
        DirectoryResourceMapping(
            resources_root / "manifests", "asdf://dkist.nso.edu/manifests/"),
    ]


def get_extensions():
    """
    Get the list of extensions.
    """
    converters=[FileManagerConverter(), DatasetConverter(), TiledDatasetConverter()]
    return [
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-1.0.0",
                                   converters=converters),
        # This manifest handles all pre-refactor tags
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-0.9.0",
                                   converters=converters)
    ]
