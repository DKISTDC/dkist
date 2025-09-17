# /// script
# requires-python = ">=3.11"
# ///

"""
This script adds and updates the appropriate files to update the version of an ASDF schema.
"""

import re
import sys
import shutil
import pathlib
import argparse


def get_latest(name, dir):
    # ? here for the major number so that it only matches one character and "dkist" doesn't match "dkist-wcs-"
    # This will break if major version numbers exceed 9 but that's a problem for future Drew
    old_files = list(dir.glob(f"{name}-?.*.*.yaml"))
    old_files.sort()
    if old_files:
        return old_files[-1]


def increment_version(old_file, increment):
    old_version = old_file.name[-10:-5]
    if increment == "major":
        new_version = f"{int(old_version[0])+1}.0.0"
    elif increment == "minor":
        new_version = f"{old_version[:2]}{int(old_version[2])+1}.0"
    elif increment == "bugfix":
        new_version = f"{old_version[:4]}{int(old_version[4])+1}"
    else:
        # obviously make this more sophisticated
        raise InputError
    new_file = old_file.parent / old_file.name.replace(old_version, new_version)
    shutil.copy(old_file, new_file)
    return new_file, old_version, new_version


def make_new_file(dir, name):
    new_file = dir / f"{name}-0.1.0.yaml"
    new_file.touch()
    return new_file


def pascalcase(string):
    parts = re.split("-|_", string)
    return "".join([p.title() for p in parts])


def main(schema_name, manifest="dkist", schema_increment="minor", manifest_increment="minor", base_branch="main"):
    repodir = pathlib.Path(__file__).parent.parent.resolve()
    asdf_dir = repodir / "dkist" / "io" / "asdf"

    old_schema = get_latest(schema_name, asdf_dir / "resources" / "schemas")
    old_manifest = get_latest(manifest, asdf_dir / "resources" / "manifests")

    if old_schema:
        new_sche_file, old_sche_ver, new_sche_ver = increment_version(old_schema, schema_increment)
    else:
        new_sche_file = make_new_file(asdf_dir / "resources" / "schemas", schema_name)
        with open(new_sche_file, "w") as f:
            f.write('%YAML 1.1\n'
                    '---\n'
                    '$schema: "http://stsci.edu/schemas/yaml-schema/draft-01"\n'
                    f'id: "asdf://dkist.nso.edu/schemas/{schema_name}-0.1.0"\n'
                    '\n'
                    'title: |\n'
                    '  # Title for this object\n'
                    'description:\n'
                    '  # Description of this object\n'
                    '\n'
                    'type: object\n'
                    'properties:\n'
                    '  # Properties of this object\n'
                    '\n'
                    'required: [] # Properties required byt his object\n'
                    'additionalProperties: # [true|false]\n'
                    '...')
    new_mani_file, old_mani_ver, new_mani_ver = increment_version(old_manifest, manifest_increment)

    # add ManifestExtension to entry_points.py
    entrypoints = asdf_dir / "entry_points.py"
    with open(entrypoints, mode="r+") as f:
        lines = f.readlines()
        old_ext_line = f'        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/{manifest}-{old_mani_ver}",\n'
        new_ext_line = old_ext_line[:-1].replace(old_mani_ver, new_mani_ver) + " converters=dkist_converters),\n"
        linenum = lines.index(old_ext_line)
        lines.insert(linenum, new_ext_line)
        f.seek(0)
        f.write("".join(lines))

    #   increment or add schema_uri and tag_uri in manifest
    with open(new_mani_file, mode="r+") as f:
        lines = f.readlines()

        old_id_line = f"id: asdf://dkist.nso.edu/manifests/{manifest}-{old_mani_ver}\n"
        linenum = lines.index(old_id_line)
        lines[linenum] = lines[linenum].replace(old_mani_ver, new_mani_ver)
        lines[linenum+1] = lines[linenum+1].replace(old_mani_ver, new_mani_ver)

        if old_schema:
            old_schema_line = f'  - schema_uri: "asdf://dkist.nso.edu/schemas/{schema_name}-{old_sche_ver}"\n'
            linenum = lines.index(old_schema_line)
            lines[linenum] = lines[linenum].replace(old_sche_ver, new_sche_ver)
            lines[linenum+1] = lines[linenum+1].replace(old_sche_ver, new_sche_ver)
        else:
            lines.append(f'  - schema_uri: "asdf://dkist.nso.edu/schemas/{schema_name}-0.1.0"\n')
            lines.append(f'    tag_uri: "asdf://dkist.nso.edu/tags/{schema_name}-0.1.0"\n')

        f.seek(0)
        f.write("".join(lines))


    converter = asdf_dir / "converters" / f"{schema_name}.py"
    if old_schema:
        # update tags list in converter
        add_increment_line(converter, f'        "asdf://dkist.nso.edu/tags/{schema_name}-{old_sche_ver}"\n',
                           old_sche_ver, new_sche_ver)
        add_increment_line(converter, f'        "tag://dkist.nso.edu:dkist/{schema_name}-{old_sche_ver}"\n',
                           old_sche_ver, new_sche_ver)
    else:
        #   create converters/<schema>.py skeleton
        with open(converter, "w") as f:
            f.write("from asdf.extension import Converter\n"
                    "\n"
                    "\n"
                    f"class {pascalcase(schema_name)}Converter(Converter):\n"
                    "    tags = [\n"
                    f'        "asdf://dkist.nso.edu/tags/{schema_name}-0.1.0"\n'
                    f'        "tag:dkist.nso.edu:dkist/{schema_name}-0.1.0"\n'
                    "    ]\n"
                    "\n"
                    "    def from_yaml_tree(cls, node, tag, ctx):\n"
                    "        # Construct and return an object of the appropriate type from the asdf yaml\n"
                    "\n"
                    "        return\n"
                    "\n"
                    "    def to_yaml_tree(cls, node, tag, ctx):\n"
                    "        # Construct and return yaml tree to represent the object being serialised\n"
                    "        tree = {}\n"
                    "\n"
                    "        return tree\n"
            )
        #   import new converter in converters/__init__.py
        #   import new converter in entry_points.py
        #   add converter to dkist_converters list in entry_points.py

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("schema_name", help="Name of the schema to add or update.")
    argp.add_argument("--manifest", help="Name of the manifest to add the new schema to."
                      "Creating a new manifest is not currently supported."
                      "(Default 'dkist')",
                      default="dkist")
    argp.add_argument("--schema_increment", help="Increment to apply to the schema version."
                      "Ignored when creating a new schema."
                      "Must be 'major', 'minor' or 'bugfix'."
                      "(Default 'minor')",
                      default="minor")
    argp.add_argument("--manifest_increment", help="Increment to apply to the manifest version."
                      "Must be 'major', 'minor' or 'bugfix'."
                      "(Default 'minor')",
                      default="minor")
    argp.add_argument("--base_branch", help="Branch of the git repo used to determine latest version numbers.", default="main")

    args = argp.parse_args(sys.argv[1:])

    main(args.schema_name, args.manifest, args.schema_increment, args.manifest_increment, args.base_branch)
