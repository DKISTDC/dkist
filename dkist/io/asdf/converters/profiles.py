from ndcube.asdf.converters.ndcollection_converter import NDCollectionConverter


class ProfilesConverter(NDCollectionConverter):
    tags = ["asdf://dkist.nso.edu/tags/profiles-0.1.0"]
    types = ["dkist.dataset.l2_dataset.Profiles"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset.inversion import Profiles

        # We are "promoting" the profiles NDCollection object to being the Profiles object
        profiles = node["profiles"]
        aligned_axes = tuple(profiles.aligned_axes[key] for key in profiles.keys())
        return Profiles(
            node["profiles"],
            meta=node["meta"],
            aligned_axes=aligned_axes,
        )

    def to_yaml_tree(self, inversion, tag, ctx):
        node = {}
        node["profiles"] = super().to_yaml_tree(profiles, tag, ctx)
        if "meta" in node["profiles"]:
            node["meta"] = node["profiles"].pop("meta")
        return node
