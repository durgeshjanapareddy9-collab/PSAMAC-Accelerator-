// full_adder.sv -- adds three 1-bit inputs.
//
// The result (0..3) needs two bits: "sum" is the low bit (same column) and
// "cout" (carry out) is the high bit, which moves one column to the left.
// In a Dadda tree a full adder turns 3 bits of a column into 1 bit there,
// plus 1 bit in the next column: the column gets 2 bits shorter.

module full_adder (
    input  logic a,
    input  logic b,
    input  logic cin,
    output logic sum,
    output logic cout
);
    assign sum  = a ^ b ^ cin;                 // 1 when an odd number of inputs are 1
    assign cout = (a & b) | (cin & (a ^ b));   // 1 when at least two inputs are 1
endmodule
