/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

#include <executorch/kernels/test/FunctionHeaderWrapper.h> // Declares the operator
#include <executorch/kernels/test/TestUtil.h>
#include <executorch/runtime/core/exec_aten/exec_aten.h>
#include <executorch/runtime/core/exec_aten/testing_util/tensor_factory.h>
#include <executorch/runtime/core/exec_aten/testing_util/tensor_util.h>
#include <executorch/runtime/platform/runtime.h>

#include <gtest/gtest.h>

using namespace ::testing;
using executorch::aten::IntArrayRef;
using executorch::aten::ScalarType;
using executorch::aten::Tensor;
using torch::executor::testing::TensorFactory;

Tensor& op_diagonal_copy_out(
    const Tensor& input,
    int64_t offset,
    int64_t dim1,
    int64_t dim2,
    Tensor& out) {
  executorch::ET_RUNTIME_NAMESPACE::KernelRuntimeContext context{};
  return torch::executor::aten::diagonal_copy_outf(
      context, input, offset, dim1, dim2, out);
}

class OpDiagonalCopyOutTest : public ::testing::Test {
 protected:
  void SetUp() override {
    // Since these tests cause ET_LOG to be called, the PAL must be initialized
    // first.
    torch::executor::runtime_init();
  }

  template <ScalarType DTYPE>
  void test_2d_dtype() {
    TensorFactory<DTYPE> tf;

    Tensor input = tf.make({3, 4}, {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12});
    Tensor out = tf.zeros({2});
    Tensor out_expected = tf.make({2}, {5, 10});
    op_diagonal_copy_out(input, 1, 1, 0, out);
    EXPECT_TENSOR_CLOSE(out, out_expected);
  }

  template <typename CTYPE, ScalarType DTYPE>
  void run_2d_complex_dtype() {
    TensorFactory<DTYPE> tf;
    Tensor input = tf.make(
        {3, 4},
        {CTYPE(1, 1),
         CTYPE(2, 2),
         CTYPE(3, 3),
         CTYPE(4, 4),
         CTYPE(5, 5),
         CTYPE(6, 6),
         CTYPE(7, 7),
         CTYPE(8, 8),
         CTYPE(9, 9),
         CTYPE(10, 10),
         CTYPE(11, 11),
         CTYPE(12, 12)});
    Tensor out = tf.make({2}, {CTYPE(0, 0), CTYPE(0, 0)});
    Tensor out_expected = tf.make({2}, {CTYPE(5, 5), CTYPE(10, 10)});
    op_diagonal_copy_out(input, 1, 1, 0, out);
    EXPECT_TENSOR_CLOSE(out, out_expected);
  }
};

TEST_F(OpDiagonalCopyOutTest, SmokeTest2D) {
#define TEST_ENTRY(ctype, dtype) test_2d_dtype<ScalarType::dtype>();
  ET_FORALL_REALHBF16_TYPES(TEST_ENTRY);
#undef TEST_ENTRY
}

TEST_F(OpDiagonalCopyOutTest, ComplexSmokeTest2D) {
#define TEST_ENTRY(ctype, dtype) \
  run_2d_complex_dtype<ctype, ScalarType::dtype>();
  ET_FORALL_COMPLEXH_TYPES(TEST_ENTRY);
#undef TEST_ENTRY
}

TEST_F(OpDiagonalCopyOutTest, SmokeTest3D) {
  TensorFactory<ScalarType::Float> tfFloat;

  Tensor input =
      tfFloat.make({2, 3, 2}, {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12});
  Tensor out = tfFloat.zeros({3, 1});
  Tensor out_expected = tfFloat.make({3, 1}, {7, 9, 11});
  op_diagonal_copy_out(input, -1, 0, -1, out);
  EXPECT_TENSOR_CLOSE(out, out_expected);
}

TEST_F(OpDiagonalCopyOutTest, SmokeTest4D) {
  TensorFactory<ScalarType::Float> tfFloat;

  Tensor input =
      tfFloat.make({2, 1, 2, 3}, {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12});
  Tensor out = tfFloat.zeros({1, 3, 2});
  Tensor out_expected = tfFloat.make({1, 3, 2}, {1, 10, 2, 11, 3, 12});
  op_diagonal_copy_out(input, 0, 0, 2, out);
  EXPECT_TENSOR_CLOSE(out, out_expected);
}
