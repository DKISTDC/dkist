import json
import urllib.parse
import urllib.request

from sunpy.net import attr
from sunpy.net import attrs as sattrs
from sunpy.net.base_client import BaseClient

from . import attrs as dattrs
from .attr_walker import walker

__all__ = ['DKISTDatasetClient']


class DKISTQueryReponse:
    """
    """


class DKISTDatasetClient(BaseClient):
    """
    A client for search DKIST datasets and retrieving metadata files describing
    the datasets.
    """
    _BASE_URL = "http://10.10.10.10/datasets/v1/"

    def search(self, *args):
        """
        Search for datasets provided by the DKIST data centre.
        """
        query = attr.and_(*args)
        queries = walker.create(query)
        for url_parameters in queries:
            query_string = urllib.parse.urlencode(url_parameters)

            full_url = f"{self._BASE_URL}?{query_string}"
            data = urllib.request.urlopen(full_url)
            data = json.loads(data)


    def fetch(self, *query_results, path=None, overwrite=False, progress=True,
              max_conn=5, downloader=None, wait=True, **kwargs):
        """
        This enables the user to fetch the data using the client, after a search.

        Parameters
        ----------
        query_results:
            Results to download.
        path : `str` or `pathlib.Path`, optional
            Path to the download directory
        overwrite : `bool`, optional
            Replace files with the same name if True.

        progress : `bool`, optional
            Print progress info to terminal.

        max_conns : `int`, optional
            Maximum number of download connections.
        downloader : `parfive.Downloader`, optional
            The download manager to use.
        wait : `bool`, optional
           If `False` ``downloader.download()`` will not be called. Only has
           any effect if `downloader` is not `None`.

        Returns
        -------
        `parfive.Results`
            The results object, can be `None` if ``wait`` is `False`.
        """
        raise NotImplementedError("Download of asdf files is not yet implemented.")

    @classmethod
    def _can_handle_query(cls, *query):
        """
        This enables the client to register what kind of searches it can
        handle, to prevent Fido using the incorrect client.
        """
        # If any specific DKIST attrs
        # If Instrument is any of the known DKIST instruments
        # Should you be able to hit this client if you don't specify instrument??

    @classmethod
    def _attrs_module(cls):
        return 'dkist', 'dkist.net.attrs'

    @classmethod
    def register_values(cls):
        """
        Known search values for DKIST data, currently manually specified.
        """
        return {
            sattrs.vso.Provider: [("DKIST", "Data provided by the DKIST Data Center")],
            # instrumentNames
            sattrs.Instrument: [("VBI", "Visible Broadband Imager"),
                                ("VISP", ""),
                                ("VTF", "Visible Tunable Filter"),
                                ("Cryo-NIRSP", "Cryogenic Near Infrared SpectroPolarimiter"),
                                ("DL-NIRSP", "")],
            # hasAllStokes
            sattrs.vso.Physobs: [("stokes_parameters", "Stokes I, Q, U and V are provided in the dataset"),
                                 ("intensity", "Only Stokes I is provided in the dataset.")],
            # isEmbargoed
            dattrs.Embargoed: [(True, "Data is subject to access restrictions."),
                               (False, "Data is not subject to access restrictions.")],
            # targetTypes
            dattrs.TargetType: [],  # This should be a controlled list.

            # Completeness
            sattrs.Level: [("1", "DKIST data calibrated to level 1.")],
        }
