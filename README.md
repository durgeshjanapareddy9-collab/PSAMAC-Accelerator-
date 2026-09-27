# AxMAC: a precision-scalable approximate MAC accelerator

AI Accelerators course project, IIIT Dharwad.

An 8x8 unsigned Dadda multiplier whose amount of approximation is a single
compile-time parameter **N**: the partial products in the lowest N columns
are dropped (N = 0 is exact). We verify it exhaustively against a Python
model, measure area, delay and power on SkyWater 130 nm with open-source
tools only (Yosys, OpenSTA), and (Milestone 2) evaluate it in a MAC unit,
a 4x4 systolic array, image filtering and a small CNN.

The multiplier architecture, a Dadda tree with truncated low-order columns,
is existing prior art. Our contribution is the parameterization, the
open-flow characterization and the evaluation framework.

Status: Milestone 1. See [docs/milestone1.md](docs/milestone1.md) for results
and [PROGRESS.md](PROGRESS.md) for the task list.

## Quick start

```bash
make venv       # create .venv/ with the Python packages (requirements.txt)
make test       # Python model tests + RTL vs model, all 65,536 pairs, N = 0..12
make metrics    # results/error_metrics.csv, figures/error_vs_N.png
make synth      # area + delay, N = 0 vs a*b     -> results/ppa_n0.csv
make power      # power,        N = 0 vs a*b     -> results/power_n0.csv
make sweep      # area + delay for every N       -> results/ppa_mul.csv
make versions   # tool versions                  -> results/tool_versions.txt
make gen        # regenerate rtl/dadda8_reduce.sv
```

`make sim-N4` / `make check-N4` simulate / check a single N.
Targets for Milestone 2 (`baselines`, `eval`, `cnn`, `analysis`, `figures`)
still print "not implemented yet" and fail on purpose.

## Requirements

Versions we used are in `results/tool_versions.txt`.

| Tool | Used for | Notes |
|---|---|---|
| Yosys (0.33) | synthesis | `apt install yosys` |
| OpenSTA | timing and power | built from source, see below |
| Icarus Verilog (12) | RTL and gate-level simulation | `apt install iverilog` |
| sky130A PDK | standard cells `sky130_fd_sc_hd` | installed with [volare](https://github.com/efabless/volare) into `~/.volare` |
| Python 3.10+ | model, metrics, flow scripts | `make venv` |

All tool and library paths are set in one place, **`flow/config.mk`**. If
yours differ, edit that file or override on the command line
(`make synth PDK_ROOT=/foss/pdks`).

The IIC-OSIC-TOOLS Docker image also contains all of these tools.

### Building OpenSTA (Ubuntu 24.04)

There is no prebuilt OpenSTA/OpenROAD package for Ubuntu 24.04, so we build
it from source into `~/tools` (no sudo needed after the first line):

```bash
sudo apt install cmake g++ bison flex swig tcl-dev libeigen3-dev zlib1g-dev

mkdir -p ~/tools/src && cd ~/tools/src

# CUDD (BDD library OpenSTA needs)
git clone https://github.com/cuddorg/cudd.git && cd cudd && git checkout 3.0.0
touch aclocal.m4 && sleep 1 && touch configure Makefile.in config.h.in   # stop make from re-running automake
./configure --prefix=$HOME/tools/cudd && make -j && make install && cd ..

# OpenSTA
git clone https://github.com/parallaxsw/OpenSTA.git && cd OpenSTA
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/tools/opensta -DCUDD_DIR=$HOME/tools/cudd -DCMAKE_BUILD_TYPE=Release
make -j && make install          # -> ~/tools/opensta/bin/sta
```

## How the flow works

1. `scripts/gen_dadda.py` plans the Dadda reduction tree, checks it in Python
   on all 65,536 inputs for every N, and writes `rtl/dadda8_reduce.sv`.
2. `rtl/approx_mul.sv` ties the dropped partial products to 0 and feeds the
   rest into the tree. The tree is the same for every N; synthesis removes the
   adders whose inputs are constant.
3. `tb/tb_approx_mul_exhaustive.sv` dumps all 65,536 outputs;
   `model/check_rtl.py` compares them with `model/approx_mul.py`.
4. `flow/ppa.py` synthesizes `rtl/mul_wrap.sv` (flip-flops around the
   multiplier) with `flow/synth.tcl` and times it with `flow/sta.tcl`.
5. `flow/power.py` simulates the gate-level netlist (`tb/tb_power.sv`) and runs
   `flow/power.tcl` (OpenSTA `read_vcd` + `report_power`).

Corner: `sky130_fd_sc_hd__tt_025C_1v80` (typical, 25 °C, 1.80 V), pre-layout.

## Repository layout

```
rtl/        full_adder.sv, half_adder.sv, dadda8_reduce.sv (generated),
            approx_mul.sv, mul_behav.sv (a*b), mul_wrap.sv (registered wrapper)
scripts/    gen_dadda.py, tool_versions.sh, md_tables.py
tb/         tb_approx_mul_exhaustive.sv, tb_power.sv
model/      approx_mul.py, check_rtl.py, metrics.py, tests/
flow/       config.mk, synth.tcl, sta.tcl, power.tcl, ppa.py, power.py, make_synth_lib.py
results/    generated CSVs and reports (never hand-edited)
figures/    generated plots
docs/       milestone1.md, REFERENCES.md
```

Large regenerable files (LUT `.npy`, RTL dumps, VCDs, netlists) are not
committed; `make` recreates them.

## Credits

References are listed in [docs/REFERENCES.md](docs/REFERENCES.md). No code
from other repositories has been copied so far; baseline designs added in
Milestone 2 will be credited here with their licenses.
