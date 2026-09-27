"""Generate rtl/dadda8_reduce.sv, the reduction tree of an 8x8 Dadda multiplier.

Background (plain language)
---------------------------
An 8x8 multiplier has 64 partial-product bits pp(i, j) = a_j & b_i, each worth
2^(i+j). Bits with the same i+j form "column" i+j (0..14). Column heights are
1, 2, 3, ..., 8, ..., 3, 2, 1 -- the tallest column has 8 bits.

We cannot add 8 bits in one go, so a Dadda tree shrinks the columns in stages
using full adders (3 bits -> 1 bit here + 1 carry to the next column) and half
adders (2 bits -> 1 bit here + 1 carry). Dadda's rule is to do the *least*
work per stage: each stage only shrinks every column to the next target height
in the sequence 6, 4, 3, 2. After the last stage every column has at most two
bits, i.e. two 16-bit rows, which a normal adder (row0 + row1) finishes.

Truncation (the N knob) is NOT handled here. approx_mul.sv ties the dropped
partial products to 0 before they enter this tree, and synthesis then deletes
any adder whose inputs are constant (constant propagation). The tree is the
same for every N; it is not re-planned per N.

Usage:  python scripts/gen_dadda.py            (writes rtl/dadda8_reduce.sv)
"""

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "rtl" / "dadda8_reduce.sv"
BITS = 8
COLS = 2 * BITS            # 16 product columns (0..15)
TARGETS = [6, 4, 3, 2]     # Dadda height sequence for a max column height of 8


