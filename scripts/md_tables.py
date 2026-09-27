"""Print Markdown tables from the result CSVs, for pasting into docs/.

Usage:  python scripts/md_tables.py
Numbers in the docs are copied from this output, never typed by hand.
Relative changes are always against the exact design approx_mul_N0.
"""

from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parent.parent / "results"


def md(df):
    """DataFrame -> Markdown table (without needing the 'tabulate' package)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def pct(new, base):
    return f"{100 * (new - base) / base:+.1f}%"


def main():
    # Error metrics
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
    print("### Error metrics (results/error_metrics.csv)\n")
    print(md(t), "\n")

    # N = 0 vs a*b: area, delay, power
    a = pd.read_csv(RESULTS / "ppa_n0.csv").set_index("design")
    p = pd.read_csv(RESULTS / "power_n0.csv").set_index("design")
    b0 = "approx_mul_N0"
    rows = []
    for d in ["approx_mul_N0", "mul_behav"]:
        rows.append({
            "design": d,
            "multiplier area (um^2)": a.loc[d, "area_mul_um2"],
            "cells": a.loc[d, "cells_mul"],
            "min clock period (ns)": a.loc[d, "min_period_ns"],
            "multiplier power (uW)": p.loc[d, "power_comb_uW"],
            "total power incl. 32 flops (uW)": p.loc[d, "power_total_uW"],
            "area vs N=0": pct(a.loc[d, "area_mul_um2"], a.loc[b0, "area_mul_um2"]),
            "delay vs N=0": pct(a.loc[d, "min_period_ns"], a.loc[b0, "min_period_ns"]),
            "mult. power vs N=0": pct(p.loc[d, "power_comb_uW"], p.loc[b0, "power_comb_uW"]),
        })
    print("### N = 0 vs a*b (results/ppa_n0.csv, results/power_n0.csv)\n")
    print(md(pd.DataFrame(rows)), "\n")

    # Area and delay sweep
    s = pd.read_csv(RESULTS / "ppa_mul.csv")
    base = s[s["design"] == b0].iloc[0]
    t = pd.DataFrame({
        "design": s["design"],
        "area (um^2)": s["area_mul_um2"],
        "cells": s["cells_mul"],
        "min period (ns)": s["min_period_ns"],
        "area vs N=0": [pct(x, base["area_mul_um2"]) for x in s["area_mul_um2"]],
        "delay vs N=0": [pct(x, base["min_period_ns"]) for x in s["min_period_ns"]],
    })
    print("### Area and delay vs N (results/ppa_mul.csv)\n")
    print(md(t))


if __name__ == "__main__":
    main()
