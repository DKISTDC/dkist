from ndcube.asdf.converters.ndcollection_converter import NDCollectionConverter


class ProfilesConverter(NDCollectionConverter):
    tags = ["asdf://dkist.nso.edu/tags/profiles-0.1.0"]
    types = ["dkist.dataset.l2_dataset.Profiles"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset.inversion import Profiles

        aligned_axes = list(node.get("aligned_axes").values())
        aligned_axes = tuple(tuple(lst) for lst in aligned_axes)
        return Profiles(node["items"], meta=node.get("meta"), aligned_axes=aligned_axes)

    def to_yaml_tree(self, inversion, tag, ctx):
        node = {}
        node["profiles"] = super().to_yaml_tree(profiles, tag, ctx)
        if "meta" in node["profiles"]:
            node["meta"] = node["profiles"].pop("meta")
        return node
