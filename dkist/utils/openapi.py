"""
Helper functions for parsing the openapi spec of the dataset search API.
"""

import json
import warnings
import urllib.request
from typing import Any, Union, Literal
from collections.abc import Callable


def get_spec():
    from dkist.net import conf

    url = conf.dataset_endpoint + "openapi.json"
    resp = urllib.request.urlopen(url)
    return json.loads(resp.read())


# This is heavily adapted from https://github.com/inspera/jsonschema-typed/blob/master/jsonschema_typed/plugin.py
# under the MIT license. The main difference being it is returning typehints rather than mypy stuff.
class JsonSchemaTypeConverter:
    """
    Given a jsonschema resolve the types to Python typehints where possible.
    """

    def __init__(self, spec: dict[str, dict[str, Any]]):
        self.spec = spec

    def get_all_types(self):
        return {name: self.get_type(prop) for name, prop in self.spec.items()}

    def get_type_handler(self, schema_type: str) -> Callable:
        """Get a handler from this schema draft version."""
        if schema_type.startswith("_"):
            raise AttributeError("No way friend")
        handler = getattr(self, schema_type, None)
        if handler is None:
            raise NotImplementedError(f"Type `{schema_type}` is not supported.")
        return handler

    def get_type(self, schema: dict[str, Any], outer=False):
        # 6.1.1. type
        # The value of this keyword MUST be either a string or an array. If it
        # is an array, elements of the array MUST be strings and MUST be
        # unique.
        #
        # String values MUST be one of the six primitive types ("null",
        # "boolean", "object", "array", "number", or "string"), or "integer"
        # which matches any number with a zero fractional part.
        #
        # An instance validates if and only if the instance is in any of the
        # sets listed for this keyword.
        schema_type = schema.get("type")
        if isinstance(schema_type, list):
            if outer:
                # Cases in which the root of the schema is anything other than
                # an object are not terribly interesting for this project, so
                # we'll ignore them for now.
                if "object" not in schema_type:
                    raise NotImplementedError(
                        "Schemas with a root type other than ``object`` are not currently supported."
                    )
                warnings.warn(
                    "Root type is an array, which is out of scope for this library. Falling back to `object`."
                )
                schema_type = "object"
            else:
                return Union[*[self._get_type(schema, primitive_type, outer=outer) for primitive_type in schema_type]]
        elif schema_type is None:
            if "$ref" in schema:
                # return self.ref(schema["$ref"])
                raise NotImplementedError("refs are not supported")
            if "allOf" in schema:
                return self.allOf(schema["allOf"])
            if "anyOf" in schema:
                return self.anyOf(schema["anyOf"])
            if "oneOf" in schema:
                return self.anyOf(schema["oneOf"])
            if "enum" in schema:
                return self.enum(schema["enum"])
            if "default" in schema:
                raise NotImplementedError("default is not supported")

        assert isinstance(schema_type, str), (
            f"Expected to find a supported schema type, got {schema_type}\nDuring parsing of {schema}"
        )

        return self._get_type(schema, schema_type, outer=outer)

    def _get_type(
        self,
        schema: dict[str, Any],
        schema_type: str,
        outer=False,
    ) -> type:
        # Enums get special treatment, as they should be one of the literal values.
        # Note: If a "type" field indicates types that are incompatible with some of
        # the enumeration values (which is allowed by jsonschema), the "type" will _not_
        # be respected. This should be considered a malformed schema anyway, so this
        # will not be fixed.
        if "enum" in schema:
            handler = self.get_type_handler("enum")
            return handler(schema["enum"])

        handler = self.get_type_handler(schema_type)
        if handler is not None:
            return handler(schema, outer=outer)

        warnings.warn(f"No handler for `{schema_type}`")
        return Any

    def const(self, const, *args, **kwargs):
        return Literal[const]

    def enum(self, values, *args, **kwargs):
        return Union[*[self.const(v) for v in values]]

    def boolean(self, boolean, *args, **kwargs):
        return bool

    def object(self, object_, *args, **kwargs):
        # TODO: Parse the nested schema
        return dict[Any, Any]

    def array(self, schema, **kwargs):
        """Generate a ``list[]`` annotation with the allowed types."""
        items = schema.get("items")
        if items is True:
            inner_types = [Any]
        elif items is False:
            raise NotImplementedError('"items": false is not supported')
        elif isinstance(items, list):
            # https://json-schema.org/understanding-json-schema/reference/array.html#tuple-validation
            if {schema.get("minItems"), schema.get("maxItems")} - {None, len(items)}:
                raise NotImplementedError('"items": If list, must have minItems == maxItems')
            inner_types = [self.get_type(spec) for spec in items]
            return tuple[*inner_types]
        elif items is not None:
            inner_types = [self.get_type(items)]
        else:
            inner_types = []
        return list[*inner_types]

    def allOf(self, subschema: list[dict], **kwargs):
        """
        Generate a ``Union`` annotation with the allowed types.
        """
        return self.anyOf(subschema, **kwargs)

    def anyOf(self, subschema: list, **kwargs):
        """Generate a ``Union`` annotation with the allowed types."""
        return Union[*[self.get_type(subs) for subs in subschema]]

    def string(self, *args, **kwargs):
        """Generate a ``str`` annotation."""
        return str

    def number(self, *args, **kwargs):
        # This probably should be float | int but that's not helpful to us.
        return float

    def integer(self, *args, **kwargs):
        """Generate an ``int`` annotation."""
        return int

    def null(self, *args, **kwargs):
        """Generate a ``None`` annotation."""
        return None  # noqa: RET501


def search_results_type_hints(spec):
    props = spec["components"]["schemas"]["SearchResult"]["properties"]
    return JsonSchemaTypeConverter(props).get_all_types()
