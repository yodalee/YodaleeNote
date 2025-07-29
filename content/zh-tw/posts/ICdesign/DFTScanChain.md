---
title: "數位電路設計系列 - ScanChain 與他們的產地"
date: 2025-06-06
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
images:
- /images/ICdesign/scanchain.png
---


在現代晶片設計中，隨著晶片功能越來越複雜、邏輯閘數量動輒上億，如何確保晶片在製造後能夠正確運作，成為一項極具挑戰性的課題。
經過 design compiler、INNOVUS 等 EDA 軟體的努力，設計的時序本身沒有錯誤，製程的變異也可能導致晶片出現缺陷。  
因此，我們需要一套有效的方法，在晶片出廠前對內部進行全面測試，這就是 DFT（Design for Testability） 出場的時機了。
<!--more-->

從 EDA 軟體的描述來看，支援的 DFT 至少有下面幾種：
* Boundary scan
* Scan Chain
* Core Wrapping
* Test points
* Compression

每種都各有其 know-how，我們這篇就單純討論 Scan Chain 就好，其目的是將原本外界看不到也摸不到的的暫存器，
串接成一條可由外部控制與觀察的資料路徑，讓我們能夠「掃描」內部狀態，進行邏輯測試。  

# Scan Chain

[![scanchain](/images/ICdesign/scanchain.png)](/files/dftdraw.sv)

