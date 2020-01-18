"""
This submodule provides tools for resolving arrays of
`asdf.ExternalArrayReference` objects to Python array-like objects.
"""
import abc
from pathlib import Path
from functools import partial

import dask.array as da
import numpy as np

from asdf.tags.core.external_reference import ExternalArrayReference
from sunpy.util.decorators import add_common_docstring

from dkist.io.loaders import AstropyFITSLoader

__all__ = ['BaseFITSArrayContainer', 'NumpyFITSArrayContainer', 'DaskFITSArrayContainer']


# This class should probably live in asdf, and there are PRs open to add it.
# However, there are issues with schemas if it's in asdf, and also I don't want
# to depend on asdf master right now, so I am copying it in here.
class ExternalArrayReferenceCollection:
    """
    A homogeneous collection of `asdf.ExternalArrayReference` like objects.

    This class differs from a list of `asdf.ExternalArrayReference` objects
    because all of the references have the same shape, dtype and target. This
    allows for much more yaml and schema efficient storage in the asdf tree.

    Parameters
    ----------

    fileuris: `list` or `tuple`
        An interable of paths to be referenced. Can be nested arbitarily deep.

    target: `object`
        Some internal target to the data in the files. Examples may include a HDU
        index, a HDF path or an asdf fragment.

    dtype: `str`
        The (numpy) dtype of the contained arrays.

    shape: `tuple`
        The shape of the arrays to be loaded.
    """

    @classmethod
    def _validate_homogenaity(cls, shape, target, dtype, ear):
        """
        Ensure that if constructing from `asdf.ExternalArrayReference` objects
        all of them have the same shape, dtype and target.
        """
        if isinstance(ear, (list, tuple)):
            return list(map(partial(cls._validate_homogenaity, shape, target, dtype), ear))

        if not isinstance(ear, ExternalArrayReference):
            raise TypeError("Every element of must be an instance of ExternalArrayReference.")
        if ear.dtype != dtype:
            raise ValueError(f"The Reference {ear} does not have the same dtype as the first reference.")
        if ear.shape != shape:
            raise ValueError(f"The Reference {ear} does not have the same shape as the first reference.")
        if ear.target != target:
            raise ValueError(f"The Reference {ear} does not have the same target as the first reference.")
        return ear.fileuri

    @classmethod
    def from_external_array_references(cls, ears, **kwargs):
        """
        Construct a collection from a (nested) iterable of
        `asdf.ExternalArrayReference` objects.
        """
        shape = ears[0].shape
        dtype = ears[0].dtype
        target = ears[0].target

        for i, ele in enumerate(ears):
            uris = cls._validate_homogenaity(shape, target, dtype, ears)

        return cls(uris, target, dtype, shape, **kwargs)

    def __init__(self, fileuris, target, dtype, shape):
        self.shape = tuple(shape)
        self.dtype = dtype
        self.target = target
        self.fileuris = fileuris

    def _to_ears(self, urilist):
        if isinstance(urilist, (list, tuple)):
            return list(map(self._to_ears, urilist))
        return ExternalArrayReference(urilist, self.target, self.dtype, self.shape)

    @property
    def external_array_references(self):
        """
        Represent this collection as a list of `asdf.ExternalArrayReference` objects.
        """
        return self._to_ears(self.fileuris)

    def __getitem__(self, item):
        uris = self.fileuris[item]
        if isinstance(uris, str):
            uris = [uris]
        return type(self)(uris, self.target, self.dtype, self.shape)

    def __len__(self):
        return len(self.fileuris)

    def __eq__(self, other):
        uri = self.fileuris == other.fileuris
        target = self.target == other.target
        dtype = self.dtype == other.dtype
        shape = self.shape == other.shape

        return all((uri, target, dtype, shape))

    @classmethod
    def to_tree(cls, data, ctx):
        node = {}
        node['fileuris'] = data.fileuris
        node['target'] = data.target
        node['datatype'] = data.dtype
        node['shape'] = data.shape
        return node

    @classmethod
    def from_tree(cls, tree, ctx):
        return cls(tree['fileuris'], tree['target'], tree['datatype'], tree['shape'])


common_parameters = """

    Parameters
    ----------

    fileuris: `list` or `tuple`
        An interable of paths to be referenced. Can be nested arbitarily deep.

    target: `object`
        Some internal target to the data in the files. Examples may include a HDU
        index, a HDF path or an asdf fragment.

    dtype: `str`
        The (numpy) dtype of the contained arrays.

    shape: `tuple`
        The shape of the arrays to be loaded.

    loader : `dkist.io.BaseFITSLoader`
        The loader subclass to use to resolve each `~asdf.ExternalArrayReference`.

    kwargs : `dict`
        Extra keyword arguments are passed to the loader class.
"""

