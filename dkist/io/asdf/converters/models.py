import astropy.units as u
from asdf_astropy.converters.transform.core import TransformConverterBase, parameter_to_value


class VaryingCelestialConverter(TransformConverterBase):
    tags = [
        "asdf://dkist.nso.edu/tags/varying_celestial_transform-*",
        "asdf://dkist.nso.edu/tags/inverse_varying_celestial_transform-*",
        # Old slit tags must be kept so we can read old files, but not types as
        # we will not save slit classes any more
        "asdf://dkist.nso.edu/tags/varying_celestial_transform_slit-1.0.0",
        "asdf://dkist.nso.edu/tags/inverse_varying_celestial_transform_slit-1.0.0",
    ]
    types = [
        "dkist.wcs.models.VaryingCelestialTransform",
        "dkist.wcs.models.InverseVaryingCelestialTransform",
        "dkist.wcs.models.VaryingCelestialTransform2D",
        "dkist.wcs.models.InverseVaryingCelestialTransform2D",
        "dkist.wcs.models.VaryingCelestialTransform3D",
        "dkist.wcs.models.InverseVaryingCelestialTransform3D",
    ]

    def select_tag(self, obj, tags, ctx):
        tag_pattern = "asdf://dkist.nso.edu/tags/varying_celestial_transform"
        if obj._is_inverse:
            tag_pattern = "asdf://dkist.nso.edu/tags/inverse_varying_celestial_transform"

        for tag in tags:
            if tag.startswith(tag_pattern):
                return tag

    def from_yaml_tree_transform(self, node, tag, ctx):
        from dkist.wcs.models import varying_celestial_transform_from_tables

        inverse = False
        if "inverse_varying_celestial_transform" in tag:
            inverse = True

        # Support reading files with the old Slit classes in them
        slit = None
        if "_slit" in tag:
            slit = 1

        # Old files (written with the 1.0.0 tag) have the wrong units attached
        # to the pc_table (because of the incorrect ordering of the affine
        # transform and scale models) so we change the units.
        if tag.endswith("1.0.0"):
            if node["pc_table"].unit is u.arcsec:
                node["pc_table"] = u.Quantity(node["pc_table"].value, unit=u.pix)

        return varying_celestial_transform_from_tables(
            crpix=node["crpix"],
            cdelt=node["cdelt"],
            lon_pole=node["lon_pole"],
            crval_table=node["crval_table"],
            pc_table=node["pc_table"],
            projection=node["projection"],
            inverse=inverse,
            slit=slit,
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
        "asdf://dkist.nso.edu/tags/coupled_compound_model-*",
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
            raise TypeError("Unknown model type '{}'".format(node["forward"][0]._tag))  # pragma: no cover

        right = node["forward"][1]
        if (not isinstance(right, Model) and
                not (oper == "fix_inputs" and isinstance(right, dict))):
            raise TypeError("Unknown model type '{}'".format(node["forward"][1]._tag))  # pragma: no cover

        return CoupledCompoundModel(oper, left, right,
                                     shared_inputs=node["shared_inputs"])



class RavelConverter(TransformConverterBase):
    """
    ASDF serialization support for Ravel
    """

    tags  = [
        "asdf://dkist.nso.edu/tags/ravel_model-*"
    ]

    types = ["dkist.wcs.models.Ravel"]

    def to_yaml_tree_transform(self, model, tag, ctx):
        return {"array_shape": model.array_shape, "order": model.order}

    def from_yaml_tree_transform(self, node, tag, ctx):
        from dkist.wcs.models import Ravel

        return Ravel(node["array_shape"], order=node["order"])


class AsymmetricMappingConverter(TransformConverterBase):
    """
    ASDF serialization support for Ravel
    """

    tags  = [
        "asdf://dkist.nso.edu/tags/asymmetric_mapping_model-*"
    ]

    types = ["dkist.wcs.models.AsymmetricMapping"]

    def to_yaml_tree_transform(self, model, tag, ctx):
        node = {
            "forward_mapping": model.forward_mapping,
            "backward_mapping": model.backward_mapping,
        }
        if model.forward_n_inputs is not None:
            node["forward_n_inputs"] = model.forward_n_inputs
        if model.backward_n_inputs is not None:
            node["backward_n_inputs"] = model.backward_n_inputs
        return node

    def from_yaml_tree_transform(self, node, tag, ctx):
        from dkist.wcs.models import AsymmetricMapping

        return AsymmetricMapping(
            node["forward_mapping"],
            node["backward_mapping"],
            node.get("forward_n_inputs"),
            node.get("backward_n_inputs"),
        )
