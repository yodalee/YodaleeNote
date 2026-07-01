---
title: "數位電路設計系列 - INNOVUS PowerPlan"
date: 2026-06-17
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
latex: true
---

終於進到 Power Plan 了，這部分就像幫你的房子接電線，從供電的 pad 一路到最底層的 standard 
cell，總共要做好 Power Ring, Macro Ring, Power Stripe 與 Follow Pin。
<!--more-->

# Power Ring

通常來說，Power Pad 會從 M1-M3 的層數供電，因此 Power Ring，一般會停在 M4 或 
M5，以免擋到 Pad 進來的走線。
Power Ring 的寬度一般我會選 3-4 um，看晶片功耗走多組的 Wire Group。  
製程的金屬會有個密度的限制，一般是 30% - 70%，Power Ring
空隙寬度用線寬的一半，這樣整體的金屬密度是 66%，剛好落在 density check 上限的 70% 之內。

以我之前的實作來說，Power Ring 寬度 3，間距 1.5，用 3 組 Wire 
Group，與晶片 Core, Power Pad 間距 1.8，那麼設定 Floorplan 時，Core to IO Boundary
的設定就要多出：  
$3 \times 6 + 1.5 \times 5 + 1.8 \times 2 = 29.1 $  
取整數的話就選 30，這個數字很常用，所以記在 A4 上。

### 實際操作

* `Power` -> `Power Planning` -> `Add Ring`
* Net 填入 `VDD VSS`
* 依序從上到下加入 Power Ring，設定 Top, Bottom 為水平金屬層；Left, Right 為垂直金屬層。
* `Advanced page`，勾選 `Wire group` 和 `Interleaving`，填入 Wire Group 組數。

有了 Power Ring 之後就能連接 Power Pad：

* `Route` -> `Special Route`
* Net(s) 填入 `VDD VSS`
* SRoute 選擇 `Pad pins`
* `Advanced Page` 的 Pad Pins 項目設定 `Number of Connections to Multiple Geometries` 為 All
* `Via Generation` 分頁，`Make Via Connections To` 選擇 `Core Ring`

# Macro 電源

一般來說 Macro 有以下幾種供電的方式：

## Power Ring

這種 black box 外面自帶兩圈 Power Ring，分別是 VDD VSS，通常會選擇直的是 M2 橫的是 M3。  
這種供電最簡單，設定 Power Stripe 時垂直的 M4 蓋過 
black box，INNOVUS 就會自動連接 M4 到橫向的 M3 了。

一樣用 Minecraft 蓋一下，分別從左和右照一張，內圈的藍棕和外圈的紅色 Macro Ring
，分別走在 M2 M3 的 VSS VDD；我們直接用綠色 M4 的 Power Stripe 蓋上去，就能完成供電。

![Macro Ring 1](/images/ICdesign/MacroRing1.png)

![Macro Ring 2](/images/ICdesign/MacroRing2.png)

## Power Rail

Power Rail 指的是 black box 的頂層會有一條條金屬，其中 VDD 
VSS 交錯，通常會是 layout 上走垂直的 pin，例如 M4。  
連接方式稱為 `Over P/G pin`，會在上面連接一條條的 M4 接到 VDD/VSS，為了阻擋 
Power Stripe 延伸到 black box 之外，要加上 Macro Ring（這倒是說明為什麼 black box 要靠邊角放）。

如下圖所示，M3 藍色與 M2 棕色的是 Macro Ring，中間的紅、棕、紅三條則是 P/G pin
，P/G pin 由 M2 接出來被 M3 的 Macro Ring 擋下。

![Macro P/G pin](/images/ICdesign/MacroPGPin.png)

## Power Pin

Power Pin 指 black box 上面有 VDD/VSS 的接點，這種就用 
INNOVUS special route (`Route` -> `SRoute`) 接線出來；與 Power Rail 一樣，需要加上 
Macro Ring 把接線給擋下來。  
沒遇過就不畫了。

### 實際操作

加入 Macro Ring 的方式與 Core Ring 相同：
* `Power` -> `Power Planning` -> `Add Ring`
* Ring Type 選擇為 `Block ring(s) around`，選擇 `Each selected block and/or group of core rows`
* 在 `Advanced Page` 指定要加入的形狀

如果是 `Over P/G Pin` 形式的話，可使用：

* `Power` -> `Power Planning` -> `Add Stripes`
* Net 填入 `VDD VSS`
* `Set Pattern` 選擇 `Over P/G pins`
* 在 `Mode` Page，`Extend to closest target` 選擇 `Ring`；
`Top stack via layer` 為 Macro Ring 上一層

即可加入 P/G pin stripe。

# Power Stripe

Power Stripe 建議做 M4 之上，M2, M3 留給 Routing，兩條又大又粗的 Power Stripe
會嚴重干擾 Routing 的走線，特別是[金屬層少的時候]({{< relref "1P3M" >}})，所以在 
1P3M 的情況下我就只稀疏的放入 M3 的 Stripe。

新手做晶片最容易疑惑的地方，最大的問題就是**所以我的寬度、距離怎麼設…？**  
答案是：**我不知道**  
有一次我把 M4 寬度從 0.44 降到 0.40，結果在 M4 接 M1 的*每一個* via
都報 DRC error，最後 Floorplan 直接重做。  

下面是之前下線時實際用過的數字，不知道怎麼來的但總之它會動，可以針對你的功耗與製程的 DRC 去進行微調。

