from dkist.io import DaskFITSArrayCollection

from ..types import DKISTType

__all__ = ['ArrayContainerType']

# Note: renaming this tag / schema from container to collection would have
# invalidated all asdf files generated so far, to avoid this I haven't renamed
# the tag / schema at the same time as the class it's serialising.

class ArrayContainerType(DKISTType):
    name = "array_container"
    types = ['dkist.io.array_collections.BaseFITSArrayCollection']
    requires = ['dkist']
    version = "0.2.0"

    @classmethod
    def from_tree(cls, node, ctx):
        return DaskFITSArrayCollection.from_tree(node, ctx)

    @classmethod
    def to_tree(cls, array_collection, ctx):
        return array_collection.to_tree(array_collection, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        """
        This method is used by asdf to test that to_tree > from_tree gives an
        equivalent object.
        """
        assert new == old
