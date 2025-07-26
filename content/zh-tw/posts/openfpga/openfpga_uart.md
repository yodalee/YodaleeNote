---
title: "Open FPGA 系列 - UART"
date: 2021-09-05
categories:
- FPGA
- verilog
tags:
- icesugar-pro
- verilog
- uart
series:
- FPGA
images:
- /images/openfpga/uart_debug.jpg
forkme: icesugar-playground
---

上一章我們打通了 FPGA 的開源工具鏈，接下來我們就能測試一下 icesugar-pro 有的介面，
首先實作 FPGA 還是需要有輸入輸出，否則也只是弄出一個無法互動的程式，而最簡單的輸出入介面，就當屬 UART 了。  
icesugar-pro 的 github 上，也附上了一個 [UART 的範例](https://github.com/wuxx/icesugar-pro/tree/master/src/uart_tx)，
會不斷對你的電腦輸出 "0" 到 "9"（然後這段 code 還有 bug XD），這篇我們就來寫一個有 tx, rx 的 UART 模組吧。
<!--more-->

# UART
UART 全名 Universal Asynchronous Receiver/Transmitter 或譯*通用非同步收發傳輸器*，
關於它的原理可以參考[這篇文章](https://www.nandland.com/articles/what-is-a-uart-rs232-serial.html)，
同一個網站還有提供 [VHDL/verilog 的 UART 實作](https://www.nandland.com/vhdl/modules/module-uart-serial-port-rs232.html)。

中文的詳細解說也可以看[Albert 的筆記](http://albert-oma.blogspot.com/2012/03/uart.html)。

UART 的相當簡單，靠一根線就能完成傳輸，一般的介面會有 Tx 跟 Rx 兩條線一來一往，未有通訊時通訊線保持在高電位
（這也是古老設備的習慣，有電表示正常，線斷了就會呈現 Open），整個通訊分為四個部分：
1. Idle：維持高電位
2. ST start：從 1->0 表示通訊開始
3. Data 5-9 bits：我對 5-9 bits 這個敘述感到好奇，查了[這篇](https://electronics.stackexchange.com/questions/150573/why-there-are-data-bit-lower-than-8-data-bit-of-uart)
發現 UART 制定時間早到 1970 年代，那時候的電傳打字機還沒統一，有 5 bits 的 [Baudot code](https://en.wikipedia.org/wiki/Baudot_code)，
7 bits 的 [ASCII](https://montcs.bloomu.edu/Information/Encodings/ascii-7.html)（是的 ASCII 其實只要 7 bits 就夠了），
以及最後一統江湖的 byte，成為當今主流 UART 的 8 bits。
4. Parity：可有可無的 Parity bit，可以設定為 odd parity/even parity。
5. Stop bit：1, 1.5 或 2 個 stop bit，直接拉回高電位即可。

這次的實作當然就選最簡單的，沒有 parity bit，1 個 stop bit，8 bit Data 的實作。

# 從 verilog 到 system verilog
這裡的故事是這樣子的，在寫的過程中我遇到了一些問題，於是去請教了強者我同學 phoning 大大，然後他就說別再用 verilog 了，那是上世紀的東西，
如果沒辦法接受下世代的 Scala/chisel，至少也要升級到 system verilog。  
於是小弟就來升級一下腦袋，看了一些文件文章之後，對 verilog 程式有如下幾個改動：

## logic
verilog 裡面變數分為 wire 跟 reg ，原意是 reg 代表真的有一個實體的暫存器儲存這個值；wire 則是邏輯閘連線的結果，但這兩者在 verilog 裡面很容易混淆，system verilog 用 logic 統一取代；強者我同學 johnjohnlin 大大就開玩笑，從 verilog 轉換到 system verilog 就是：
```vim
:%s/reg/logic/g
:%s/wire/logic/g
```

## enum
因為（至少個人）寫 verilog 很常會需要寫到狀態機，等等 UART 的模組實作就會看到了，那寫狀態機就會需要先把代表狀態的 bits 拉出來，
在 verilog 裡我可能會用 localparam 來定義，但那會讓 code 變得亂糟糟，而且各狀態的型別無法統一。  
system verilog 提供 enum 統一狀態的資料型態，並且可以用 enum 來宣告變數。

## bit/byte/shortint/int/longint
比起 verilog 只能用 `reg/wire [WIDTH:0]` 宣告一定資料寬度的接線，system verilog 提供這些型別，
直接表示 1/8/16/32/64 寬的資料，寫起來簡潔很多。

## always_ff always_comb always_latch
verilog 只有一個 always 關鍵字，就有可能因為寫法，合成出 combinational circuit、flip flop、latch 等電路，
就算經驗老道的電路設計師也可能會踩到，合成出不會預期的結果。  
system verilog 分割出 always_ff/always_comb/always_latch 三個不同的關鍵字來對應三種合成的電路，
讓合成能進行更多的檢查，確保設計和結果一致。

# 實作

## reset 信號

一般來說 FPGA 都會需要一個 reset 的信號，至於我們的 icesugar…沒有。  
它唯一有的按鈕是 re-program，會從 flash 再讀一次 bitstream 燒錄進 FPGA 裡面。  

幸好它有很多 GPIO 可以用，最後我的接線如圖所示，把 3.3V, GND 跟 GPIO F14 接出來，用手讓 F14 接到 GND 就能完成 reset 了，
之前在 [nixie tube clock]({{< relref "posts/nixie/introduction.md" >}}) 時買的電子零件又再次派上用場了。

![fpga_reset](/images/openfpga/uart_reset.jpg)

## LPF 檔

我們 UART 模組的接腳如下：
```txt
LOCATE COMP "clk" SITE "P6";
IOBUF PORT "clk" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk" 25 MHZ;

LOCATE COMP "rst" SITE "F14";
IOBUF PORT "rst" IO_TYPE=LVCMOS33;

LOCATE COMP "uart_tx" SITE "B9";
IOBUF PORT "uart_tx" IO_TYPE=LVCMOS33;

LOCATE COMP "uart_rx" SITE "A9";
IOBUF PORT "uart_rx" IO_TYPE=LVCMOS33;
```

* F14 是 GPIO 的一個 port，可以對照 github 裡面的 [接線圖](https://github.com/wuxx/icesugar-pro/blob/master/doc/iCESugar-pro-pinmap.png) 找到是對應哪個 port。
* B9 是 FPGA 的 UART Tx，在 [schematic](https://github.com/wuxx/icesugar-pro/blob/master/schematic/) 上會看到這根線連到 iCElink 的 UART Rx，iCElink 有另一套 UART 透過 USB 接到電腦上。
* 同理 A9 連接到 iCElink UART Tx。

## module UART Tx

我們先從 UART Tx 模組開始，介面設計：

```systemverilog
module uart_tx (
  /* input */
  input clk_baud,
  input rst,
  input [7:0] tx_byte,
  input start_send,

  /* output */
  output logic tx,
  output logic done
);

parameter CLK_PER_BAUD = 1;
localparam CLK_CNT_LIMIT = CLK_PER_BAUD-1;
localparam TX_LENGTH = 10; // start 1'b0, 1 byte, end 1'b1

typedef enum logic {
  STATE_IDLE  = 0,
  STATE_TXING = 1
} State_t;
State_t state = STATE_IDLE, state_next;
logic [9:0] tx_buf;
logic [3:0] tx_idx, tx_idx_next;
int  clk_cnt, clk_cnt_next;
```

介面的設計跟 verilog 沒差多少，input/output 的資料寬還度是要自己設定，沒辦法使用 byte來代表 byte 輸入；
start_send 跟 done 是要接受開始發送的命令跟通知傳送完成；tx 連接到 UART tx 傳輸線。  

[parameter module](https://www.chipverify.com/verilog/verilog-parameters) 是這次新學會的招式，
因為 FPGA 運作頻率遠比 baud rate 9.6 kHz 高很多，由外部生一個 9.6 kHz 的時脈給 UART module 用顯然不合理；
這裡 UART module 會吃全速的 clk，外面用 parameter 告訴 UART module 這個時脈是多少。  
如同上面所提的，我們使用 enum 來定義 state_t，令我不甚滿意的是，yosys 的合成器顯然不會做靜態檢查，我寫 `STATE_TEST = 2` 它也一聲不坑，這明明填不進去，好歹出個警告給我呀。

再來就是寫[狀態機](https://iamard.blogspot.com/2014/03/verilog-how-to-write-finite-state.html)，
用非常非常早之前我寫過的[三大塊的架構]({{<relref "verilog1.md" >}})，寫起來我覺得有點冗但就結構清楚好讀。

將下一個狀態敲入 register 的 flip flop，tx_buf 只有在 IDLE 搭配 start_send 的瞬間會敲入：

```systemverilog
/* update state logic */
always_ff @(posedge clk or negedge rst) begin
  if (!rst) begin
    state   <= STATE_IDLE;
    tx_buf  <= 0;
    tx_cnt  <= 0;
    clk_cnt <= 0;
  end
  else begin
    if (state == STATE_IDLE && start_send) begin
      tx_buf <= {1'b1, tx_byte, 1'b0};
    end
    state   <= state_next;
    tx_cnt  <= tx_cnt_next;
    clk_cnt <= clk_cnt_next;
  end
end
```

邏輯電路的部分，使用 systemverilog 的 always_comb 來產生下個狀態；
注意到我們只有兩個狀態 IDLE 跟 TXING，這是聽從強者我同學 JJL 的建議，開頭的 1'b0 跟結尾的 1'b1 都塞進要傳輸的 tx_buf 裡面。  
tx_idx 記錄現在要送第幾個位元；clk_cnt 計算 clk 以產生符合 9600 kHz 的時脈。
```systemverilog
/* next logic for clk_cnt */
always_comb begin
  clk_cnt_next = (state == STATE_IDLE || clk_cnt == CLK_CNT_LIMIT) ? 0 : clk_cnt+1;
end

/* next logic for state */
always_comb begin
  case (state)
    STATE_IDLE: begin
      state_next = (start_send == 1'b1) ? STATE_TXING : state;
    end
    STATE_TXING: begin
      if (clk_cnt == CLK_CNT_LIMIT && tx_idx == TX_LENGTH-1) begin
        state_next = STATE_IDLE;
      end
      else begin
        state_next = state; end
      end
  endcase
end
```

output 邏輯的部分就沒什麼特別的了。
```systemverilog
/* output logic */
assign done = tx_idx == TX_LENGTH - 1;
assign tx = (state == STATE_IDLE) ? 1'b1 : tx_buf[tx_idx];
```

## module UART Rx
rx 模組其實跟 tx 沒差很多：

```systemverilog
module uart_rx (
  /* input */
  input clk,
  input rst,
  input rx,

  /* output */
  output logic [7:0] rx_byte,
  output logic done
);

parameter CLK_PER_BAUD = 1;
localparam CLK_CNT_LIMIT = CLK_PER_BAUD-1;
localparam SAMPLE_CLK_CNT = CLK_CNT_LIMIT / 2;
localparam RX_LENGTH = 10; // start 1'b0, 1 byte, end 1'b1

typedef enum logic {
  STATE_IDLE  = 0,
  STATE_RXING = 1
} State_t;
State_t state = STATE_IDLE, state_next;
logic [9:0] rx_buf;
logic [3:0] rx_idx, rx_idx_next;
int  clk_cnt, clk_cnt_next;

/* output logic */
assign done = rx_idx == RX_LENGTH - 1;
assign rx_byte = rx_buf[8:1];
```

多一個 SAMPLE_CLK_CNT 的用意是找出 9600 Hz 週期的中點，在那個時間點取 rx 線上的值；
狀態機一樣用兩個狀態，進 STATE_RXING 就會依序把開頭結尾的 1'b0, 1'b1 跟資料都寫入 rx_buf，輸出的 rx_byte 取 rx_buf 中段部分出來即可。

```systemverilog
/* next logic for clk_cnt */
always_comb begin
  clk_cnt_next = (state == STATE_IDLE || clk_cnt == CLK_CNT_LIMIT) ? 0 : clk_cnt+1;
end

/* next logic for state */
always_comb begin
  case (state)
    STATE_IDLE: begin
      state_next = (rx == 1'b0) ? STATE_RXING : state;
    end
    STATE_RXING: begin
      if (clk_cnt == CLK_CNT_LIMIT && rx_idx == RX_LENGTH-1) begin state_next = STATE_IDLE; end
      else begin state_next = state; end
    end
  endcase
end

/* next logic for rx_idx */
always_comb begin
  if (state == STATE_RXING && rx_idx < RX_LENGTH) begin
    if (clk_cnt == CLK_CNT_LIMIT) begin
      rx_idx_next = rx_idx+1;
    end
    else begin
      rx_idx_next = rx_idx;
    end
  end
  else begin
    rx_idx_next = 0;
  end
end

/* update state logic */
always_ff @(posedge clk or negedge rst) begin
  if (!rst) begin
    state   <= STATE_IDLE;
    rx_buf  <= 0;
    rx_idx  <= 0;
    clk_cnt <= 0;
  end
  else begin
    if (clk_cnt == SAMPLE_CLK_CNT) begin
      rx_buf[rx_idx] <= rx;
    end
    state   <= state_next;
    rx_idx  <= rx_idx_next;
    clk_cnt <= clk_cnt_next;
  end
end
```

這段就沒有什麼特別的了，唯一的不同在 flip flop 敲 register 的地方，會在 SAMPLE_CLK_CNT 的時候，把 rx 的 bit 敲進 rx_buf 對應的位置。

## module Top

```systemverilog
module top (
  input clk,
  input rst,
  input  rx,
  output tx,
);

parameter CLK_FREQ = 25_000_000;
parameter BAUDRATE = 9600;
parameter CLK_PER_BAUD = CLK_FREQ / BAUDRATE;

byte rx_byte;
logic uart_rxed;
```

top module 對外連結 UART 的 tx, rx 線，用 parameter 算出 CLK_PER_BAUD，如果要修改 baud rate，改寫這裡即可

```systemverilog
uart_tx # (.CLK_PER_BAUD(CLK_PER_BAUD))
mod_uart_tx (
  /* input */
  .clk(clk),
  .rst(rst),
  .tx_byte(rx_byte),
  .start_send(uart_rxed),

  /* output */
  .tx(tx),
  .done(uart_txed)
);

uart_rx # (.CLK_PER_BAUD(CLK_PER_BAUD))
mod_uart_rx (
  /* input */
  .clk(clk),
  .rst(rst),
  .rx(rx),

  /* output */
  .rx_byte(rx_byte),
  .done(uart_rxed)
);
```

這段就是宣告 uart_tx, uart_rx 兩個模組，用 `# (.parameter())` 的方式，在宣告模組名稱前把參數灌進去；
我把 rx 的 done 直接灌回 tx 的 start_send；rx_byte 送到 tx_byte。  
簡單來說我在 UART 送什麼進去，它就會反射同樣的字元給我。

## verilator

這小節未來可以自己獨立寫一篇，或者我懶得寫大家可以直接去看強者我同學 JJL 寫的三篇介紹文：
* [高品質＆開源的 SystemVerilog(Verilog) 模擬器介紹＆教學（一）](https://ys-hayashi.me/2020/12/verilator/)
* [高品質＆開源的 SystemVerilog(Verilog) 模擬器介紹＆教學（二）](https://ys-hayashi.me/2020/12/verilator-2/)
* [高品質＆開源的 SystemVerilog(Verilog) 模擬器介紹＆教學（三）](https://ys-hayashi.me/2021/01/verilator-3/)

因為在寫 UART 的過程中，有一度 code 寫不出來，有借助一下 verilator 的力量幫我輸出波形檔（真是古早味的 debug 方法…）；
試用的時候發現 verilator 的 sanity check 比 yosys 的還要完整（很多），幫我找出許多小小的錯誤。

## 測試

icesugar 會透過 iCElink，一次把可用的介面都打開，UART 介面會開在 /dev/ttyACM0，可以用 `screen /dev/ttyACM0 -s 9600` 來與我們的 UART 模組溝通，如果你對付的是其他設定的 UART protocol，可以[透過 stty 設定 tty 裝置的參數](https://stackoverflow.com/questions/41266001/screen-dev-ttyusb0-with-different-options-such-as-databit-parity-etc)。

在 debug UART 的時候我比較推薦用 `xxd /dev/ttyACM0`，因為 screen 幫你把位元組變成字元，UART 壞掉收到非可印的 ASCII 字元時，
用 screen 就看不出它寫了什麼東西。

讓我們把裝置插上去，燒錄、reset 之後，在一個終端連接 UART 介面， 我們就能看到我們實作的 UART 模組運作的樣子了。  
注意到 screen 本來打字是不會出現對應字元的，但因為我的 FPGA 把我打的字反射回來，螢幕上才會出現這些字。

![uart_screen](/images/openfpga/uart_screen.png)

另外附上 debug rx 中的照片，LED 顯示我剛剛按了 0x30 '0' 這個字。

![uart_debug](/images/openfpga/uart_debug.jpg)

# 結語

這章我們從 verilog 升級到 system verilog，整體來說算是語法的小小升級，但寫起來的架構不會差太多。
花了一點時間，我們成功用 system verilog 實作了 UART 的 tx/rx 模組，在未來的 project 也許有機會可以用得上。  
剛好昨天去光華商場買了 HDMI 對 VGA 的轉接頭，今天 UART 模組就完成了，看來下一步就是實驗 HDMI 模組了。  

本文的完成，要感謝強者我同學 JJL 跟 phoning 大大的強力支援，畢竟小弟已經快十年沒碰 verilog，
多虧兩位在業界工作的大大幫我惡補 system verilog 的知識，才能順利完成這個 project。  
