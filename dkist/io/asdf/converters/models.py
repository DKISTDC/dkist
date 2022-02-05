from asdf_astropy.converters.transform.core import TransformConverterBase, parameter_to_value


class VaryingCelestialConverter(TransformConverterBase):
    tags = [
        "asdf://dkist.nso.edu/tags/varying_celestial_transform-1.0.0",
        "asdf://dkist.nso.edu/tags/inverse_varying_celestial_transform-1.0.0",
    ]
    types = [
        "dkist.wcs.models.VaryingCelestialTransform",
        "dkist.wcs.models.InverseVaryingCelestialTransform",
    ]

    def from_yaml_tree_transform(self, node, tag, ctx):
        from dkist.wcs.models import InverseVaryingCelestialTransform, VaryingCelestialTransform

        if tag.endswith("varying_celestial_transform-1.0.0"):
            cls = VaryingCelestialTransform
        elif tag.endswith("inverse_varying_celestial_transform-1.0.0"):
            cls = InverseVaryingCelestialTransform
        else:
            raise ValueError(f"Unsupported tag: {tag}")

        return cls(
            crpix=node["crpix"],
            cdelt=node["cdelt"],
            lon_pole=node["lon_pole"],
            crval_table=node["crval_table"],
            pc_table=node["pc_table"],
            projection=node["projection"],
        )

    def to_yaml_tree_transform(self, model, tag, ctx):
        return {
            "crpix": parameter_to_value(model.crpix),
            "cdelt": parameter_to_value(model.cdelt),
            "lon_pole": parameter_to_value(model.lon_pole),
            "crval_table": parameter_to_value(model.crval_table),
            "pc_table": parameter_to_value(model.pc_table),
            "projection": model.projection,
        }
