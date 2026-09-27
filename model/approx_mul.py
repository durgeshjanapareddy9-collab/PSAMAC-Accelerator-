"""Bit-exact Python model of the truncated 8x8 Dadda multiplier (rtl/approx_mul.sv).

How an 8x8 multiplier works, in one paragraph:
    Multiplying a (bits a_0..a_7) by b (bits b_0..b_7) creates 64 "partial
    product" bits, pp(i, j) = a_j AND b_i. Each one is worth 2^(i+j). Bits with
    the same i+j sit in the same "column" (column 0 is worth 1, column 1 is
    worth 2, ...). Adding all 64 weighted bits gives the exact product a*b.

Truncation with depth N:
    We simply never generate the partial products in the lowest N columns
    (those with i + j < N). Fewer bits to add means less hardware, at the cost
    of a small error. N = 0 drops nothing, so it is exact.

        approx_mul(a, b, N) = sum of a_j * b_i * 2^(i+j) over all i + j >= N

Because dropped bits can only remove value, the result is never larger than
the exact product: error = exact - approx >= 0.

This file is deliberately written from the formula above, NOT from a*b, so
that it is an independent check of the RTL.
"""

from pathlib import Path

import numpy as np

BITS = 8                      # operand width
N_MAX = 12                    # largest truncation depth we study
REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"


def approx_mul(a, b, n):
    """Truncated product of two unsigned 8-bit numbers (plain Python ints)."""
    if not (0 <= a < 256 and 0 <= b < 256):
        raise ValueError("a and b must be in 0..255")
    total = 0
    for i in range(BITS):              # i indexes the bits of b (rows)
        for j in range(BITS):          # j indexes the bits of a (columns)
            if i + j >= n:             # keep only columns i+j >= N
                total += ((a >> j) & 1) * ((b >> i) & 1) << (i + j)
    return total


def compute_lut(n):
    """256x256 table: compute_lut(n)[a, b] = approx_mul(a, b, n).

    Same formula as approx_mul, but done on all 65,536 pairs at once with numpy.
    """
    a = np.arange(256, dtype=np.int64).reshape(256, 1)   # rows    = a
    b = np.arange(256, dtype=np.int64).reshape(1, 256)   # columns = b
    table = np.zeros((256, 256), dtype=np.int64)
    for i in range(BITS):
        for j in range(BITS):
            if i + j >= n:
                table += ((a >> j) & 1) * ((b >> i) & 1) << (i + j)
    return table


def lut(n, cache=True):
    """Return the 256x256 LUT for depth n, cached as results/lut_N{n}.npy."""
    path = RESULTS / f"lut_N{n}.npy"
    if cache and path.exists():
        return np.load(path)
    table = compute_lut(n)
    if cache:
        RESULTS.mkdir(exist_ok=True)
        np.save(path, table)
    return table


def exact_lut():
    """256x256 table of exact products a*b (for computing errors)."""
    a = np.arange(256, dtype=np.int64).reshape(256, 1)
    b = np.arange(256, dtype=np.int64).reshape(1, 256)
    return a * b


def dropped_weight(n):
    """Sum of 2^(i+j) over all dropped partial products (i + j < n).

    This is the error when every dropped bit is 1, i.e. the largest possible
    error EDmax. Under uniformly random inputs each bit a_j*b_i is 1 with
    probability 1/4, so the mean error is dropped_weight(n) / 4.
    """
    return sum(1 << (i + j) for i in range(BITS) for j in range(BITS) if i + j < n)


if __name__ == "__main__":
    # Build and cache every LUT, printing a one-line summary for each.
    exact = exact_lut()
    for n in range(N_MAX + 1):
        t = lut(n, cache=True)
        ed = exact - t
        print(f"N={n:2d}  saved {RESULTS / f'lut_N{n}.npy'}  max error {ed.max()}")
