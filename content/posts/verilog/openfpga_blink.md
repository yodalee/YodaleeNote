---
title: "Open FPGA 系列 - blink led"
date: 2021-08-23
categories:
- FPGA
- verilog
tags:
- icesugar-pro
- verilog
series:
- FPGA
images:
- /images/verilog/icesugar-pro.jpg
forkme: icesugar-playground
---

故事是這樣子的，[今年的 COSCUP]({{< relref "2021_coscup_online" >}}) 投了一個 System Software 的 session ，
然後該議程軌的主持人自行提供了投稿獎勵，以下 Facebook 原文：

> 為了鼓勵各位同學投稿、以及體驗知識有價的參與感，在跟Jserv老師討論後，我們將提供兩位 **有償** 徵稿名額給這邊的同學。  
> 投稿後有獲得錄取的前兩位同學，將會獲得新台幣 2,500 元的獎勵金，以及可以配製成RISC-V核心、運行Linux的FPGA開發板乙張！

獎勵金的部分我就回絕了，畢竟有薪人士拿這個錢道義上說不過去，留給比我有才的許多學生講者比較好。  
不過 FPGA 我評估之後就收下了，畢竟 FPGA 難買，之前實驗室玩的 [DE2](https://www.terasic.com.tw/cgi-bin/page/archive.pl?Language=Taiwan&CategoryNo=185&No=56)
 都要破萬元（然後它竟然停產了），然後有些 project 只用軟體寫實在沒 fu，一直想弄一塊 FPGA 來玩，於是就接受了 FPGA。
<!--more-->

過幾天到貨之後，發現是 icesugar-pro 的 FPGA 開發板：  
* [官方網頁](https://www.muselab-tech.com/)
* [Github](https://github.com/wuxx/icesugar-pro)

# 規格

下面是實體照片：
![icesugar-pro](/images/verilog/icesugar-pro.jpg)

中間部分的主板包括 Lattice 的 FPGA、SDRAM 跟 FLASH：

* FPGA： ECP5 LFE5U-25F
* SDRAM： ISSI IS42S16160B (32MB)
* Flash： Winbond W25Q256JV (32MB)

icesugar 使用 ARM 的晶片提供 iCELink 來做燒錄，這讓燒錄變得非常簡單，插上電腦之後 它會模擬成一個檔案系統，
就像把檔案複製進隨身碟一樣，把 .bin 檔複製進去就完成燒錄了，比喝水還要輕鬆。

使用的 FPGA 是作為 FPGA 老三的 Lattice，完全支援開放原始碼工具鏈，
也許就是因為第一名 Xilinx 吃肉、第二名 Altera 喝湯、老三 Lattice 只能舔碗療飢，才會選擇加入開放工具鏈，吸引開源社群跟自幹玩家加入作為助力。  
本板使用的 Lattice ECP5 LFE5U-25F FPGA，總共有 24K 個 LUTs ([Look Up Table](https://programmermagazine.github.io/201408/htm/focus1.html))，基本應用絕對夠用了。  
通過 SODIMM 可以連接到擴充板，共有 106 支 I/O pin 可供使用，有八支接腳接到 HDMI 的輸出。我個人是覺得多媒體的部分有點嫌少啦，除非你要用這 106 支 I/O pin 硬幹，不然買專業生產的 DE2 好像比較簡單XD。

# 安裝工具鏈

以下在 Archlinux 上面安裝相關工具鏈，我必須說這部分還滿雜亂的，沒有一份很完整的 tutorial 在講這件事，目前還是開源的戰國時代的感覺，
以至於文件講的、看範例寫的、實際可以動的往往全部不一樣，~~很有在看 MDN 文件的感覺~~。

要玩 FPGA ，也就是從 verilog 一路來到可燒錄的我們會需要[下列幾樣工具](https://www.fpga4fun.com/FPGAsoftware5.html)：
1. Synthesis：一般叫合成，把 verilog 的 RTL 合成為邏輯閘。
2. Place and Route：佈線，依照邏輯閘的數量限制，生成邏輯閘的連線。
3. Bitstream Creation：將邏輯閘的連線，依照對應的 FPGA 型號生成可燒錄的 bitstream 檔。

來到開源工具鏈 icestorm 的[官方網頁](http://www.clifford.at/icestorm/)，搜尋 install 的話會看到在 Archlinux 推薦安裝的工具 AUR：
1. Synthesis: yosys-git，指令 yosys
2. Place and Route: arachne-pnr-git，指令 arachne-pnr
3. Bitstream Creation: icestorm-git，指令 icepack

很可惜的，我最後成功生成 bitstream 的工具如下，除了 yosys 之外其他兩個都被換掉了，
* arachne-pnr 已停止支援，由 [nextpnr](https://github.com/YosysHQ/nextpnr) 取代
* icestorm 應該還可以用，但最後成功的是 [prjtrellis](https://github.com/YosysHQ/prjtrellis)。

安裝開發工具鏈：
```bash
yay -S yosys
yay -S nextpnr-git place and route
yay -S trellis-git
```

裡面最肥的當屬 yosys，整個安裝檔編完有 50 MB，編起來花了我一點點的時間；trellis-git 也不小，安裝的時候我剛好在 hamivideo 上面看斯卡羅，
結果影片就一直 lag，害我以為中華電信的網路又不給力了。

# Blink LED

準備好這些我們就能開始寫點 verilog 了，~~可惡為什麼我一把年紀了還要自找苦吃寫 verilog QQ~~ ，上一次發 verilog 文已經是 2012，
幾乎就是我剛開始在 blogger 上面開始寫 blog 的時候了……。  
就先來弄個 FPGA 的 Hello World：閃爍的 LED 吧。

```verilog
// blink.v
module blink (output reg led, input clk);
  localparam CNT_RST = 25_000_000;
  reg [24:0] counter;
  always @(posedge clk) begin
    if (counter == 25'd0) begin
      led <= led + 1;
      counter <= CNT_RST;
    end
    else begin
      counter <= counter - 1;
    end
  end
endmodule
```

因為 icesugar 的基礎頻率為 25 MHz，counter 每降到 0 就會把將 led 反向，讓 led 以 0.5 Hz 的頻率閃爍。

除了這個 `blink.v` 之外，我們還要準備 `blink.lpf` 告訴佈線軟體要怎麼連接 clk 跟 led，
對照 icesugar-pro 的 [schematic](https://github.com/wuxx/icesugar-pro/blob/master/schematic/iCESugar-Pro-v1.3.pdf)
（或是看 github 的 README.md 也可），準備 lpf 如下：

```txt
LOCATE COMP "clk" SITE "P6";
IOBUF PORT "clk" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk" 25 MHZ;

LOCATE COMP "led" SITE "B11";
IOBUF PORT "led" IO_TYPE=LVCMOS25;
```

整個編譯過程，一般都會寫成 Makefile：
```makefile
$(TARGET).json: $(SRCS)
  yosys -p "synth_ecp5 -json $@" $^

$(TARGET)_out.config: $(TARGET).json $(TARGET).lpf
  nextpnr-ecp5 --25k --package CABGA256 --speed 6 \
  --json $< --textcfg $@ --lpf $(TARGET).lpf

$(TARGET).bin: $(TARGET)_out.config
  ecppack $< $@
```

yosys 先把我們的 .v 轉成 json，會用 json 的原因是 nextpnr 只吃 json input；
nextpnr-ecp5 會吃下我們產生的 json 跟 lpf 檔，生成燒錄的 config；最後再由 ecppack 將 config 打包成 bit stream。  
用純文字介面的 Makefile 來生成 bitstream 好像有點 low，其實無論是 xilinx 還是 altera 的圖形介面應用程式，
也只是把這些 command 幫你封裝好而已。

## 燒錄
如前所述，把生成的 blink.bit 燒進去，就能看到閃爍的 led 了，我們設定的 port 是 B11，連接紅色的 led；
只要修改 lpf 檔就能讓不同的 led 亮起來了。

{{< video src="/video/fpga_blink.mp4" >}}

# 下一步

這一步基本上是先順一下流程，目前已經確定開源工具鏈真的能建出可燒錄、執行的 bit stream，
再來應該會實驗依序測試一下如何連接 SDRAM 跟 hdmi 螢幕（啊不過我家的螢幕接不了 hdmi 線……）。  
最終要做什麼 project 目前還沒決定好，大家如果有想到什麼也可以留言跟我說一聲。