def plan_tree():
    """Run the Dadda algorithm on signal names.

    Returns (stages, final_cols):
      stages     -- per stage: dict with target height, the adders used, and
                    the column heights before the stage
      final_cols -- list of 16 columns, each a list of <= 2 signal names
    Each adder is a tuple (kind, column, input_names, sum_name, cout_name).
    """
    # Column c starts with every pp(i, j) where i + j == c.
    cols = [[] for _ in range(COLS)]
    for i in range(BITS):
        for j in range(BITS):
            cols[i + j].append(f"pp[{i * BITS + j}]")

    stages = []
    for s, d in enumerate(TARGETS, start=1):
        heights = [len(c) for c in cols]
        new = [[] for _ in range(COLS)]
        adders = []
        carries_in = 0                     # carries arriving from column c-1 this stage
        for c in range(COLS):
            bits = list(cols[c])
            # Bits this column will hold after the stage, if we do nothing:
            # its own bits plus the carries coming in from the right.
            excess = len(bits) + carries_in - d
            n_fa, n_ha = (excess // 2, excess % 2) if excess > 0 else (0, 0)
            assert 3 * n_fa + 2 * n_ha <= len(bits), f"stage {s} col {c}: not enough bits"
            carries_out = 0
            for k in range(n_fa):
                ins, bits = bits[:3], bits[3:]
                name = f"s{s}_c{c}_fa{k}"
                adders.append(("fa", c, ins, f"{name}_sum", f"{name}_cout"))
                new[c].append(f"{name}_sum")
                carries_out += 1
            for k in range(n_ha):
                ins, bits = bits[:2], bits[2:]
                name = f"s{s}_c{c}_ha{k}"
                adders.append(("ha", c, ins, f"{name}_sum", f"{name}_cout"))
                new[c].append(f"{name}_sum")
                carries_out += 1
            new[c].extend(bits)            # bits not used by any adder pass straight through
            # This stage's carries land in the next column of the NEXT stage.
            for kind, col, _, _, cout in adders:
                if col == c:
                    if c + 1 >= COLS:
                        raise AssertionError("carry out of column 15 -- impossible for 8x8")
                    new[c + 1].append(cout)
            carries_in = carries_out
        assert max(len(c) for c in new) <= d, f"stage {s} missed target {d}"
        stages.append({"target": d, "heights": heights, "adders": adders})
        cols = new
    return stages, cols


def self_check(stages, final_cols):
    """Evaluate the planned tree on all 65,536 input pairs with numpy.

    For every N it must give exactly the Python model's LUT; this catches
    generator bugs before any Verilog is simulated.
    """
    sys.path.insert(0, str(REPO))
    from model.approx_mul import N_MAX, compute_lut

    a = np.repeat(np.arange(256, dtype=np.int64), 256)   # all pairs, a-major order
    b = np.tile(np.arange(256, dtype=np.int64), 256)
    for n in range(N_MAX + 1):
        sig = {}
        for i in range(BITS):
            for j in range(BITS):
                bit = ((a >> j) & 1) & ((b >> i) & 1)
                sig[f"pp[{i * BITS + j}]"] = bit if i + j >= n else np.zeros_like(bit)
        for st in stages:
            for kind, _, ins, s_name, c_name in st["adders"]:
                total = sum(sig[x] for x in ins)
                sig[s_name], sig[c_name] = total & 1, total >> 1
        result = np.zeros_like(a)
        for c, col in enumerate(final_cols):
            for x in col:
                result += sig[x] << c
        expected = compute_lut(n)[a, b]
        bad = np.count_nonzero(result != expected)
        if bad:
            raise AssertionError(f"self-check FAILED at N={n}: {bad} mismatches")
    print(f"self-check: tree matches the Python model on all 65,536 pairs for N = 0..{N_MAX}")


def emit_verilog(stages, final_cols):
    n_fa = sum(1 for st in stages for x in st["adders"] if x[0] == "fa")
    n_ha = sum(1 for st in stages for x in st["adders"] if x[0] == "ha")
    L = []
    w = L.append
    w("// dadda8_reduce.sv -- GENERATED by scripts/gen_dadda.py. Do not edit by hand;")
    w("// change the script and re-run:  python scripts/gen_dadda.py")
    w("//")
    w("// Reduction tree of an 8x8 Dadda multiplier.")
    w("//   Input : pp[i*8+j] = a[j] & b[i], the 64 partial-product bits.")
    w("//           pp[i*8+j] belongs to column i+j and is worth 2^(i+j).")
    w("//   Output: two 16-bit rows. row0 + row1 = sum of all partial products.")
    w("//")
    w("// Each stage uses full adders (FA: 3 bits -> sum here + carry to the next")
    w("// column) and half adders (HA: 2 bits -> sum here + carry) to bring every")
    w("// column down to the stage's target height (Dadda sequence 6, 4, 3, 2).")
    w("//")
    w("// Column heights before each stage (column 0 on the left):")
    for s, st in enumerate(stages, start=1):
        fa = sum(1 for x in st["adders"] if x[0] == "fa")
        ha = sum(1 for x in st["adders"] if x[0] == "ha")
        w(f"//   stage {s} (target {st['target']}): {' '.join(str(h) for h in st['heights'])}"
          f"   -> {fa} FA, {ha} HA")
    w(f"//   final: {' '.join(str(len(c)) for c in final_cols)}")
    w(f"// Total: {n_fa} full adders, {n_ha} half adders.")
    w("//")
    w("// Truncation is done OUTSIDE this module (approx_mul.sv ties dropped")
    w("// partial products to 0); synthesis removes adders fed only by zeros.")
    w("")
    w("module dadda8_reduce (")
    w("    input  logic [63:0] pp,     // partial products, pp[i*8+j] = a[j] & b[i]")
    w("    output logic [15:0] row0,   // first final row")
    w("    output logic [15:0] row1    // second final row (row0 + row1 = product)")
    w(");")
    for s, st in enumerate(stages, start=1):
        w("")
        w(f"    // ---- Stage {s}: reduce every column to at most {st['target']} bits ----")
        for kind, c, ins, s_name, c_name in st["adders"]:
            w(f"    logic {s_name}, {c_name};")
            inst = s_name[: -len("_sum")]
            if kind == "fa":
                w(f"    full_adder u_{inst} (.a({ins[0]}), .b({ins[1]}), .cin({ins[2]}), "
                  f".sum({s_name}), .cout({c_name}));  // column {c}")
            else:
                w(f"    half_adder u_{inst} (.a({ins[0]}), .b({ins[1]}), "
                  f".sum({s_name}), .cout({c_name}));  // column {c}")
    w("")
    w("    // ---- Final two rows: column c has at most two bits left ----")
    for c, col in enumerate(final_cols):
        r0 = col[0] if len(col) > 0 else "1'b0"
        r1 = col[1] if len(col) > 1 else "1'b0"
        w(f"    assign row0[{c}] = {r0};")
        w(f"    assign row1[{c}] = {r1};")
    w("endmodule")
    OUT.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}: {n_fa} full adders, {n_ha} half adders")


def main():
    stages, final_cols = plan_tree()
    self_check(stages, final_cols)
    emit_verilog(stages, final_cols)


if __name__ == "__main__":
    main()
