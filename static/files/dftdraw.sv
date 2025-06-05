module Draw (
  input clk,
  input rst_n,
  input i_data,
  output o_data,
  input scan_in,
  input scan_en,
  output scan_out
);

logic data0, data1;

always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin data0 <= 'b0; end
  else begin data0 <= scan_en ? scan_in : i_data; end
end

always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin data1 <= 'b0; end
  else begin data1 <= scan_en ? data0 : !data0; end
end

assign scan_out = data1;
assign o_data = data1;

endmodule
