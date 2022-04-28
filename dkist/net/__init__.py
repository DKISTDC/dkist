"""
DKIST specific plugins for `sunpy.net` and download helpers.

.. warning::

   Classes in this module should not be used directly, they should be used
   through the `sunpy.net.Fido` and `sunpy.net.attrs.dkist` modules. The
   classes in this module will be automatically registered with sunpy upon
   importing this module with `import dkist.net`.

"""
import dkist.config as _config

from .client import DKISTDatasetClient

__all__ = ["DKISTDatasetClient", "conf"]


class Conf(_config.ConfigNamespace):
    """
    Configuration Parameters for the IO Package.
    """
    dataset_endpoint = _config.ConfigItem("https://api.dkistdc.nso.edu/datasets/",
                                          "Base URL for dataset search.")
    download_endpoint = _config.ConfigItem("https://api.dkistdc.nso.edu/download",
                                           "Base URL for metadata streamer")
    dataset_search_path = _config.ConfigItem("v1", "Path for the dataset search endpoint")
    dataset_search_values_path = _config.ConfigItem("v1/searchValues",
                                                    "Path for querying known values "
                                                    "for dataset search parameters.")
    dataset_config_path = _config.ConfigItem("v1/config", "Path for dataset config endpoint.")

    dataset_path = _config.ConfigItem("/{bucket}/{primaryProposalId}/{datasetId}",
                                      "The path template to a dataset on the main endpoint.")


conf = Conf()
