"""
This is a temporary home for a bunch of code for removing stuff from CompoundModels

I would imagine this will end up in gwcs or maybe even astropy at somepoint.
"""

from collections import defaultdict

from astropy.modeling import separable
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

        if tree.isleaf or tree.value != "&":
            # If the tree is a leaf node then the inputs map to the original tree.
            return {tree: set(tree.inputs)}

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


def make_forward_input_map(tree):
    """
    Given a tree, generate a mapping of inputs to the tree, to inputs of it's
    branches.
    """
    inp_map = {}
    assert tree.value == "&"
    for i, ori_inp in enumerate(tree.inputs):
        if i < len(tree.left.inputs):
            inp_map[ori_inp] = tree.left.inputs[i]
        else:
            inp_map[ori_inp] = tree.right.inputs[i - len(tree.left.inputs)]
    return inp_map


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
    # If the input is not found, noop
    if inp not in tree.inputs:
        return [tree]

    if tree.value != "&":
        # If the input is not a "&" then we have to respect remove_coupled_trees
        sep = tree_is_separable(tree)
        if all(~sep):
            if not remove_coupled_trees:
                return [tree]
        # Otherwise, we know this tree has the input, so we just drop it.
        return []

    # map the input names of this tree to the names of it's children
    inp_map = make_forward_input_map(tree)

    # Map the names of the inputs of tree to the two subtrees of tree
    global_input_map = make_tree_input_map(tree)

    ori_trees = [tree.left, tree.right]
    new_trees = []
    for i, stree in enumerate(ori_trees):
        # Before we check the sub_trees of this side of the tree, let us check
        # if we have a situation where we can just discard or keep one half of
        # the original tree.

        # Get the names of the inputs for this subtree
        global_inputs = tuple(global_input_map[stree])
        # If the input we want to drop is not in this subtree, we keep it and
        # check the next subtree.
        if inp not in global_inputs:
            new_trees.append(stree)
            continue
        # If the input is in this subtree, and this subtree only takes one
        # input (which is the input we want to drop) drop this subtree and then
        # check the next one. (In the case where we have dropped this tree we
        # would expect the next iteration (if there is one) to keep the other
        # half of the tree, i.e. meet the above if criteria).
        elif len(global_inputs) == 1 and global_inputs[0] == inp:
            continue

        # If we haven't been able to drop the input by splitting the original
        # tree, then we need to split one of the subtrees.

        # TODO: Can we now shortcut the rest of this block by recursively
        # calling the function again? We would need to add a separable check in
        # somewhere above this point.

        # Generate the input mapping
        ti_map = make_tree_input_map(stree)
        # Keep a list of the left and right trees for this tree
        sub_trees = list(ti_map.keys())
        # Find if the input we are after is in one of the subtrees for this tree.
        sub_tree = get_tree_with_input(ti_map, inp_map[inp])
        if sub_tree is None:
            # If we don't have the input, then we save the original tree unmodified.
            new_trees.append(stree)
            continue

        # If this subtree only has one input, we drop it and keep all the other one.
        if len(sub_tree.inputs) == 1:
            sub_trees.remove(sub_tree)
            new_trees += sub_trees
            break  # Once we remove a tree we are done.

        # If we have more than one input, but they are not separable then we
        # either drop the whole subtree or we keep the original tree
        # unmodified.
        sep = tree_is_separable(sub_tree)
        if all(~sep):
            if remove_coupled_trees:
                sub_trees.remove(sub_tree)
                new_trees += sub_trees
            else:
                new_trees.append(stree)
            break  # Once we remove a tree we are done.

        # TODO: What if we need to recurse down the tree another many levels?!
        # We shouldn't? All the inputs have to be at the top level of the expression??
        # new_trees += remove_input_frame(sub_tree, inp, remove_coupled_trees)

    return new_trees + ori_trees[i+1:]


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
