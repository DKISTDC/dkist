# /// script
# requires-python = ">=3.11"
# ///

"""
This script adds and updates the appropriate files to update the version of an ASDF schema.
"""

def main(schema_name, schema_increment_type="minor", manifest_increment_type="minor", base_branch="main"):
    # if schema exists in base branch:
    #   get latest schema version on base branch
    #   copy <schema>-<latest>.yaml to <schema>-<latest+increment>.yaml
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
    pass

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)

    args = argp.parse_args(sys.argv[1:])

    main()
