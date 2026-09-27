"""Power of synthesized multipliers: gate-level simulation + OpenSTA report_power.

For each design (whose wrapper netlist flow/ppa.py already produced):
  1. simulate the gate-level netlist of mul_wrap with the sky130 cell models
     (tb/tb_power.sv), uniform random inputs, and record a VCD;
  2. run OpenSTA (flow/power.tcl): read_vcd, then report_power;
  3. write one CSV row per design.

Every design uses the same clock (10 ns), number of cycles, random seed and
corner, so the numbers can be compared with each other.

Usage (normally via `make power`):
  python flow/power.py --out results/power_n0.csv --design approx_mul:0 --design mul_behav:0 \
      --lib <lib> --sta <sta> --cell-models <sky130 verilog dir>
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppa import REPO, SYNTH_OUT, run   # noqa: E402  (same helpers as the area/delay flow)

BUILD = REPO / "build"


def power_one(mul, n, args):
    tag = f"wrap_{mul}_N{n}"
    netlist = SYNTH_OUT / f"{tag}.v"
    if not netlist.exists():
        sys.exit(f"ERROR: {netlist} not found -- run the synthesis step first")
    BUILD.mkdir(exist_ok=True)
    vcd = BUILD / f"{tag}.vcd"
    vvp = BUILD / f"{tag}_power.vvp"
    # Only exact designs can be checked against a*b inside the testbench.
    exact = (mul == "mul_behav") or (mul == "approx_mul" and n == 0)

    # 1. Gate-level simulation.
    models = Path(args.cell_models)
    run([args.iverilog, "-g2012", "-DFUNCTIONAL", "-DUNIT_DELAY=#1",
         f"-Ptb_power.CYCLES={args.cycles}", f"-Ptb_power.CLK_NS={args.clk_ns}",
         f"-Ptb_power.SEED={args.seed}", f"-Ptb_power.CHECK_EXACT={int(exact)}",
         f'-Ptb_power.VCD_FILE="{vcd.relative_to(REPO)}"',
         "-o", str(vvp), "tb/tb_power.sv", str(netlist),
         str(models / "primitives.v"), str(models / "sky130_fd_sc_hd.v")],
        {}, BUILD / f"{tag}_iverilog.log")
    sim = run([args.vvp, "-n", str(vvp)], {}, BUILD / f"{tag}_sim.log")
    if exact:
        m = re.search(r"gate-level check (\d+)/(\d+) outputs correct", sim)
        if not m or m.group(1) != m.group(2):
            sys.exit(f"ERROR: gate-level simulation of {tag} gives wrong products:\n{sim}")

    # 2. Power analysis.
    out = run([args.sta, "-no_init", "-no_splash", "-exit", "flow/power.tcl"],
              {"NETLIST": str(netlist), "LIB": args.lib, "VCD": str(vcd),
               "SCOPE": "tb_power/dut", "CLK_NS": str(args.clk_ns),
               "OUT": str(SYNTH_OUT / tag)},
              SYNTH_OUT / f"{tag}_power.log")
    ann = re.search(r"^vcd\s+(\d+)\s*\nunannotated\s+(\d+)", out, re.M)
    if not ann or int(ann.group(2)) != 0:
        sys.exit(f"ERROR: not every pin got simulation activity for {tag}:\n{out}")

    # Rows look like: "Combinational  7.1e-04  4.9e-04  8.4e-10  1.2e-03  83.5%"
    def row(group):
        m = re.search(rf"^{group}\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", out, re.M)
        if not m:
            sys.exit(f"ERROR: no '{group}' row in report_power output for {tag}")
        return [float(x) for x in m.groups()]      # internal, switching, leakage, total (W)

    seq, comb, tot = row("Sequential"), row("Combinational"), row("Total")
    uw = 1e6                                          # watts -> microwatts
    vcd.unlink()                                      # VCDs are large; the report is kept
    return {
        "design": f"{mul}_N{n}" if mul == "approx_mul" else mul,
        "module": mul,
        "N": n,
        "clk_ns": args.clk_ns,
        "cycles": args.cycles,
        "stimulus": "uniform_random",
        "annotated_pins": int(ann.group(1)),
        "power_comb_uW": round(comb[3] * uw, 3),
        "power_seq_uW": round(seq[3] * uw, 3),
        "power_total_uW": round(tot[3] * uw, 3),
        "switching_uW": round(tot[1] * uw, 3),
        "internal_uW": round(tot[0] * uw, 3),
        "leakage_uW": round(tot[2] * uw, 6),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--design", action="append", required=True, help="module:N (repeatable)")
    p.add_argument("--out", required=True)
    p.add_argument("--lib", required=True)
    p.add_argument("--sta", required=True)
    p.add_argument("--cell-models", required=True, help="sky130_fd_sc_hd/verilog directory")
    p.add_argument("--iverilog", default="iverilog")
    p.add_argument("--vvp", default="vvp")
    p.add_argument("--clk-ns", type=float, default=10.0)
    p.add_argument("--cycles", type=int, default=5000)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    rows = []
    for d in args.design:
        mul, n = d.split(":")
        r = power_one(mul, int(n), args)
        print(", ".join(f"{k}={v}" for k, v in r.items()))
        rows.append(r)
    with open(REPO / args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
