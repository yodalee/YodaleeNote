---
title: "數位電路設計系列 - INNOVUS Place and Route"
date: 2026-06-18
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
---

基本上下線的時候，要花時間操作的部分都是 floorplan 跟 powerplan，只要進到
placement 之後，就是按個按鍵，然後開始看動畫，看個段落回來看看它跑完了沒。
<!--more-->
例如最近的一次下線，看完整季的 [MYGO](https://ani.gamer.com.tw/animeVideo.php?sn=34030)
，先前的 [1P3M]({{< relref "1P3M" >}}) 的時候，則是看完整季芙莉連。

大體上來說這裡的步驟就是一直重複：
1. Report Timing，等結果
2. 如果結果有 timing violation，跑 ECO，等結果
3. 重複 ECO 直到 Report Timing 沒問題，進行下一步

大致上要做這些：
1. Placement
2. 分析 Pre-CTS setup time
3. CTS
4. 分析 Post CTS setup time
5. 分析 Post CTS hold time
6. 插入 TieHi, TieLo cells
7. Route
8. 分析 Post Route setup time
9. 分析 Post Route hold time
10. 改用 tempus 分析 Signoff setup time
11. tempus 分析 Signoff hold time
12. 用一個什麼 tool 進行 Signoff ECO

視你的設計大小，其中每一步都是上述的*點下去+看動畫+存檔*的組合，甚至去小睡一下也行，簡單來說就是：

![Unhappy layout](/images/ICdesign/LayoutUnhappy.png)

這一連串流程有幾個值得提點的地方：

1. 不要管 DRC 了，雖然 Floorplan 跑過 DRC，但開始 placement 後就會有大量的 
DRC 錯誤跑出來，這些錯誤要到 Route 後才會解掉。
2. 不要往回跑，做完 CTS 就不要跑 Pre-CTS 的 Analysis；做完 
Route 就不要跑 Post-CTS 的 ECO，INNOVUS 會直接爛掉；請關掉 INNOVUS 重新讀檔。
3. 承上，請記得存檔；如果是工作上的下線，也可以養成把 Timing Report, Placement Report
的結果給截圖存起來，最後下線前的報告會用到。

# Placement

在 placement 階段，會把 standard cell 放置到前一步畫好的 Follow Pin 上。  
INNOVUS 有一個率先推出，事後被 Synopsys ICC2 學走的功能叫
**early clock flow (EOF)**，它的故事是這樣子的：  
以往在 placement 的時候會把 standard cell 擺上去，在 CTS 的時候長出 clock tree。
但問題是 placement 把可用的空間都佔滿了，Clock Tree cell 進來發現沒空間，擺遠了 Clock Tree 長不好。  
與其這樣，不如在 placement 的時候就簡單放一下 CTS，雖然這樣 
placement 會多花時間，但省得 CTS 又跑出 timing issue 需要 ECO 解。

會提這件事是因為這會造成一個效果：Placement 後的密度會飆高，
CTS 之後反而會降低，在報告的時候是個會被質問的點。

placement 設定 placement.tcl 如下（含 early_clock_flow）：
```tcl
set_db design_process_node 90
set_db timing_analysis_type ocv
set_db timing_analysis_cppr both
set_db design_early_clock_flow true
create_basic_path_groups -expanded
```

執行 
```tcl
source placement.tcl
place_opt_design
```

# CTS

CTS 的全名是 Clock Tree Synthesis，也就是合成 
clock signal，我們在硬體實作上的一個重大假設，就是 
clock 會**同時**抵達晶片上的所有 register，而 CTS 就是由工具儘可能達到這一點。

CTS 事關晶片的好壞，像是晶片功耗主要來自於信號的切換，而最大的切換來源就是 
Clock（變動頻率 50%，真是謝囉），其功耗可以佔到晶片整體的 30% 左右。  
同時，CTS 上經過的 Cell，無論是 Buffer 或 Inverter，都是特殊設計的 
cells，縮短 Transition Time 並平衡 Rising/Falling Time，其面積比一般信號用的 
Buffer 大一圈，所以 CTS 整體的面積可以吃到晶片的 10% 左右。

想知道背後相關的技術，可以研究看看 H-tree，這個東西我在早年[蓋 Minecraft 農場]({{< relref "farm_building" >}}
)的時候曾經利用過，貼一下以前的舊圖：

![H tree](/images/minecraft/farm/ceiling.png)

H tree 是每次把晶片切成兩個區塊然後逐步切細，但 INNOVUS 似乎是切成三塊，所以算是 
H tree 的改良版，不過這有點太細節，而且只要 CTS 長得好誰管你用什麼 tree。

CTS 做完之後會產生幾個指標：
1. Clock latency：Clock 從進來到 register 的延遲有多久
2. Clock transition time：Clock 從 0->1 要多少時間
3. Clock skew：因為再怎麼完全到每個 registers 的時間絕對不會一樣，其中最快與最慢的時間差是多少。

Transition time 與 skew 的品質會影響到後續 STA 的分析，可以想見 
skew 愈大，則兩個 register 接收到的 clock 時間也會差愈多，壓縮到兩者間的週期則 
setup time 較難滿足。
Clock Latency 與 transition time 的設定則會影響 CTS 的合成，如果要求極致的 
transition time，則 CTS 路徑上的 buffer 選用最大最快，會增加功耗以及面積；如果 
transition time 太長，同樣會壓縮到 clock 周期造成 timing issue。

## CTS 設定

INNOVUS 把 CTS 的結構如樹一樣分成三段：`Top` `Trunk` `Leaf`。  
由粗至細，為了確保 clock 信號的乾淨，避免旁邊電路的串擾，有以下的手段可以使用：

* CTS 距離旁邊的電線 (spacing) 遠一點
* CTS 的走線粗一點 (width)
* 像 pad 一樣兩旁用 ground 把它夾起來

相關設定如下：

```tcl
# 請依照你的製程修改 cell 的名字
set_db cts_buffer_cells {CLKBUF*}
set_db cts_inverter_cells {CLKINV*}
set_db cts_clock_gating_cells {CLKGATE*}

set_db cts_update_clock_latency false

set_db cts_target_max_transition_time_trunk 150ps
set_db cts_target_max_transition_time_leaf 100ps
set_db cts_target_skew 100ps

create_route_rule -name cts_2w2s \
  -spacing_multiplier {metal3:metal6 2} \
  -width_multiplier {metal3:metal6 2} \
  -generate_via
create_route_rule -name cts_2s
  -spacing_multiplier {metal3:metal6 2} \

create_route_type -name cts_leaf \
  -top_preferred_layer metal4 \
  -bottom_preferred_layer metal3 \
  -route_rule cts_2s
create_route_type -name cts_trunk \
  -top_preferred_layer metal6 \
  -bottom_preferred_layer metal5 \
  -route_rule cts_2w2s
create_route_type -name cts_top \
  -top_preferred_layer metal6 \
  -bottom_preferred_layer metal5 \
  -route_rule cts_2w2s

set_db cts_route_type_top cts_top
set_db cts_route_type_trunk cts_trunk
set_db cts_route_type_leaf cts_leaf
set_db cts_top_fanout_threshold 1000
```

我想應該是不用多做解釋，執行 CTS：

```tcl
source cts_setup.tcl
create_clock_tree_spec
ccopt_design
```
## CTS 除錯

整體 CTS 的平衡可以在 CTS 結束後，使用：
* `Clock` -> `CCOpt Clock Tree Debugger`
* Debugger 的 `View` -> `Enable clock path browser` 來檢視。

把頻率往上逼到設計極限的時候，INNOVUS 會調整 CTS，透過 
useful skew 的機制把更多的時間撥給比較耗時的路徑，在 
Clock path browser 就會慢慢看到 clock tree 變得不平衡，skew 往上升。

執行 CTS 時，INNOVUS 針對 max_transition 是用 
CLKBUF 最大顆的去算的，也就是說 CLKBUF 最大顆能達到的 
transition 就這麼小了，你設更小自然更達不到，有遇到的錯誤如下：

```txt
IMPCCOPT-1209 Non-leaf slew time target of 0.150ns is too low
IMPCCOPT-1013 The target_max_trans is too low for at least one clock tree, net type and timing corner
```

往上翻可以找到如下的警告訊息：

```txt
Slew time target (leaf, trunk, top} 0.100ns (Too low; min: 0.500ns)
```

這時候就乖乖的設定為 500ps ~~或者換一套製程~~。

# ECO 怎麼跑


跑完一步之後，先分析 Timing
* `Timing` -> `Report Timing`
* Design Stage 依當下階段選擇，有 
`Pre CTS` `Post CTS` `Post Route` `Signoff` 四關要過
* Analysis Type 依序選 `Setup` 與 `Hold`，Pre CTS 因為還沒有 
Clock Tree 所以沒有 Hold 可以分析~~過四關斬七將~~

執行完後，在終端機看一下是否有 Timing violation，有的話開始進行 ECO

* `ECO` -> `Optimize Design`
* Design Stage 依照現階段選擇，記得已經過了那階段就不要重跑
* Optimization Type 選擇 `Setup` 或 `Hold`，其實可以兩個一起跑只是我也沒試過
* Incremental 與選擇 Setup/Hold 那種完整的 ECO 是互斥的，詳見下述
* Design Rules Violations 中的 `Max Cap` `Max Tran` `Max Fanout` 只要有違反就選擇

由於 ECO Timing Violation 是最優先，它背後的順序觀察是這樣：
1. 修 Timing
2. 修 DRVs
3. 如果 Timing 又修壞了，那就再把 Timing 修好

第三步存在的關係，有時候會出現 DRVs 怎麼樣都無法修復的狀況。  
這裡有一個奇怪的小技巧，不用一直跑 Setup/Hold，輪流跑完整的 ECO 與 
Incremental 的 ECO，意外比較容易同時修好 Timing Violation 與 DRVs。

# Route

到這裡真的就沒啥好講的了，直上實際操作，第一步先插入 Tie High / Tie Low cell：
* `Place` -> `Tie HI/LO` -> `Add`
* `Select` 選擇 High Low  cell
* `Mode` 中可以設定插入的參數，一般的參考值 
`max_distance` 100，`max_fanout` 16，但我一般都選擇不設定

開始 Routing

* `Route` -> `NanoRoute` -> `Route`
* 勾選 `Optimize Via` 跟 `Optimize Wire`
* End Iteraton 選 `default`
* 勾選 `Fix Antenna` `Insert Diodes`；Diode Cell name 填入製程提供的 ANTENNA cell
* 勾選 `Timing Driven` `SI Driven`

按 OK 就可以去睡了，這個會跑很久；跑完可以放大看看細節，
看看點與點是怎麼連起來的，這麼精細而複雜的結構，看了還真有種異樣的美感。

Route 進行中，INNOVUS 會開始收尾把 DRC 錯誤都解決掉，如果你的 
layout 在 Route 結束後還有錯誤，就需要檢視一下 Floorplan 是不是有需要修正的地方。  
例如說過不少次的：black box 沒劃 placement halo，其 power ring M2 蓋在 
standard cell 上，怎麼繞線都無解，就會在 Route 結束後看到 DRC 錯誤。

# 收尾匯出

> 在這裡正常來要搭配波形檔進行一次動態的功耗分析，不過一樣我們先跳過。
{.warning}

完成 signoff timing check 之後，剩下一些收尾工作：

## 填入 Filler Cell

Filler cell 是指 standard cell 中間的空隙部分，填入 dummy cell

* `Place` -> `Physical Cells` -> `Add Filler`
* `Select` 把 X1, X2 … X64 所有寬度的 Cell 都選起來
* OK 插入 Filler Cell

## 填入 Dummy Metal

Dummy Metal 是要讓金屬層的密度能符合製程的限制，
這一步可以跟你上頭整合的單位確認，不一定是你這裡要做：

* `Route` -> `Metal Fill` -> `Setup`
* 設定每層金屬目標的 `Max Metal Density`，DRC 上限通常是 70，一般設 40-50 就足夠了。
* `Route` -> `Metal Fill` -> `Add`
* 取消 Tie High/Low to net(s)；Timing Aware 選 
`Critical net from Timing Analysis` ，`Slack Threshold` 輸入 0.1 到 0.2 皆可
* OK 插入 Metal Fill

加入 dummy metal 應該會增加金屬間的電容，導致 timing 受到影響，
INNOVUS 會確保（好吧至少你相信它）影響的量級不超過 slack 值。

## Final Check

三條檢查應該都跑出沒有錯誤：

* `Check` -> `Check DRC`
* `Check` -> `Check Connectivity`，取消 `DanglingWire (Antenna)
* `Check` -> `Check Process Antenna`

## 匯出 .sdf

直接操作，執行以下的 script 

```tcl
# write_sdf.tcl
# source write_sdf.tcl
write_sdf CHIP.sdf \
  -max_view AV_func_max \
  -typical_view AV_func_max \
  -min_view AV_func_min \
  -map_removal -recompute_delaycal
write_netlist CHIP.v
write_netlist -include_pg_ports CHIP_pg.v
```

其中 CHIP.sdf CHIP.v 用於 post-layout simulation。  
CHIP_pg.v 包含了 power/ground pin，用於 LVS。

## 匯出 .gds

這裡會用到一個 streamOut.map，負責把 INNOVUS 的 layer 轉譯到 
gds layer，檔案這個我寫過，但檔案已經流失了…所以暫時略過。  
standardcel.gds hardmacro.gds 在 PDK 與 hard macro 供應商應該要提供。  

```tcl
# write_stream.tcl
write_stream CHIP.gds -map_file streamOut.map -lib_name DesignLib 
  -merge { \
    standardcell.gds \
    pad.gds \
    hardmacro.gds \
  } \
  -uniquify_cell_names -unit 2000 -mode all
```

CHIP.gds 就是最終 tapeout 要送出的 layout，在送出前要經過最後的 
signoff 步驟，就請參考（其實很早之前就寫完發出來的）
[Signoff 章]({{< relref "signoff" >}})的說明啦。
