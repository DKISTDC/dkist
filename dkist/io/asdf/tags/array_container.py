from dkist.io import FileManager

from ..types import DKISTType

__all__ = ['ArrayContainerType']


class ArrayContainerType(DKISTType):
    name = "array_container"
    types = ['dkist.io.file_manager.FileManager']
    requires = ['dkist']
    version = "0.2.0"

    @classmethod
    def from_tree(cls, node, ctx):
        return FileManager.from_tree(node, ctx)

    @classmethod
    def to_tree(cls, array_container, ctx):
        return array_container.to_tree(array_container, ctx)
