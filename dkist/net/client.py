import os
import json
import urllib.parse
import urllib.request
from typing import Any, Mapping, Iterable
from collections import defaultdict

from sunpy.net import attr
from sunpy.net import attrs as sattrs
from sunpy.net.base_client import BaseClient, QueryResponseTable

from . import attrs as dattrs
from .attr_walker import walker

__all__ = ['DKISTQueryReponse', 'DKISTDatasetClient']


class DKISTQueryResponseTable(QueryResponseTable):
    """
    Results of a DKIST Dataset search.
    """

    # Define some class properties to better format the results table.

    # These keys are shown in the repr and str representations of this class.
    _core_keys = ("Start Time", "End Time", "Instrument", "Wavelength Min", "Wavelength Max")

    # Map the keys in the response to human friendly ones.
    key_map: Mapping[str, str] = {
        "asdfObjectKey": "asdf Filename",
        "boundingBox": "Bounding Box",
        "browseMovieObjectKey": "Movie Filename",
        "browseMovieUrl": "Preview URL",
        "bucket": "Storage Bucket",
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

    @classmethod
    def from_results(cls, results: Iterable[Mapping[str, Any]], *, client: "DKISTDatasetClient") -> "DKISTQueryResponseTable":
        """
        Construct the results table from the API results.
        """
        # TODO: Follow the other sunpy clients and make wavelength and len-2 Quantity
        # Also map Time to Time objects etc
        new_results = defaultdict(list)
        for result in results:
            for key, value in result.items():
                new_results[cls.key_map[key]].append(value)

        return cls(new_results, client=client)


class DKISTDatasetClient(BaseClient):
    """
    Search DKIST datasets and retrie metadata files describing them.
    """

    _BASE_URL = os.environ.get("DKIST_DATASET_ENDPOINT", "https://dkistdcapi2.colorado.edu/datasets/v1")

    def search(self, *args) -> DKISTQueryResponseTable:
        """
        Search for datasets provided by the DKIST data centre.
        """
        query = attr.and_(*args)
        queries = walker.create(query)

        results = []
        for url_parameters in queries:
            query_string = urllib.parse.urlencode(url_parameters)

            full_url = f"{self._BASE_URL}?{query_string}"
            data = urllib.request.urlopen(full_url)
            data = json.loads(data.read())
            results += data["searchResults"]

        res = DKISTQueryResponseTable.from_results(results, client=self)
        all_cols: Iterable[str] = list(res.colnames)
        first_names = [n for n in res._core_keys if n in all_cols]
        extra_cols = [col for col in all_cols if col not in first_names]
        all_cols = first_names + extra_cols
        return res[[col for col in all_cols]]

    def fetch(self, *query_results, path=None, overwrite=False, progress=True,
              max_conn=5, downloader=None, wait=True, **kwargs):
        """
        Fetch asdf files describing the datasets.

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
    def _can_handle_query(cls, *query) -> bool:
        # This enables the client to register what kind of searches it can
        # handle, to prevent Fido using the incorrect client.
        from sunpy.net import attrs as a

        supported = set(walker.applymm.registry)
        # This function is only called with arguments of the query where they are assumed to be ANDed.
        supported.remove(attr.AttrAnd)
        query_attrs = set(type(x) for x in query)

        # The DKIST client only requires that one or more of the support attrs be present.
        if not query_attrs.issubset(supported) or len(query_attrs.intersection(supported)) < 1:
            return False

        for x in query:
            if isinstance(x, a.Instrument):
                # TODO: Obviously "inst" shouldn't be here, but it's in the test data.
                if x.value.lower() not in ("inst", "vbi", "vtf", "visp", "cryo-nirsp", "dl-nirsp"):
                    return False

            if isinstance(x, a.Physobs):
                if x.value.lower() not in ("stokes_parameters", "intensity"):
                    return False

            if isinstance(x, a.Level):
                if x.value not in (1, "1", "one"):
                    return False

        return True

    @classmethod
    def _attrs_module(cls):
        return 'dkist', 'dkist.net.attrs'

    @classmethod
    def register_values(cls):
        """
        Known search values for DKIST data, currently manually specified.
        """
        return {
            sattrs.Provider: [("DKIST", "Data provided by the DKIST Data Center")],
            # instrumentNames
            sattrs.Instrument: [("VBI", "Visible Broadband Imager"),
                                ("VISP", "Visible Spectro-Polarimeter"),
                                ("VTF", "Visible Tunable Filter"),
                                ("Cryo-NIRSP", "Cryogenic Near Infrared SpectroPolarimiter"),
                                ("DL-NIRSP", "Diffraction-Limited Near-InfraRed Spectro-Polarimeter")],
            # hasAllStokes
            sattrs.Physobs: [("stokes_parameters", "Stokes I, Q, U and V are provided in the dataset"),
                             ("intensity", "Only Stokes I is provided in the dataset.")],
            # isEmbargoed
            dattrs.Embargoed: [("True", "Data is subject to access restrictions."),
                               ("False", "Data is not subject to access restrictions.")],
            # targetTypes
            #dattrs.TargetType: [],  # This should be a controlled list.

            # Completeness
            sattrs.Level: [("1", "DKIST data calibrated to level 1.")],
        }
