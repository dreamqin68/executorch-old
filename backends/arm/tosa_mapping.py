# Copyright 2023-2025 Arm Limited and/or its affiliates.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-unsafe

#
# PyTorch to Tosa mapping - simple mapping functions and multi-type extraction
# of key information. These are used by the initial compile stage which captures
# the standardised TOSA representation.
#

from typing import Any, Sequence

import torch

import tosa_tools.v0_80.serializer.tosa_serializer as ts  # type: ignore


UNSUPPORTED_DTYPES = (
    torch.float64,
    torch.double,
    torch.complex64,
    torch.cfloat,
    torch.complex128,
    torch.cdouble,
    torch.uint8,
    torch.int64,
    torch.long,
)

DTYPE_MAP = {
    torch.float32: ts.DType.FP32,
    torch.float: ts.DType.FP32,
    torch.float16: ts.DType.FP16,
    torch.half: ts.DType.FP16,
    torch.bfloat16: ts.DType.BF16,
    torch.int8: ts.DType.INT8,
    torch.int16: ts.DType.INT16,
    torch.short: ts.DType.INT16,
    torch.int32: ts.DType.INT32,
    torch.int: ts.DType.INT32,
    torch.bool: ts.DType.BOOL,
}


def map_dtype(data_type: torch.dtype) -> ts.DType:
    if data_type in UNSUPPORTED_DTYPES:
        raise ValueError(f"Unsupported type: {data_type}")
    if data_type not in DTYPE_MAP:
        raise ValueError(f"Unknown type: {data_type}")
    return DTYPE_MAP[data_type]


# Returns the shape and type of a node
# TODO: other types, can be
# SymInt, FakeTensor, a List[Union[FakeTensor, SymInt]], or None
def extract_tensor_meta(meta):
    assert meta.get("val") is not None
    val = meta["val"]
    if type(val) is tuple:
        # TODO: should use first concrete representation
        val = val[0]

    if not isinstance(val, torch._subclasses.fake_tensor.FakeTensor):
        raise ValueError(
            f"Expected first value in node.meta['val'] to be FakeTensor, got {val.__class__}"
        )
    dtype = map_dtype(val.dtype)
    shape = tuple(val.size())

    if meta.get("tosa_dim_order") is not None:
        dim_order = meta["tosa_dim_order"]
    else:
        dim_order = tuple(range(len(shape)))
    return (dtype, shape, dim_order)


# Class to capture arguments and turn into tensor references for TOSA OPs
class TosaArg:
    def __process_node(self, argument: torch.fx.Node):
        self.name: str = argument.name
        self.dtype, self.shape, self.dim_order = extract_tensor_meta(argument.meta)

    def __process_list(self, argument):
        self.special: list = list(argument)

    def __process_number(self, argument: float | int):
        self.number: float | int = argument

    def __init__(self, argument: Any) -> None:
        if argument is None:
            return

        if isinstance(argument, torch.fx.Node):
            self.__process_node(argument)
            return
        if isinstance(argument, Sequence):
            self.__process_list(argument)
            return
        if isinstance(argument, (int, float)):
            self.__process_number(argument)
            return
        if isinstance(argument, torch.dtype):
            # Dtype is parsed from fake tensor
            return

        raise RuntimeError(
            f"Unhandled node input argument: {argument}, of type {type(argument)}"
        )

    def __repr__(self):
        attrs = []
        if hasattr(self, "name"):
            if self.name is not None:
                attrs.append(f"name={self.name!r}")
            if self.dtype is not None:
                attrs.append(f"dtype={ts.DTypeNames[self.dtype]}")
            if self.shape is not None:
                attrs.append(f"shape={self.shape!r}")
            if self.dim_order is not None:
                attrs.append(f"dim_order={self.dim_order!r}")
        if hasattr(self, "special") and self.special is not None:
            attrs.append(f"special={self.special!r}")
        if hasattr(self, "number") and self.number is not None:
            attrs.append(f"number={self.number!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"
