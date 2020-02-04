import json
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Sequence

import astropy.table
from sunpy.net import attr
from sunpy.net import attrs as sattrs
from sunpy.net.base_client import BaseClient

from . import attrs as dattrs
from .attr_walker import walker

__all__ = ['DKISTQueryReponse', 'DKISTDatasetClient']


class DKISTQueryReponse(Sequence):
    """
    """
    _core_keys = ("Start Time", "End Time", "Instrument", "Wavelength Min", "Wavelength Max")

    def __init__(self, table=None):
        self.table = table or astropy.table.Table()

    @property
    def client(self):
        return DKISTDatasetClient()

    def __len__(self):
        return len(self.table)

    def __getitem__(self, item):
        return type(self)(self.table[item])

    def __iter__(self):
        return (t for t in [self])

    def build_table(self):
        return self.table

    def response_block_properties(self):
        """
        Returns a set of class attributes on all the response blocks.
        """
        raise NotImplementedError()

    def __str__(self):
        """Print out human-readable summary of records retrieved"""
        return "\n".join(self.build_table()[self._core_keys].pformat(max_width=200, show_dtype=False))

    def __repr__(self):
        """Print out human-readable summary of records retrieved"""
        return object.__repr__(self) + "\n" + str(self)

    @classmethod
    def from_results(cls, results):
        res = cls()
        res._append_results(results)
        return res

    def _append_results(self, results):
        """
        Append a list of results from the API.

        This method translates the API names into ones similar to the query attrs.

        Parameters
        ----------
        results : `list`
            A list of dicts as returned by the dataset search API.
        """
        key_map = {
            "asdfObjectKey": "asdf Filename",
            "boundingBox": "Bounding Box",
            "browseMovieObjectKey": "Movie Filename",
            "browseMovieUrl": "Preview URL",
            "bucket": "bucket",
            "contributingExperimentIds": "Experiment IDs",
            "contributingProposalIds": "Proposal IDs",
            "createDate": "Creation Date",
            "datasetId": "Dataset ID",
            "datasetSize": "Dataset Size",
            "embargoEndDate": "Embargo End Date",
            "endTime": "End Time",
            "experimentDescription": "Experiment Description",
            "exposureTime": "Exposure Time",
            "filterWavelengths": "Filter Wavelengths",
            "frameCount": "Number of Frames",
            "hasAllStokes": "Full Stokes",
            "instrumentName": "Instrument",
            "isDownloadable": "Downloadable",
            "isEmbargoed": "Embargoed",
            "observables": "Observables",
            "originalFrameCount": "Level 0 Frame count",
            "primaryExperimentId": "Primary Experiment ID",
            "primaryProposalId": "Primary Proposal ID",
            "qualityAverageFriedParameter": "Average Fried Parameter",
            "qualityAveragePolarimetricAccuracy": "Average Polarimetric Accuracy",
            "recipeId": "Recipe ID",
            "recipeInstanceId": "Recipie Instance ID",
            "recipeRunId": "Recipie Run ID",
            "startTime": "Start Time",
            "stokesParameters": "Stokes Parameters",
            "targetType": "Target Type",
            "updateDate": "Last Updated",
            "wavelengthMax": "Wavelength Max",
            "wavelengthMin": "Wavelength Min"
        }

        new_results = defaultdict(list)
        for result in results:
            for key, value in result.items():
                new_results[key_map[key]].append(value)

        full_table = astropy.table.Table(data=new_results)

        self.table = astropy.table.vstack(full_table, self.table)


class DKISTDatasetClient(BaseClient):
    """
    A client for search DKIST datasets and retrieving metadata files describing
    the datasets.
    """
    _BASE_URL = "http://10.224.182.25:31675/datasets/"

    def search(self, *args):
        """
        Search for datasets provided by the DKIST data centre.
        """
        query = attr.and_(*args)
        queries = walker.create(query)

        results = DKISTQueryReponse()
        for url_parameters in queries:
            query_string = urllib.parse.urlencode(url_parameters)

            full_url = f"{self._BASE_URL}?{query_string}"
            data = urllib.request.urlopen(full_url)
            data = json.loads(data.read())
            results._append_results(data["searchResults"])

        return results


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
