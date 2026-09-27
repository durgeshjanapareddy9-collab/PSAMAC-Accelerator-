# flow/power.tcl -- power of a synthesized mul_wrap netlist from simulation activity.
#
# Run with OpenSTA (normally from flow/power.py):
#   NETLIST=... LIB=... VCD=... SCOPE=tb_power/dut CLK_NS=10 OUT=... \
#       sta -no_init -exit flow/power.tcl
#
# Method:
#   1. The gate-level netlist was simulated (tb/tb_power.sv) and every net's
#      switching was recorded in a VCD file.
#   2. read_vcd attaches that activity (toggle rate and time-at-1) to every
#      cell pin (the VCD includes cell pins, see tb/tb_power.sv).
#   3. report_power adds up, per cell: internal power (inside the cell),
#      switching power (charging the capacitance it drives) and leakage.
#   Corner: the liberty file in LIB (tt, 25 C, 1.80 V). Pre-layout: no wire
#   capacitance, ideal clock. Zero-delay simulation: glitches are not counted.

read_liberty $::env(LIB)
read_verilog $::env(NETLIST)
link_design  mul_wrap

create_clock -name clk -period $::env(CLK_NS) [get_ports clk]
set_input_delay  0.0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0.0 -clock clk [all_outputs]

read_vcd -scope $::env(SCOPE) $::env(VCD)

# How many cell pins got their activity from the simulation ("vcd") and how
# many did not ("unannotated"). flow/power.py requires unannotated = 0.
report_activity_annotation

report_power -digits 6 > $::env(OUT).power.txt
report_power -digits 6
