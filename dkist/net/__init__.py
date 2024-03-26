"""
DKIST specific plugins for `sunpy.net` and download helpers.
"""
import dkist.config as _config

__all__ = ["DKISTClient", "conf", "transfer_complete_datasets"]


class Conf(_config.ConfigNamespace):
    """
    Configuration Parameters for the `dkist.net` Package.
    """
    default_page_size = _config.ConfigItem(300, "Default number of datasets to return in search results.")
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

    attr_max_age = _config.ConfigItem(7,
                                      "The number of days beyond which to refresh search attr values from the Data Center")


conf = Conf()

# Put imports after conf so that conf is initialized before import
from .client import DKISTClient
from .helpers import transfer_complete_datasets
