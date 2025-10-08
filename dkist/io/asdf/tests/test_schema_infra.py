import pathlib
import itertools

import pytest

import dkist
from dkist.io.asdf import entry_points

repodir = pathlib.Path(dkist.__file__).parent
mandir = repodir / "io" / "asdf" / "resources" / "manifests"

def tagname(fulltag):
    if isinstance(fulltag, pathlib.Path):
        return fulltag.name.split("/")[-1]
    return fulltag.split("/")[-1]


def get_infra_info():
    man_yamls = itertools.groupby(
        sorted(mandir.glob("*")), lambda x: tagname(x)[:-11]
    )
    latest_man_yamls = {man: sorted(yamls)[-1] for man, yamls in man_yamls}
    latest_extensions = {ext: list(manifests)[-1] for ext, manifests in itertools.groupby(sorted(entry_points.get_extensions(), key=lambda x: x.extension_uri),
                                                                                         lambda x: tagname(x.extension_uri)[:-6])}

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

    return latest_man_yamls, latest_extensions, latest_sche_yamls, converters, latest_schemas_in_manifest


def get_schema_info(schema, yaml):
    yaml_version = yaml.name[-10:-5]
    converter = "".join([p.title() for p in schema.replace("_model", "").replace("_transform", "").split("_")]) + "Converter"
    return yaml_version, converter


def manifest_yaml_versions_match_entry_points(latest_man_yamls, latest_extensions):
    # Check that latest manifest.yaml == latest listed in entry_points
    for man, yaml in latest_man_yamls.items():
        man_yaml_ver = yaml.name[-10:-5]
        return man_yaml_ver == tagname(latest_extensions[man].extension_uri)[-5:]


def schema_converter_imported(converter):
    # Check schema converter is imported in entry_points
    return hasattr(entry_points, converter)


def schema_in_converters_list(converter, converters):
    # Check schema is in [dkist|wcs]_converters in entry_points
    return eval(f"dkist.io.asdf.converters.{converter}") in converters


def schema_yaml_matches_manifest(yaml_version, latest_schemas_in_manifest):
    # Check that latest schema.yaml version == latest listed in manifest
    return yaml_version == latest_schemas_in_manifest


def schema_ver_matches_filename(yaml, yaml_version):
        # Check that schema version in schema matches filename
        with open(yaml) as f:
            schema_version_in_yaml = f.readlines()[3][-7:-2]
        return schema_version_in_yaml == yaml_version


def num_schema_yamls_matches_num_schema_in_entry_points(latest_sche_yamls, schemas):
    # varying_celestial_transform schema is reused for inverse_, so the list from entry_points will be one shorter
    return len(latest_sche_yamls.values())+1 == len(schemas)


def test_schema_infrastructure():
    latest_man_yamls, latest_extensions, latest_sche_yamls, converters, latest_schemas_in_manifest = get_infra_info()

    assert manifest_yaml_versions_match_entry_points(latest_man_yamls, latest_extensions)

    schemas = [tagname(tag.tag_uri) for ext in latest_extensions.values() for tag in ext.tags]
    assert num_schema_yamls_matches_num_schema_in_entry_points(latest_sche_yamls, schemas)
    for schema, yaml in latest_sche_yamls.items():
        yaml_version, converter = get_schema_info(schema, yaml)
        assert schema_converter_imported(converter)
        assert schema_in_converters_list(converter, converters)
        assert schema_yaml_matches_manifest(yaml_version, latest_schemas_in_manifest[schema])
        assert schema_ver_matches_filename(yaml, yaml_version)


def test_incorrect_schema_infrastructure():
    latest_dkist_manifest = sorted(mandir.glob("dkist-?.*.*.yaml"))[-1]
    with open(latest_dkist_manifest, mode="r+") as f:
        lines = f.readlines()
        lines[2] = lines[2].replace(latest_dkist_manifest.name[-10:-5], "9.9.9")
        lines[3] = lines[3].replace(latest_dkist_manifest.name[-10:-5], "9.9.9")
        f.seek(0)
        f.write("".join(lines))

    latest_man_yamls, latest_extensions, _, _, _ = get_infra_info()
    with pytest.raises(AssertionError):
        assert manifest_yaml_versions_match_entry_points(latest_man_yamls, latest_extensions)
