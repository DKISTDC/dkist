from ndcube.asdf.converters.ndcollection_converter import NDCollectionConverter


class ProfilesConverter(NDCollectionConverter):
    tags = ["asdf://dkist.nso.edu/tags/profiles-0.1.0"]
    types = ["dkist.dataset.inversion.Profiles"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset.inversion import Profiles

        aligned_axes = list(node.get("aligned_axes").values())
        aligned_axes = tuple(tuple(lst) for lst in aligned_axes)
        return Profiles(node["items"], meta=node.get("meta"), aligned_axes=aligned_axes)
