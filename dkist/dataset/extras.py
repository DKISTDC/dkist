import os
from pathlib import Path

import dask.array

import asdf
from astropy.table import Table

from dkist.io.dask.loaders import AstropyFITSLoader


class DatasetExtra:
    """
    This class represents information about all the files for a specific dataset extra.
    """

    def __init__(self, name: str, headers: Table, ears: list[asdf.ExternalArrayReference], basepath: os.PathLike | None = None):
        self._name = name
        self._headers = headers
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
        return self._headers

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
