---
title: "數位電路設計系列 - Design Compiler 在幹嘛"
date: 2025-01-28
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
images:
- /images/ICdesign/ChipAll.png
---

講完了 design constraint，這篇就要來介紹晶片下線時合成的龍頭老大 - Synopsys 的 Design Compiler 啦。  
其實要寫這篇我是有點猶豫的啦，畢竟 Design Compiler 身為龍頭老大哪缺我這一篇介紹，
Cadence 也是有對應的下線工具 Genus，但就…我也只會 Design Compiler，如果 Cadence 願意贊助我上課的話我倒是願意幫忙寫一篇(欸。
<!--more-->

# Design Compiler 的工作

說穿了，合成工具就是把一般我們寫的 RTL 電路，轉換成各種 and, or, xor, oai 等邏輯閘實現的實作。在轉換的過程中，合成工具也會幫我們注意 PPA：
* Performance，怎麼樣合成邏輯閘以達成設計的頻率
* Power，怎樣合成最省電
* Area，怎樣合成的晶片面積最小
三個限制當中，Performance 的優先度是最高的，做不到想要的頻率，面積很小功耗很低也沒用，~~我想應該不會有人接受買了 i9 但跑起來像是 pentium 4~~。

![ChipAll](/images/ICdesign/ChipAll.png)

讓我們把上一篇的圖再拉出來，要好好設定 Design Compiler 對 Design Constraint 的了解是不可或缺的，建議大家可以把上一篇的 [Design Constraint]({{<relref "designconstraint">}}) 多看個幾遍。  
轉換成邏輯閘之後，合成工具就會開始做時序檢查，每個 Register 間都是一條 Path，合成工具會檢查是不是每條 path
的 Delay 都能符合 Timing Constraint，以下舉幾個合成工具會做的事：

1. path 太慢，會調整邏輯閘，用面積去換 Performance，換面積更大時序更快的電路來符合時序要求。
2. path 太快，在中間插入 buffer，加一點時間讓 hold time 足夠。
3. DRV 的狀況，如 fanout 太多、capacitance 太大，插入 buffer 讓後續推得動。
4. 用性能換面積，在 Path 符合要求的情況下，選用面積小但比較慢的電路，保住時序要求又能減少電路面積。
5. 在高階製程中 [會提供不同 Vt 的元件](https://www.2cm.com.tw/2cm/zh-tw/tech/6520667B928A4026B904266BC4D88B79)
，高 Vt (HVT)的元件會比較慢但漏電少、低 Vt (LVT) 則是較快但漏更多電，合成工具會在緊要路徑上選用 LVT 元件達成時序要求，其他路徑則會用 RVT 或 HVT 元件降低功耗。

# Design Compiler 環境設定

Design Compiler 的設定檔是 .synopsys_dc.setup，會依照下列的順序進行設定
1. 系統設定：位在 $SYNOPSYS/admin/setup `內的 .synopsys_dc.setup。
2. 個人設定：位在使用者家目錄下的 .synopsys_dc.setup。
3. 專案設定：工作目錄下的 .synopsys_dc.setup。

通常 1 是系統管理者設定的，會是安裝時與軟體版本相關的設定文件；2 是個人的設定；3 則是每個工作目錄獨有的，例如製程等相關的設定。  
設定相衝突的話，個人設定會蓋掉系統設定，專案設定會蓋掉個人設定。  
目前由於個人只會用一種製程，所以全部都用個人設定而不用專案設定，如果你的電腦上很奢侈的有多種製程可以選，那就可以切換為專案設定。

.synopsys_dc.setup 的內容如下：

```tcl

set search_path "."
set search_path "/path/to/synopsys/db $search_path"
set search_path "/path/to/memory/db $search_path"

set target_library "\
    core_rvt_tt.db \
    core_rvt_ff.db \
    core_rvt_ss.db"

set link_library"\
    * \
    memory_tt.db \
    memory_ff.db \
    memory_ss.db \
    io_tt.db \
    io_ff.db \
    io_ss.db \
    $target_library"

set symbol_library "generic.sdb"
set synthetic_library "dw_foundation.sldb"

set verilogout_no_tri true
set hdlin_enable_presto_for_vhdl "TRUE"
set sh_enable_line_editing true
history keep 2000
```

下面就依序解釋這幾個項目的意思：

## search_path
尋找 .v 以及 .db 的路徑，一個是我們設計晶圓廠會提供製程中 standard cell 的 db 檔；另外我們要為晶片中使用的 memory 生成 db 檔，把這些路徑都加入 search_path 中。  
為了避免混淆，我習慣會把 standard cell 的 db 檔跟記憶體分開來加入 search_path。

## target_library
合成用的邏輯閘的元件庫，由晶圓廠提供，合成工具會使用 target_library 裡的元件進行合成。  
例如你寫了一個 operator +，target_library 內提供了 xor 跟 and，合成工具就會用 xor 跟 and 實作出你要的 operator +；
但如果你 target_library 裡面只提供 nand，那合成工具就只會用 nand 來堆出 operator + ~~無痛達成 Nand2Tetris~~。  
先前提過的 HVT, RVT, LVT，一般是選用 RVT 進行合成，並在 layout 的時候由 layout 工具進行替換，合成時只要加入 tt, ff, ss 等邊界條件即可（這部分沒那麼肯定，有前輩知道的話麻煩指正）。

## link_library
連結用的的元件庫，合成工具在把你的設計讀入之後，需要在 link_library 裡面找到所有元件的定義，一般會在這裡加入不需要合成的元件，包括下面幾個：
* \* 表示從 design compiler 已經讀入的記憶體去找
* target_library 的內容
* 用工具產生的 memory macro
* IO Pad
* 其他各種 macro

這裡特別說明一下 [target_library 跟 link_library 的不同](https://www.edaboard.com/threads/whats-the-difference-between-the-target-library-to-the-link.72856/)
，target_library 是合成時 mapping 用的，link_library 則是合成後必須要找到參考的對象。雖然機率不太高，
但如果你把 IO Pad 加入 target_library ，設計的一部分又太奇葩，合成工具有機會用 IO Pad 的 cell 來組合你的電路。

如果用軟體的角度來理解的話，target_library 就像定義了許多基本的 assembly 指令，在編譯的時候會用這些 assembly 指令實作高階語言；
link_library 則是定義一些特殊的 assembly，如果你的電路裡直接寫了一些特殊的 avx 指令，就需要 link_library 提供 avx 指令的定義。  
當然，會看到我把整個 target_library 加到 link_library 裡面，因為基本的指令在合成後也要被 design compiler 看到，不然也跳警告或錯誤。

## symbol_library

這是開圖形化介面需要的，定義元件在 schemetic 上要怎麼顯示；如果晶圓廠沒提供的話，
使用 design compiler 提供的 generic.sdb 應該就夠用了，頂多有些元件可能變成空洞的小正方形。

## synthetic_library
合成函式庫，告訴合成工具一個高階功能要怎麼對應到實際的邏輯閘，dw_foundation 的 dw 指的是 synopsys 的 [DesignWare](https://www.synopsys.com/dw/buildingblock.php)
，例如裡面就定義了 2, 3, 4, 5, 6 級 pipeline 的乘法器如何合成，還有許多其他的 IP block。  
如果有買特殊的 IP，或是某些高階的合成方式，就要把 .sldb 填在這裡。

# Design Compiler 跑起來
執行 Design Compiler 有幾種方式，一種是使用圖形介面：
```bash
dv
```
Design Compiler 圖形介面可以做很多事，例如圖形化檢視 design compiler 如何分析你的設計。

另一種是文字介面，如下節所示，我基本上是一套 script 走天下：
```bash
dc_shell
dc_shell -f compile.tcl # 執行 compile.tcl
```

合成工具的使用步驟（也就是 script 的內容）大致分為如下幾個步驟：
1. 讀入設計
2. 設定 constraint
3. 執行編譯
4. 輸出結果

Synopsys 官方有提供一張圖，估且做個參考：
![Design Compiler Flow](/images/ICdesign/DesignCompilerFlow.png)

## 讀入設計

讀入設計的部分，design compiler 是使用類似 vcs 的三步驟做法：

第一步使用 analyze 讀入設計 `analyze -f sverilog -vcs "-f chip_top.f"`  
可以讀入 verilog, sverilog, vhdl 三種格式的設計；讀入檔案使用 vcs 的格式，下面是 chip_top.f 的內容：
```txt
// top
src/define.sv
src/chip_top.v
src/block_wrap.sv

// add project top directory as include path
+incdir+projdir
-f proj.f
```

除了 top 連接之外，其他模組都單獨寫一個 .f 檔，透過 chip_top.f 中加入 -f 包含進來。  
在 proj.f 中一樣，把所有需要的 .sv 檔寫進去，如果你的設計有更多不同的 block，只要增加 .f 檔即可。

第二步 elaborate，這步做設計的分析，
```txt
elaborate $toplevel
```
從 $toplevel 模組去分析你的設計，把整個設計連結在一起，看看設計裡面有什麼東西。

analyze 的時候 design compiler 會將你的設計轉為 .pvl 和 .syn 兩種檔案，都是 design compiler 特有的 binary 
檔案，只要知道它是某種 design compiler 可以更快讀入設計的格式即可。  
如果覺得現下工作目錄一堆 .pvl .syn .mr 檔很煩的話，可以參考使用：
```tcl
mkdir work
define_design_lib $top_level -path work
```
把這些中繼檔丟去 work 資料夾內（其實我之前都沒用這個，寫這篇文才知道可以這樣用）

elaborate 的輸出，最重要的是下面的資訊：
```txt
Inferred memory devices in process
   in routine DMA line 161 in file
    	' . ./DMA.sv
==========================================================================
| Register Name  | Type      | Width | Bus | MB | AR | AS | SR | SS | ST |
==========================================================================
| input_data_reg | Flip-flop |  256  |  Y  | N  | Y  | N  | N  | N  | N  |
==========================================================================
```

這裡的意思是，在這個檔案裡推論出一個 Flip-flop，後面列出的則是對應的屬性：
* Type： Flip-flop 或是 latch
* Width/Bus： 單一 bit 或是多個 bit 組合
* MB： multibit，這個我沒開設定時都不會推論出 multibit，詳細可能要另外拉[另一篇文章](https://blog.csdn.net/i_chip_backend/article/details/124972693) 出來講了
* AR/AS： Asynchronous Reset 與 Asynchronous Set，透過 asynchronous 信號設定 register 內容為 0 或 1。
* SR/SS/ST： Synchronous Reset, Synchronous Set, Synchronous Toggle，透過 synchronous 信號設定 register 內容為 0, 1 或反向。

這裡最重要的就是先檢查有沒有語法上的錯誤導致 elaborate 失敗，再來是看看有沒有推導出 Latch 就可以了。

## 設定 constraint

請參考下面的 TL;DR 的 script ，以及熟讀上一篇 [Design Constraint]({{<relref "designconstraint">}})。
設定完 constraint 之後可以使用 check_timing 檢查設定有沒有問題。

## 執行編譯
在 design compiler 下 compile 指令開始進行合成。  

我也不懂它背後到底做了多少事情，下面就節錄 log 的大標題，寫一下我大概知道的部分：

### Beginning Implementation Selection

首先 design compiler 會先用 DesignWare 裡面的 block 替換掉你設計中的部分，例如把加法代換成 DesignWare 提供的邏輯閘實作，這在 design compiler 裡叫 Mapping。

### Beginning Mapping Optimization

第一次的最佳化，這裡會第一次看到下表：  

```txt
| ELAPSED TIME | AREA | WORST NEG SLACK | TOTAL SETUP COST
| DESIGN RULE COST | ENDPOINT | MIN DELAY COST |
```

* Elapsed time：目前的執行時間
* Area：目前設計的面積
* Worst Negative Slack (WNS)：所有 Setup time  違反設計規則路徑中，違反最大的差距值
* Total Setup Cost：有些工具像 Xilinx Vivado，會稱這格為 Total Negative Slack (TNS)，
這是把所有的 slack 經過加權後的總和值，就描述上來看可能包含 max_path (setup) 與 min_path (hold) 的 slack
* Design Rule Cost：design rule 上，現下設計與使用者設定目標的差距值
* Endpoint：當 design compiler 開始進行最佳化的時候，當下最佳化的點會寫在這裡，當修復 delay violation
時，會寫出修復的邏輯閘 (cell) 或埠 (port)；如果修復的是 design rule，會寫出修復的走線 (net)
* Min Delay Cost：這個是 min_path 上的 TNS。

一開始合成時很多設計指標如 WNS 面積都很大，但不用單心，很快就會降下來。

### Beginning Delay Optimization Phase

WNS 跟 timing constraint 有關，在合成結束的時候一定要降到 0，而 TNS 是 WNS 的加權總和，也應該要降到 0。  
如果 WNS 降不下來，就要考慮改設計或是放寬 timing constraint 然後重新合成。

### Beginning Design Rule Fixing

可能要修復的 design rule 包括 (min_path) (min_capacitance) (max_transition) (max_capacitance)。  
修正完最重要的 delay，再來會會插入 buffer 去修復 design rule，不一定會修到 0。  
如果設定了 set_fix_hold ，這步會開始出現 Min Delay Cost

### Beginning Area-Recovery Phase

開始面積最佳化，一般面積的最佳化目標是 0，愈小愈好，讓 design compiler 自己做到放棄就好；從這個順序也可看出，
對 design compiler 來說，最重要的就是先解決 timing (delay) 的問題，再來修 design rule，最後再來顧面積；
另外無論 design rule 跟面積最佳化做了什麼，導致 WNS 曾經脫離 0，都會修正回去。  
有設定 set_fix_hold 的話也會在這步開始插入 buffer，就我個人的經驗這個插 buffer 還滿慢的，
覺得太久也可以放棄這步，讓 layout tool 修正就好。

### Optimization Complete

該做的都做完了，結束 compile。
如果想再做更進一步用 HVT 做power 最佳化，可以加上指令
```tcl
set_leakage_optimization true
compile -inc
```
來完成。

## 輸出結果

Design Compiler 在合成完成之後（通常就是 script 跑下去，然後去看兩集動畫就會合成完了），再來只要確定兩件事即可：

第一是把合成結果寫出來，總共有四個：
1. 合成完設計的 ddc 檔，未來可以再讀入進行最佳化，例如抽換為 HVT device，甚至換到新製程上
2. 寫出 standard delay format (.sdf) 資訊，這個檔案記錄了電路中各節點到另一個位置的 delay，在 post-synthesis 的模擬會需要用到
3. 寫出合成結果，以邏輯閘打造的 .v 檔，一般我會叫 .syn.v 表示這是合成過的
4. 寫出 constraint 檔 (.sdc)，使用 INNOVUS 進行 layout 時會需要

第二是輸出 design compiler 合成的報告，下面 TL;DR script 會固定輸出一堆報告，重要的大概有幾個：
1. 檢查 max_timing 與 min_timing 報告，確定沒有 timing violation
2. area report 可以看看每個 cell 使用的面積，決定你的設計哪裡需要最佳化
3. latch report 再次確認電路裡沒有 latch
4. power report 看看 design compiler 預告合成後電路的功耗是多少，由於 design compiler 沒有 clock tree
的資訊，這個功耗會比 layout 完成後，由 layout 軟體或是 PrimeTime 估得要少，我的經驗從最終結果的 52% 到 71% 
不等（當然量測又量到比 design compiler 估得功耗更小那就是另一個故事了）

# TL;DR

以上就是 design compiler 如何用以及它做了什麼的介紹，不過我知道很多人如果跑進來，很有可能是第一次使用 Design Compiler，又或者是死線將近要趕快開始合成，這個時候什麼都不想看只想趕快拿到一個可以用的 design compiler script 開始跑。

這些小弟都懂，以下附上我合成用的 script，反正可能有 >50% 也是從其他網站抄來的，對以下 script 來源還找得到的，我就在這裡附上：
* 基礎架構來自 Washington University 的上課講義 [Tutorial for Design Compiler](https://classes.engineering.wustl.edu/ese461/)。
* STOP_HERE 來自 CSDN [DC/PT在任意位置停止执行脚本的方法](https://blog.csdn.net/SH_UANG/article/details/54178459)。
* Output 第一節的 naming rule，應該部分來自於 [IThome DC 個人筆記](https://ithelp.ithome.com.tw/articles/10231993)。

至少小弟可以確定，用這套 script 合成、製作的晶片，最終是符合預期有量到的，也許可以讓各位直接複製的看倌們放心一些。

## read_file.tcl

第一個部分是 read_file.tcl，elaborate 這步稍花時間，如果沒改設計也不用重新讀入，因此特別分一個 read_file.tcl 出來，生成原始的 .ddc 檔供後續使用。

```tcl
########################################
# User Defined Parameters             #
########################################

# Set the top module of your design
set toplevel chip_top

# set the filelist
set filelist chip_top.f

set sh_continue_on_error false
set compile_preserve_subdesign_interfaces true

define_design_lib work -path work

########################################
# Read in Verilog Source Files         #
########################################
analyze -f sverilog -vcs "-f $filelist"
elaborate $toplevel

set filename [format "%s%s" $toplevel "_raw.ddc"]
write -format ddc -hierarchy -output $filename
```

## compile.tcl

第二部分就是真正編譯的部分，要改動的有幾項：
1. set_operating_conditions 與 set_wire_load_model 請改成真正使用的 library。
2. Constraint 的部分請自己改想要的數字，至少要改 clock 與 input/output delay。
3. 這裡我會在第一次編譯之前，會先反註解 STOP_HERE，檢視一下 check_timing 跟 report_net_fanout 的輸出，第一看看 timing 有沒有問題，第二看看還有沒有 high fanout 要加進 set_ideal_network 裡的。
4. set_fix_hold 是用來指定修復 hold issue，可放可不放，放了 design compiler 可能會花很多時間插入 buffer 修復 hold time issue，但這些 buffer 隨後在 layout 時就會全部被移除掉。
5. 一般我會先把 effort 設定成 medium，先跑過一次合成，確定沒問題再用 high 去挑戰極限；當然兩者的能力也有差，我有一個 400 MHz 的合成，用 medium 的話 WNS 只能收斂到 0.1，high 就能順利降到 0。
6. set_timing_derate 我還沒嘗試過，它的目的是在合成時先插入 10% 的 delay，讓設計面對製程變異可以更強健，但我記得設下去會跑出一些合成問題。

```tcl
########################################
# User Defined Parameters             #
########################################

# Set the top module of your design
set toplevel chip_top

# set the filelist
set filelist chip_top.f

set sh_continue_on_error false
set compile_preserve_subdesign_interfaces true

# compile design (medium or high)
set effort high

########################################
# Read in Verilog Source Files         #
########################################
# analyze -f sverilog -vcs "-f $filelist"
# elaborate $toplevel
set filename [format "%s%s" $toplevel "_raw.ddc"]
# write -format ddc -hierarchy -output $filename
read_ddc $filename

current_design $toplevel

########################################
# Define constraints                   #
########################################

set_operating_conditions -min <ff.lib> -max <ss.lib>
set_wire_load_model -name Tiny -library <ss.lib>

# 100 MHz main clock
create_clock -period 10 -waveform {0 5} -name clk [get_ports clk]

set_fix_hold              [get_clocks clk]
set_dont_touch_network    [get_clocks clk]
set_ideal_network         [get_ports clk]

# reset and clock gating
set_ideal_network         [get_ports rstn]

set_clock_uncertainty 0.2 [get_clocks clk]
set_clock_latency 1       [get_clocks clk]

set_input_transition 0.5  [all_inputs]
set_clock_transition 0.1  [all_clocks]
set_drive 0.1 [all_inputs]
set_load 20 [all_outputs]

# 6 = 10 * 0.6
set_input_delay -clock clk -max 6 [remove_from_collection [all_inputs] [get_ports "clk"]]
set_input_delay -clock clk -min 0 [remove_from_collection [all_inputs] [get_ports "clk"]]
set_output_delay 4 -clock clk [get_ports "dbg_data"]

# set_timing_derate -late 1.10 -cell_delay [get_cells -hier *]

check_timing
report_net_fanout -high_fanout

# STOP_HERE

########################################
# Design Compiler settings            #
########################################

# max_area
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants [get_designs *]

compile -exact_map -map_effort $effort -area_effort $effort -power_effort $effort

# power optimization
# set_leakage_optimization true
# compile -inc

########################################
# Output files                         #
########################################

set bus_inference_style {%s[%d]}
set bus_naming_style    {%s[%d]}
set hdlout_internal_busses true
change_names -hierarchy -rule verilog
define_name_rules name_rule -allowed "A-Za-z0-9_" -max_length 255 -type cell
define_name_rules name_rule -allowed "A-Za-z0-9_[]" -max_length 255 -type net
define_name_rules name_rule -map {{"\\*cell\\*" "cell"}}
define_name_rules name_rule -case_insensitive
change_names -hierarchy -rules name_rule

# save design
set filename [format "%s%s" $toplevel "_opt.ddc"]
write -format ddc -hierarchy -output $filename

# save delay and parasitic data
set filename [format "%s%s" $toplevel ".sdf"]
write_sdf -version 2.1 -load_delay net $filename

# save synthesized verilog netlist
set filename [format "%s%s" $toplevel ".syn.v"]
write -format verilog -hierarchy -output $filename

# this file is necessary for P&R with Encounter
set filename [format "%s%s" $toplevel ".sdc"]
write_sdc $filename

redirect [format "%s%s" $toplevel _design.repC] { report_design }
redirect [format "%s%s" $toplevel _area.repC] { report_area }
redirect -append [format "%s%s" $toplevel _area.repC] { report_area  -hierarchy }
redirect [format "%s%s" $toplevel _reference.repC] { report_reference }
redirect [format "%s%s" $toplevel _latches.repC] { report_register -level_sensitive }
redirect [format "%s%s" $toplevel _flops.repC] { report_register -edge }
redirect [format "%s%s" $toplevel _violators.repC] { report_constraint -all_violators }
redirect [format "%s%s" $toplevel _power.repC] { report_power }
redirect [format "%s%s" $toplevel _max_timing.repC] { report_timing -delay max -nworst 3 -max_paths 20 -greater_path 0 -path full -nosplit }
redirect [format "%s%s" $toplevel _min_timing.repC] { report_timing -delay min -nworst 3 -max_paths 20 -greater_path 0 -path full -nosplit }
redirect [format "%s%s" $toplevel _out_min_timing.repC] { report_timing -to [all_outputs] -delay min -nworst 3 -max_paths 1000 -greater_path 0 -path full -nosplit}

# STOP_HERE
```

# 結語

以上就是小弟目前所知 Design Compiler 相關的使用方法和內部的一些資訊，最後並附上我現下合成用的 script，希望對各位看倌有幫助。  
另外提一下，Cadence 的 Genus synthesis solution 我沒碰過沒辦法寫介紹文，但據一些不可靠的消息來源，據說 Genus 
現在的表現己經比 Design Compiler 好了，Synopsys 加油好嗎~~不要只會買東西~~。
