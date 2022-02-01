from pathlib import Path

from asdf.extension import Converter


class FileManagerConverter(Converter):
    tags = [
        "tag:dkist.nso.edu:dkist/array_container-0.2.0",
        "asdf://dkist.nso.edu/array_container-1.0.0",
    ]
    types = ['dkist.io.file_manager.FileManager']

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.io.file_manager import FileManager
        from dkist.io.loaders import AstropyFITSLoader

        filepath = Path((".").replace("file:", ""))
        base_path = filepath.parent

        file_manager = FileManager(node['fileuris'],
                                   node['target'],
                                   node['datatype'],
                                   node['shape'],
                                   loader=AstropyFITSLoader,
                                   basepath=base_path)
        return file_manager

    def to_yaml_tree(self, obj, tag, ctx):
        node = {}
        node['fileuris'] = obj._fileuris
        node['target'] = obj.target
        node['datatype'] = obj.dtype
        node['shape'] = obj.shape
        return node