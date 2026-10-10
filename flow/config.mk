# flow/config.mk -- the ONE place where tool and library paths are set.
#
# Every Makefile rule and flow script reads these values, so if your machine
# keeps the PDK or tools somewhere else, change them here (or override on the
# command line, e.g.  make synth PDK_ROOT=/foss/pdks ).
#
# "?=" means "use this default unless it is already set".

# ---- Process design kit (PDK) ---------------------------------------------
# sky130A is SkyWater's open 130 nm process. We installed it with volare.
PDK_ROOT ?= $(HOME)/.volare
PDK      ?= sky130A

# Standard-cell library: sky130_fd_sc_hd ("high density").
# Corner: tt = typical transistors, 25 degrees C, 1.80 V supply.
LIB_NAME ?= sky130_fd_sc_hd__tt_025C_1v80.lib
LIB      ?= $(PDK_ROOT)/$(PDK)/libs.ref/sky130_fd_sc_hd/lib/$(LIB_NAME)
# Verilog simulation models of the same cells (for gate-level simulation).
CELL_MODELS ?= $(PDK_ROOT)/$(PDK)/libs.ref/sky130_fd_sc_hd/verilog

# ---- Tools -----------------------------------------------------------------
YOSYS     ?= yosys
STA       ?= $(HOME)/tools/opensta/bin/sta
# OpenSTA was built from source (see README); its git commit is recorded too.
OPENSTA_SRC ?= $(HOME)/tools/src/OpenSTA
IVERILOG  ?= iverilog
VVP       ?= vvp
VERILATOR ?= verilator
# Graphviz, draws the Yosys `show` diagrams (make diagrams).
DOT       ?= dot

# Python from the project virtual environment (created by `make venv`).
VENV   ?= .venv
PYTHON ?= $(VENV)/bin/python
