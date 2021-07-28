from collections import UserDict

__all__ = ['SliceCache']


class SliceCache(UserDict):
    """
    A dictionary where the keys are `slice` objects.

    Slices aren't hashable, so we do some crazy processing to convert them to tuples.
    """
    def _slice_to_hashable(self, aslice):
        if isinstance(aslice, slice):
            return aslice.__reduce__()[1]

        return tuple((self._slice_to_hashable(sub_slice) for sub_slice in aslice))

    def __getitem__(self, key):
        key = self._slice_to_hashable(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        key = self._slice_to_hashable(key)
        return super().__setitem__(key, item)
