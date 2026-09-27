# flow/synth.tcl -- synthesize one design to sky130_fd_sc_hd standard cells.
#
# Run through Yosys in Tcl mode (normally via `make synth`):
#   TOP=mul_behav N=0 SRCS="rtl/mul_behav.sv" LIB=/path/to.lib OUT=results/synth \
#       yosys -c flow/synth.tcl
#
# Inputs (environment variables):
#   TOP   name of the top module
#   N     truncation depth passed to the top module's parameter N
#   SRCS  space-separated list of SystemVerilog files
#   LIB   liberty file (set in flow/config.mk)
#   OUT   output directory
#
# Outputs, with TAG = <TOP>_N<N>:
#   $OUT/<TAG>_stat.txt     cell list, cell count and area (um^2)
#   $OUT/<TAG>.v            gate-level netlist (used later by OpenSTA)
#
# (We use a .tcl script instead of a plain .ys script because .ys scripts
#  cannot take variables such as N or the liberty path.)

yosys -import

set top  $::env(TOP)
set n    $::env(N)
set lib  $::env(LIB)
set out  $::env(OUT)
set tag  "${top}_N${n}"
file mkdir $out

# 1. Read the RTL and pick the top module, setting its parameter N.
foreach f $::env(SRCS) { read_verilog -sv $f }
hierarchy -check -top $top -chparam N $n

# 2. Generic synthesis: turn the RTL into simple logic gates, flattened into
#    one module. Hardware whose inputs are constant 0 (the dropped partial
#    products) is removed here by constant propagation.
synth -flatten -top $top

# 3. Technology mapping: replace generic flip-flops and gates with real
#    sky130 cells from the liberty file.
dfflibmap -liberty $lib
abc -liberty $lib

# 4. Clean-up so the netlist is easy for OpenSTA to read:
#    constant 0/1 outputs are driven by a sky130 "tie" cell (conb_1),
#    and multi-bit wires are split into single bits.
setundef -zero
hilomap -singleton -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
splitnets -ports
opt_clean -purge

# 5. Reports and netlist.
tee -o $out/${tag}_stat.txt stat -liberty $lib
write_verilog -noattr -noexpr -nohex -nodec $out/${tag}.v
