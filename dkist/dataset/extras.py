import dask.array

import asdf
from astropy.table import Table

from dkist.io.dask.loaders import AstropyFITSLoader


class DatasetExtra:
    """
    This class represents information about all the files for a specific dataset extra.
    """
    def __init__(self, name: str, headers: Table, ears: list[asdf.ExternalArrayReference]):
        self._name = name
        self._headers = headers
        self._ears = ears

    @property
    def name(self) -> str:
        return self._name

    @property
    def headers(self) -> Table:
        return self._headers

    @property
    def data(self) -> list[dask.array.Array]:
        return [dask.array.from_array(AstropyFITSLoader(
            ear.fileuri,
            ear.shape,
            ear.dtype,
            ear.target,
            basepath=None,
        )) for ear in self._ears]
