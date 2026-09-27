"""Make a copy of the liberty file with "do not use" cells removed.

Why: the sky130_fd_sc_hd library contains special-purpose cells that a normal
design flow never uses for ordinary logic -- e.g. the low-power isolation cells
(lpflow_*) meant for power-gated blocks, and probe cells for debugging. If they
are left in, ABC happily picks them (they are small), which makes our area
numbers unrealistic. OpenLane excludes the same families.

Yosys 0.33 has no "-dont_use" option, so instead we delete those cells from a
copy of the liberty file and give that copy to Yosys only. OpenSTA reads the
original file; the cells we keep are byte-for-byte identical in both.

Usage:  python flow/make_synth_lib.py <input.lib> <output.lib>
"""

import fnmatch
import re
import sys

# Cell-name patterns to remove (fnmatch style).
DONT_USE = [
    "sky130_fd_sc_hd__lpflow_*",   # power-gating / isolation cells
    "sky130_fd_sc_hd__probe_*",    # debug probe cells
]

CELL_START = re.compile(r'^\s*cell\s*\(\s*"?([^")\s]+)"?\s*\)\s*\{')


def filter_liberty(text):
    """Return (filtered_text, removed_cell_names).

    Walks the file line by line. When a `cell (name) {` line matches a
    DONT_USE pattern, it skips lines until the braces opened by that cell are
    closed again.
    """
    out, removed = [], []
    depth = 0          # brace depth inside a cell being skipped (0 = not skipping)
    for line in text.splitlines(keepends=True):
        if depth == 0:
            m = CELL_START.match(line)
            if m and any(fnmatch.fnmatch(m.group(1), p) for p in DONT_USE):
                removed.append(m.group(1))
                depth = line.count("{") - line.count("}")
                continue
            out.append(line)
        else:
            depth += line.count("{") - line.count("}")
    return "".join(out), removed


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src) as f:
        text = f.read()
    filtered, removed = filter_liberty(text)
    with open(dst, "w") as f:
        f.write(filtered)
    print(f"{dst}: removed {len(removed)} cells: {', '.join(removed)}")


if __name__ == "__main__":
    main()
