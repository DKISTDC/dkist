"""
This file contains the entry points for asdf.
"""
import importlib.resources as importlib_resources

from asdf.extension import ManifestExtension
from asdf.resource import DirectoryResourceMapping

from dkist.io.asdf.converters import (AsymmetricMappingConverter, CoupledCompoundConverter,
                                      DatasetConverter, FileManagerConverter, RavelConverter,
                                      TiledDatasetConverter, VaryingCelestialConverter)


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
    dkist_converters = [FileManagerConverter(), DatasetConverter(), TiledDatasetConverter()]
    wcs_converters = [VaryingCelestialConverter(), CoupledCompoundConverter(), RavelConverter(), AsymmetricMappingConverter()]
    return [
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-1.2.0",
                                   converters=dkist_converters),
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-1.1.0",
                                   converters=dkist_converters),
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-1.0.0",
                                   converters=dkist_converters),
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-wcs-1.3.0",
                                   converters=wcs_converters),
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-wcs-1.2.0",
                                   converters=wcs_converters),
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-wcs-1.1.0",
                                   converters=wcs_converters),
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-wcs-1.0.0",
                                   converters=wcs_converters),
        # This manifest handles all pre-refactor tags
        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/dkist-0.9.0",
                                   converters=dkist_converters,
                                   # Register that this is a replacement for the old extension
                                   legacy_class_names=["dkist.io.asdf.extension.DKISTExtension"])
    ]
