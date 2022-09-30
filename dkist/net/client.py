import os
import cgi
import json
import urllib.parse
import urllib.request
from typing import Any, List, Mapping, Iterable
from functools import partial
from collections import defaultdict

import aiohttp
import numpy as np
import parfive

import astropy.units as u
from astropy.table import TableAttribute
from astropy.time import Time
from sunpy.net import attr
from sunpy.net import attrs as sattrs
from sunpy.net.base_client import (BaseClient, QueryResponseRow,
                                   QueryResponseTable, convert_row_to_table)

from dkist.utils.inventory import INVENTORY_KEY_MAP

from . import attrs as dattrs
from .attr_walker import walker

__all__ = ["DKISTQueryResponseTable", "DKISTClient"]


class DKISTQueryResponseTable(QueryResponseTable):
    """
    Results of a DKIST Dataset search.
    """

    # Define some class properties to better format the results table.
    # TODO: remove experimentDescription from this list, when we can limit the
    # length of the field to something nicer
    hide_keys: List[str] = ["Storage Bucket", "Full Stokes", "asdf Filename", "Recipie Instance ID",
                            "Recipie Run ID", "Recipe ID", "Movie Filename", "Level 0 Frame count",
                            "Creation Date", "Last Updated", "Experiment IDs", "Proposal IDs",
                            "Preview URL", "Quality Report Filename", "Experiment Description"]

    # These keys are shown in the repr and str representations of this class.
    _core_keys = TableAttribute(default=["Start Time", "End Time", "Instrument", "Wavelength"])


    @staticmethod
    def _process_table(results: "DKISTQueryResponseTable") -> "DKISTQueryResponseTable":
        times = ["Creation Date", "End Time", "Start Time", "Last Updated", "Embargo End Date"]
        units = {"Exposure Time": u.s, "Wavelength Min": u.nm,
                 "Wavelength Max": u.nm, "Dataset Size": u.Gibyte,
                 "Filter Wavelengths": u.nm, "Average Spectral Sampling": u.nm,
                 "Average Spatial Sampling": u.arcsec, "Average Temporal Sampling": u.s}

        for colname in times:
            if colname not in results.colnames:
                continue  # pragma: no cover
            if not any([v is None for v in results[colname]]):
                results[colname] = Time(results[colname])

        for colname, unit in units.items():
            if colname not in results.colnames:
                continue  # pragma: no cover
            none_values = results[colname] == None
            if any(none_values):
                results[colname][none_values] = np.nan
            results[colname] = u.Quantity(results[colname], unit=unit)

        if results:
            results["Wavelength"] = u.Quantity([results["Wavelength Min"], results["Wavelength Max"]]).T
            results.remove_columns(("Wavelength Min", "Wavelength Max"))

        return results

    @classmethod
    def from_results(cls, results: Iterable[Mapping[str, Any]], *, client: "DKISTClient") -> "DKISTQueryResponseTable":
        """
        Construct the results table from the API results.
        """
        new_results = defaultdict(list)
        for result in results:
            for key, value in result.items():
                new_results[INVENTORY_KEY_MAP[key]].append(value)

        data = cls._process_table(cls(new_results, client=client))
        data = data._reorder_columns(cls._core_keys.default, remove_empty=True)

        return data


class DKISTClient(BaseClient):
    """
    Search DKIST datasets and retrieve metadata files describing them.

    .. note::

        This class is not intended to be used directly.
        You should use `~sunpy.net.Fido` to search and download data, see :ref:`sunpy:fido_guide`.
    """
    @property
    def _dataset_search_url(self):
        # Import here to avoid circular import
        from dkist.net import conf

        return conf.dataset_endpoint + conf.dataset_search_path

    @property
    def _metadata_streamer_url(self):
        # Import here to avoid circular import
        from dkist.net import conf

        return conf.download_endpoint

    def search(self, *args) -> DKISTQueryResponseTable:
        """
        Search for datasets provided by the DKIST data centre.
        """

        query = attr.and_(*args)
        queries = walker.create(query)

        results = []
        for url_parameters in queries:
            query_string = urllib.parse.urlencode(url_parameters)
            full_url = f"{self._dataset_search_url}?{query_string}"
            data = urllib.request.urlopen(full_url)
            data = json.loads(data.read())
            results += data["searchResults"]

        return DKISTQueryResponseTable.from_results(results, client=self)

    @staticmethod
    def _make_filename(path: os.PathLike, row: QueryResponseRow,
                       resp: aiohttp.ClientResponse, url: str):
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
    def fetch(self, query_results: QueryResponseTable, *,
              path: os.PathLike = None,
              downloader: parfive.Downloader, **kwargs):
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
        if not len(query_results):
            return

        for row in query_results:
            url = f"{self._metadata_streamer_url}/asdf?datasetId={row['Dataset ID']}"
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
                if x.value.lower() not in ("stokes_parameters", "intensity", "spectral_axis", "temporal_axis"):
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
