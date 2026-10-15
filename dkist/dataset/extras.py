import os
from pathlib import Path

import dask.array

import asdf
from astropy.table import Table

from dkist.io.dask.loaders import AstropyFITSLoader


class DatasetExtra:
    """
    This class represents information about all the files for a specific dataset extra.

    Parameters
    ----------

    name
        The name of the extra.
    full_header_table
        The header table of either headers for this extra or all
        extras associated with the dataset.
    header_rows
        The rows in ``full_header_table`` which correspond to this
        extra (in the order of ``ears``). If `None` then all rows from
        ``full_header_table`` are used.
    ears
        The `asdf.ExternalArrayReference` objects for the extra data
        in the FITS files, must be the same length as
        ``full_header_table[header_rows]``.
    basepath
        The path where the FITS files described by the URIs in
        ``ears`` can be found. If `None`, the URIs are assumed to be absolute.
    """

    def __init__(
        self,
        name: str,
        *,
        full_header_table: Table,
        header_rows: list[int] | None = None,
        ears: list[asdf.ExternalArrayReference],
        basepath: os.PathLike | None = None,
    ):
        self._name = name
        self._full_header_table = full_header_table
        self._header_rows = header_rows
        self._ears = ears
        self.basepath = basepath

    def __str__(self) -> str:
        shapes: list[tuple[int, ...]] = [e.shape for e in self._ears]
        if len(set(shapes)) == 1:
            shapes = list(shapes)[0]
        else:
            shapes = tuple(shapes)
        return f"DatasetExtra<name={self.name}, length={len(self.headers)}, shape={shapes}>"

    def __repr__(self) -> str:
        return f"<{self} object at {hex(id(self))}>"

    @property
    def basepath(self) -> Path | None:
        return self._basepath

    @basepath.setter
    def basepath(self, basepath: os.PathLike | None):
        if basepath is None:
            self._basepath = basepath
        else:
            self._basepath = Path(basepath)

    @property
    def name(self) -> str:
        return self._name

    @property
    def headers(self) -> Table:
        if self._header_rows is not None:
            return self._full_header_table[self._header_rows]
        return self._full_header_table

    @property
    def data(self) -> list[dask.array.Array]:
        return [
            dask.array.from_array(
                AstropyFITSLoader(
                    ear.fileuri,
                    ear.shape,
                    ear.dtype,
                    ear.target,
                    basepath=self.basepath,
                )
            )
            for ear in self._ears
        ]
