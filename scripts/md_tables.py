"""Print Markdown tables from the result CSVs, for pasting into docs/.

Usage:  python scripts/md_tables.py
Numbers in the docs are copied from this output, never typed by hand.
Relative changes are always against the exact design approx_mul_N0.

Each table is built by one function returning (title, markdown), so
flow/report.py can put the same tables into results/flow_report.md.
"""

import re
import sys
from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parent.parent / "results"
sys.path.insert(0, str(RESULTS.parent / "flow"))
from ppa import parse_stat   # noqa: E402  (same Yosys stat parser as the flow)

BASE = "approx_mul_N0"       # every relative change is against this design
# The two exact designs compared side by side.
DESIGNS = {"approx_mul_N0": "N = 0 (Dadda)", "mul_behav": "a*b (Yosys)"}

# sky130 cell name (without "sky130_fd_sc_hd__" and drive strength) -> what it does.
# First matching pattern wins.
CELL_GROUPS = [
    (r"s?df|edf", "flip-flops"),
    (r"x(n)?or", "XOR / XNOR (sum bits)"),
    (r"maj", "majority, maj3 (carry bits)"),
    (r"nand|nor", "NAND / NOR"),
    (r"and|or", "AND / OR"),
    (r"[ao]\d", "compound AND-OR / OR-AND (a21oi, o21ai, ...)"),
    (r"(clk)?inv|buf", "inverters / buffers"),
    (r"conb", "tie cells (constant 0/1)"),
]


def cell_group(cell):
    base = re.sub(r"_\d+$", "", cell.replace("sky130_fd_sc_hd__", ""))
    for pattern, group in CELL_GROUPS:
        if re.match(pattern, base):
            return group
    return "other"


def cell_groups(design_tag):
    """Cell counts per function group from a Yosys stat report."""
    counts, _ = parse_stat(RESULTS / "synth" / f"{design_tag}_stat.txt")
    out = {}
    for cell, k in counts.items():
        out[cell_group(cell)] = out.get(cell_group(cell), 0) + k
    return out