@add_common_docstring(append=common_parameters)
class BaseFITSArrayContainer(ExternalArrayReferenceCollection, metaclass=abc.ABCMeta):
    """
    A collection of references to homogenous FITS arrays.
    """

    @classmethod
    def from_tree(cls, node, ctx):
        # TODO: Work out a way over overriding this at dataset load.
        filepath = Path((ctx.uri or ".").replace("file:", ""))
        base_path = filepath.parent

        # TODO: The choice of Dask and Astropy here should be in a config somewhere.
        array_container = DaskFITSArrayContainer(node['fileuris'],
                                                 node['target'],
                                                 node['datatype'],
                                                 node['shape'],
                                                 loader=AstropyFITSLoader,
                                                 basepath=base_path)
        return array_container


    def __init__(self, fileuris, target, dtype, shape, *, loader, **kwargs):
        super().__init__(fileuris, target, dtype, shape)
        reference_array = np.asarray(self.external_array_references, dtype=object)

        # If the first dimension is one we are going to squash it.
        reference_shape = self.shape
        if reference_shape[0] == 1:
            reference_shape = reference_shape[1:]
        if len(reference_array) == 1:
            self.output_shape = reference_shape
        else:
            self.output_shape = tuple(list(reference_array.shape) + list(reference_shape))

        loader_array = np.empty_like(reference_array, dtype=object)
        for i, ele in enumerate(reference_array.flat):
            loader_array.flat[i] = loader(ele, **kwargs)

        self.loader_array = loader_array
        self._loader = partial(loader, **kwargs)

    def __getitem__(self, item):
        uris = self.fileuris[item]
        if isinstance(uris, str):
            uris = [uris]
        return type(self)(uris, self.target, self.dtype, self.shape, loader=self._loader)

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        names = []
        for furi in np.asarray(self.fileuris).flat:
            names.append(furi)
        return names

    @abc.abstractproperty
    def array(self):
        """
        Return an array type for the given array of external file references.
        """


@add_common_docstring(append=common_parameters)
class NumpyFITSArrayContainer(BaseFITSArrayContainer):
    """
    Load an array of `~asdf.ExternalArrayReference` objects into a single
    in-memory numpy array.
    """

    def __array__(self):
        """
        This dosen't seem to work if it returns a Dask array, so it's only
        useful here.
        """
        return self.array

    @property
    def array(self):
        """
        The `~numpy.ndarray` associated with this array of references.
        """
        aa = map(np.asarray, self.loader_array.flat)
        return np.stack(aa, axis=0).reshape(self.output_shape)


@add_common_docstring(append=common_parameters)
class DaskFITSArrayContainer(BaseFITSArrayContainer):
    """
    Load an array of `~asdf.ExternalArrayReference` objects into a
    `dask.array.Array` object.
    """

    @property
    def array(self):
        """
        The `~dask.array.Array` associated with this array of references.
        """
        return stack_loader_array(self.loader_array).reshape(self.output_shape)


def stack_loader_array(loader_array):
    """
    Stack a loader array along each of its dimensions.

    This results in a dask array with the correct chunks and dimensions.

    Parameters
    ----------
    loader_array : `dkist.io.reference_collections.BaseFITSArrayContainer`

    Returns
    -------
    array : `dask.array.Array`
    """
    if len(loader_array.shape) == 1:
        return da.stack(loader_to_dask(loader_array))
    stacks = []
    for i in range(loader_array.shape[0]):
        stacks.append(stack_loader_array(loader_array[i]))
    return da.stack(stacks)


def loader_to_dask(loader_array):
    """
    Map a call to `dask.array.from_array` onto all the elements in ``loader_array``.

    This is done so that an explicit ``meta=`` argument can be provided to
    prevent loading data from disk.
    """

    if len(loader_array.shape) != 1:
        raise ValueError("Can only be used on one dimensional arrays")

    # The meta argument to from array is used to determine properties of the
    # array, such as dtype. We explicitly specify it here to prevent dask
    # trying to auto calculate it by reading from the actual array on disk.
    meta = np.zeros((0,), dtype=loader_array[0].dtype)

    to_array = partial(da.from_array, meta=meta)

    return map(to_array, loader_array)
