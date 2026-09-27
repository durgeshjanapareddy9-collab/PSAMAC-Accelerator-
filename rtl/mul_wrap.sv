// mul_wrap.sv -- registered wrapper used for timing and power measurements.
//
// Timing tools measure the delay between flip-flops (register-to-register).
// A bare multiplier has no flip-flops, so we put one bank on the inputs and
// one on the output:
//
//     a_in, b_in --> [a_q, b_q flops] --> multiplier --> [p_q flops] --> p_out
//                     ^ clk                                ^ clk
//
// The critical path is then clk -> a_q/b_q -> multiplier -> p_q, and the
// minimum clock period tells us how fast the multiplier is.
//
// Which multiplier? Set the macro MUL when compiling (default approx_mul):
//     yosys:    read_verilog -sv -DMUL=mul_behav ...
//     iverilog: -DMUL=mul_behav
// Every multiplier in the project has the same ports (a, b, p) and a
// parameter N, so this one wrapper serves them all, baselines included.

`ifndef MUL
`define MUL approx_mul
`endif

module mul_wrap #(
    parameter int N = 0            // truncation depth, passed to the multiplier
) (
    input  logic        clk,
    input  logic [7:0]  a_in,
    input  logic [7:0]  b_in,
    output logic [15:0] p_out
);
    logic [7:0]  a_q, b_q;         // registered inputs
    logic [15:0] p_d;              // multiplier output (combinational)

    // Input registers.
    always_ff @(posedge clk) begin
        a_q <= a_in;
        b_q <= b_in;
    end

    // The multiplier under test.
    `MUL #(.N(N)) u_mul (
        .a (a_q),
        .b (b_q),
        .p (p_d)
    );

    // Output register.
    always_ff @(posedge clk) begin
        p_out <= p_d;
    end
endmodule
