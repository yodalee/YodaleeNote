---
title: "數位電路設計系列 - APR 前準備"
date: 2025-05-11
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
images:
- /images/ICdesign/PinPlanning.jpg
---

上一篇我們看了 Design Compiler 的使用，把我們的電路合成為邏輯閘，下一步看是先送 LEC 
或是做 post-synthesis simulation，再來就要進到重頭戲用 APR 來畫 Layout 了，
在 APR 之前，我們先用單獨一篇文來看看 APR 前要準備的東西。
<!--more-->

要注意這裡說明的對象是 Cadence 的 INNOVUS，有些內容跟 Synopsys ICC2 很可能不一樣，如果是 ICC2 
使用者請小心參考。

# 你的設計

一般我會叫 chip_top.syn.v，也就是從 design compiler 吐出來的 verilog file
，常理來說不用經過太多處理可以直接使用，只要注意下面幾點即可：
1. 如果你的設計要打 pad，建議在送合成前就先加入 IO cell，如 [Desicn Constraint 篇]({{<relref "DesignConstraint">}}) 所說，這樣合成時序才會對。  
輸出的 .syn.v 匯入 layout 軟體時，這些 io pad 會和下面 .io 檔案設定的 cell 連結在一起。
2. 之前上課的時候講師會提醒 .syn.v 裡不應該有 assign 語法，其一是在 design compiler tcl 內加入：
```tcl
set_fix_multiple_port_nets -all -buffer_constants [get_designs *]
```
就能消除掉 assign 語法；其二是我之前也曾把有 assign 的 verilog file 丟進 INNOVUS 也沒出事
（而且晶片有量到），我判斷這個現在已經不是問題。

# design constraint .sdc 檔

上一回 design compiler tcl 設定中 `write_sdc` 寫出的檔案，在匯入 layout 軟體前，
先把下面幾個設定槓掉：
* set_wire_load_model
* set_dont_touch_network
* set_fix_hold
* set_ideal_network

wire load model 是因為 APR 軟體可以知道真正的線寬並選用對應的負載模型；
dont_touch_network, fix_hold, ideal_network 都是用在 clk, reset 訊號上，Design Compiler 
沒有實體繞線，不會知道 clock tree 的分佈方式，因此透過這些設定讓它別動這些訊號線，
別浪費時間處理這些高負載的線路，而 APR 軟體一定要去處理這些線路，如果在 .sdc 檔中指定不要碰，APR 
會在跑 clock tree 時回報無法達到 constraint 讓你做不下去。

# IO 設定 chip_top.io

雖然我們做著技術前沿的工作，但有些東西還是古早的工具最有效。  
每一次下線我都會準備一張如下的 A4 紙，最上面的方框代表我的晶片（外框畫起來很像 Mac 的 Command 符號），
並用**鉛筆**在四周開始安排每個接腳，方便隨時塗改抽換。

![PinPlanning](/images/ICdesign/PinPlanning.jpg)

接腳圖之外，再打開 APR 軟體，看到實際電路尺寸後，可以在方格中可以畫上 macro 的資訊，
例如我這個設計用了四顆 memory，其中兩顆大顆的跟兩顆小顆的，就把大致的位置畫上去（一樣請愛用鉛筆），
建議尺寸 -- 特別是跟各接腳的相對位置要畫對，因為電源的 pad 會拉
金屬[到周圍的 Power Ring 上]({{< relref "chipstructure#pad">}})，而 hard macro 周圍
也要加上自己的 Macro Ring 供電，兩者就會相衝，在紙上做好記錄在安排 pad 的時候可以先迴避這點，
後續 Layout 流程可以省掉很多的問題。

上半部的接腳圖之外，下半部我們會寫上其他的資訊，這部分等到正式講 Layout 時再來說。

安排 IO 的時候，除了各式訊號線之外，還要安排 Core 使用的電源，和 IO 接腳使用的電源，
第一次遇到鐵定是有點疑惑該怎麼規劃，大致可以參考的規則如下所述：

## Core 電源

