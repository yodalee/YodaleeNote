---
title: "數位電路設計系列 - Design Constraint 是什麼"
date: 2024-08-17
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
images:
- /images/ICdesign/ChipAll.png
---

在寫完 verilog 之後會進到一個有點複雜不是很好懂的主題，也就是要討論電路的合成 synthesis 在幹嘛。  
如果用軟體來比喻的話，合成做的事情就像軟體的 Compiler，軟體寫高階語言，透過 compiler 轉換成 Assembly 與機械碼。  
硬體同樣是寫高階語言如 VHDL/Verilog（呃是的，他們算高階語言），透過 synthesis tool 轉換成 gate-level design。
除非你是研究 standard library 的，不然應該沒有多少人自己寫過加法器與乘法器吧？  

<!--more-->

因為 synthesis tool 可以直接幫你把 verilog 裡面寫的 `+` `*` 換成內建的加法器與乘法器。
也因此 Synopsys 叫它 Design Compiler；Cadence 倒是直接叫 Genus Synthesis。  

要說好這個主題，首先我們要先知道電路的基本架構，
最近我看到介紹這個主題最好的是 Clash 作者寫的 [Retrocomputing with Clash](https://gergo.erdi.hu/retroclash/)，
第一章對這個內容有詳細的解釋。

# 電路的基本架構

來到這裡的人我應該可以假設都知道數位電路的運算就是由邏輯閘所組成了，在電路上我們除了邏輯閘，
還會加上具有儲存功能元件如 latch (鎖存器) flip-flop (正反器) 和控制用的 clock (時脈)。

時脈基本上可以想成一個頻率固定不斷上下的正弦波，配合電路最常使用的正緣觸發的 D Flip Flop，
在時脈從 0 切換到 1 的瞬間，把這瞬間它 input 的資料記錄下來並呈現在輸出。  
D Flip Flop 只能用來儲存一個 bit 的資訊，但這簡單，把一排 D Flip flop 並起來就可以一次儲存一堆資料了，一般會以 Register 來代稱。

邏輯閘加上正反器與時脈，才是現在數位電路的全部。

例如之前有上過的 [Nand2Tetris](https://yodalee.me/categories/nand2tetris/)這門課，
嚴格來說它其實是 Nand + Register to Tetris，它在 Week 3: Sequential logic 的時候直接當成一個己知的 block 來使用，
這也無可厚非，即便 [Register 也是用 Nand 堆出來](https://www.electronicshub.org/sr-flip-flop-design-with-nor-and-nand-logic-gates/)，
箇中的原理跟細節卻多上不少，作為讓人從大方向掌握電腦技衝的課程跳過非常合理。

## Setup time / Hold time

遇到 Register 時要提到的就是 setup time 跟 hold time 了。  
在 Clock 的正緣瞬間，Register 會更新內部的值，電路會要求在正緣的前後，
在 Register 輸入的資料必須維持住一段時間，如下圖我們要把 `1` 存進 Register 裡：

![SetupHold](/images/ICdesign/SetupHold.png)

事前準備好的時間是 Setup Time；事後要維持的時間是 Hold Time，在 Setup/Hold Time 之外要怎麼變都沒差，
但在正緣周圍就是要保持住，不然 Register 會吃到什麼無法保證。
一般來說 Setup Time 的要求會比 Hold time 來得長一些，在規格書上都找得到，
以德儀離散晶片的 [CDx4HCT74](https://www.ti.com/lit/ds/symlink/cd74hct74.pdf?ts=1721415610747)
系列來說，Setup Time 是 15 ns，Hold Time 是 3 ns。

數位電路大體上的架構可以畫成下面這張圖：

![Reg2Reg](/images/ICdesign/Reg2Reg.png)

上一級 Register 收到資料呈現在輸出，經過一連串的 combinational circuit 邏輯閘，來到下一級 Register 的輸入。  
理想的邏輯閘是不花時間的，但現實電路就是會有那麼一咪咪的運算時間，電路合成要確保的，
就是那團 combinational circuit 計算的東西不會太複雜，在一個 clock 的週期內，能把東西算好，又符合 setup time、hold time 的要求。

在 CDx4HCT74 這種離散元件，15 ns 這種等級的時間幾乎可以忽略不級，但在晶片中若 clock 來到 100 MHz，運算時間就只剩下 10 ns。  
當然隨著製程進步與頻率提升，Register 的 setup/hold time 也會愈來愈小，這也是為什麼我們現在能用到 GHz 等級的晶片。

# SDC 的設定

讓我們進一步，把晶片基本架構擴展到你實作的區域之外，實線方塊是我們實作的區域，外面是其他人做的或是晶片的外面：

![ChipAll](/images/ICdesign/ChipAll.png)

所有合成相關的設定都畫在這張圖上了，既然虛線的部分是合成工具看不到的，
那要怎麼計算從 Input 到第一個 Register 的 Delay？  
解法也很直接：設計者要設定好 Input/Output 長什麼樣子，不然合不出來，這些設定就稱之為 Design Constraint，中文一般叫它設計約束，或者設計限制。

以下我們介紹幾個比較常見，幾乎所有設計都非設不可的設定，其他的就是有需要再查詢怎麼設就好；每個設定都會指明往哪個方向設定，你的電路會愈難合成。

常見的 SDC 設定大致可以分類如下：

## 與 input 相關

### set_input_delay
set_input_delay 指的是，從 input 的 register，經過外面的 combinational circuit 到達電路的 input port，
會用掉多少時間，單位為 ns，值愈大表示外面用愈多，電路愈難合成。  
設定外部 delay 的時候，當然大家都會跟你說依照你電路的實際情況下去設，但實際上大概都是：
**設定為時脈週期的 50%，再加個 10% 的保險，於是就設定為 60%**，例如 100 MHz 的時脈，週期 10 ns 那 input/output delay 就設定為 6ns。  
如此一來我的電路用 40%，前後級如果用同樣設定用掉 40%，就保證可以在一個週期內跑完了。

另外 input/output delay 分為兩種，一種算 setup time 用的 max delay，另一種是 hold time 用的 min delay，min delay 設 0 就可以了。  
如果有設值，例如 1，那麼合成器會這樣看：  
1. 外面的 hold time delay 會有 1  
1. Input 直接接進 register 的 port，這個 1 已經滿足 hold time (通常只有 0.x ns) 了  
1. 好耶 hold time 滿足了不用插 buffer  

所以 min delay 不要亂設，記住這句話：

> Setup time 出了問題，量測的時候頻率降一下就解了；Hold time 出了問題，那就是沒救了降頻也沒用

### set_input_transition/set_drive/set_driving_cell

transition 的意思是，一條線上的信號，變化的時間有多快，單位為 ns。  
設定 0 是最理想，表示信號一瞬間就能從 0 拉到 1，這愈大愈難合成。

### set_drive/set_driving_cell
這關係到的是 input 這級的推動能力，推動電路的負載模型一般可以簡化為一個串聯的電阻與一個並聯的電容，
知道這兩個值就能算出這條線的 delay，即一般所稱的 Wire RC Delay。  
set_drive 這個名字其實有點誤導，它設定的是上述 RC 中的 R 值，值愈小表示此路徑的 delay 愈小，
驅動能力愈強，設為 0 則驅動能力為無限，設愈大愈難合成。

如果設計的是 cell 層級，前後都知道的情況下，可以用 set_driving_cell，直接指定是哪個 cell 在驅動這個 port，
DC 可以從對應的 library 取得元件模型的 transition 和 drive 值，一定是最精準的值。

如果實作的是整個 chip 的時候，port 外就是實際的驅動電路了，這時候就會改用 set_drive 和 set_input_transition 命令來設定，
相較於 set_driving_cell 會 set_drive/set_input_transition 使用的是固定值，在不同條件下會不如 set_driving_cell 精準，我試過有量測到的晶片設定是：

```tcl
set_drive 0.1            [all_inputs]
set_input_transition 0.5 [all_inputs]
```

## 與 output 相關

### set_output_delay

set_output_delay 和 input delay 是一樣的，設愈大表示從你的 output port 出去外面會用愈多時間，電路愈難合成。  
套用同樣的概念，通常 output delay 設定成 60% 的 cycle time 即可。

### set_load
set_load 指 output port 之後的電容有多大，預設的單位是 pF，較大的 C 會導致較大的延遲，設愈大電路愈難合成。  

和 set_driving_cell 一樣，如果知道電路後的 cell，可以使用：
```tcl
set_load [ load_of "<Library>/<Cell>/<port>" ] [ get_port "<port_name>" ]
```
設定 load 的 cell，同樣是引用 library 的模型，算出來一定是最精確的。

倘若不知道的，以下是大略的參考資料：

* 合成一個 cell 時，往外接到其他的邏輯閘，大約是 0.002 pF，可以參考 library 中的設定。
* 合成 top 電路時，往外接到晶片的 output pad，大約是 0.05 pF，也可以參考 pad library 的設定
* 連著 output pad 一起合成，往外接到電路板或量測儀器，大約是 5-10 pF，可以去量測儀器的廠商查詢 spec，例如我去查了 Arduino 用的 ATmega328P 的輸入阻抗，會查到 [14 pF](https://electronics.stackexchange.com/questions/67171/input-impedance-of-arduino-uno-analog-pins)。

但也有一些儀器，怎麼樣都找不到對應的 spec。
一般我學到的是，大概就設 20 pF，想保險可以設到 40 pF，這樣子時序有過就可以了。

## 與 clock 相關

clock 大概是所有設計中最煩人的部分了，但別慌其實也沒這麼難，下面如果看不懂沒關係，APR 應該會再提到。

### create_clock

這當然就是用來生一個 clock 用的，照著設就對了，有幾個 clock 就打幾個，週期是多少 ns 就設多少。

```tcl
create_clock -name clk -period 10 [get_ports clk]
set_ideal_network                 [get_ports clk]
# set_dont_touch_network          [get_ports clk]
set_fix_hold                      [get_ports clk]
```

一般來說，會建議對 clock port 設定 set_ideal_network，讓這條 clock 路徑變成 transition 跟 delay 都是 0，
因為 clock 路徑在 layout 的時候，會交由 APR 軟體生成 clock tree synthesis (CTS)，
所以這條路徑的 transition 跟 delay 會在那時候再決定。  
如果在你的 clock 上有經過一些 combinational circuit，ideal_network 的屬性可能會消失，
這時候可以選用更強力的 set_dont_touch_network，就可以防止 design compiler 動你的 clock network。  
set_fix_hold 則是選擇性的，因為 hold time 的修正一樣可以延遲到 APR 時再做，
考慮了 wire delay 可能就己經滿足了 hold time 要求，連 buffer 都不用加，而且就我所知 APR 通常在執行 CTS 前，
第一步就是把 clock path 上所有 buffer 等等都刪光，這時候加這條可能會拖慢 Design Compiler 的合成時間。

有了 clock 之後，如上所述 clock 都會設為 ideal_network，那實際有的不理想效應要怎麼辦？  
因此要加設下面三個屬性，讓 design compiler 可以做分析。

### set_clock_latency

set_clock_latency 是指，從 clock 的來源，經過 CTS 上一連串的 buffer 之後，會經過多少的時間，合成時沒 CTS 自然不知道實際值。  
一般看製程，如果是 90 nm 左右的 source latency 大約是 2-3 左右。

### set_clock_uncertainty

set_clock_uncertainty 對應的則是 CTS skew。  
APR 階段在 CTS 會盡可能把 clock 平均分散到每一個 register，問題是再怎麼平均還是會有偏差，
這個偏差值就會影響到 data path timing 的計算，必須在計算時從 timing 盈餘中扣掉。  
設愈大晶片愈難合成，但也不能設太小，如果實際 CTS 的 skew 沒這麼小就有可能會讓晶片 fail。  
通常會設定在0.1~0.3之間，看晶片的尺寸，大的設 0.3 小的設 0.1，實際的值在 APR 中合成完 CTS 再觀察實際值，比你設定的值小即可。

### set_clock_transition

這是指 clock 從 10%-90% 的時間，值越大 clock 上升速度越慢，越難合成；這我沒有經驗值，一般設個 0.1。  
同樣的 APR 會幫我們處理這段，在 CTS 上面選好 buffer。

## 與 DRV 相關

這裡的設定是關乎晶片的 design rule violation，與 library 模型有關，不是指晶圓廠製造上的 design rule，
那種是違反了晶圓廠直接做不出來，會打你槍的。
這邊的違反是如電容太大、fanout 太多這種，其實違反還是做得出來，只是你的晶片效能會下降，例如電容太大導致信號速度不夠快，使頻率上不去達不到規格要求。

### set_max_capacitance

如上所述每條線都有對應的電容，library 中會有一張時序表，將電容值對映 cell 的 delay 和 transition，
合成工具透過此表去查找值以計算 timing，如果電容值超過了這個表，合成工具就只能用外插法去估計，會比較不準。  
如果沒設定 max capacitance，那工具也會自己去 library 裡面找最大值來用。

### set_max_transition

set_max_transition 一樣可以去 library 中查找關鍵字 max_transition，可以設一個比最大值還小的值；值設得愈小，對 transition 要求愈高，愈難合成。  
另外 transition 的要求設太小，則合成工具可能會選用推動力較強的 buffer 來驅動電路，代價就是功耗會更高。

### set_max_fanout/set_ideal_network

最後是 max_fanout，指一個元件的輸出，接到非常多的輸入，這顆 cell 的負擔就會很重。
一般來說 high fanout 的線就那幾種：
* clock：設定 ideal_network，在 CTS 中會解決。
* reset_n, scan_enable：設定 ideal_network，一樣在 APR placement 中解決
* 接 0, 1 的線路：不理它，APR 中會插入 TieHi, TieLo cell 解決

比較需要特殊處理的，像是：
1. clock gating cell 的輸出，合成工具如果沒辦法識別 clock gating 的 output 是 clock 的一部分，
則需要設定 ideal_network。
2. 真的有大量 fanout 的 net，set_max_fanout 設下去就會解決，一般建議 20-30 左右，我成功的 chip 是設 20，讓合成工具去插入 buffer 即可。

所以就我自己公版的 script 來說，會這樣子設定：
```tcl
set_max_capacitance 0.1
set_max_transition 0.1
set_max_fanout 25
```

## 隨堂考

以下是我親身遇過，因為設計上的一些狀況而出現的，在這裡列出來讓大家~~笑一下~~測驗看看你了解多少，舉例使用 100 MHz clock，period 為 10ns。

### 案例一
我在電路中插入了 debug signal，透過 Input 的 Debug Select 選擇內部要看哪根信號，將對應的信號送到 Debug Output ，如下圖所示：

![In2out](/images/ICdesign/In2Out.png)

設定同上面所說的 60% 原則：
```tcl
set_input_delay 6 [all_inputs]
set_output_delay 6 [all_outputs]
```

請問這樣的設定會有什麼問題？

### 案例二

我們在電路中常會有位移電路，例如 serializer 跟 deserializer 中會用到，如下最這種 deserializer 的 RTL 行為：

```systemverilog
always @(posedge clk) begin
  temp_data <= {temp_data[1:0], in};
end
assign out = temp_data[2:0];
```

實際電路大概會接成這個樣子：

![HoldTime](/images/ICdesign/HoldTime.png)

請問這樣的電路會有什麼樣的 Timing Issue？

## 隨堂考解答

案例一
一定會有 timing violation。  
因為輸入的外面會吃 60%，所以從輸入到第一個 register 只能用 40% 的時間；輸出也是。
但是這個電路裡面沒有 register，所以輸入到輸出可用的時間被壓到 -20%，絕對無法解到沒問題。  

案例二
因為從 register 到 register 只有一小段線，clock 來的時候，第一個 register 的輸出更新後，
一瞬間就會來到第二個 register 的輸入，第二個 register 的輸入維持不夠久，導致 hold time violation。  
在合成工具會在這些線上都插入 buffer 解決這個問題。

# 後記

雖然一開始就覺得這篇好像不會寫，但最後還是寫了。

個人在攻克 Design Compiler 的過程其實查了不少資料，例如 set_load 好了，查了只會得到一個網頁介紹 set_load 是在幹嘛，
卻沒有一個巨觀的 set_load 解釋，為了自己解決這個問題，寫著寫著就變成超長一篇，
不過如果能對大家有幫助那就太好了太好了 ~~好高興好高興~~。

其實這種設定都是大同小異，有一些 command 你丟去 google，找到的會是 AMD/Xilinx 的網頁…是的，
就算是 FPGA 的合成也是需要這些東西，只不過一般是 FPGA 的工具套了預設的設定幫你做掉了，
可以找找專案內有沒有 .xdc 檔，也就是 Xilinx Design Constraint，那就是相關的設定了。  
如果你 FPGA 的專案比較複雜，例如有低速如 UART/IIC 等介面，就需要額外的 xdc 設定，
Vivado 才能正確合成你的設計。

因此，可以的話把這些設定弄熟是絕對不吃虧的。

# 參考資料

* [Design Compiler User Guide](http://beethoven.ee.ncku.edu.tw/testlab/course/VLSIdesign_course/course_96/Tool/Design_Compiler%20_User_Guide.pdf)