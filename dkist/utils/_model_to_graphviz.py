"""
This module visualises compound models by rendering them as a graphviz graph.

It is provided as a helper module which is useful for debugging complex compound models.

It is not tested, incomplete and *should be used at your own risk*.
"""

from functools import singledispatch

import pydot

from astropy.modeling import CompoundModel, Model
from astropy.modeling.mappings import Mapping


@singledispatch
def to_subgraph(model, inputs: tuple[str] = None, outputs: tuple[str] = None):
    """
    Parameters
    ----------
    model
        The model instance
    inputs
        The names to use for the model inputs, must be the same length as
        model.n_inputs.
    outputs
        The names to use for the model outputs, must be the same length as
        model.n_outputs.
    """
    raise NotImplementedError("Nope")


@to_subgraph.register(Model)
def model_to_subgraph(model, inputs=None, outputs=None):
    inputs = inputs or model.inputs
    outputs = outputs or model.outputs

    input_labels = inputs
    output_labels = outputs

    if isinstance(model, Mapping):
        output_labels = [input_labels[i] for i in model._mapping]

    label = repr(model)
    if len(label) > 30:
        label = model.__class__.name

    subgraph = pydot.Subgraph(f"{id(model)}_subgraph", label=label)
    model_node = pydot.Node(name=id(model), label=label, shape="box")
    subgraph.add_node(model_node)

    for inp, label in zip(inputs, input_labels):
        input_node = pydot.Node(name=inp, label=label, shape="none")
        subgraph.add_node(input_node)
        subgraph.add_edge(pydot.Edge(input_node, model_node))

    for out, label in zip(outputs, output_labels):
        output_node = pydot.Node(name=out, label=label, shape="none")
        subgraph.add_node(output_node)
        subgraph.add_edge(pydot.Edge(model_node, output_node))

    return subgraph


global_int_count = 0


@to_subgraph.register(CompoundModel)
def compound_model_to_subgraph(model, inputs=None, outputs=None):
    global global_int_count
    name = model.name or model.__class__.name
    subgraph = pydot.Subgraph(name)

    inputs = inputs or model.inputs
    outputs = outputs or model.outputs

    left_inputs = None
    left_outputs = None
    right_inputs = None
    right_outputs = None

    if model.op == "|":
        left_inputs = inputs
        right_outputs = outputs
        left_outputs = right_inputs = [f"int{n}" for n in range(global_int_count,
                                                                model.left.n_outputs + global_int_count)]
        global_int_count += model.left.n_outputs
    elif model.op == "&":
        left_inputs = inputs[:model.left.n_inputs]
        right_inputs = inputs[model.left.n_inputs:]

        left_outputs = outputs[:model.left.n_outputs]
        right_outputs = outputs[model.left.n_outputs:]

    left_node = to_subgraph(model.left, inputs=left_inputs, outputs=left_outputs)
    right_node = to_subgraph(model.right, inputs=right_inputs, outputs=right_outputs)
    subgraph.add_subgraph(left_node)
    subgraph.add_subgraph(right_node)

    return subgraph


try:
    from dkist.wcs.models import CoupledCompoundModel
    @to_subgraph.register(CoupledCompoundModel)
    def coupledcompound_model_to_subgraph(model, inputs=None, outputs=None):
        global global_int_count
        name = model.name or model.__class__.name
        subgraph = pydot.Subgraph(name)

        # Get the full unabridged list of inputs
        inputs = inputs or (model.left.inputs + model.right.inputs)
        outputs = outputs or model.outputs

        assert model.op == "&", "CoupledCompoundModel is always &"

        left_inputs = inputs[:model.left.n_inputs]
        right_inputs = inputs[-model.right.n_inputs:]

        left_outputs = outputs[:model.left.n_outputs]
        right_outputs = outputs[model.left.n_outputs:]

        left_node = to_subgraph(model.left, inputs=left_inputs, outputs=left_outputs)
        right_node = to_subgraph(model.right, inputs=right_inputs, outputs=right_outputs)
        subgraph.add_subgraph(left_node)
        subgraph.add_subgraph(right_node)

        return subgraph
except ImportError:
    pass


def recursively_find_node(top, name):
    if node := top.get_node(name):
        return node

    for sg in top.get_subgraph_list():
        [n.get_label() for n in sg.get_node_list()]
        if node := recursively_find_node(sg, name):
            return node


def recursively_find_node_by_label(top, label):
    if top.get_label() == label:
        return top

    if isinstance(top, pydot.Node):
        return

    if nodes := top.get_node_list():
        for node in nodes:
            if node := recursively_find_node_by_label(node, label):
                return node

    if subgraphs := top.get_subgraph_list():
        for subgraph in subgraphs:
            if node := recursively_find_node_by_label(subgraph, label):
                return node

def make_model_graph(model):
    inputs = [f"in_{inp.replace('-', '_')}" for inp in model.inputs]
    outputs = [f"out_{inp.replace('-', '_')}" for inp in model.outputs]
    sg = to_subgraph(model, inputs, outputs)
    # for inp in model.inputs:
    #     inp = f"in_{inp.replace('-', '_')}"
    #     node = recursively_find_node(sg, inp)
    #     if node is None:
    #         raise ValueError(f"Could not find input node {inp}")
    #     node[0].set_group("input")

    # for out in model.outputs:
    #     out = f"out_{out.replace('-', '_')}"
    #     node = recursively_find_node(sg, out)
    #     if node is None:
    #         raise ValueError(f"Could not find output node {out}")
    #     node[0].set_group("output")

    doc = pydot.Dot()
    doc.add_subgraph(sg)
    return doc