晶片要運作就要吃電，基本來說頻率愈高就要吃更多電，如果電給的不夠頻率就會上不去，
但我們要怎麼知道設計的晶片會吃多少電？  

在設計各階段，都有各種工具給的功耗的預估：
* Design Compiler 合成完之後，使用 report_power 得到功耗預估。
* APR 的時候，INNOVUS 內建功耗工具，會再給出一個功耗預估。
* 業界的功耗預估標準是用 Synopsys 的 PrimeTime，搭配模擬時的真實行為，
在大廠工作的同學說可以估到非常準，但我自己是還沒試用過。

注意這些功耗全部都不是真實的功耗，例如 Design Compiler 缺乏 clock tree、實際運作行為等資訊，所以預估只能當作參考。  
以下就列出我過去下線時，Design Compiler、INNOVUS 與實際量測的結果，給大家做個參考：

| Design Compiler (mW) | INNOVUS (mW) | Measurement (mW) |
|:-|:-|:-|
| 114 | 220 | 77 |
| 18 | 32 | 10 |
| 58 | 81 | 31 |

可以看到無論是 Design Compiler 亦或 INNOVUS 都會高估，INNOVUS 更是估到 2-3 倍的功耗；
不過功耗這種東西不嫌多，多加兩個 pad ，總好過晶片出來發現功耗吃滿跑不到 spec ~~畢不了業~~只能降頻來跑。  
因為在進行 APR 之前就要先安排 pad，我一般會用 Design Compiler 預估的功率，抓 1.5-2 倍的餘裕，
相信就算 APR 估更高也能吃得下。  
接著在 Pad 的文件裡，能找到 VDD/VSS Pad 所能承受的電流或是功率，用這樣去算所需的 VDD/VSS 對數。

## IO 電源

