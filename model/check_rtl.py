"""Compare an RTL simulation dump with the Python model.

Usage:  python -m model.check_rtl <N> [<N> ...]

Reads results/rtl_dump_N{N}.txt (lines "a b p" written by
tb/tb_approx_mul_exhaustive.sv) and checks every line against lut(N).
Prints PASS or FAIL, the number of mismatches and the first few mismatches.
Exits with status 1 if any N fails, so `make test` stops.
"""

import sys

import numpy as np

from model.approx_mul import RESULTS, lut

SHOW = 5   # how many mismatches to print


def check(n):
    path = RESULTS / f"rtl_dump_N{n}.txt"
    if not path.exists():
        print(f"N={n:2d}: FAIL  missing {path}")
        return False
    data = np.loadtxt(path, dtype=np.int64, ndmin=2)
    if data.shape != (65536, 3):
        print(f"N={n:2d}: FAIL  expected 65536 lines of 'a b p', got shape {data.shape}")
        return False
    a, b, p = data[:, 0], data[:, 1], data[:, 2]

    # Every pair must appear exactly once.
    if len(np.unique(a * 256 + b)) != 65536:
        print(f"N={n:2d}: FAIL  dump does not cover all 65,536 distinct pairs")
        return False

    expected = lut(n)[a, b]
    bad = np.flatnonzero(p != expected)
    if len(bad) == 0:
        print(f"N={n:2d}: PASS  65536/65536 match")
        return True
    print(f"N={n:2d}: FAIL  {len(bad)} mismatches out of 65536")
    for k in bad[:SHOW]:
        print(f"        a={a[k]:3d} b={b[k]:3d}  rtl={p[k]:5d}  model={expected[k]:5d}")
    return False


def main():
    ns = [int(x) for x in sys.argv[1:]] or [0]
    ok = all([check(n) for n in ns])     # list, so every N is checked and reported
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
