from ndcube.asdf.converters.ndcollection_converter import NDCollectionConverter


class InversionConverter(NDCollectionConverter):
    tags = ["asdf://dkist.nso.edu/tags/inversion-0.1.0"]
    types = ["dkist.dataset.l2_dataset.Inversion"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset.inversion import Inversion

        aligned_axes = list(node["quantities"].get("aligned_axes").values())
        aligned_axes = tuple(tuple(lst) for lst in aligned_axes)
        return Inversion(
            node["quantities"]["items"],
            meta=node.get("meta"),
            aligned_axes=aligned_axes,
            profiles=node["profiles"],
        )

    def to_yaml_tree(self, inversion, tag, ctx):
        node = {}
        node["quantities"] = super().to_yaml_tree(inversion, tag, ctx)
        if "meta" in node["quantities"]:
            node["meta"] = node["quantities"].pop("meta")
        node["profiles"] = inversion.profiles
        return node
