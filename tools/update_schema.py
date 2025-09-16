# /// script
# requires-python = ">=3.11"
# ///

"""
This script adds and updates the appropriate files to update the version of an ASDF schema.
"""

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
    if old_file:
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
    new_file = dir / f"{name}-0.1.0.yaml"
    new_file.touch()
    return new_file, None, "0.1.0"


def main(schema_name, manifest="dkist", schema_increment="minor", manifest_increment="minor", base_branch="main"):
    repodir = pathlib.Path(__file__).parent.parent.resolve()
    asdf_dir = repodir / "dkist" / "io" / "asdf"

    old_schema = get_latest(schema_name, asdf_dir / "resources" / "schemas")
    old_manifest = get_latest(manifest, asdf_dir / "resources" / "manifests")

    new_sche_file, old_sche_ver, new_sche_ver = increment_version(old_schema, schema_increment)
    new_mani_file, old_mani_ver, new_mani_ver = increment_version(old_manifest, manifest_increment)

    # add ManifestExtension to entry_points.py
    entrypoints = asdf_dir / "entry_points.py"
    converters = "wcs" if manifest == "dkist-wcs" else "dkist"
    with open(entrypoints) as f:
        lines = f.readlines()
    old_ext_line = f'        ManifestExtension.from_uri("asdf://dkist.nso.edu/manifests/{manifest}-{old_mani_ver}",\n'
    new_ext_line = old_ext_line[:-1].replace(old_mani_ver, new_mani_ver) + f" converters='{converters}'),\n"
    linenum = lines.index(old_ext_line)
    lines.insert(linenum, new_ext_line)
    with open(entrypoints, mode="w") as f:
        f.write("".join(lines))

    # if schema exists on base_branch:
    if old_schema:
        #   increment schema_uri and tag_uri in manifest
        with open(new_mani_file) as f:
            lines = f.readlines()

        old_id_line = f"id: asdf://dkist.nso.edu/manifests/{manifest}-{old_mani_ver}\n"
        linenum = lines.index(old_id_line)
        lines[linenum] = lines[linenum].replace(old_mani_ver, new_mani_ver)
        lines[linenum+1] = lines[linenum+1].replace(old_mani_ver, new_mani_ver)

        old_schema_line = f'  - schema_uri: "asdf://dkist.nso.edu/schemas/{schema_name}-{old_sche_ver}"\n'
        linenum = lines.index(old_schema_line)
        lines[linenum] = lines[linenum].replace(old_sche_ver, new_sche_ver)
        lines[linenum+1] = lines[linenum+1].replace(old_sche_ver, new_sche_ver)

        with open(new_mani_file, mode="w") as f:
            f.write("".join(lines))

    # if !(schema exists) on base branch:
    else:
        #   add schema_uri and tag_uri
        #   create converters/<schema>.py skeleton
        #   import new converter in converters/__init__.py
        #   import new converter in entry_points.py
        #   add converter to dkist_converters list in entry_points.py
        pass

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
