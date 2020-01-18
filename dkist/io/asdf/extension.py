from pathlib import Path

from asdf import AsdfExtension
from asdf.util import filepath_to_url

from .tags.array_container import ArrayContainerType  # noqa
from .tags.dataset import DatasetType  # noqa
from .types import DKISTType

__all__ = ['DKISTExtension']


class DKISTExtension(AsdfExtension):
    schema_uri_base = "http://dkist.nso.edu/schemas/"

    @property
    def types(self):
        return DKISTType._tags

    @property
    def tag_mapping(self):
        return [('tag:dkist.nso.edu:dkist', self.schema_uri_base + 'dkist{tag_suffix}')]

    @property
    def url_mapping(self):
        filepath = Path(__file__).parent / "schemas" / "dkist.nso.edu"
        return [(self.schema_uri_base,
                 filepath_to_url(str(filepath)) + "/{url_suffix}.yaml")]