def md(df):
    """DataFrame -> Markdown table (without needing the 'tabulate' package)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def pct(new, base):
    return f"{100 * (new - base) / base:+.1f}%"


def load():
    """The result CSVs: ppa_n0 and power_n0 indexed by design, ppa_mul as rows."""
    return (pd.read_csv(RESULTS / "ppa_n0.csv").set_index("design"),
            pd.read_csv(RESULTS / "power_n0.csv").set_index("design"),
            pd.read_csv(RESULTS / "ppa_mul.csv"))


def side_by_side(a, metrics):
    """One row per (name, function of a CSV row), one column per design in DESIGNS."""
    return md(pd.DataFrame([{"result": name, **{DESIGNS[d]: str(f(a.loc[d])) for d in DESIGNS}}
                            for name, f in metrics]))


def table_error_metrics():
    e = pd.read_csv(RESULTS / "error_metrics.csv")
    t = pd.DataFrame({
        "N": e["N"],
        "ER (%)": (100 * e["ER"]).round(2),
        "ME": e["ME"],
        "MED": e["MED"],
        "NMED": e["NMED"].map(lambda x: f"{x:.3e}"),
        "MRED": e["MRED"].map(lambda x: f"{x:.3e}"),
        "EDmax": e["EDmax"],
        "pairs at EDmax": e["EDmax_count"],
    })
    return "Error metrics (results/error_metrics.csv)", md(t)


def table_n0(a, p):
    """N = 0 vs a*b: area, delay, power."""
    rows = []
    for d in DESIGNS:
        rows.append({
            "design": d,
            "multiplier area (um^2)": a.loc[d, "area_mul_um2"],
            "cells": a.loc[d, "cells_mul"],
            "min clock period (ns)": a.loc[d, "min_period_ns"],
            "multiplier power (uW)": p.loc[d, "power_comb_uW"],
            "total power incl. 32 flops (uW)": p.loc[d, "power_total_uW"],
            "area vs N=0": pct(a.loc[d, "area_mul_um2"], a.loc[BASE, "area_mul_um2"]),
            "delay vs N=0": pct(a.loc[d, "min_period_ns"], a.loc[BASE, "min_period_ns"]),
            "mult. power vs N=0": pct(p.loc[d, "power_comb_uW"], p.loc[BASE, "power_comb_uW"]),
        })
    return "N = 0 vs a*b (results/ppa_n0.csv, results/power_n0.csv)", md(pd.DataFrame(rows))


def table_sweep(s):
    """Area and delay for every N."""
    base = s[s["design"] == BASE].iloc[0]
    t = pd.DataFrame({
        "design": s["design"],
        "area (um^2)": s["area_mul_um2"],
        "cells": s["cells_mul"],
        "min period (ns)": s["min_period_ns"],
        "area vs N=0": [pct(x, base["area_mul_um2"]) for x in s["area_mul_um2"]],
        "delay vs N=0": [pct(x, base["min_period_ns"]) for x in s["min_period_ns"]],
    })
    return "Area and delay vs N (results/ppa_mul.csv)", md(t)


def table_yosys(a):
    """Detailed Yosys results, N = 0 vs a*b."""
    return "Yosys results, N = 0 vs a*b (results/ppa_n0.csv)", side_by_side(a, [
        ("total standard cells (incl. flip-flops)", lambda x: x["cells_mul"] + x["flops"]),
        ("logic gates (multiplier)", lambda x: x["cells_mul"]),
        ("flip-flops (wrapper, dfxtp_1)", lambda x: x["flops"]),
        ("different cell types used", lambda x: x["cell_types"]),
        ("total cell area (um^2)", lambda x: x["area_wrap_um2"]),
        ("multiplier area (um^2)", lambda x: x["area_mul_um2"]),
        ("flip-flop area (um^2)", lambda x: round(x["area_wrap_um2"] - x["area_mul_um2"], 4)),
        ("`check` problems", lambda x: x["yosys_check_problems"]),
        ("warnings in Yosys log", lambda x: x["yosys_warnings"]),
        ("of which: liberty cells Yosys cannot model", lambda x: x["yosys_liberty_warnings"]),
    ])


def table_cells():
    """Cells grouped by function, N = 0 vs a*b."""
    groups = {d: cell_groups(f"wrap_{d}_N0" if d == "mul_behav" else f"wrap_{d}")
              for d in DESIGNS}
    order = [g for _, g in CELL_GROUPS] + ["other"]
    t = pd.DataFrame([{"cell function": g, **{DESIGNS[d]: groups[d].get(g, 0) for d in DESIGNS}}
                      for g in order if any(g in groups[d] for d in DESIGNS)])
    return "Cells by function, N = 0 vs a*b (results/synth/*_stat.txt)", md(t)


def table_sta(a):
    """Detailed OpenSTA results, N = 0 vs a*b."""
    return "OpenSTA results, N = 0 vs a*b (results/ppa_n0.csv)", side_by_side(a, [
        ("max path delay, critical path (ns)", lambda x: x["max_path_ns"]),
        ("of which: cell delay (ns)", lambda x: x["max_path_cell_ns"]),
        ("of which: net (wire) delay (ns)", lambda x: x["max_path_net_ns"]),
        ("cells on the critical path (incl. launch flop)", lambda x: x["max_path_cells"]),
        ("min clock period (ns)", lambda x: x["min_period_ns"]),
        ("max frequency (MHz)", lambda x: x["fmax_mhz"]),
        ("setup slack at 10 ns (ns)", lambda x: x["setup_slack_ns"]),
        ("setup WNS / TNS (ns)", lambda x: f"{x['setup_wns_ns']} / {x['setup_tns_ns']}"),
        ("setup violations", lambda x: x["setup_violations"]),
        ("min path delay, flop to flop (ns)", lambda x: x["min_path_ns"]),
        ("hold slack, flop to flop (ns)", lambda x: x["hold_slack_r2r_ns"]),
        ("hold slack, any path (ns)", lambda x: x["hold_slack_ns"]),
        ("hold WNS / TNS (ns)", lambda x: f"{x['hold_wns_ns']} / {x['hold_tns_ns']}"),
        ("hold violations", lambda x: x["hold_violations"]),
        ("timing endpoints checked", lambda x: x["endpoints"]),
        ("SDC/constraint problems (`check_setup`)", lambda x: x["sta_check_issues"]),
    ])


def table_timing_vs_n(s):
    """Timing details for every N."""
    t = pd.DataFrame({
        "design": s["design"],
        "max path (ns)": s["max_path_ns"],
        "cells on path": s["max_path_cells"],
        "setup slack (ns)": s["setup_slack_ns"],
        "min path (ns)": s["min_path_ns"],
        "hold slack (ns)": s["hold_slack_r2r_ns"],
        "WNS setup/hold (ns)": [f"{x} / {y}" for x, y in zip(s["setup_wns_ns"], s["hold_wns_ns"])],
        "TNS setup/hold (ns)": [f"{x} / {y}" for x, y in zip(s["setup_tns_ns"], s["hold_tns_ns"])],
        "violations": s["setup_violations"] + s["hold_violations"],
        "`check` problems": s["yosys_check_problems"],
    })
    return ("Timing details vs N (results/ppa_mul.csv; slack at 10 ns, hold flop to flop)",
            md(t))


def main():
    a, p, s = load()
    tables = [table_error_metrics(), table_n0(a, p), table_sweep(s), table_yosys(a),
              table_cells(), table_sta(a), table_timing_vs_n(s)]
    print("\n\n".join(f"### {title}\n\n{body} " for title, body in tables).rstrip())


if __name__ == "__main__":
    main()
