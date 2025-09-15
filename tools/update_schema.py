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


def main(schema_name, schema_increment="minor", manifest_increment="minor", base_branch="main"):
    repodir = pathlib.Path(__file__).parent.parent.resolve()
    schemas_dir = repodir / "dkist" / "io" / "asdf" / "resources" / "schemas"
    old_schemas = list(schemas_dir.glob(f"{schema_name}-*.*.*.yaml"))
    old_schemas.sort()
    # if schema exists in base branch:
    if old_schemas:
        # get latest schema filename on base branch
        old_schema_file = old_schemas[-1]
        # get latest version number
        old_schema_version = old_schema_file.name[-10:-5]
        # copy <schema>-<latest>.yaml to <schema>-<latest+increment>.yaml
        if schema_increment == "major":
            new_schema_version = f"{int(old_schema_version[0])+1}.0.0"
        elif schema_increment == "minor":
            new_schema_version = f"{old_schema_version[:2]}{int(old_schema_version[2])+1}.0"
        elif schema_increment == "bugfix":
            new_schema_version = f"{old_schema_version[:4]}{int(old_schema_version[4])+1}"
        else:
            # obviously make this more sophisticated
            raise InputError
        new_schema_file = schemas_dir / f"{schema_name}-{new_schema_version}.yaml"
        shutil.copy(old_schema_file, new_schema_file)
    # else:
    #   create new <schema>-0.1.0.yaml file
    # get latest manifest version on base branch
    # create manifests/dkist-<latest+increment>.yaml
    # if schema exists on base_branch:
    #   increment schema_uri and tag_uri
    # else:
    #   add schema_uri and tag_uri
    # add ManifestExtension to entry_points.py
    # if !(schema exists) on base branch:
    #   create converters/<schema>.py skeleton
    #   import new converter in converters/__init__.py
    #   import new converter in entry_points.py
    #   add converter to dkist_converters list in entry_points.py

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("schema_name", help="Name of the schema to add or update.")
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

    main(args.schema_name, args.schema_increment, args.manifest_increment, args.base_branch)
