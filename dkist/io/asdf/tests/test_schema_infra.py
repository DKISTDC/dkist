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
    latest_sche_yamls = {sche: sorted(yamls)[-1] for sche, yamls in schema_yamls}
    latest_schemas_in_manifest = {}
    for yaml in latest_man_yamls.values():
        with open(yaml) as f:
            schema_uris = [l.replace('  - schema_uri: "', "").replace('"\n', "") for l in f.readlines() if "schema_uri" in l]
            for tag in schema_uris:
                latest_schemas_in_manifest[tagname(tag)[:-6]] = tag[-5:]

    for schema, yaml in latest_sche_yamls.items():
        yaml_version = yaml.name[-10:-5]
        converter = "".join([p.title() for p in schema.replace("_model", "").replace("_transform", "").split("_")]) + "Converter"
        # Check schema converter is imported in entry_points
        assert hasattr(entry_points, converter)
        # Check schema is in [dkist|wcs]_converters in entry_points
        assert eval(f"dkist.io.asdf.converters.{converter}") in converters
        # Check that latest schema.yaml version == latest listed in manifest
        assert yaml_version == latest_schemas_in_manifest[schema]
        # Check that schema version in schema matches filename
        with open(yaml) as f:
            schema_version_in_yaml = f.readlines()[3][-7:-2]
        assert schema_version_in_yaml == yaml_version
