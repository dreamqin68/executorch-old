# Copyright 2025 Arm Limited and/or its affiliates.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-unsafe

from typing import List

import executorch.backends.arm.tosa_quant_utils as tqutils

import tosa_tools.v0_80.serializer.tosa_serializer as ts  # type: ignore
from executorch.backends.arm.operators.node_visitor import (
    NodeVisitor,
    register_node_visitor,
)
from executorch.backends.arm.tosa_mapping import TosaArg

from torch.fx import Node


@register_node_visitor
class LessEqualVisitor(NodeVisitor):
    target = "aten.le.Tensor"

    def __init__(self, *args):
        super().__init__(*args)

    def define_node(
        self,
        node: Node,
        tosa_graph: ts.TosaSerializer,
        inputs: List[TosaArg],
        output: TosaArg,
    ) -> None:
        if inputs[0].dtype != inputs[1].dtype:
            raise TypeError(
                "All inputs need to have the same data type for operator LE but got "
                f"{inputs[0].dtype=}, {inputs[1].dtype=}"
            )

        input_nodes = inputs
        # Handle quantization
        if inputs[0].dtype == ts.DType.INT8:
            # Rescale inputs to 32 bit
            rescaled_inputs, _ = tqutils.insert_rescale_ops_to_int32(
                tosa_graph, inputs, node
            )

            # Update IO
            input_nodes = rescaled_inputs

        tosa_graph.addOperator(
            ts.TosaOp.Op().GREATER_EQUAL,
            [input_nodes[1].name, input_nodes[0].name],
            [output.name],
            None,
        )
