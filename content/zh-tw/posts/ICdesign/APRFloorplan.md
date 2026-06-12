---
title: "數位電路設計系列 - INNOVUS Floorplan"
date: 2026-06-11
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
---

準備好下線材料之後，這篇就開始操作 INNOVUS 進行 layout 了。  
其實這篇我是真的不確定要寫什麼，因為現在手邊沒有 INNOVUS 
可以用，除非盜圖不然沒有螢幕截圖可以用，沒圖只講步驟會很像說明文件，所以這篇就一直擱著沒寫。
<!--more-->

但總之最後還是寫了，除了步驟之外多加一些個人經驗還有名詞解釋，最後全文有點長就拆成三部分，
Floorplan、Powerplan 跟 P&R。

不過請千萬注意這裡有三點：
1. 最早寫的 [晶片的物理架構]({{< relref "chipstructure" >}}) 建議熟讀，這裡不會再重複解釋。
2. 上一篇[APR準備]({{< relref "APRmaterial" >}}) 也是，內容不會再重述，請確定你那篇的東西都準備好了。
3. 因為 layout 很多奇奇怪怪的步驟，我這篇只能涵蓋一小部分，實際操作的部分不可能看著我這篇就可以下出一顆晶片，
很多的眉角需要自己多玩幾次，或是直接 1on1 指導才能領會。
4. 個人經驗只到 40 nm，就個人所知，這個經驗大體適用到 28nm，頂多 
22nm，再往下的 16nm 進到 FinFET 之後，APR 是完全不一樣的故事。

我現在聽過的傳說可以簡稱*十億錯誤大大*，簡言之他做了 16nm 或 7nm 的 FinFET APR，做出來的 
layout DRC 跑出十億個錯誤，然後離 tapeout 只剩一個月，幸好最後在一個月內修掉十億個錯誤，順利下線。  

FinFET 目前我看我這輩子可能沒機會了，遇到問題去找有相關經驗的人問吧。

# 基本流程

首先我們先對 APR 有個基本的了解，以下是我統整 APR 大致的流程：

* Import Design/IO：讀入 design compiler 合成的 verilog code，設定 IO 位置
* Floorplan：擺上所需要的 Macro，設定 blockage
* PowerPlan：擺上 Power Ring, Power Stripe, Follow Pin
* PowerCheck：利用 INNOVUS 整合的 Voltus 進行功耗分析
* Placement：將各 standard cell 擺上 Follow Pin
* Clock Tree Synthesis (CTS)：合成 clock tree
* Route：實際將線路連接起來
* Signoff：最後的 timing check

# 記得存檔

APR 是一個耗時的流程，有時一個按鍵按下去花個幾小時也不算太奇怪，而且大部分的動作是無法復原的，所以說跑
INNOVUS 跟你玩 RPG 一樣 **最重要的就是存檔**，好過後來要再重做。  
以下是個人習慣大家參考就好，我會用開頭數字來分階段，各階段的存檔就能乖乖照順序排：

* init: 匯入檔案，設定完全域電源後的第一個存檔。
* 0 Power plan，從開始到做完所有 Power 相關的設定，包含下列階段：
  * 0Macro：擺放完 Macro
  * 0PowerRing：擺放完 Power Ring 和 Macro Ring
  * 0PowerStripe：設定完 Power Stripe
  * 0PowerFollowpin：跑完第一階段的 Power Analysis 擺上 Follow pin
  * 0Power_drcfix1：修正 INNOVUS 內建 DRC 檢測到的錯誤
  * 0Power_drcfix2：修正匯出 Floorplan 後由 Calibre DRC 檢測到的錯誤
* 1 開頭，從 Place 開始到完成 CTS
  * 1placed：執行完 placement
  * 1prects：placement 後修正完 pre-cts Timing Violation
  * 1cts：執行完 CTS
  * 1postcts：cts 後Setup time/Hold time 修正
* 2 從 Route 開始到完成剩下的 signoff 流程
  * 2routed：執行完 Route
  * 2routed_setup：修正 Setup timing violation
  * 2routed_hold：修正 Hold timing violation
  * 2signoff：透過 Tempus 做完最後的 signoff 後存檔
* Filler：插入 Filler cell、metal fill，最後一個存檔，打開這個檔案，應該什麼都不用做，匯出即得到下線要的 gds 檔。

