"""Area and delay of multipliers: Yosys synthesis + OpenSTA timing.

For each design (a multiplier module and a value of N) this script
  1. synthesizes rtl/mul_wrap.sv around that multiplier (flow/synth.tcl),
  2. reads the cell counts from Yosys and the cell areas from the liberty file,
     and splits the area into flip-flops (the wrapper) and the multiplier,
  3. runs OpenSTA (flow/sta.tcl) for the minimum clock period,
and writes one CSV row per design.

Area and delay come from the same netlist. Area is also reported for the
multiplier alone (total minus the 32 wrapper flip-flops: 8 + 8 inputs, 16 outputs), which is the number
we compare across N.

Usage (normally via the Makefile, which passes the tool paths):
  python flow/ppa.py --out results/ppa_n0.csv --design approx_mul:0 --design mul_behav:0 \
      --lib <lib> --synth-lib <filtered lib> --yosys yosys --sta <sta>
"""

import argparse
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYNTH_OUT = REPO / "results" / "synth"

# RTL needed by each multiplier module (mul_wrap.sv is added automatically).
MUL_SRCS = {
    "approx_mul": ["rtl/full_adder.sv", "rtl/half_adder.sv",
                   "rtl/dadda8_reduce.sv", "rtl/approx_mul.sv"],
    "mul_behav": ["rtl/mul_behav.sv"],
}


def liberty_areas(lib_path):
    """Map cell name -> area (um^2), read from the liberty file."""
    areas, cell = {}, None
    cell_re = re.compile(r'^\s*cell\s*\(\s*"?([^")\s]+)"?\s*\)')
    area_re = re.compile(r'^\s*area\s*:\s*([0-9.eE+-]+)')
    with open(lib_path) as f:
        for line in f:
            m = cell_re.match(line)
            if m:
                cell = m.group(1)
                continue
            m = area_re.match(line)
            if m and cell and cell not in areas:
                areas[cell] = float(m.group(1))
    return areas


def parse_stat(stat_path):
    """Return (cell counts dict, total chip area) from a Yosys `stat` report."""
    counts, area = {}, None
    for line in Path(stat_path).read_text().splitlines():
        m = re.match(r"^\s+(sky130_\S+)\s+(\d+)\s*$", line)
        if m:
            counts[m.group(1)] = int(m.group(2))
        m = re.search(r"Chip area for module .*:\s*([0-9.]+)", line)
        if m:
            area = float(m.group(1))
    if area is None:
        raise RuntimeError(f"no 'Chip area' line in {stat_path}")
    return counts, area


def is_flop(cell):
    """True for sky130 flip-flop cells (dfxtp, dfrtp, ...)."""
    return re.match(r"sky130_fd_sc_hd__(s?df|edf)", cell) is not None


def run(cmd, env, log_path):
    """Run a tool, save its full output to a log, stop with the error if it fails."""
    res = subprocess.run(cmd, cwd=REPO, env={**os.environ, **env},
                         capture_output=True, text=True)
    Path(log_path).write_text(res.stdout + res.stderr)
    if res.returncode != 0:
        tail = "\n".join((res.stdout + res.stderr).splitlines()[-20:])
        sys.exit(f"ERROR: {' '.join(cmd)} failed (see {log_path}):\n{tail}")
    return res.stdout


def ppa_one(mul, n, args, areas):
    tag = f"wrap_{mul}_N{n}"
    SYNTH_OUT.mkdir(parents=True, exist_ok=True)
    srcs = MUL_SRCS[mul] + ["rtl/mul_wrap.sv"]

    # 1. Synthesis.
    run([args.yosys, "-q", "-c", "flow/synth.tcl"],
        {"TOP": "mul_wrap", "N": str(n), "SRCS": " ".join(srcs), "LIB": args.synth_lib,
         "OUT": str(SYNTH_OUT), "DEFINES": f"-DMUL={mul}", "TAG": tag},
        SYNTH_OUT / f"{tag}.log")

    # 2. Area split: flip-flops (wrapper) vs everything else (multiplier).
    counts, total_area = parse_stat(SYNTH_OUT / f"{tag}_stat.txt")
    missing = [c for c in counts if c not in areas]
    if missing:
        sys.exit(f"ERROR: cells not found in liberty: {missing}")
    flop_area = sum(areas[c] * k for c, k in counts.items() if is_flop(c))
    flop_cells = sum(k for c, k in counts.items() if is_flop(c))
    all_cells = sum(counts.values())

    # 3. Timing.
    out = run([args.sta, "-no_init", "-no_splash", "-exit", "flow/sta.tcl"],
              {"NETLIST": str(SYNTH_OUT / f"{tag}.v"), "LIB": args.lib,
               "OUT": str(SYNTH_OUT / tag)},
              SYNTH_OUT / f"{tag}_sta.log")
    m = re.search(r"MIN_PERIOD_NS\s+([0-9.]+)", out)
    if not m:
        sys.exit(f"ERROR: no MIN_PERIOD_NS in OpenSTA output for {tag}:\n{out}")
    min_period = float(m.group(1))

    return {
        "design": f"{mul}_N{n}" if mul == "approx_mul" else mul,
        "module": mul,
        "N": n,
        "area_mul_um2": round(total_area - flop_area, 4),
        "cells_mul": all_cells - flop_cells,
        "area_wrap_um2": round(total_area, 4),
        "flops": flop_cells,
        "min_period_ns": min_period,
        "fmax_mhz": round(1000.0 / min_period, 2),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--design", action="append", required=True,
                   help="module:N, e.g. approx_mul:4 (repeatable)")
    p.add_argument("--out", required=True)
    p.add_argument("--lib", required=True)
    p.add_argument("--synth-lib", required=True)
    p.add_argument("--yosys", default="yosys")
    p.add_argument("--sta", required=True)
    args = p.parse_args()

    areas = liberty_areas(args.lib)
    rows = []
    for d in args.design:
        mul, n = d.split(":")
        row = ppa_one(mul, int(n), args, areas)
        print(", ".join(f"{k}={v}" for k, v in row.items()))
        rows.append(row)

    with open(REPO / args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
