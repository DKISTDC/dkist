from asdf.extension import Converter


class VaryingCelestialConverter(Converter):
    tags = [
        "asdf://dkist.nso.edu/tags/varying_celestial_transform-1.0.0",
        "asdf://dkist.nso.edu/tags/inverse_varying_celestial_transform-1.0.0",
    ]
    types = [
        "dkist.wcs.models.VaryingCelestialTransform",
        "dkist.wcs.models.InverseVaryingCelestialTransform",
    ]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.wcs.models import InverseVaryingCelestialTransform, VaryingCelestialTransform

        if tag.endswith("varying_celestial_transform-1.0.0"):
            cls = VaryingCelestialTransform
        elif tag.endswith("inverse_varying_celestial_transform-1.0.0"):
            cls = InverseVaryingCelestialTransform
        else:
            raise ValueError("Unsupported tag")

        return cls(
            crpix=node["crpix"],
            cdelt=node["cdelt"],
            lon_pole=node["lon_pole"],
            crval_table=node["crval_table"],
            pc_table=node["pc_table"],
            projection=node["projection"]
        )

    def to_yaml_tree(self, dataset, tag, ctx):
        pass
