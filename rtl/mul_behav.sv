// mul_behav.sv -- reference 8x8 unsigned multiplier written as plain "a * b".
//
// This is the "let the tool decide" baseline: we do not describe HOW to
// multiply, we just ask for the product and Yosys/ABC build whatever circuit
// they think is best. Comparing it with our hand-built Dadda tree (approx_mul
// with N = 0) tells us whether our exact tree is a sensible starting point.
//
// The parameter N is accepted but ignored, so every multiplier in the project
// has the same interface and the flow scripts can treat them all alike.

module mul_behav #(
    parameter int N = 0            // unused; kept for a uniform interface
) (
    input  logic [7:0]  a,         // first operand, unsigned 0..255
    input  logic [7:0]  b,         // second operand, unsigned 0..255
    output logic [15:0] p          // exact product, 0..65025
);
    assign p = a * b;              // 8 bits x 8 bits needs 16 bits of result
endmodule
