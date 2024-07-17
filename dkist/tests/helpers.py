from pathlib import Path
from functools import wraps

import matplotlib as mpl
import pytest

import astropy

import ndcube


def get_hash_library_name():
    """
    Generate the hash library name for this env.
    """
    import mpl_animators

    animators_version = "dev" if (("dev" in mpl_animators.__version__) or ("rc" in mpl_animators.__version__)) else mpl_animators.__version__.replace(".", "")
    ft2_version = f"{mpl.ft2font.__freetype_version__.replace('.', '')}"
    mpl_version = "dev" if (("dev" in mpl.__version__) or ("rc" in mpl.__version__)) else mpl.__version__.replace(".", "")
    astropy_version = "dev" if (("dev" in astropy.__version__) or ("rc" in astropy.__version__)) else astropy.__version__.replace(".", "")
    ndcube_version = "dev" if (("dev" in ndcube.__version__) or ("rc" in ndcube.__version__)) else ndcube.__version__.replace(".", "")
    return f"figure_hashes_mpl_{mpl_version}_ft_{ft2_version}_astropy_{astropy_version}_animators_{animators_version}_ndcube_{ndcube_version}.json"


def figure_test(test_function):
    """
    A decorator for a test that verifies the hash of the current figure or the
    returned figure, with the name of the test function as the hash identifier
    in the library. A PNG is also created in the 'result_image' directory,
    which is created on the current path.

    All such decorated tests are marked with `pytest.mark.mpl_image` for convenient filtering.

    Examples
    --------
    @figure_test
    def test_simple_plot():
        plt.plot([0,1])
    """
    hash_library_name = get_hash_library_name()
    hash_library_file = Path(__file__).parent / hash_library_name

    @pytest.mark.mpl_image_compare(hash_library=hash_library_file,
                                   style="default")
    @wraps(test_function)
    def test_wrapper(*args, **kwargs):
        return test_function(*args, **kwargs)
    return test_wrapper