|Metal Layer| Direction | Width | Space | Set to Set | Start | Stop |
|:-|:-|:-|:-|:-|:-|:-|
|M4|Vertical|0.44|0.27|11.2|4.375|5.375|
|M5|Horizontal|0.44|0.27|14|5.375|5.375|
|M6|Vertical|0.44|0.27|14|20|20|
|M7|Horizontal|0.8|0.5|40|20|20|
|M8|Vertical|0.8|0.5|40|20|20|

這個表實在太重要了，也會記在我的 Layout A4
紙上，行列的部分用原子筆，**數值的部分用鉛筆**，我的經驗為了要閃一些 Macro 或是 
Power Pad，通常 start/stop 是更動最頻繁的地方，也是因此有上面那些 4.375 一個不合群的數字。  

### 實際操作
* `Power` -> `Power Planning` -> `Add Stripes`
* Net 填入 `VDD VSS`
* 設定 `Layer` `Sets-to-set distance` `Width` `Spacing` `Start` `Stop` 等參數
* 在 `Mode Page` 設定 `Top stack via layer` 為上一層，`Bottom stack via layer` 為下一層。
例如在加入 M5 Stripe，則 Top 設 M6 Bottom 設 M4。
* Allow Jogging 取消勾選 `Pad/Core ring connection` `Block ring connection`

# Follow Pin

Follow Pin 的高度與寬度都是預先設定好的，所以這沒什麼好講的：

### 實際操作
* `Route` -> `Special Route`
* Net(s) 填入 `VDD VSS`
* SRoute 選擇 `Follow pins`；`Layer Change Control` 取消 `Allow jogging`
* `Via Generation` 分頁 `Top Stack Via Layer` 請選擇**最低一層**的 Power Stripe，我這次是 M4
* `Via Generation` 分頁 `Make Via Connections To` 選擇 
`Core Ring` `Stripe` `Block Ring` `Block Pin`

接續先前提過的那張 A4 紙，下半部就是為了 Power Plan
準備的，請記得改動的機會所在多有，所以記錄**一定要用鉛筆**。  
這張混合了某次下線的 pin 腳跟另一次的製程資訊，鉛筆填的就是可能會變動的部分，
原子筆的部分則是大體上不會動的。

![A4 Planning](/images/ICdesign/A4Planning.jpg)

# DRC check

> 在這裡正常來說要跑一次 Rail Analsis 進行功耗分析，不過這部分要講可以多寫一篇文章，暫時先跳過。
{.warning}

完成 FloorPlan 先進行一次 DRC 與 connectivity check。

## Connectivity Check

* 選擇 `Check` -> `Check Connectivity`
* Net Type 選 `Special Only`
* Net 選 `Named` 並填入 `VDD VSS`
* 取消 `Dangling Wire (Antenna)`

檢查是否有 violation，有就表示有 VDD/VSS 短路了。

## INNOVUS DRC Check

`Check` -> `Check DRC`，把相關的錯誤修正掉。  
在 FloorPlan, PowerPlan 中出現的錯誤，最容易報錯的地方有幾個：

1. 在 Power Stripe 與 Power Pad 畫出 Pad Pin 的地方，兩者在 Power Ring 的位置交錯的地方。
2. 與上相同，在 Follow Pin 與 Pad Pin 交錯的地方，簡而言之 Pad Pin 就是萬惡之源
3. P/G pin 與 Power Stripe 在 Macro Ring 上相交錯的地方

像是 Via 太接近 (Cut_Spacing)、Via 重疊 (Cut_Short)、或是兩排金屬太過接近 (
parallel run length spacing)，諸如此類。

## Calibre DRC Check

由於 INNOVUS 的檢查是要求快，讓工具可以快速知道這樣畫有沒有問題，其規則與檢查機制不會那麼完整。  

請參考 [Signoff篇]({{< relref "signoff" >}}) 匯出 .gds 檔，使用 Calibre 等 
DRC 工具進行檢查，修正所有 DRC 錯誤。

# 延伸內容與結語

這篇限於篇幅與緊貼主題，有部分的內容我略過不提，大致有下面幾個：

第一個是如何使用 Blockage 輔助與 DRC 除錯。
如果完全照著上述的步驟實作，在 DRC Check 那步一定會超級痛苦，會噴出超多上述會發生的錯誤。

跟 Pad Pin 有關的，有個方便的解法是在 Pad Pin 的位置直接上 Blockage，讓 
Power Stripe 與 Follow Pin 不要延伸進 Power Ring 與 Pad Pin 交錯，就能輕鬆避掉許多錯誤。  
Macro Ring 上的 Via 則有一些操作方法，可以很快的處理掉 DRC Error，
但這方法網路上找不到，手邊沒 INNOVUS 我沒辦法寫怎麼操作。

----

第二個是 Power Analysis 的部分。

畫完 PowerPlan 之後，理應用 INNOVUS 整合的 Voltus 進行 Power Analysis 與 
IR Drop Analysis，確認 Power Ring 跟 Power Stripe 足夠承載晶片核心需要的電流不會造成明顯的壓降。  
其實跟真的在蓋房子也沒什麼兩樣，拉完電線看看線夠不夠粗，不夠就準備火燒厝，
這部分要寫的話大概足夠寫一章，我自己也還沒完全學會，
都是套用別人幫忙弄好的設定，就先略過。  

解完所有的 DRC 錯誤之後，晶片的 FloorPlan/PowerPlan 就完成了，先存個檔，準備進到 
P&R，後續就是操作上比較枯燥的一章了。
