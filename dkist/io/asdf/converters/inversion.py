from asdf.extension import Converter

from dkist.dataset.inversion import Inversion


class InversionConverter(Converter):
    tags = [
        "tag:dkist.nso.edu:dkist/inversion-0.1.0",
    ]
    types = ["dkist.dataset.inversion.Inversion"]

    def from_yaml_tree(cls, node, tag, ctx):
        return Inversion(node["inversion"], meta=node["meta"], profiles=node["profiles"])

    def to_yaml_tree(cls, inversion, tag, ctx):
        tree = {}
        # Copy the meta so we don't pop from the one in memory
        meta = copy.copy(inversion.meta)
        # If the history key has been injected into the meta, do not save it
        meta.pop("history", None)
        tree["meta"] = meta
        tree["inversion"] = inversion.items()
        tree["profiles"] = inversion.profiles.items()
        return tree
