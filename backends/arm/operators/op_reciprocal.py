# Copyright 2023-2025 Arm Limited and/or its affiliates.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-unsafe
from typing import Any, List

import torch

from executorch.backends.arm.operators.node_visitor import (
    NodeVisitor,
    register_node_visitor,
)
from executorch.backends.arm.tosa_mapping import TosaArg
from executorch.backends.arm.tosa_specification import TosaSpecification


@register_node_visitor
class ReciprocalVisitor_080_MI(NodeVisitor):
    target = "aten.reciprocal.default"

    # BI case should be handled by op_table
    tosa_specs = [TosaSpecification.create_from_string("TOSA-0.80+MI")]

    def __init__(self, *args):
        super().__init__(*args)

    def define_node(
        self,
        node: torch.fx.Node,
        tosa_graph: Any,
        inputs: List[TosaArg],
        output: TosaArg,
    ) -> None:
        import tosa_tools.v0_80.serializer.tosa_serializer as ts  # type: ignore

        if len(node.all_input_nodes) != 1:
            raise ValueError(
                f"Expected 1 input for {self.target}, got {len(node.all_input_nodes)}"
            )
        if inputs[0].dtype != ts.DType.FP32 or output.dtype != ts.DType.FP32:
            raise ValueError(
                f"Input and output for {self.target} need to be FP32, got "
                f"{inputs[0].dtype=} and {output.dtype=}"
            )

        tosa_graph.addOperator(
            ts.TosaOp.Op().RECIPROCAL, [inputs[0].name], [output.name]
        )


@register_node_visitor
class ReciprocalVisitor(NodeVisitor):
    target = "aten.reciprocal.default"

    # INT case should be handled by op_table
    tosa_specs = [TosaSpecification.create_from_string("TOSA-1.0+FP")]

    def __init__(self, *args):
        super().__init__(*args)

    def define_node(
        self,
        node: torch.fx.Node,
        tosa_graph: Any,
        inputs: List[TosaArg],
        output: TosaArg,
    ) -> None:
        import serializer.tosa_serializer as ts

        if len(node.all_input_nodes) != 1:
            raise ValueError(
                f"Expected 1 input for {self.target}, got {len(node.all_input_nodes)}"
            )
        if inputs[0].dtype != ts.DType.FP32 or output.dtype != ts.DType.FP32:
            raise ValueError(
                f"Input and output for {self.target} need to be FP32, got "
                f"{inputs[0].dtype=} and {output.dtype=}"
            )

        tosa_graph.addOperator(
            ts.TosaOp.Op().RECIPROCAL, [inputs[0].name], [output.name]
        )
