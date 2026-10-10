# flow/mul_wrap.sdc -- timing constraints for mul_wrap (SDC = Synopsys Design
# Constraints, the standard format every timing tool reads).
#
# Read by OpenSTA in flow/sta.tcl (timing) and flow/power.tcl (power).
#
#   * one clock, "clk", on port clk; period CLK_NS (default 10 ns = 100 MHz)
#   * inputs arrive right at the clock edge (input delay 0)
#   * outputs only need to be valid at the next clock edge (output delay 0)
#   * ideal clock: no clock-tree delay or skew (pre-layout)

set clk_ns [expr {[info exists ::env(CLK_NS)] ? $::env(CLK_NS) : 10.0}]

create_clock -name clk -period $clk_ns [get_ports clk]
set_input_delay  0.0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0.0 -clock clk [all_outputs]
