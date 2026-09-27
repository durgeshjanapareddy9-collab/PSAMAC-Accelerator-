# flow/sta.tcl -- static timing analysis of a synthesized mul_wrap netlist.
#
# Run with OpenSTA (normally from flow/ppa.py):
#   NETLIST=... LIB=... OUT=... sta -no_init -exit flow/sta.tcl
#
# Setup (stated plainly, as the report must):
#   * corner: the liberty file given in LIB (tt, 25 C, 1.80 V)
#   * pre-layout: no wire parasitics, ideal clock (no clock tree)
#   * inputs arrive right at the clock edge, outputs are captured by flops
#
# Outputs:
#   $OUT.timing.txt   worst register-to-register path in detail
#   stdout line "MIN_PERIOD_NS <value>" parsed by flow/ppa.py

read_liberty $::env(LIB)
read_verilog $::env(NETLIST)
link_design  mul_wrap

# A 10 ns clock on port clk. The exact value does not matter for the result:
# we ask OpenSTA for the *minimum* period the design could run at.
create_clock -name clk -period 10.0 [get_ports clk]
set_input_delay  0.0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0.0 -clock clk [all_outputs]

# Detailed report of the slowest path (for humans).
report_checks -path_delay max -fields {slew cap input_pins} -digits 3 \
    > $::env(OUT).timing.txt

# Minimum clock period = clk-to-Q of the launch flop + logic delay
#                        + setup time of the capture flop.
set min_period [sta::find_clk_min_period [get_clocks clk] 0]
puts "MIN_PERIOD_NS [format %.4f [expr {$min_period * 1e9}]]"
