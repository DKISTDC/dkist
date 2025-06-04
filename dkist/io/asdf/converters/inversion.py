from asdf.extension import Converter


class InversionConverter(Converter):
    tags = ["asdf://dkist.nso.edu/tags/inversion-0.1.0"]
    types = ["dkist.dataset.l2_dataset.Inversion"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset.inversion import Inversion

        aligned_axes = list(node.get("aligned_axes").values())
        aligned_axes = tuple(tuple(lst) for lst in aligned_axes)
        return Inversion(node["items"], meta=node.get("meta"), aligned_axes=aligned_axes, profiles=node["profiles"])

    def to_yaml_tree(self, inversion, tag, ctx):
        node = {}
        if inversion.meta is not None:
            node["meta"] = inversion.meta
        if inversion._aligned_axes is not None:
            node["aligned_axes"] = inversion._aligned_axes
        node["items"] = dict(inversion)
        node["profiles"] = inversion.profiles
        return node
