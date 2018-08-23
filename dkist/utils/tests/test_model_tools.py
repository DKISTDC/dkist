import pytest

from astropy.modeling.core import Model
from astropy.modeling.models import Identity, Pix2Sky_AZP

import astropy.units as u
from astropy.modeling.separable import is_separable
from astropy.modeling.models import Identity, Pix2Sky_AZP, Shift, Multiply

from dkist.utils.model_tools import make_tree_input_map, remove_input_frame, re_model_trees


@pytest.fixture
def double_input_flat():
    return (Identity(1) | Identity(1)) & Identity(1)


@pytest.fixture
def triple_input_flat():
    return Identity(1) & Identity(1) & Identity(1)


@pytest.fixture
def triple_input_nested():
    return (Identity(1) | Identity(1) | Identity(1)) & (Identity(1) | Identity(1)) & Identity(1)


@pytest.fixture
def single_non_separable():
    return Pix2Sky_AZP() | Identity(2)


@pytest.fixture
def double_non_separable():
    return (Pix2Sky_AZP() | Identity(2)) & Identity(1)

@pytest.fixture
def spatial_like():
    crpix1, crpix2 = (100, 100)*u.pix
    cdelt1, cdelt2 = (10, 10)*(u.arcsec/u.pix)

    shiftu = Shift(-crpix1) & Shift(-crpix2)
    scale = Multiply(cdelt1) & Multiply(cdelt2)

    return (shiftu | scale | Pix2Sky_AZP()) & Identity(1)


def test_input_map(triple_input_flat):
    ti_map = make_tree_input_map(triple_input_flat._tree)
    assert len(ti_map) == 2
    assert "x00" in list(ti_map.values())[0]
    assert "x01" in list(ti_map.values())[0]
    assert "x0" in list(ti_map.values())[1]


def test_not_and(single_non_separable):
    tree = single_non_separable._tree
    ti = make_tree_input_map(tree)
    assert len(ti) == 1
    assert tree in ti.keys()


def test_leaf_map(triple_input_nested):
    tree = triple_input_nested._tree
    ti_map = make_tree_input_map(tree)
    assert list(ti_map.keys())[1] is tree.right
    assert isinstance(list(ti_map.keys())[1].value, Model)


def test_spatial_imap(spatial_like):
    tree = spatial_like._tree
    trees = make_tree_input_map(tree.left)
    assert len(trees) == 1
    assert len(list(trees.values())[0]) == 2


def test_spatial_remove(spatial_like):
    tree = spatial_like._tree
    trees = remove_input_frame(tree, "x01")
    assert len(trees) == 1
    assert len(trees[0].inputs) == 2


def test_remove_non_sep(single_non_separable):
    tree = single_non_separable._tree
    trees = remove_input_frame(tree, "x")
    assert len(trees) == 1
    assert trees[0] is tree

    trees = remove_input_frame(tree, "x", remove_coupled_trees=True)
    assert len(trees) == 0


def test_remove_non_sep_double(double_non_separable):
    tree = double_non_separable._tree
    trees = remove_input_frame(tree, "x")
    assert len(trees) == 2
    assert trees[0] is tree.left
    assert trees[1] is tree.right

    trees = remove_input_frame(tree, "x", remove_coupled_trees=True)
    assert len(trees) == 1
    assert trees[0] is tree.right


def test_remove_no_input(single_non_separable):
    tree = single_non_separable._tree
    trees = remove_input_frame(tree, "x00000")
    assert len(trees) == 1
    assert trees[0] is tree


def test_remove_frame_flat(triple_input_flat):
    # x0 is the last input
    trees = remove_input_frame(triple_input_flat._tree, "x0")
    assert len(trees) == 1
    assert len(trees[0].inputs) == 2


def test_remove_frame_flat_split(triple_input_flat):
    # x0 is the last input
    trees = remove_input_frame(triple_input_flat._tree, "x01")
    assert len(trees) == 2
    assert len(trees[0].inputs) == 1
    assert len(trees[1].inputs) == 1


def test_remove_frame_nested(triple_input_nested):
    # x01 is the second input, therefore splitting the tree
    trees = remove_input_frame(triple_input_nested._tree, "x01")
    assert len(trees) == 2
    assert len(trees[0].inputs) == 1
    assert len(trees[1].inputs) == 1


def test_re_model_nested(triple_input_nested):
    # x01 is the second input, therefore splitting the tree
    trees = remove_input_frame(triple_input_nested._tree, "x01")
    assert len(trees) == 2
    model = re_model_trees(trees)
    assert isinstance(model, Model)
    assert len(model.inputs) == 2