再來是 IO 電源，IO 電源的消耗來自於訊號 pad 工作時會需要耗電，如果 VDD/VSS 不夠，就會導致 VDD/VSS 抖動（例如從 1V 抖到 0.99V）。  
如果晶片上有大量訊號同時上下開關，而 IO VDD/VSS 不夠以致壓不住，就會像在小巨蛋開唱 
[We will rock you](https://www.youtube.com/watch?v=-tJYN-eG1zk) 
一樣，抖動大到引發問題，例如影響到 clock 的穩定性，
或者把 active low 的 reset 訊號抖下去，晶片就重設了。  
IC 設計業有一個 DF 值來描述這個問題，如果你做的晶片沒使用 Serial Interface
，而是把大量訊號拉出來，上 [V93000](https://www.advantest.com/en/products/semicondoctor-test-system/soc/v93000-exa-scale/) 
這種自動量測平台去量測，就需要好好算一下 DF 值並預估需要的 VDD/VSS 數。
在我學會之前就請先參考[皓宇的筆記](https://timsnote.wordpress.com/2017/08/09/pad-selection/#io_power_pad)。  
如果有使用 Serial Interface，則不太可能會有大量訊號同時跳動，IO VDD/VSS 放個 1-2 對就絕對夠用了。

職場前輩給的建議是：

> 接腳中 ⅓ 是訊號線；⅓ 是 Core 電源；⅓ 是 IO 電源。  

我自己是覺得這個估計電源抓得比較誇張一點，確保電源絕對夠用，信號完整度絕不崩盤。

## 其他建議

最後還有一些為了訊號完整性建議的規則，簡列如下：

* Clock pad 的兩邊，用 VSS 夾住，確保不會有其他訊號跑進來干擾 clock
* 視封裝把 Clock 安排在路徑最短的邊上，減上 clock 的抖動與干擾
* 平均分配 Core VDD/VSS 的位置，不要集中在某邊，離電源太遠的那邊就會缺乏供電。
* IO Ring 也是，在有大量輸出的部分插入一些 IO VDD/VSS，以免抖動影響量測

~~你仔細看就會看到我上面那張圖根本是亂畫的~~

# IO 設定

安排好接線之後就來改寫 io 檔案，一個完整的 io 設定如下所示，設定的方向是依照座標軸的，
上排和下排是依 X 軸方向，由左到右；左排跟右排則是依照 Y 軸方向，由下到上：
```io
(globals
  version = 3
  io_order = default
)
(iopad
  (top
    (inst name="IVSS_T0"      cell="VSS_io"   place_status=placed)
    (inst name="IVSS_T1"      cell="VSS_io"   place_status=placed)
    (inst name="CVDD_T2"      cell="VDD_core" place_status=placed)
    (inst name="CVDD_T3"      cell="VDD_core" place_status=placed)
    (inst name="CVSS_T4"      cell="VSS_core" place_status=placed)
    (inst name="CVSS_T5"      cell="VSS_core" place_status=placed)
    (inst name="IVDD_T6"      cell="VDD_io"   place_status=placed)
    (inst name="IVDD_T7"      cell="VDD_io"   place_status=placed)
  )
  (left
    (inst name="ipad_ss"                      place_status=placed)
    (inst name="ipad_dbg_clk_gate"            place_status=placed)
    (inst name="ipad_sck"                     place_status=placed)
    (inst name="ipad_mosi"                    place_status=placed)
    (inst name="opad_miso"                    place_status=placed)
    (inst name="CVSS_L0"      cell="VSS_core" place_status=placed)
    (inst name="ipad_clk"                     place_status=placed)
    (inst name="CVSS_L1"      cell="VSS_core" place_status=placed)
    (inst name="ipad_rstn"                    place_status=placed)
    (inst name="ipad_dbg_sel0"                place_status=placed)
    (inst name="CVDD_L2"      cell="VDD_core" place_status=placed)
    (inst name="ipad_dbg_sel1"                place_status=placed)
  )
  (bottom
    (inst name="IVDD_B0"      cell="VDD_io"   place_status=placed)
    (inst name="IVDD_B1"      cell="VDD_io"   place_status=placed)
    (inst name="CVDD_B2"      cell="VDD_core" place_status=placed)
    (inst name="CVDD_B3"      cell="VDD_core" place_status=placed)
    (inst name="CVSS_B4"      cell="VSS_core" place_status=placed)
    (inst name="CVSS_B5"      cell="VSS_core" place_status=placed)
    (inst name="IVSS_B6"      cell="VSS_io"   place_status=placed)
    (inst name="IVSS_B7"      cell="VSS_io"   place_status=placed)
  )
  (right
    (inst name="opad_dbg_data7"               place_status=placed)
    (inst name="opad_dbg_data6"               place_status=placed)
    (inst name="opad_dbg_data5"               place_status=placed)
    (inst name="CVDD_R0"      cell="VDD_core" place_status=placed)
    (inst name="opad_dbg_data4"               place_status=placed)
    (inst name="opad_dbg_data3"               place_status=placed)
    (inst name="CVSS_R1"      cell="VSS_core" place_status=placed)
    (inst name="opad_dbg_data2"               place_status=placed)
    (inst name="opad_dbg_data1"               place_status=placed)
    (inst name="opad_dbg_data0"               place_status=placed)
    (inst name="CVDD_R2"      cell="VDD_core" place_status=placed)
    (inst name="ipad_dbg_sel2"                place_status=placed)
  )
  (topleft
    (inst name="CORNER_TL"    cell="CORNER"   place_status=placed)
  )
  (topright
    (inst name="CORNER_TR"    cell="CORNER"   place_status=placed)
  )
  (bottomleft
    (inst name="CORNER_BL"    cell="CORNER"   place_status=placed)
  )
  (bottomright
    (inst name="CORNER_BR"    cell="CORNER"   place_status=placed)
  )
)
```
我歸納出來，針對電源的命名原則如下：
* 首字母 I, C 代表 IO 跟 Core
* VDD/VSS 代表電源和接地，要用 VDD/GND 也可以
* 後綴使用 T,B,L,R 代表上排、下排、左排、右排，再加上流水號，不建議用全域流水號像 VDD1, VDD2…，
這樣會變成你要追蹤 1, 2, 3 … 分別出現在四個方向的哪裡，會很麻煩。

除了電源之外，訊號線不用設定 Input/Output cell，INNOVUS 可以自動從 .v 檔內的 cell 推論出該
 pad 使用的元件。

# PDK
準備製程廠提供的 PDK 檔，跟每一家不同的製程廠有關，參考前請再三確認，套用你製程的設定而不是照抄。  

至少應該會有 tech.lef, core.lef 和 io.lef 三類檔案，core 還會依製程分成 slow/fast 
等變體，全部都要用到；在 layout 之前，需要將製程模型轉為 INNOVUS 使用的 
OASIS library，以下是匯入用的 script
```shell
lef2oa -lef tech.lef -lib macroLib -techRef N90 -useFoundryInnovus
lef2oa -lef core_fast.lef -lib macroLib
lef2oa -lef core_slow.lef -lib macroLib
lef2oa -lef io.lef -lib macroLib
```

晶圓廠提供的檔案會是 LEF 格式，內含標準元件庫的各式抽像的物理資訊，
[Team VLSI](https://teamvlsi.com/2020/05/lef-lef-file-in-asic-design.html) 可以看到相關的範例。  
tech.lef 是定義該製程基礎參數的 Technology LEF 檔，像是
* 尺寸單位
* 有多少金屬層與多少 Via
* 每層金屬的名字、類型
* 金屬是水平或垂直
* 最小/最大寬度
* 金屬間的建議間隔

包山包海，這些資訊讓 APR 軟體在 layout 的時候，有個基本的規則可以依循。

core_fast/slow.lef 是 Cell LEF，裡面會是所有可用的元件，資訊如：
* 名字
* 元件類型
* 座標、尺寸
* 接點名字、輸出入、性質 (signal, power, clock...)、接點形狀、使用金屬層

如果用 [阿嬤都能懂的晶片設計](https://m105.nthu.edu.tw/~s105062901/ppt/RMaKnowsICDesignFlow.pdf) 來比喻，
LEF 就是提供一個高層次的建築描述，像是這棟房子是用鋼筋混凝土建的，有四層樓可以蓋，然後跟 IKEA 
拿到家俱型錄，桌子的尺寸有這些選擇，浴缸的尺寸有這些，要固定的話哪裡可以鎖螺絲，要用幾號螺絲…，
APR 軟體會利用這些資訊完成 Layout。

# Hard Macro

與 PDK 類似，在 layout 前也要將 Hard Macro (因為是數位電路，這裡指的是記憶體) 所用 .lef 
和 .v 檔匯入。  
我所用的記憶體都是從產生器產生的，包含。
* hardmacro.lef
* hardmacro.v
* hardmacro.gds

轉換的 script 包含 lef2oa 和 verilogAnnotate 兩個 script，前者提供 layout，後者提供 verilog 
的參照。

```bash
lef2oa -lef hardmacro.lef -lib macroLib
verilogAnnotate -refLibs macroLib -verilog hardmacro.head.v
```

一般來說 memory compiler 輸出的 verilog 包含行為的模型，verilogAnnotate 只需要 port 跟 
port 寬度即可，hardmacro.head.v 請如下方把所有行為相關的 code 都砍掉。

```verilog
module hardmacro (clk, cen, wen, addr, i_data, o_data)
  input clk;
  input cen;
  input wen;
  input [15:0] addr;
  input [31:0] i_data;
  output [31:0] o_data;
endmodule
```

# mmmc 檔

[MMMC](https://semiengineering.com/knowledge_centers/eda-design/methodologies-and-flows/multi-corner-multi-mode-analysis/) 
的全名是 multi-mode multi-corner 的簡稱，也有人反過來簡稱為 MCMM。  
MMMC 的來由是這樣的，隨著製程進步與晶片的複雜化，要整體考慮的模式也愈來愈多，例如
本來的晶片也許只要時序過了就行了，但製程微縮後兩條線中間信號的耦合也要考慮，做很小之後散熱也變成問題，
所以功耗密度也要考慮；為了測試我們加個 scan chain，那多出來的 scan timing 也要分析。  
問題是時序、功耗、耦合本來是多個不同工具負責的，如果先來修時序，修完可能最佳化太多，變成功耗過不了；
這種跨模式違反規則變得異常麻煩，會耗費大量的 ECO 時間反覆進行修正。  
到了高階的設計，模式和需要分析的邊角案例會成倍增加
（例如我在時序最快、功耗最高的狀況下，RC 的耦合是否符合規則），組合起來的數量可能達到數百個。  

要怎麼辦呢？於是 MMMC 出現了。  
MMMC 大致依照下圖的階層圖進行組合，每個組合都會得到一個邊角的條件讓軟體進行分析。  
APR 軟體會就所有條件進行分析，確保都符合規範，省去手動迭代不同種類測試的功夫。

![MMMC](/images/ICdesign/MMMC.png)

一個範例用的 MMMC 設定如下，同樣這裡請參考使用製程的檔案，複製時請謹慎：

```tcl
create_rc_corner -name RC_worst
  -cap_table {rcworst.captble}
  -qrc_tech {rcworst.tch}
create_rc_corner -name RC_best
  -cap_table {rcbest.captble}
  -qrc_tech {rcbest.tch}

create_library_set -name lib_max -timing
  { slow.lib io_slow.lib hardmacro_slow.lib }

create_library_set -name lib_min -timing
  { fast.lib io_fast.lib hardmacro_fast.lib }

create_opcond -name 0p9v_125c -process 1 -voltage 0.9 -temperature 125
create_opcond -name 1p1v_m40c -process 1 -voltage 1.1 -temperature -40

create_timing_condition -name TC_max -library_set {lib_max} -opcond 0p9v_125c
create_timing_condition -name TC_min -library_set {lib_min} -opcond 1p1v_m40c

create_delay_corner -name DC_max -timing_condition {TC_max} -rc_corner {RC_worst}
create_delay_corner -name DC_min -timing_condition {TC_min} -rc_corner {RC_best}

create_constraint_mode -name CM_func -sdc_files { func.sdc }
create_constraint_mode -name CM_scan -sdc_files { scan.sdc }

create_analysis_view -name AV_func_max
  -constraint_mode {CM_func} -delay_corner {DC_max}
create_analysis_view -name AV_func_min
  -constraint_mode {CM_func} -delay_corner {DC_min}
create_analysis_view -name AV_scan_max
  -constraint_mode {CM_scan} -delay_corner {DC_max}
create_analysis_view -name AV_scan_min
  -constraint_mode {CM_scan} -delay_corner {DC_min}

set_analysis_view
  -setup {AV_func_max AV_scan_max}
  -hold {AV_func_max AV_func_min AV_scan_min}
```

可以看到，其實不過是把我上面畫的階層圖改成用文字描述罷了。  
* create_rc_corner：使用 capTable PDK 的 RC 模型與 qrctechfile 給 RC 萃取軟體使用的檔案，
建立一個 RC 案例。
* create_library_set：打包所有相關的 library，注意有使用的 hardmacro 也要包進來一起分析。
* create_opcond： 設定運作溫度、電壓，常見就是溫度 -40\~125℃，電壓 -10%\~+10%；
高階製程可能會多出其他的溫度條件，例如在高溫時電晶體反而跑更快了，會需要多一個 operating conditon。
* create_timing_condition：組合 operating condition 和 library。
* create_delay_corner：組合 timing condition 和對應的 RC 案例。
* create_constraint_mode：匯入需要達成的 constraint
* create_analysis_view：針對各 constraint 創建各種 analysis view。

最後用 set_analysis_view 把各 analysis view 分類到 setup 條件或 hold 條件，就完成啦。

# 結語

雖然只是幾個檔案，但加上說明還真不少，相信大家也看到頭昏腦脹了。  
正常情況來說，文中大部分的設定，例如 MMMC，.sdc 等，都應該會有舊有的檔案可以參考，
常年在下線的公司，其設定都應該會有一年年的留存，照著往年的設定些微修改即可，工具*理應*都自動化了，
也沒多少調整的空間；除非你有幸參與到換製程的大年份，那就恭禧了，這可是難得的經驗呢。