Scan Chain 畫成電路圖表示如上，使用的工具是 [digitaljs online](http://digitaljs.tilk.eu/)，
晶片的輸出入會多出三支腳位：
1. Scan Input
2. Scan Enable
3. Scan Output

所有的 register 會被連成長長一列，在 register 的前面會多出一個 mux，用以選擇：
1. 正常資料輸入（D input）：這是原本邏輯功能要用的輸入
2. Scan 資料輸入（Scan in）：用於測試時，從外部送進來的測試資料

scan chain 由 Scan Input 經過 **每一個** register 到 Scan Output，這裡單純示意所以只有兩個 register，
實際上的 scan chain 可能有幾萬個 register。  
而在輸入來源的選擇上，我們使用控制訊號 Scan Enable（或簡稱 SE），來決定這個暫存器現在要動作在哪種模式：
* SE = 0：功能模式（Function Mode）Register 用的是正常的邏輯輸入
* SE = 1：掃描模式（Scan Mode）Register 用的是 Scan input，像 shift register 一樣運作

在功能模式下，我們在兩個 register 中間夾了一個 Not gate，我們怎麼知道這個 Not gate 有做好呢？  
有了這樣的結構，晶片製作完成後，測試就能依下列步驟進行測試：
1. 開啟 Scan Enable 啟動掃描模式
1. 自 Scan Input 餵入資料，輸入一定量的 clock 使資料移動到 Scan Chain 上對應的位置
1. 關閉 Scan Enable 啟動功能模式
1. 輸入一次正緣 clock，邏輯電路的輸出（Not gate 的輸出） 存入輸出的 Register
1. 開啟 Scan Enable 啟動掃描模式
1. 輸入一定量的 clock 使資料自 Scan Chain 中移出，檢查 Scan Output 收到的結果是否符合預期

本來可能深藏在電路中的 combinational circuit 就變得可見了，也就能在晶片出廠後打入各種測資，確認是不是每個電晶體都有好好工作。

了解 Scan Chain 之後，剩下的問題有兩個？
1. 怎麼插入 Scan Chain
1. 如何生成 Scan Chain 用的測資

這篇就讓我們來回答第一個問題，事實上我也只是邊寫邊學，寫作過程中的參考資料如下：
* [Design Compiler for DFT](https://hackmd.io/@derek8955/SkoY2WNfh)
* [set_dft_signal -view的参数existing_dft和spec有什么区别](https://blog.csdn.net/SH_UANG/article/details/54767176)

如果對文中內容有疑或，想找官方對於指令的說明文件，不要找 Design Compiler Manual，要找 **DFT Compiler Manual**。

# 測試的模組

為了測試 Design Compiler 如何加入 ScanChain，我實作了一個大約 100 行的極簡模組
（對啦 verilog 100 行已經算極簡了啦，我保證它合成 10 秒內就可以跑完）。  
裡面會敲一次 register，做一個加法再敲一次 register；這個實作不需要第一層的 register，但為了測試 DFT 的功效，就請忽略我亂寫吧。

```systemverilog
typedef logic [15:0] Data;
module DftTester (
  input     	clk,
  input     	rst_n,

  // Input IO
  input     	i_valid,
  output logic  i_ready,
  input Data    i_a,
  input Data	i_b,

  // Output IO
  output logic  o_valid,
  input     	o_ready,
  output Data   o_add
);

logic en1;
logic reg_valid, reg_ready;
Data a, b;

Pipeline i_pipe1 (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(i_valid),
  .i_ready(i_ready),
  .o_en(en1),
  .o_valid(reg_valid),
  .o_ready(reg_ready)
);

always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    a <= 'b0;
    b <= 'b0;
  end else if (en1) begin
   a <= i_a;
   b <= i_b;
  end
end

logic en2;

Pipeline i_pipe2 (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(reg_valid),
  .i_ready(reg_ready),
  .o_en(en2),
  .o_valid(o_valid),
  .o_ready(o_ready)
);

always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    o_add <= 'b0;
  end else if (en2) begin
    o_add <= a + b;
  end
end

endmodule

module Pipeline (
  input clk,
  input rst_n,
  input i_valid,
  output logic i_ready,
  output logic o_en,
  output logic o_valid,
  input o_ready
);

logic o_valid_w;

assign o_valid_w = i_valid || (o_valid && !o_ready);
assign i_ready = !o_valid || o_ready;
assign o_en = i_ready && i_valid;

always_ff @( posedge clk or negedge rst_n ) begin
  if (!rst_n) begin o_valid <= 1'b0; end
  else begin o_valid <= o_valid_w; end
end

endmodule
```

# Design Compiler 設定
第一部分是利用 Synopsys 的 DFT Compiler 在 verilog 中插入 Scan Chain，DFT Compiler 和 Design Compiler 
已高度整合，因此可以在合成的時候一併插入 Scan Chain。

以下參考大大們並實際測試過的 tcl 內容，DFT 有兩種插入方式：
1. unmapped flow，從 RTL 開始
2. mapped flow，從合成後的 netlist 開始

我不確定哪一種比較常見，前者可以寫一個 tcl 就好，一口氣做到結尾；
後者可以把 DFT 的 tcl 和合成使用的 tcl 分開，合成後先把內容輸出到 top_opt.ddc
，換一個 DFT 的 tcl 讀入、插入 Scan Chain 之後再寫出最終的 verilog 檔案。

```tcl
create_port -dir in  scan_in
create_port -dir out scan_out
create_port -dir in  scan_en

set_dft_signal -view exist -type ScanClock -timing {90 100} -port clk
set_dft_signal -view exist -type Reset -active_state 0 -port rst_n
create_test_protocol
dft_drc

# compile -scan -map_effort high -area_effort high -boundary_optimization

# insert DFT scan cells
set_scan_configuration -chain_count 1 -style multiplexed_flip_flop
set_dft_signal -view spec -port scan_in -type ScanDataIn
set_dft_signal -view spec -port scan_out -type ScanDataOut
set_dft_signal -view spec -port scan_en -type ScanEnable -active_state 1
set_scan_path chain1 -scan_data_in scan_in -scan_data_out scan_out

preview_dft -show all
insert_dft
write_test_protocol -out chip_scan.spf
```

## 準備 Test Protocol

我們分段來看，首先用 create_port 在輸出的 .syn.v 加上 scan_in, scan_en, scan_out 這些 port
，畢竟一般人不會想要在本來的 verilog code 裡面插入 DFT 用的 code。  
設定完 scan clock 和 scan reset 之後，呼叫 create_test_protocol 生成 test_protocol 確認 DFT compiler 理解你的設定，
dft_drc 的輸出如下，後續確定 dft_drc 沒報錯即可：

```txt
  ...reading user specified clock signals...
Information: Identified system/test clock port clk (90.0,100.0). (TEST-265)
  ...reading user specified asynchronous signals...
Information: Identified active low asynchronous control port rst_n. (TEST-266)
```
## Compile Scan
如果你選用的是 unmapped flow，這個時候就要呼叫 compile 命令並加上 -scan 參數，將你的設計從 RTL 轉成 netlist
，後續的 preview_dft, insert_dft 都只能作用在 gate-level 的 netlist 上面。  
加上 -scan 參數的 compile，會把本來的 D flip-flop (下稱 DFF) 換成可測試的 Scan D flip-flop (下稱 SDFF)。

本來的 DFF 可能是四支腳：輸入 D, Clock, Reset 和輸出 Q；SDFF 變成六支腳：新增 scan 用的 ScanIn, ScanEn；還沒插 DFT 之前 ScanIn, ScanEn 都會接上 1'b0。  
沒錯，雖然你看到的示意圖都是在 DFF 前面加上一個 Mux，實際上因為 Scan Chain 太廣泛使用了，比起一個 Mux 跟一個 DFF，製程廠直接弄一個 SDFF 面積比較小（當然還是比 DFF 大，我參考的資料是大 20% 左右）。

這點跟 multibit flip flop ( [MBFF](https://blog.csdn.net/i_chip_backend/article/details/135711500) )
滿像的，因為電路設計上太多（與其說太多不如說幾乎都是）出現一團 register 吃同一個條件更新它們的內容，所以乾脆弄個
Multi-bit 2, 4, 6, 8 的 standard cell 讓 design compiler 去選。  
又如把 2 選 1 的信號輸入 Flip-Flop 裡，太常用了所以 standard cell 就提供一個 Mux D flip-flop，這樣面積可以比較小。

## set_scan_configuration

準備妥當之後，使用 set_scan_configuration ，這個指令的參數還不少，如果你設計不大的話，跟這裡一樣設定就好。  
這裡可以設定的包括像 scan chain 的長度、要幾條，還有像是 [scan chain 的種類](https://blog.csdn.net/NBA_kobe_24/article/details/119952348)
，在大型設計用到多個 clock 時，-clock_mixing 能設定 scan 信號要如何在 register 間進行 Clock Domain Crossing。

但就跟上篇的 Design Compiler 一樣，當你碰到的設計有這麼複雜的時候，高機率你已經不需要自己調整 DFT 的設定了。

## 插入 DFT

先用 preview_dft 看看 DFT compiler 想要插入什麼內容，沒問題就用 insert_dft 插入 scan chain 吧。  

preview_dft 的結果如下：

```
Scan chain 'chain1' (scan_in --> scan_out) contains 50 cells:

  a_reg[0]                  	(clk, 90.0, rising)
  a_reg[1]
  a_reg[2]
  a_reg[3]
  a_reg[4]
  a_reg[5]
  a_reg[6]
  a_reg[7]
  a_reg[8]
  a_reg[9]
  a_reg[10]
  a_reg[11]
  a_reg[12]
  a_reg[13]
  a_reg[14]
  a_reg[15]
  b_reg[0]
  b_reg[1]
  b_reg[2]
  b_reg[3]
  b_reg[4]
  b_reg[5]
  b_reg[6]
  b_reg[7]
  b_reg[8]
  b_reg[9]
  b_reg[10]
  b_reg[11]
  b_reg[12]
  b_reg[13]
  b_reg[14]
  b_reg[15]
  i_pipe1/o_valid_reg
  i_pipe2/o_valid_reg
  o_add_reg[0]
  o_add_reg[1]
  o_add_reg[2]
  o_add_reg[3]
  o_add_reg[4]
  o_add_reg[5]
  o_add_reg[6]
  o_add_reg[7]
  o_add_reg[8]
  o_add_reg[9]
  o_add_reg[10]
  o_add_reg[11]
  o_add_reg[12]
  o_add_reg[13]
  o_add_reg[14]
  o_add_reg[15]

  Scan signals:
	test_scan_in: scan_in (no hookup pin)
	test_scan_out: scan_out (no hookup pin)
```

這裡也可以衍生出另一個話題，看一下我們的設定：
```tcl
set_dft_signal -view spec -port scan_en -type ScanEnable -active_state 1
```
設定 scan_en 是 ScanEnable signal，信號是 active high，如果把 1 換成 0 就會變 active low。
當然你*可以*這樣設定，但會出一個大問題，因為預鑄的 SDFF 的 SI port 是 active high 的，設定 active low 的 scan_en port
會導致 design compiler 在你的 D flip-flop 前插入一堆反向器，徒增一堆面積，所以請不要這麼做。  

## 輸出結果

新增 DFT 之後，會需要新增更多輸出的檔案：
```tcl
# this file is necessary for P&R with Encounter
set filename [format "%s%s" $toplevel ".sdc"]
write_sdc $filename

# this file is necessary for TetraMax
set filename [format "%s%s" $toplevel ".spf"]
write_test_protocol -out $filename

# write scan definition
set filename [format "%s%s"  $toplevel ".scandef"]
write_scan_def -output $filename
```

### scan.sdc
由於 scan 測試時不需要和晶片執行使用同等條件，在[MMMC]({{< relref "APRmaterial#MMMC-檔">}}) 的範例也可以看到我列出了
func 和 scan 兩種不同的 .sdc，會有重大不同的也就只有 Clock Timing，畢竟只是測試頻率不用太高。  
目前我因為全部都寫在同一個 .tcl 裡，還沒成功寫出過 scan 用的 sdc，用上述的 mapped flow 應該比較容易分隔兩種類型的 .sdc 檔。  

### .spf
SPF 的意思是：Standard Test Interface Language (STIL) Procedure File (SPF)。  
這個文件描述晶片的介面，像是輸入有哪些？輸出有哪些？有幾條 chain 存在？如何把這顆晶片進入 Test Mode 等等的資訊。  
可以由 Design Compiler 生成，看文件似乎也可以由 TetraMax 生成，這部分我還沒碰過，等我碰過了再跟大家分享。

### .scandef
沒人規定副檔名要取這個，可自取，這是描述 scan chain 的文件，讓 APR 軟體知道這裡有一條 scan chain 的存在，以及它的設定是什麼？  
APR 在 Place&Route 的時候可以參考 scan chain 的設定去擺放 cell 或是依照 P&R 的結果去改動 scan chain 的 register
順序，在兩條 scan chain 中交換 register 等，詳情可參考
[scandef文件和scan reorder介绍](https://blog.csdn.net/weixin_44495082/article/details/136819364)，等我遇到了再來介紹。

# 測試結果
以下列出上述測試模組的合成結果，我邊寫文章邊操作，測試了四種不同的情境：
1. 完全沒設 DFT，單純合成設計 (baseline)
2. 設定 DFT，使用 compile -scan 合成後插入 DFT
3. 不使用 compile -scan，compile 後一口氣完成 DFT 設定與插入
4. 同 3，但插入 DFT 後再呼叫一次 compile -inc

面積比較：

| Setting | Area |
|:-|:-|
| No DFT | 1444 |
| compile -scan; insert_dft | 1729 |
| compile; insert_dft | 1759 |
| compile; insert_dft; compile -inc | 1658 |

可以看到，最差的結果是合成時完全不考慮 DFT 存在事後插入，DFT compiler 在插入時只做有限量的最佳化，面積最大。  
如果在合成時先加入 -scan，則可以在合成時考慮 DFF 換成 SDFF 可執行的最佳化，稍微減小面積。  
執行 insert_dft 時，design compiler 都會執行一定程度的最佳化，由於 scan chain 等於是把 register 用一堆線連結在一起，
很自然的會出現一般 Min Delay Cost，可修可不修，反正不修 APR 階段還是會幫你修掉。

面積最佳的當然是插入 DFT 完之後，再執行一次 incremental compile，代價就是額外一次的 compile 時間；
但如果製程想對 power leakage 進行最佳化，兩次的 incremental compile 可以一起做，不會多出額外的 compile，在實務上也許是可接受的。

# 結語

本文試著用個人有限的知識介紹了 DFT ScanChain 的相關概念，DFT 是個相當龐大的主題，光 Scan Chain 本文介紹的就只是一小部分。  
像是 scan clock 其實可以給多個；在多 clock 的設計，也要考慮如何跨越 clock domain，插入 CDC 後如何執行 STA，
有許多實務才能學會的知識。  
接下來還有 TetraMax 產生向量、INNOVUS APR 如何處理 DFT 等等，留待未來有機會再和大家分享。

我想我的結語跟 [APR前準備]({{< relref "APRmaterial">}})篇是一樣的，
如果你在其位，文中大部分的設定都應該會有舊有的檔案可以參考，就從舊檔案好好學；
如果你不在其位，那高機率這不是你的職責，你連碰都不用碰（甚至是不準，不然晶片投片量不到你出錢嗎？）  

其實大部分的**科技公司跟創新是沾不上邊的**，都是穩健的計劃，確保每個季度、每個年度都有穩定的改良與進步，
從這點來看晶片設計其實也是挺窩曩的，大家都是在某種晶圓廠訂下的框架裡東改西改罷了。  
聽起來也許有些厭世，但其實不會，經年累月下來，這樣的模式讓我們手機效能翻倍、續航力翻倍，還有高效能~~又浪費電~~的AI晶片讓我們看著不同人喊：露比醬？嗨~

