import os
import cgi
import json
import urllib.parse
import urllib.request
from typing import Any, Mapping, Iterable
from pathlib import Path
from functools import partial
from collections import defaultdict

from sunpy import config
from sunpy.net import attr
from sunpy.net import attrs as sattrs
from sunpy.net.base_client import (BaseClient, QueryResponseRow,
                                   QueryResponseTable, convert_row_to_table)

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

    _BASE_SEARCH_URL = os.environ.get("DKIST_DATASET_ENDPOINT", "https://dkistdcapi2.colorado.edu/datasets/v1")
    _BASE_ASDF_URL = os.environ.get("DKIST_ASDF_ENDPOINT", "https://dkistdcapi2.colorado.edu/download/")

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

    @staticmethod
    def _make_filename(path: os.PathLike, row: QueryResponseRow, resp: "aiohttp.ClientResponse", url: str):
        """
        Generate a filename for a file based on the Content Disposition header.
        """
        # The fallback name is just the dataset id.
        name = f"{row['Dataset ID']}.asdf"

        if resp:
            cdheader = resp.headers.get("Content-Disposition", None)
            if cdheader:
                _, params = cgi.parse_header(cdheader)
                name = params.get('filename', "")

        return str(path).format(file=name, **row.response_block_map)

    @convert_row_to_table
    def fetch(self, query_results: QueryResponseTable, *, path: os.PathLike = None, downloader: "parfive.Downloader", **kwargs):
        """
        Fetch asdf files describing the datasets.

        Parameters
        ----------
        query_results:
            Results to download.
        path : `str` or `pathlib.Path`, optional
            Path to the download directory
        downloader : `parfive.Downloader`
            The download manager to use.
        """
        if downloader is None:
            raise ValueError("The DKIST client should only be used via sunpy's Fido. "
                             "It does not support downloading files directly.")

        # This logic is being upstreamed into Fido
        if path is None:
            path = Path(config.get('downloads', 'download_dir')) / '{file}'
        elif isinstance(path, (str, os.PathLike)) and '{file}' not in str(path):
            path = Path(path) / '{file}'
        else:
            path = Path(path)

        path = path.expanduser()

        if not len(query_results):
            return

        for row in query_results:
            url = urllib.parse.urljoin(self._BASE_ASDF_URL, "?" + urllib.parse.urlencode((('datasetId', row['Dataset ID']),)))
            downloader.enqueue_file(url, filename=partial(self._make_filename, path, row))

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
