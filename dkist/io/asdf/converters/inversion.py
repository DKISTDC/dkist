from ndcube import NDCollection
from ndcube.asdf.converters.ndcollection_converter import NDCollectionConverter


class InversionConverter(NDCollectionConverter):
    tags = ["asdf://dkist.nso.edu/tags/inversion-0.1.0"]
    types = ["dkist.dataset.inversion.Inversion"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset.inversion import Inversion

        # We are "promoting" the quantities NDCollection object to being the Inversion object
        quantities = node["quantities"]
        aligned_axes = tuple(quantities.aligned_axes[key] for key in quantities.keys())
        meta = {**quantities.meta, **node["meta"]}
        return Inversion(
            node["quantities"],
            meta=meta,
            aligned_axes=aligned_axes,
            profiles=node["profiles"],
        )

    def to_yaml_tree(self, inversion, tag, ctx):
        node = {}
        aligned_axes = list(inversion.aligned_axes.values())
        aligned_axes = tuple(tuple(lst) for lst in aligned_axes)
        node["quantities"] = NDCollection(inversion.items(), meta=inversion.meta, aligned_axes=aligned_axes)
        meta = {}
        if "meta" in node["quantities"]:
            meta = node["quantities"].pop("meta")
        node["meta"] = {**inversion.meta, **meta}
        node["profiles"] = inversion.profiles
        return node
