import pathlib
import itertools

import dkist
from dkist.io.asdf import entry_points

repodir = pathlib.Path(dkist.__file__).parent

def tagname(fulltag):
    if isinstance(fulltag, pathlib.Path):
        return fulltag.name.split("/")[-1]
    return fulltag.split("/")[-1]


def test_schema_infrastructure():

    man_yamls = itertools.groupby(
        sorted((repodir / "io" / "asdf" / "resources" / "manifests").glob("*")), lambda x: tagname(x)[:-11]
    )
    latest_man_yamls = {man: sorted(yamls)[-1] for man, yamls in man_yamls}
    latest_extensions = {ext: list(manifests)[-1] for ext, manifests in itertools.groupby(sorted(entry_points.get_extensions(), key=lambda x: x.extension_uri),
                                                                                         lambda x: tagname(x.extension_uri)[:-6])}
    # Check that latest manifest.yaml == latest listed in entry_points
    for man, yaml in latest_man_yamls.items():
        man_yaml_ver = yaml.name[-10:-5]
        assert man_yaml_ver == tagname(latest_extensions[man].extension_uri)[-5:]

    schemas = [tagname(tag.tag_uri) for ext in latest_extensions.values() for tag in ext.tags]
    converters = [type(conv) for ext in latest_extensions.values() for conv in ext.converters]
    schema_yamls = itertools.groupby(
        sorted((repodir / "io" / "asdf" / "resources" / "schemas").glob("*")), lambda x: tagname(x)[:-11]
    )
    latest_sche_yamls = {sche.replace("_model", "").replace("_transform", ""): sorted(yamls)[-1] for sche, yamls in schema_yamls}

    for schema, yaml in latest_sche_yamls.items():
        converter = "".join([p.title() for p in schema.split("_")]) + "Converter"
        # Check schema converter is imported in entry_points
        assert hasattr(entry_points, converter)
        # Check schema is in [dkist|wcs]_converters in entry_points
        assert eval(f"dkist.io.asdf.converters.{converter}") in converters
        # For all schemas
        # Check that latest schema.yaml version == latest listed in manifest
        # Check that schema version in schema matches filename