這個存檔順序當然不是固定的，例如當初有 0Power_drcfix1 
是因為加 Power Stripe 太容易出現 DRC violation，學會使用 blockage layer 這個問題就緩解不少。  
如果是先進製程也許還需要更多階段的存檔也不一定。

# INIT

## 匯入檔案

選擇 `File` -> `Import Design`
* Netlist 選擇合成完的 *.syn.v，填入 top cell name（我不太讓他自己抓，怕他抓錯）
* Reference Libraries 選擇轉好的 macroLib
* FloorPlan 選擇上一篇寫好的 chip_top.io
* Power 填入 VDD VSS
* MMMC 選擇上一篇寫好~~或是前輩留下~~的 .mmmc 檔

## 設定電源

匯入 design 的時候，設定了兩個虛擬的全域電源，VDD 與 
VSS，現在要把實際 standard cell 在使用的電源連接到這兩個全域電源上。

點選 `Floorplan` -> `Connect Global Nets`：
* Pin Name(s) 填入 VDD，To Global Net 填入 VDD，按 `Add to List`
* Pin Name(s) 填入 VSS，To Global Net 填入 VSS，按 `Add to List`
* 選擇 Tie High，To Global Net 填入 VDD，按下 `Add to List`
* 選擇 Tie Low，To Global Net 填入 VSS，按下 `Add to List`

相同的名字會有點混淆，前者是標準元件實際的 pin name，後者是虛擬的全域電源，是上面 
import design 時設定的名字，下面有遇過幾個例子，可以幫助大家更了解這段在幹嘛：
1. standard cell 的接地用的是 GND，上述第二步的 Pin Name 要改為 GND
2. 有些 SRAM 在高階製程的命名會是 VDDCE (Core) VDDPE (Peripheral) 兩組，同時 
standard cell 還是叫 VDD，這時候第一步要做三次，Pin Name 填入 VDD VDDCE 跟 VDDPE。

如果是多電源的設計，就需要匯入 common power format (.cpf) 檔，這個目前筆者也還沒有經驗，遇到了再來寫。

## 檢查存檔

點選 `File` -> `check Design`，取消還沒做的 `Floorplan` 跟 `Placement` 
兩項，勾選 Display HTML，檢查結束就會跳個陽春的網頁給你看結果。

最重要要看的就下面這個（或是有其他的一樣嚴重的只是我還沒踩過）：
> Cells with missing timing data
{.error}

這是指有 cell 沒有時序資料，通常是 black box cell 在 
MMMC 檔中沒有成功載入 black box 的 .lib 檔，沒有這個資料到了 
CTS 就會做不下去，請務必修正再往下做。

檢查完沒問題就把 layout 存成 init，我的經驗至少會用個 3-4 次吧。  
另外可以把上述的步驟複製起來，存到 script/init.tcl，設計有修改的時候也可以直接重用。

# FloorPlan

匯入設計之後，第一步就是決定 Floorplan。

## Utilization 是什麼
Utilization 的意思，是把現有晶片的 standard cell 的面積全加起來，與實際晶片面積的比值，最高的 
1.0 就是只有 standard cell 沒有任何其他空間。

0.7 是一般的開場，如果 memory (black box) 佔比很高的話可以再低一點，前文 
[1P3M]({{< relref "1P3M" >}}) 完全沒有 black box 的設計，我自己有向上逼到 77%。  

一開始拿到新製程想熟悉整個 layout 流程，建議建議先用 0.4 這種~~浪費沙子~~很低的 
utilization rate 進行一次 layout，確定整個設定例如 clock buffer/inverter 到 
signoff 的 DRC LVS 等等都沒問題，再來壓縮面積挑戰極限。  
如果 U rate 設定太高，**通常**不會有明顯的症狀，它不會像 BSOD 一樣直接讓 APR 軟體 
crash 掉，APR 軟體也是硬頸子絕不輕言放棄，它會不斷嘗試直到試不出來為止，一般而言把 
U rate 逐漸調低是會在各階段的時候出狀況：
* 我有一次發神經， U rate 設定 0.9，在 placement 的時候就跳一堆錯誤，放不下了。
* U rate 0.85，做到最後一步的 Routing 出現 Timing violation，
ECO 無法修正，有一條非常長的 path 解不掉。
* 調到 U rate 0.8，CTS 後的 Design Rule Violation (DRVs) 的 
Capacitance, Transition 出現違反，ECO 無法修正。
* U rate 0.7 就~~謝天謝地~~一路順風做到最後。

