import matplotlib
import pytest
from sybil import Sybil
from sybil.parsers.myst import DocTestDirectiveParser as MarkdownDocTestParser
from sybil.parsers.myst import PythonCodeBlockParser as MarkdownPythonCodeBlockParser
from sybil.parsers.myst import SkipParser as MarkdownSkipParser
from sybil.parsers.rest import DocTestParser as ReSTDocTestParser
from sybil.parsers.rest import PythonCodeBlockParser as ReSTPythonCodeBlockParser
from sybil.parsers.rest import SkipParser as ReSTSkipParser

matplotlib.use("Agg")

markdown_examples = Sybil(
    parsers=[
        # MarkdownDocTestParser(),
        MarkdownPythonCodeBlockParser(),
        MarkdownSkipParser(),
    ],
    patterns=['*.md'],
    fixtures=[]
)

rest_examples = Sybil(
    parsers=[
        # ReSTDocTestParser(),
        ReSTPythonCodeBlockParser(),
        ReSTSkipParser(),
    ],
    patterns=['*.py', '*.rst'],
    fixtures=[]
)

pytest_collect_file = (markdown_examples+rest_examples).pytest()
