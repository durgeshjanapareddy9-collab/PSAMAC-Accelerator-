# Makefile for AxMAC -- one command per project step.
#
#   make venv       create .venv/ and install Python packages
#   make versions   record tool versions in results/tool_versions.txt
#   make gen        regenerate rtl/dadda8_reduce.sv from scripts/gen_dadda.py
#   make test       RTL vs Python model, all 65,536 input pairs, N = 0..12
#   make metrics    error metrics (MED, NMED, MRED, ER, ME, EDmax)
#   make synth      Yosys synthesis to sky130 (area)
#   make power      OpenSTA power from simulation activity
#   make sweep      area/delay/power for every N
#   make baselines  EvoApproxLib / TruMD designs through the same flow
#   make eval       image convolution quality (PSNR, SSIM)
#   make cnn        CNN top-1 accuracy
#   make analysis   which error metric predicts quality loss
#   make figures    regenerate every plot in figures/
#   make all        everything above, in order
#
# Paths to tools and the liberty file live in flow/config.mk.

include flow/config.mk

# Truncation depths covered by the sweep.
NS := 0 1 2 3 4 5 6 7 8 9 10 11 12

.PHONY: venv versions gen test test-model metrics synth synth-one power sweep baselines eval cnn \
        analysis figures all clean

# ---- Setup -------------------------------------------------------------------

venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	touch $@

versions: venv
	bash scripts/tool_versions.sh "$(YOSYS)" "$(STA)" "$(IVERILOG)" "$(VERILATOR)" "$(PYTHON)" "$(LIB)"

# Regenerate the Dadda reduction tree (the output file is committed).
gen: venv
	$(PYTHON) scripts/gen_dadda.py

# ---- Project steps (filled in as the tasks in PROGRESS.md are done) ----------
# Each placeholder fails on purpose, so nobody mistakes it for a passing step.

# RTL files of the approximate multiplier.
MUL_SRCS := rtl/full_adder.sv rtl/half_adder.sv rtl/dadda8_reduce.sv rtl/approx_mul.sv

# Full test: Python model tests, then RTL vs model for every N.
test: test-model $(addprefix sim-N,$(NS))
	$(PYTHON) -m model.check_rtl $(NS)

# Simulate one N and write results/rtl_dump_N<n>.txt:  make sim-N4
sim-N%: venv
	@mkdir -p build results
	$(IVERILOG) -g2012 -Wall -Wno-timescale -P tb_approx_mul_exhaustive.N=$* -o build/tb_mul_N$*.vvp \
	    tb/tb_approx_mul_exhaustive.sv $(MUL_SRCS)
	$(VVP) -n build/tb_mul_N$*.vvp

# Simulate and check a single N:  make check-N4
check-N%: sim-N%
	$(PYTHON) -m model.check_rtl $*

# Python model unit tests, and build the cached LUTs in results/.
test-model: venv
	$(PYTHON) -m pytest -q model/tests
	$(PYTHON) -m model.approx_mul

metrics:
	@echo "make metrics: not implemented yet (M1.7)"; false

# Liberty copy without "do not use" cells, for Yosys only (see flow/make_synth_lib.py).
SYNTH_LIB := build/sky130_fd_sc_hd_synth.lib
$(SYNTH_LIB): $(LIB) flow/make_synth_lib.py
	@mkdir -p build
	python3 flow/make_synth_lib.py $(LIB) $@

# Synthesize the reference multiplier (a*b) and print its area.
synth:
	$(MAKE) synth-one TOP=mul_behav N=0 SRCS="rtl/mul_behav.sv"
	@grep -H "Chip area" $(SYNTH_OUT)/mul_behav_N0_stat.txt

# Synthesize one design:  make synth-one TOP=<module> N=<n> SRCS="<files>"
SYNTH_OUT := results/synth
synth-one: $(SYNTH_LIB)
	@mkdir -p $(SYNTH_OUT)
	TOP=$(TOP) N=$(N) SRCS="$(SRCS)" LIB=$(SYNTH_LIB) OUT=$(SYNTH_OUT) \
	    $(YOSYS) -q -l $(SYNTH_OUT)/$(TOP)_N$(N).log -c flow/synth.tcl

power:
	@echo "make power: not implemented yet (M1.10)"; false

sweep:
	@echo "make sweep: not implemented yet (M1.11/M2.5)"; false

baselines:
	@echo "make baselines: not implemented yet (M2.6/M2.7)"; false

eval:
	@echo "make eval: not implemented yet (M2.3/M2.8)"; false

cnn:
	@echo "make cnn: not implemented yet (M2.9)"; false

analysis:
	@echo "make analysis: not implemented yet (M2.10)"; false

figures:
	@echo "make figures: not implemented yet (M2.12)"; false

all: test metrics synth power sweep baselines eval cnn analysis figures

# Remove generated files (keeps .venv/).
clean:
	rm -rf results/*.npy results/rtl_dump_*.txt results/*.vcd results/*.saif \
	       results/synth build
