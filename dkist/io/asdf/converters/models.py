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

    def select_tag(self, obj, tags, ctx):
        from dkist.wcs.models import InverseVaryingCelestialTransform, VaryingCelestialTransform
        if isinstance(obj, VaryingCelestialTransform):
            return "asdf://dkist.nso.edu/tags/varying_celestial_transform-1.0.0"
        elif isinstance(obj, InverseVaryingCelestialTransform):
            return "asdf://dkist.nso.edu/tags/inverse_varying_celestial_transform-1.0.0"
        else:
            raise ValueError(f"Unsupported object: {obj}")  # pragma: no cover

    def from_yaml_tree_transform(self, node, tag, ctx):
        from dkist.wcs.models import InverseVaryingCelestialTransform, VaryingCelestialTransform

        if tag.endswith("inverse_varying_celestial_transform-1.0.0"):
            cls = InverseVaryingCelestialTransform
        elif tag.endswith("varying_celestial_transform-1.0.0"):
            cls = VaryingCelestialTransform
        else:
            raise ValueError(f"Unsupported tag: {tag}")  # pragma: no cover

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


class CoupledCompoundConverter(TransformConverterBase):
    """
    ASDF serialization support for CompoundModel.
    """
    tags = [
        "asdf://dkist.nso.edu/tags/coupled_compound_model-1.0.0",
    ]

    types = ["dkist.wcs.models.CoupledCompoundModel"]

    def to_yaml_tree_transform(self, model, tag, ctx):
        left = model.left

        if isinstance(model.right, dict):
            right = {
                "keys": list(model.right.keys()),
                "values": list(model.right.values())
            }
        else:
            right = model.right

        return {
            "forward": [left, right],
            "shared_inputs": model.shared_inputs
        }

    def from_yaml_tree_transform(self, node, tag, ctx):
        from astropy.modeling.core import Model

        from dkist.wcs.models import CoupledCompoundModel

        oper = "&"

        left = node["forward"][0]
        if not isinstance(left, Model):
            raise TypeError("Unknown model type '{0}'".format(node["forward"][0]._tag))  # pragma: no cover

        right = node["forward"][1]
        if (not isinstance(right, Model) and
                not (oper == "fix_inputs" and isinstance(right, dict))):
            raise TypeError("Unknown model type '{0}'".format(node["forward"][1]._tag))  # pragma: no cover

        model = CoupledCompoundModel(oper, left, right,
                                     shared_inputs=node["shared_inputs"])

        return model
