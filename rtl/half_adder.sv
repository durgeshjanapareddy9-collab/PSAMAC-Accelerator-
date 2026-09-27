// half_adder.sv -- adds two 1-bit inputs.
//
// The result (0..2) needs two bits: "sum" stays in the same column and
// "cout" moves one column to the left. In a Dadda tree a half adder turns
// 2 bits of a column into 1 bit there: the column gets 1 bit shorter.

module half_adder (
    input  logic a,
    input  logic b,
    output logic sum,
    output logic cout
);
    assign sum  = a ^ b;   // 1 when exactly one input is 1
    assign cout = a & b;   // 1 when both inputs are 1
endmodule
