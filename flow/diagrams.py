"""Draw the design as Graphviz diagrams with Yosys `show` -> figures/yosys_*.{svg,png}.

Views (small to large):
  half_adder_rtl, full_adder_rtl  one adder cell, as RTL logic ($and, $xor, ...)
  dadda_tree                      the generated Dadda tree: all 35 full and 7 half
                                  adders as boxes, wired from the partial
                                  products (pp) to the two output rows
  gates_N12, gates_N8             real sky130 cells after synthesis (mul_wrap
                                  netlist, flip-flops included)
  gates_N0                        the exact multiplier, every cell (very large,
                                  best opened as SVG and zoomed)

How it works: Yosys `show -format dot` writes the circuit as a Graphviz .dot
file (boxes = cells, lines = wires); Graphviz `dot` lays it out and draws it.
The gate-level views read the netlists from results/synth/, so run
`make sweep` first.

Usage (normally via `make diagrams`):
  python flow/diagrams.py --lib <liberty file> [--yosys yosys] [--dot dot]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppa import REPO, SYNTH_OUT, run   # noqa: E402  (same helpers as the area/delay flow)

FIGURES = REPO / "figures"
BUILD = REPO / "build" / "diagrams"
ADDERS = "rtl/full_adder.sv rtl/half_adder.sv"


def views(lib):
    """name -> (Yosys commands ending in a module to show, PNG resolution in dpi)."""
    # read_liberty -lib: sky130 cells as empty boxes with known pin directions,
    # so wires are drawn from each cell's outputs to the next cell's inputs.
    def gates(n):
        netlist = SYNTH_OUT / f"wrap_approx_mul_N{n}.v"
        if not netlist.exists():
            sys.exit(f"ERROR: {netlist} not found -- run `make sweep` first")
        # Paths relative to the repo: the repo path may contain spaces, which
        # would split a path inside a Yosys command.
        rel = netlist.relative_to(REPO)
        return f"read_liberty -lib {lib}; read_verilog {rel}; hierarchy -top mul_wrap", "mul_wrap"

    # proc turns `assign` statements into logic cells; opt_clean removes
    # unused wires. The adders are not flattened, so each stays one box.
    rtl = f"read_verilog -sv {ADDERS}"
    return {
        "half_adder_rtl": (f"{rtl}; hierarchy -top half_adder; proc; opt", "half_adder", 110),
        "full_adder_rtl": (f"{rtl}; hierarchy -top full_adder; proc; opt", "full_adder", 110),
        "dadda_tree": (f"{rtl} rtl/dadda8_reduce.sv; hierarchy -top dadda8_reduce; proc; opt_clean",
                       "dadda8_reduce", 60),
        "gates_N12": (*gates(12), 70),
        "gates_N8": (*gates(8), 50),
        "gates_N0": (*gates(0), 30),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--lib", required=True)
    p.add_argument("--yosys", default="yosys")
    p.add_argument("--dot", default="dot")
    args = p.parse_args()

    FIGURES.mkdir(exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    for name, (cmds, top, dpi) in views(args.lib).items():
        dot_file = (BUILD / f"yosys_{name}").relative_to(REPO)   # Yosys adds .dot
        # -notitle: no title line; -width: label buses with their bit width.
        run([args.yosys, "-q", "-p",
             f"{cmds}; show -format dot -notitle -width -prefix {dot_file} {top}"],
            {}, BUILD / f"yosys_{name}.log")
        for fmt, extra in (("svg", []), ("png", [f"-Gdpi={dpi}"])):
            out = FIGURES / f"yosys_{name}.{fmt}"
            run([args.dot, f"-T{fmt}", *extra, f"{dot_file}.dot", "-o", str(out)],
                {}, BUILD / f"yosys_{name}_dot.log")
        print(f"wrote figures/yosys_{name}.svg and .png")


if __name__ == "__main__":
    main()
