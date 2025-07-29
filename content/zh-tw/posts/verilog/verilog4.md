---
title: "數位電路之後，verilog系列文4：寫 testbench"
date: 2012-07-08
categories:
- verilog
tags:
- verilog
series:
- verilog introduction
---

testbench是verilog另一個很好用的功能，一般來說，如果設計的電路是要完成某個特定的演算法，比如我們在實驗中要實作256bits的montgomery algorithm，把電路透過quartus合成、燒進FPGA執行，透過Logic analyser分析行為實在太曠日費時（那時寫的不好，合成一次就要30分鐘= =）。  
這時候testbench出現了，testbench提供了一個方式，讓我們能利用軟體模擬電路的行為，看看電路的反應，每次模擬只需要幾秒鐘，就可以得到電路的行為。  
<!--more-->

這篇文章就是要來談testbench的譔寫，會分成以前幾個部分：  

## 軟體安裝
為了要進行 verilog code 的模擬，我們需要安裝 verilog 的模擬軟體，有不少公司都有相關的軟體，如學校工作站安裝 Cadence 公司的 NCverilog ，但這是需要付費的，也要連結到工作站才能使用。
這裡我推薦使用另一套免費提供的開源模擬軟體：iverilog，可以裝在Linux或Windows上使用，如果是在 Ubuntu 或 Debian 系列可以使用apt來安裝：  
```shell
apt-get install iverilog
```
個人使用 Archlinux，也可以用 pacman 安裝。  
```shell
pacman -S iverilog
```

另外還要安裝gtkwave，才能看到電路輸出訊號的波型檔。  
```shell
apt-get install gtkwave
pacman –S gtkwave
```

## testbench 譔寫
其實，testbench也就是一個verilog module，用來產生輸入電路的信號，如果把電路燒在FPGA裡面，輸入的信號可能是來自晶體振盪器的時脈信號，按鈕輸入、信號產生器的輸入……，但寫testbench時，就要自己寫信號的輸入，以及時脈信號的模擬。  
這個testbench的module會將待測的電路整個包進去，然後把信號輸給它。  
注意在譔寫時，給input 的連接需要用reg，輸出則使用wire來連接。  

下面是我在測試 Montgomery algorithm module 的 testbench，目標測試的 module 的輸入是 3 個 256bits 的數A,B,N，n\_start 降下就會開始運算；輸出則是告知計算完成的n\_ready與輸出結果的S：  

```verilog
`timescale 1ns/100ps
`define CYCLE 10

module Montgomery_tb ();

//**************************** wire & reg**********************//
reg clk;
reg [255:0] A;
reg [255:0] B;
reg [255:0] N;
reg n_rst;
reg n_start;

wire [255:0] S;
wire n_ready;
//**************************** module **********************//

Montgomery lalala(.clk(clk),.A(A),.B(B),.N(N),.S(S),.n_rst(n_rst),.n_start(n_start),.n_ready(n_ready));

//**************************** clock gen **********************//
always begin #(`CYCLE/2) clk = ~clk; end

//**************************** initial and wavegen **********************//
initial begin
 $dumpfile("montgomery.vcd");
 $dumpvars;
end

//**************************** testdata **********************//
initial begin
 clk = 1'b0;
 A = 256'd0;
 B = 256'd0;
 N = 256'd0;
 n_rst = 1'b0;
 n_start = 1'b1;
 #1 n_rst = 1'b1;
 A = 256'h4;
 B = 256'h8;
 N = 256'd13;
 #100 n_start = 1'b0;
 #10 n_start = 1'b1;
 #100000 $finish;
end

endmodule
```
第一行的
```verilog
`timescale 1ns/10ps
```
告訴iverilog等模擬軟體，以前者(1ns)為單位，以後者(10ps)的時間，查看一次電路的行為。   
首先要先連接測試信號，在Module的地方將待測的電路連起來，再次提醒輸入要接reg，這是我們可以指定其值的地方，輸出接wire，只能觀看。  
以下這幾行也是很重要的，用來產生給該module的時脈信號：  
```verilog
`define CYCLE 10 reg clk; always begin #(`CYCLE/2) clk <= ~clk; end initial begin clk = 1'b0; end
```
在testbench裡面，#(數字)代表經過多少delay，initial則是在電路開始時賦值，否則會如下圖一樣，輸出預設為X的信號：  
![non-initial](/images/verilog/non-initial.png)

這樣就能產生一個週期為CYCLE* (1ns)長的信號。  

```verilog
initial begin
 $dumpfile("montgomery.vcd");
 $dumpvars;
end
```
讓 iverilog 把記錄的波型寫入 montgomery.vcd 中，dumpvars則可以指定要記錄哪些信號的輸出，一般，我都不寫直接記下全部的信號。  
以上都算是前置作業，最後，就可以對輸入的信號進行給值：  
```verilog
#1 n_rst = 1'b1;
A = 256'h4;
B = 256'h8;
N = 256'd13;
#100 n_start = 1'b0;
#10 n_start = 1'b1;
#100000 $finish;
```
A給4, B給8，N給13，嗯…非常白爛的測資，哎呀舉例啦  
在 100ns 時把 n\_start 降下來，10ns 後升回去，100000ns 讓它慢慢算。  

## 看模擬結果

寫好testbench後，就可以用iverilog編譯，記得要把testbench跟所有相關的v檔都包進去。  
```shell
iverilog *.v -o out
```
這樣 iverilog 會~~產生syntax error的訊息~~一個執行檔，再執行這個執行檔。  
如果有寫dumpfile的話，就會產生相對應的波型檔囉，這一切都是在轉瞬間完成。  

用 gtkwave 打開該波型檔，如下圖所示，這時候可以從左邊把想要看的信號加到右邊去，階層下的 module 都可以打開，看裡面的信號波型。  
像現在我把A,B,N拉出來，看到他們的確變成4,8,13這三個白爛的測資，在信號上點右鍵可以改變表示的方式，我現在開的是16進位，所以13是d。  
![gtkwave](/images/verilog/gtkwave.png)

這樣是不是比直接燒電路快多了呢？  
祝大家testbench愉快！  

## 常見問題
### 1. 為什麼執行檔一執行下去就停不下來了？  
如果testbench是你從頭到尾寫完的話，有可能是忘了加$finish，個人因為都改用模板去改，這個問題很少出現。  
另一個可能就是你的combinational circuit中出現了，條件中修改了條件；這時候在該時間點上，會讓模擬軟體陷到模擬的迴圈中，也就停不下來了。  
### 2. 其實我也不知道有什麼常見問題…….  

## 相關資源
1. [iverilog官網](http://iverilog.icarus.com)