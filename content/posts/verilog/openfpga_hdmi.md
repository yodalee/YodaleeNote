---
title: "Open FPGA 系列 - HDMI"
date: 2021-09-13
categories:
- FPGA
- verilog
tags:
- icesugar-pro
- verilog
- hdmi
series:
- FPGA
images:
- /images/verilog/hdmi_test_pattern.jpg
forkme: icesugar-playground
---

上回我們實作了 UART 的輸入輸出，這回就來挑戰板子上有附的另一個介面：HDMI，這個實作出來我們就有影像輸出可以用了呢。  
不過因為 HDMI 的難度比起來上升了一個層次，這次我是直接用 icesugar-pro 的[範例程式碼](https://github.com/wuxx/icesugar-pro/tree/master/src/hdmi_test_pattern)改寫，
TMDS 的部分則有參考網路上的 [encoder](https://gist.github.com/alsrgv/3cf171c17fffe25806693c26ebb276a8)。
<!--more-->

# HDMI protocol

High Definition Multimedia Interface，HDMI （高畫質多媒體介面）是應用相當廣泛的視訊介面，板子使用的是 [HDMI pin A 17 支針腳](https://www.electronics-notes.com/articles/audio-video/hdmi/hdmi-pinouts-connections.php)，
不過如果近拍的話，可以看到它只連接了 8 支腳跟接地，分別是：
* 1,3 Data 2+/- 藍色
* 4,6 Data 1+/- 綠色
* 7,9 Data 0+/- 紅色
* 10,12 Data Clock +/-

![hdmi_pin](/images/verilog/hdmi_pin.jpg)

HDMI 的信號走的是差動傳輸，比起 UART 的單端傳輸能做到更高的速率，相關的文章可以看[這篇](https://sipitogether.blog/signal-integrity/differential/singleend-or-differential/)，
因為沒接所以我們沒辦法玩 HDMI 後面針腳提供 I2C，反正那個應該是用來走音訊用的，不玩沒差(欸。  
另外，不知道為什麼，但在它的 schematic 跟圖片找不到 HDMI 的接腳是走哪支腳，只能照抄範例的 lpf 檔：
```txt
LOCATE COMP "hdmi_dp[0]" SITE "G1"; # Blue +
LOCATE COMP "hdmi_dn[0]" SITE "F1"; # Blue -
LOCATE COMP "hdmi_dp[1]" SITE "J1"; # Green +
LOCATE COMP "hdmi_dn[1]" SITE "H2"; # Green -
LOCATE COMP "hdmi_dp[2]" SITE "L1"; # Red +
LOCATE COMP "hdmi_dn[2]" SITE "K2"; # Red -
LOCATE COMP "hdmi_dp[3]" SITE "E2"; # Clock +
LOCATE COMP "hdmi_dn[3]" SITE "D3"; # Clock -

IOBUF PORT "hdmi_dp[0]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dn[0]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dp[1]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dn[1]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dp[2]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dn[2]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dp[3]" IO_TYPE=LVCMOS33 DRIVE=4;
IOBUF PORT "hdmi_dn[3]" IO_TYPE=LVCMOS33 DRIVE=4;
```

# PLL

由於 HDMI 的運作原理是這樣子的，在螢幕上每個像素用的是 24 位元的高彩，也就是 RGB 各佔一個 byte，在傳輸的時候，它會使用 [8b/10b 編碼](https://en.wikipedia.org/wiki/8b/10b_encoding)，
把一個 byte 的資料加上兩個 bit ，透過 [TMDS 最小化傳輸差動信號](https://en.wikipedia.org/wiki/Transition-minimized_differential_signaling) 
填充成 10 個 bits，然後由上述的差動信號傳輸出去。

FPGA 運作在 25MHz，serial port 上行走的資料速度就要 250 MHz，要在 FPGA 上拿到這麼快的 clock，就一定要用上 PLL 不可。  
幸好，icesugar-pro 用的 FPGA `LFE5U-25F-6BG256C` 還真的有提供一個 PLL 可用， 搭配型號與 datasheet 去 google 可以看到 Lattice 提供的 datasheet；
另外可以用 `ECP5 and ECP5-5G sysCLOCK PLL/DLL Design and Usage Guide` 查到另一份專門講解 PLL 的 datasheet，
因為都是 pdf 的連結我這裡就不附上了。

如果有使用 Lattice 的整合開發環境 [Lattice Diamond](https://www.latticesemi.com/latticediamond) ，
它們裡面就會提供圖形化介面的 PLL 設定工具，應該是會直接幫你生出可用的 verilog code，但我們沒 license 就只能手爆了。

手爆步驟如下，首先是查看 PLL datasheet，在第 18 章開始介紹完整的 PLL 架構：
![hdmi_pll](/images/verilog/hdmi_pll.png)

PLL 的運作是這個樣子的，首先你會有個 input clock，然後提供一個 feedback 的時脈，兩個一齊進到中間的 VCO，
VCO 會調整輸出時脈的頻率，直到 input 跟 feedback 的 phase 鎖定為止，至於怎麼實現就是一門專門的學問了，
可能要去修 [Abyss](https://www.ee.ntu.edu.tw/profile1.php?teacher_id=901116) 的鎖相迴路課程。

表 18.1 提供了 verilog module 所有的 input/output 列表，另外有一些是要由參數來設定的，在表 18.6 有參數的列表。  
我們的目標是從 25 MHz 的 input 生成 250 MHz 的 output，選用 primary output CLKOP 生成 250 MHz；
CLKOS 生成 25 MHz 的 clk 作為 feedback clk，其他的 clock 就全部關掉。  
這裡不知道為什麼 PLL 的文件沒寫，反而寫在 `LFE5U-25F-6BG256C` 的文件裡，VCO 推薦的使用範圍是 400-800 MHz ，
因此我們讓 VCO 頻率為 500 MHz，CLKOP 跟 CLKOS 分頻 2 跟 20。

以下是我寫出來的 clock.sv 檔：
```systemverilog
module clock
(
  input clkin_25MHz,
  output clk_25MHz,
  output clk_250MHz,
  output locked
);

(* ICP_CURRENT="9" *) (* LPF_RESISTOR="8" *) (* MFG_ENABLE_FILTEROPAMP="1" *) (* MFG_GMCREF_SEL="2" *)
EHXPLLL
#(
  .CLKOS_FPHASE(0),
  .CLKOP_FPHASE(0),
  .CLKOS_CPHASE(2),
  .CLKOP_CPHASE(20),
  .CLKOS_ENABLE("ENABLED"),
  .CLKOP_ENABLE("ENABLED"),
  .CLKI_DIV(1),
  .CLKOP_DIV(2),
  .CLKOS_DIV(20),
  .CLKFB_DIV(1),
  .FEEDBK_PATH("CLKOS")
)
pll_i
(
  .CLKI(clkin_25MHz),
  .CLKFB(clk_25MHz),
  .CLKOP(clk_250MHz),
  .CLKOS(clk_25MHz),
  .CLKOS2(),
  .CLKOS3(),
  .RST(1'b0),
  .STDBY(1'b0),
  .PHASESEL0(1'b0),
  .PHASESEL1(1'b0),
  .PHASEDIR(1'b0),
  .PHASESTEP(1'b0),
  .PLLWAKESYNC(1'b0),
  .ENCLKOP(1'b0),
  .ENCLKOS(1'b0),
  .ENCLKOS2(),
  .ENCLKOS3(),
  .LOCK(locked),
  .INTLOCK()
);
endmodule
```

最上面那串 ICP_CURRENT 我不知道是幹嘛，查了 [FAQ](https://www.latticesemi.com/en/Support/AnswerDatabase/4/0/4/4041) 
是一些 LPF 參數的設定，會由工具自動產生，我留不留都不影響最終結果。  
可以看到我只留下 CLKOP 跟 CLKOS 的設定，CLKOP 除 2 變 250 MHz，CLKOS 除 20 變 25 MHz 灌回去 CLKFB；
搭配 FPHASE 跟 CPHASE 可以調整輸出信號的相位，不過我們這邊都不設定相位。

# HDMI

```systemverilog
module hdmi(
  input clk_tmds,
  input clk_pixel,
  input rst,
  input [7:0] i_red, i_green, i_blue,
  output logic o_enable,
  output logic o_newline,
  output logic o_newframe,
  output logic o_red,
  output logic o_green,
  output logic o_blue);
```

HDMI 模組的介面如下：
* clk_tmds/clk_pixel 250 MHz 和 25 MHz 的時脈
* i_red/green/blue RGB 各一個 byte 的資料
* o_red/o_green/o_blue 送到串列上的 bit
* o_enable, o_newline, o_newline 告知資料源現在顯示到哪的線，不會真的送到螢幕上。

```systemverilog
parameter WIDTH = 640;
parameter HEIGHT = 480;
parameter VWIDTH = 800;
parameter VHEIGHT = 525;

logic [9:0] CounterX, CounterY;

// update counterX and counterY
always_ff @(posedge clk_pixel or negedge rst) begin
  if (!rst) begin
    CounterX <= 0;
  end
  else begin
    if (CounterX == VWIDTH-1) begin
      CounterY <= (CounterY == VHEIGHT-1) ? 0 : CounterY+1;
    end
  end
end

always_ff @(posedge clk_pixel or negedge rst) begin
  if (!rst) begin
    CounterY <= 0;
  end
  else begin
    if (CounterX == VWIDTH-1) begin
      CounterY <= (CounterY == VHEIGHT-1) ? 0 : CounterY+1;
    end
  end
end
```

透過 clk_pixel 計算 counterX, counterY 我們可以知道現在正在處理哪個像素。

```systemverilog
logic hSync, vSync, DrawArea;

// Signal end of line, end of frame
assign o_newline  = (CounterX == WIDTH-1);
assign o_newframe = (CounterX == WIDTH-1) && (CounterY == HEIGHT-1);
assign DrawArea   = (CounterX < WIDTH) && (CounterY < HEIGHT);
assign o_enable   = rst & DrawArea;
assign hSync = (CounterX >= 656) && (CounterX < 752);
assign vSync = (CounterY >= 490) && (CounterY < 492);
```
這邊就只是一些順著 CounterX, Y 變化的線，hSync 跟 vSync 的時序似乎是 [HDMI 標準有制定](https://projectf.io/posts/video-timings-vga-720p-1080p/)，
才會出現 X=656~752 間和 Y=490~492 間必須進到 hSync 跟 vSync 設定。  
因為未來其他 project 的緣故，我真的很好奇這個 hSync, vSync 的時序是不是能隨意調整？

```systemverilog
logic [9:0] tmds_red, tmds_green, tmds_blue;
logic [9:0] tmds_red_next, tmds_green_next, tmds_blue_next;
TMDS_encoder encode_R(.clk(clk_pixel), .rst(rst), .data(i_red), .control(2'b00),
  .enable(DrawArea), .tmds(tmds_red_next));
TMDS_encoder encode_G(.clk(clk_pixel), .rst(rst), .data(i_green), .control(2'b00),
  .enable(DrawArea), .tmds(tmds_green_next));
TMDS_encoder encode_B(.clk(clk_pixel), .rst(rst), .data(i_blue), .control({vSync,hSync}),
  .enable(DrawArea), .tmds(tmds_blue_next));
```
把 red/green/blue byte 塞進 TMDS_encoder 編碼成 10 bits 的信號 tmds_*_next。

```systemverilog
logic [3:0] tmds_counter=0;
always @(posedge clk_tmds) begin
  if (!rst) begin
    tmds_counter <= 0;
    tmds_red   <= 0;
    tmds_green <= 0;
    tmds_blue  <= 0;
  end else begin
    tmds_counter <= (tmds_counter==4'd9) ? 4'd0 : tmds_counter+4'd1;
    tmds_red   <= (tmds_counter == 4'd9)? tmds_red_next: tmds_red >> 1;
    tmds_green <= (tmds_counter == 4'd9)? tmds_green_next: tmds_green >> 1;
    tmds_blue  <= (tmds_counter == 4'd9)? tmds_blue_next: tmds_blue >> 1;
  end
end

assign o_red   = tmds_red[0];
assign o_green = tmds_green[0];
assign o_blue  = tmds_blue[0];
```

每經過 10 個 tmds clock，我們就把下一輪的 data 更新到 tmds_RGB 裡面；
反之就是原本的 data 右移，o_red/o_green/o_blue 把該資料的 LSB 送出去就可以了。

# TMDS

TMDS 應該是這次最麻煩的部分，模組的宣告：

```systemverilog
module TMDS_encoder(
  input clk, // 250 MHz
  input rst,
  input [7:0] data,  // video data (red, green or blue)
  input [1:0] control,  // control data
  input enable,  // enable == 1 ? data : control
  output logic [9:0] tmds
);

typedef enum logic [9:0] {
  CTRL_00 = 10'b1101010100,
  CTRL_01 = 10'b0010101011,
  CTRL_10 = 10'b0101010100,
  CTRL_11 = 10'b1010101011
} control_t;
```
我們要把 8 bits data 編碼成 10 bits tmds，control 如 hdmi 模組的呼叫，在藍色的通道上會傳送控制的信號 h_sync, v_sync，
這兩個信號會對應到上面寫的四個 TMDS control signal。

再來可以把 TMDS 流程可以分成下面兩步：

## 1. XOR/XNOR
第一步會先把 data 進行 rolling xor 或 rolling [xnor](https://en.wikipedia.org/wiki/XNOR_gate)，要選哪個則是根據哪一個出來的結果的 0-1 transition 的數量比較少。
實作上會直接去算 8 bits 中 1 的數量，比 4 多就會是 xnor，原因如下：

|input|operator|output|
|:-|:-|:-|
|00|XOR |   00|
|00|XNOR|  01|
|01|XOR |    01|
|01|XNOR|  00|
|10|XOR |   11|
|10|XNOR| 10|
|11|XOR |   10|
|11|XNOR| 11|

可以看到，只要後一個 bit 是 0，XOR 的結果就不會有 transition，反之則是 XNOR，因此 1 愈多 XNOR 的 transition 就愈少；
如果序列中 0 跟 1 剛好對半，那麼就要看第一個 bit，如果是 1 表示剩下的 7 個 bits 1 會比較少，就要選 XOR。

```systemverilog
logic [3:0] ones_d;
bit use_xor;
logic [7:0] qm;

function automatic logic [3:0] count_ones(input logic [7:0] bits);
  count_ones = 0;
  int i;
  for (i = 0; i < 8; i = i+1) begin
    count_ones += $bits(count_ones)'(bits[i]);
  end
endfunction

function automatic logic [7:0] rolling_xor(input logic [7:0] bits);
  rolling_xor[0] = bits[0];
  int i;
  for (i = 1; i < 8; i = i+1) begin
    rolling_xor[i] = rolling_xor[i-1] ^ bits[i];
  end
endfunction

function automatic logic [7:0] rolling_xnor(input logic [7:0] bits);
  rolling_xnor[0] = bits[0];
  int i;
  for (i = 1; i < 8; i = i+1) begin
    rolling_xnor[i] = rolling_xnor[i-1] ^~ bits[i];
  end
endfunction

// stage 1: rolling_xor or rolling_xnor the data
assign ones_d = count_ones(data);
assign use_xor = ones_d < 4 || (ones_d == 4 && data[0] == 1'b1);
assign qm = (use_xor)? rolling_xor(data) : rolling_xnor(data);
```
這裡用 systemverilog 的 function，還有用 for loop 展開程式碼；
雖然說 yosys 的 for loop 就像 C89 一樣，沒辦法把宣告寫在 for loop 裡面，~~死廢物耶~~。

> JJL：不廢一點你覺得什麼 S 公司 C 公司靠什麼賺錢

## 2. Invert
第二步 TMDS 會看 XOR/XNOR 出來的結果，其中 0 跟 1 數量的差距，必要時反轉全部的 bits 讓 0 1 的數量平衡；

```systemverilog
// stage 2: invert bits to compensate diff in 1s or 0s
assign ones_qm = count_ones(qm);
assign diff_qm = (signed'(5'(ones_qm) << 1)) - 5'd8;

always_comb begin
  if (disparity == 0 && ones_qm == 4) begin
    // balanced, set invert_qm to compensate xor bit
    invert_qm = ~use_xor;
  end
  else begin
    invert_qm = (disparity > 0 && ones_qm > 4) || (disparity < 0 && ones_qm < 4);
  end
end
```

使用的是 XOR 1 / XNOR 0 保存在第 9 個 bit，invert 1 / non-invert 0 保存在第 10 個 bit。  
最後我們把信號放進 output tmds 中並更新 disparity，如果不在畫面裡就送 control signal。
```systemverilog
always_ff @(posedge clk) begin
  if (enable) begin
    tmds <= {invert_qm, use_xor, invert_qm ? ~qm : qm};
    disparity <= disparity +
      (invert_qm ? -($bits(disparity)'(diff_qm)) : $bits(disparity)'(diff_qm)) +
      (invert_qm ? $bits(disparity)'('sd1) : -($bits(disparity)'('sd1)));
  end
  else begin
    disparity <= 0;
    case (control)
      2'b00: tmds <= CTRL_00;
      2'b01: tmds <= CTRL_01;
      2'b10: tmds <= CTRL_10;
      2'b11: tmds <= CTRL_11;
    endcase
  end
end
```

# Test Pattern

跟範例 code 一樣，使用 [vgatestsrc](https://github.com/ZipCPU/vgasim/blob/master/rtl/vgatestsrc.v) 來產生測試的畫面，
就能看到顯示的 [Test Pattern](https://en.wikipedia.org/wiki/Test_card) 了。

![hdmi_test_pattern](/images/verilog/hdmi_test_pattern.jpg)

看著這畫面實在有點古早的感覺。

# 結語

無論是上一篇的 UART 還是這篇的 HDMI，要理解一些通訊介面的運作原理，最好的方式就是用 FPGA 去實作它；
正如要理解作業系統的原理，最好的方法就是自幹一個作業系統，~~雖然我現在幹到一半還沒幹完~~。  

有了 UART 跟 HDMI，現在我們已經有了文字介面的輸入輸出，以及畫面的輸出，下一步應該會來測試一下上面附的 SDRAM，看要如何存取，
這部分我記得強者我同學施博神有自幹過 DRAM controller，是不是該跟他要個 code(欸
