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
from astropy.wcs.wcsapi.wrappers.sliced_wcs import sanitize_slices
from sunpy.util.decorators import add_common_docstring

from dkist.io.loaders import AstropyFITSLoader
from dkist.io.utils import SliceCache

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
        ear0 = np.array(ears).flat[0]
        shape = ear0.shape
        dtype = ear0.dtype
        target = ear0.target

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
class BaseFITSArrayCollection(ExternalArrayReferenceCollection, metaclass=abc.ABCMeta):
    """
    A collection of references to homogenous FITS arrays.
    """

    @classmethod
    def from_tree(cls, node, ctx):
        # TODO: Work out a way over overriding this at dataset load.
        filepath = Path((ctx.uri or ".").replace("file:", ""))
        base_path = filepath.parent

        array_container = cls(node['fileuris'],
                              node['target'],
                              node['datatype'],
                              node['shape'],
                              loader=AstropyFITSLoader,
                              basepath=base_path)
        return array_container


    def __init__(self, fileuris, target, dtype, shape, *, loader, **kwargs):
        super().__init__(fileuris, target, dtype, shape)
        self.reference_array = np.asarray(self.external_array_references, dtype=object)

        self.full_output_shape = self.get_output_shape()

        # Initialise internal attributes
        self._loader = None
        self._loader_array_cache = None
        self._array_cache = SliceCache()

        # Store the loader and the kwargs as a partial function.
        self.loader_class = loader
        self.loader = partial(loader, **kwargs)

    def get_output_shape(self, aslice=None):
        ref_array = self.reference_array
        if aslice is not None:
            ref_array = ref_array[aslice]

        # If the first dimension of the external arrays are one we are going to
        # squash that dimension.
        reference_shape = self.shape
        if reference_shape[0] == 1:
            reference_shape = reference_shape[1:]

        # If for some reason we have a collection of one, our output shape is
        # the (squashed) array shape.
        if self.reference_array.size == 1:
            output_shape = reference_shape
        else:
            output_shape = tuple(list(ref_array.shape) + list(reference_shape))

        return output_shape

    @property
    def loader(self):
        """
        Partial function version of the loader class with kwargs set.
        """
        return self._loader

    @loader.setter
    def loader(self, loader):
        """
        Update the loader, clear the cache.
        """
        self._loader = loader
        self._loader_array_cache = None
        self._array_cache = SliceCache()

    def set_loader_kwargs(self, **kwargs):
        """
        Set new kwargs for the loader.
        """
        self.loader = partial(self.loader_class, **kwargs)

    @property
    def loader_array(self):
        """
        A numpy array of correct shape with instantiated loader objects.
        """
        if self._loader_array_cache is None:
            loader_array = np.empty_like(self.reference_array, dtype=object)
            for i, ele in enumerate(self.reference_array.flat):
                loader_array.flat[i] = self._loader(ele)
            self._loader_array_cache = loader_array

        return self._loader_array_cache

    def _parse_aslice(self, aslice):
        """
        Helper to set a default aslice
        """
        if aslice is None:
            aslice = tuple([slice(None)] * self.reference_array.ndim)

        if not isinstance(aslice, tuple):
            aslice = (aslice,)
        return aslice

    def get_filenames(self, aslice=None):
        """
        Return a list of file names referenced by this Array Container.
        """
        reference_array = self.reference_array[aslice]
        return [ear.fileuri for ear in reference_array.flat]

    def get_array(self, aslice=None):
        """
        Return an array type for the given array of external file references.

        Parameters
        ----------
        aslice: tuple, slice
            The slice of the array collection to generate an array for.
        """
        aslice = self._parse_aslice(aslice)
        output_shape = self.get_output_shape(aslice)
        return self._array_cache.get(aslice,
                                     self.get_new_array(self.loader_array, aslice, output_shape))

    @staticmethod
    @abc.abstractmethod
    def get_new_array(loader_array, aslice, output_shape):
        """
        Generate a whole new array.
        """


@add_common_docstring(append=common_parameters)
class NumpyFITSArrayCollection(BaseFITSArrayCollection):
    """
    Load an array of `~asdf.ExternalArrayReference` objects into a single
    in-memory numpy array.
    """
    @staticmethod
    def get_new_array(loader_array, aslice, output_shape):
        """
        The `~numpy.ndarray` associated with this array of references.
        """
        aa = list(map(np.asarray, loader_array[aslice].flat))
        return np.stack(aa, axis=0).reshape(output_shape)


@add_common_docstring(append=common_parameters)
class DaskFITSArrayCollection(BaseFITSArrayCollection):
    """
    Load an array of `~asdf.ExternalArrayReference` objects into a
    `dask.array.Array` object.
    """

    @staticmethod
    def get_new_array(loader_array, aslice, output_shape):
        """
        The `~dask.array.Array` associated with this array of references.
        """
        return stack_loader_array(loader_array[aslice]).reshape(output_shape)


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
