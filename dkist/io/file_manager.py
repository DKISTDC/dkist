"""
This file contains the DKIST specific FileManager code.
"""

import os
from typing import Any, Protocol
from pathlib import Path

import parfive

from dkist.io.dask.striped_array import FileManager
from dkist.utils.inventory import humanize_inventory, path_format_inventory

__all__ = ["DKISTFileManager"]


class FileManagerProtocol(Protocol):
    """
    Protocol to quack like a `FileManager` object for the `DKISTFileManager`.
    """

    @property
    def basepath(self) -> os.PathLike: ...

    @basepath.setter
    def basepath(self, path: str | os.PathLike) -> None: ...

    @property
    def filenames(self) -> list[str]: ...


class DKISTFileManager:
    """
    Manage the collection of FITS files backing a `~dkist.Dataset`.

    Each `~dkist.Dataset` object is backed by a number of FITS files, each holding a
    slice of the total array. This class provides tools for inspecting and
    retrieving these FITS files, as well as specifying where to load these
    files from.
    """

    __slots__ = ["_fm", "_ndcube"]

    @classmethod
    def from_parts(cls, fileuris, target, dtype, shape, *, loader, basepath=None, chunksize=None):
        return cls(
            FileManager.from_parts(
                fileuris, target, dtype, shape, loader=loader, basepath=basepath, chunksize=chunksize
            )
        )

    def __init__(self, file_manager: FileManagerProtocol, parent_ndcube: Any = None):
        self._fm = file_manager
        # When this object is attached to a Dataset object this attribute will
        # be populated with a reference to that Dataset instance.
        # The name `_ndcube` comes from using NDCubeLinkedDescriptor in Dataset
        self._ndcube = parent_ndcube

    @property
    def basepath(self) -> os.PathLike:
        """
        The path all arrays read data from.
        """
        return self._fm.basepath

    @basepath.setter
    def basepath(self, basepath: str | os.PathLike):
        self._fm.basepath = basepath

    def __getattr__(self, attr):
        # We want to proxy most API through to the FileManager object
        return getattr(self._fm, attr)

    @property
    def _metadata_streamer_url(self) -> str:
        # Import here to avoid circular import
        from dkist.net import conf

        return conf.download_endpoint

    def quality_report(self, path: str | os.PathLike = None, overwrite: bool = None) -> parfive.Results:
        """
        Download the quality report PDF.

        Parameters
        ----------
        path
            The destination path to save the file to. See
            `parfive.Downloader.simple_download` for details.
            The default path is ``.basepath``, if ``.basepath`` is None it will
            default to `~/`.
        overwrite
            Set to `True` to overwrite file if it already exists. See
            `parfive.Downloader.simple_download` for details.

        Returns
        -------
        results: `parfive.Results`
            A `~parfive.Results` object containing the filepath of the
            downloaded file if the download was successful, and any errors if it
            was not.
        """
        dataset_id = self._ndcube.meta["inventory"]["datasetId"]
        url = f"{self._metadata_streamer_url}/quality?datasetId={dataset_id}"
        if path is None and self.basepath:
            path = self.basepath
        return parfive.Downloader.simple_download([url], path=path, overwrite=overwrite)

    def preview_movie(self, path: str | os.PathLike = None, overwrite: bool = None) -> parfive.Results:
        """
        Download the preview movie.

        Parameters
        ----------
        path
            The destination path to save the file to. See
            `parfive.Downloader.simple_download` for details.
            The default path is ``.basepath``, if ``.basepath`` is None it will
            default to `~/`.
        overwrite
            Set to `True` to overwrite file if it already exists. See
            `parfive.Downloader.simple_download` for details.

        Returns
        -------
        results: `parfive.Results`
            A `~parfive.Results` object containing the filepath of the
            downloaded file if the download was successful, and any errors if it
            was not.
        """
        dataset_id = self._ndcube.meta["inventory"]["datasetId"]
        url = f"{self._metadata_streamer_url}/movie?datasetId={dataset_id}"
        if path is None and self.basepath:
            path = self.basepath
        return parfive.Downloader.simple_download([url], path=path, overwrite=overwrite)

    def download(
        self,
        path: str | os.PathLike = None,
        destination_endpoint: str = None,
        progress: bool = True,
        wait: bool = True,
        label: str = None,
    ):
        """
        Start a Globus file transfer for all files in this Dataset.

        Parameters
        ----------
        path
            The path to save the data in, must be accessible by the Globus
            endpoint.
            The default value is ``.basepath``, if ``.basepath`` is None it will
            default to ``/~/``.
            It is possible to put placeholder strings in the path with any key
            from the dataset inventory dictionary which can be accessed as
            ``ds.meta['inventory']``. An example of this would be
            ``path="~/dkist/{datasetId}"`` to save the files in a folder named
            with the dataset ID being downloaded.
            If ``path`` is specified, and ``destination_endpoint`` is `None`
            (i.e. you are downloading to a local Globus personal endpoint) this
            method will set ``.basepath`` to the value of the ``path=``
            argument, so that the array can be read from your transferred
            files.

        destination_endpoint
            A unique specifier for a Globus endpoint. If `None` a local
            endpoint will be used if it can be found, otherwise an error will
            be raised. See `~dkist.net.globus.get_endpoint_id` for valid
            endpoint specifiers.

        progress
           If `True` status information and a progress bar will be displayed
           while waiting for the transfer to complete.
           If ``progress="verbose"`` then all globus events generated during
           the transfer will be shown (by default only error messages are
           shown.)

        wait
            If `False` then the function will return while the Globus transfer task
            is still running. Setting ``wait=False`` implies ``progress=False``.

        label
            Label for the Globus transfer. If `None` then a default will be used.
        """
        # Import here to prevent triggering an import of `.net` with `dkist.dataset`.
        from dkist.net import conf as net_conf
        from dkist.net.helpers import _orchestrate_transfer_task

        if self._ndcube is None:
            raise ValueError("This file manager has no associated Dataset object, so the data can not be downloaded.")

        inv = self._ndcube.meta["inventory"]
        path_inv = path_format_inventory(humanize_inventory(inv))

        base_path = Path(net_conf.dataset_path.format(**inv))
        destination_path = path or self.basepath or "/~/"
        destination_path = Path(destination_path).as_posix()
        destination_path = Path(destination_path.format(**path_inv))

        # TODO: If we are transferring the whole dataset then we should use the
        # directory not the list of all the files in it.
        file_list = [base_path / fn for fn in self.filenames]
        file_list.append(Path("/") / inv["bucket"] / inv["asdfObjectKey"])
        if inv["browseMovieObjectKey"]:
            file_list.append(Path("/") / inv["bucket"] / inv["browseMovieObjectKey"])
        if inv["qualityReportObjectKey"]:
            file_list.append(Path("/") / inv["bucket"] / inv["qualityReportObjectKey"])

        # TODO: Ascertain if the destination path is local better than this
        is_local = not destination_endpoint

        _orchestrate_transfer_task(
            file_list,
            recursive=False,
            destination_path=destination_path,
            destination_endpoint=destination_endpoint,
            progress=progress,
            wait=wait,
            label=label,
        )

        if is_local:
            if str(destination_path).startswith("/~/"):
                local_destination = Path(str(destination_path)[1:])
            local_destination = destination_path.expanduser()
            self.basepath = local_destination