Timing violation 出現大概就不用玩了，只能把目標 slack 值調高一點看 INNOVUS
願不願意解，input/output 可以賭看看合成時 input_delay/output_delay 有沒有可能補回這個差值。  
有 DRVs 則也是可以賭一下，看最後晶片出來是否能動，我賭過一次最後賭贏了。

## 設定 FloorPlan

選擇 `Floorplan` -> `Specify Floorplan`。  
一般來說，除非實際有要求，不就我都是用 W/H Ratio = 1，跟 
Urate 兩個值下去設定，讓 INNOVUS 幫我決定最終的寬度跟高度。  
看到寬度跟高度不是整數別強迫症發作，它的高度一定會是 M1 followpin 高度的整數倍，不能是任意值。

Core Margin 的設定請參考下一篇的 Power Ring 一節。

## 擺放 black box

black box 如果叫 INNOVUS 擺，可使用 `Floorplan` -> `Generate Floorplan` 
-> `Place Macro`，它會依照整體設計去計算 black box 最佳的位置，但我的經驗會遇到兩個問題：

1. 這步它會去動我的 IO pad，要這麼做把 
[IO 設定](https://yodalee.me/2025/05/aprmaterial/#io-%E8%A8%AD%E5%AE%9A) 
中的 place_status 改成 fixed
2. 這步會依照整體的狀況把 black box 放到晶片的中間，而我們一般習慣會把 
black box 往邊邊放，讓中間儘量是一個完整的空間給 standard cell 用。

我都不用自動的 `Place Maco`，改用 `Floorplan` -> `Floorplan toolbox`。
工具箱的介紹可參考[图形界面介绍<Floorplan ToolBox>](https://www.sohu.com/a/383153201_99933533)。  
我會使用對齊 Core 邊界，把一個 black box 靠到邊上，再依序把其他的 black box
對齊上去（必須說往邊邊放也許是人類的偏見，往晶片中心擺其實有機會更有效率也說不定）。

兩個 black box 間的距離要抓好，如果有記憶體有 Power Ring 記得要算進去，一般來說間隔 
1μm 就相當足夠（是的，在線寬只有 0.1 μm 的晶片世界 1μm 是相當大的距離了）。

擺放完 black box ，將它們的狀態改成 fixed。  
```tcl
set_instance_placement_status -all_hard_macros -status fixed
```

## blocking layer

在 INNOVUS layout 中有兩種 blockage：
* Place blockage：不要在這裡放 standard cell。
* Routing blockage：除非是一定要通過這裡（例如要接線給 black box），不然不要在這裡繞線。

在 black box 相關的設定叫 Halo ~~最後一戰系列~~，分別是 Placement 
Halo 和 Routing Halo，Halo 的設定沒有什麼定論，下面幾個原則給大家參考：
1. 一般來說，Placement Halo 1μm；Routing Halo 0.5μm。
2. 兩個 black box 放很近的，placement halo 要填滿中間的空隙。
3. 如果 black box 有 power ring，placement blockage 要把整個 
ring 都包進去；否則 INNOVUS 會在 power ring 下面放 cell，在繞線時很容易出錯。

使用 `Floorplan` -> `Edit Floorplan` -> `Edit Halo` 來編輯：
* Action 選擇 `Placement Halo` -> `All Blocks`
* 上下左右都設定為 1 並 `Apply`
* Action 選擇 `Routing Halo`
* 上下左右都設定為 0.5 並 `Apply`

如果要更精細的調控，也可以選擇 `Selected Block/Pad` 來針對各別 black box 設定 Halo 的值。

INNOVUS 有個*神奇的設計*：可以放 standard cell 的地方就會長出 follow pin。  
所以 placement halo 中間出現空隙，就會看到 INNOVUS 在中間長出一些短短的 
followpin，甚至放一些 standard cell 進去，很容易滋生 DRC 錯誤跟繞線的 timing violation。

# 結語

這章我們完成了晶片整體的 Floorplan，就像把一棟房子的格局先劃出來，牆有多厚，房間怎麼隔。
其實也不用太認真，Floorplan 用一般的數值，如 U rate 0.7 高機率都做得完，會怕晶片不動就先留多一點，
Macro 距離給個 2μm 也不會怎麼樣。  
下一章進入 Power Plan，開始幫房子拉電線囉。
