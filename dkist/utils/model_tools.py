"""
This is a temporary home for a bunch of code for removing stuff from CompoundModels

I would imagine this will end up in gwcs or maybe even astropy at somepoint.
"""

from collections import defaultdict

from astropy.modeling import Model, separable
from astropy.modeling.core import BINARY_OPERATORS, _model_oper


OPERATORS = dict((oper, _model_oper(oper)) for oper in BINARY_OPERATORS)


def tree_is_separable(tree):
    """
    Given a tree, convert it to a `CompoundModel` and then return the
    separability of the inputs.
    """
    return separable.is_separable(tree.evaluate(OPERATORS))


def make_tree_input_map(tree):
    """
    Construct a mapping of tree to input names.

    This function iterates over all the inputs of a model and determines which
    side of the tree (left or right) the input corresponds to. It returns a
    mapping of tree to set of all inputs for that side of the tree (which is
    also a tree).

    Parameters
    ----------
    tree : `astropy.modelling.utils.ExpressionTree`
        The tree to analyse the inputs of.

    Returns
    -------
    tree_input_map : `dict`
       A mapping of tree to a set of input names.
    """
    tree_input_map = defaultdict(set)
    for i, inp in enumerate(tree.inputs):

        if isinstance(tree.value, Model):
            # In the situation where the value is a model, we just have the
            # given input for this tree. Here the tree is the root tree and not
            # a child of the tree.

            # TODO: Rethink this to use `isleaf`?
            return {tree: {inp}}

        if tree.value != "&":
            # Because we are only dealing with extra inputs to the tree we
            # should only have to parse trees with & as the operator. If we hit
            # this something has gone wrong.
            raise Exception("We should never get here.")

        # If this input number is less than the number of inputs in the left
        # hand side of the tree then the input maps to the LHS of the tree. If
        # not it maps to the right.
        if i < len(tree.left.inputs):
            tree_input_map[tree.left].add(inp)
        else:
            tree_input_map[tree.right].add(inp)
    return tree_input_map


def get_tree_with_input(ti_map, input):
    """
    Given the input name and a tree input mapping, return the tree which takes
    the input.
    """
    for t, inputs in ti_map.items():
        if input in inputs:
            return t


def remove_input_frame(tree, inp, remove_coupled_trees=False):
    """
    Given a tree, remove the smallest subtree needed to remove the input from the tree.

    This method traverses the expression tree until it finds a tree with only
    the given input or a tree which has non-separable inputs and takes the
    given input. It then removes this tree and returns a list of all the other
    trees in the original tree.

    Parameters
    ----------
    tree : `astropy.modelling.utils.ExpressionTree`
        The tree to analyse the inputs of.

    inp : `str`
        The name of the input to be removed.

    remove_coupled_trees : (optional) `bool`
        If `True` remove the subtree that contains input even if it has other
        non-separable inputs as well. Defaults to `False`.

    Returns
    -------
    new_trees : `list`
        A list of all the trees. Can have the `&` operator applied to
        reconstruct a `CompoundModel`.
    """
    new_trees = []
    for tree in (tree.left, tree.right):
        # Generate the input mapping
        ti_map = make_tree_input_map(tree)
        # Keep a list of the left and right trees for this tree
        sub_trees = list(ti_map.keys())
        # Find if the input we are after is in one of the subtrees for this tree.
        sub_tree = get_tree_with_input(ti_map, inp)
        if sub_tree is None:
            # If we don't have the input, then we save the original tree unmodified.
            new_trees.append(tree)
            continue

        # If this subtree only has one input, we drop it and keep all the other one.
        if len(sub_tree.inputs) == 1:
            sub_trees.remove(sub_tree)
            new_trees += sub_trees

        # If we have more than one input, but they are not separable then we
        # either drop the whole subtree or we keep the original tree
        # unmodified.
        sep = tree_is_separable(sub_tree)
        if all(~sep):
            if remove_coupled_trees:
                sub_trees.remove(sub_trees)
                new_trees += sub_trees
            else:
                new_trees.append(tree)

        # TODO: What if we need to recurse down the tree another many levels?!
        # new_trees += remove_input_frame(sub_tree, inp, remove_coupled_trees)

    return new_trees


def re_model_trees(trees):
    """
    Given a list of trees return a `CompoundModel` by applying the `&` operator.

    Parameters
    ----------
    tree : `list`
        A list of `astropy.modelling.utils.ExpressionTree` objects.

    Returns
    -------
    model : `astropy.modelling.CompoundModel`
        A model.
    """
    left = trees.pop(0).evaluate(OPERATORS)
    for right in trees:
        left = left & right.evaluate(OPERATORS)
    return left
