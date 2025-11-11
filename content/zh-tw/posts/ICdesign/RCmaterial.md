---
title: "RC Extraction 設定"
date: 2025-09-29
categories:
- ICdesign
tags:
- ICdesign
images:
- /images/ICdesign/RCmaterial.png
---

> 當你身處戰國時代，周遊列國就是必要技能

在先前的 [design contraint]({{< relref "designconstraint">}}) 與 
[design compiler]({{< relref "designcompiler" >}}) 時都有提過，在晶片中會檢查每條 path - 
也就是每組 register 間的 Delay 都能符合 Timing Constraint，這項檢查是重中之重，如果 
Timing Constraint 達不到，晶片就只能降規格執行。

<!--more-->

在 design compiler 時，這個數值只包含邏輯閘本身的延遲，並不包含實際佈局後的線長與連線的物理效應。  
這也是為什麼在 synthesis 的時候，如果指定修正 hold time issues (script 加入 set_fix_hold)，
design compiler 可能會插入大量的 buffer，因為對 design compiler 
來說連線的延遲並不存在，只要沒有邏輯閘的 register 都需要修正 hold time。  

加上這個選項缺點包括延長合成時間、造成 design compiler 高估功耗等；
這些 buffer 在實際 APR 時，因為有了連線的延遲又會被移除，等於是白做工。  
儘管大廠如 Synopsys 的 Fusion Compiler 有嘗試把 synthesis 與 APR 兩步整合在一起，讓合成時能看到實際 
layout 的位置資訊，在 synthesis 階段能取得的仍然只是預估性的時序。

# RC extraction 是什麼？

隨著設計進入 Place & Route，訊號延遲就能夠考慮實際的金屬走線與相鄰線路的耦合電容等物理因素。  
這時就需要透過 RC extraction，萃取每條連線上的電阻與電容值，由寄生參數計算出 layout 
上每條路徑的延遲，再將延遲送進時序分析工具如 Synopsys 的 PrimeTime 或 Cadence 的 Tempus
，完成最後的 Signoff 流程與靜態時序分析 (STA)，確保晶片在考量所有寄生效應後還是能達到時序目標。

透過 STA 工具會得到最終結果 spef file (Standard Parasitic Extraction Format)。  
spef 格式是 IEEE 標準，可參考同一個人的 blog [understanding SPEF](https://ileonsun.github.io/understanding-spef/)。  
spef 可以匯入 layout 後模擬，確保在真實的延遲下晶片仍能正常工作。  
可以想見，如果沒有這步，我們就無法在製造前模擬 layout 的延遲，也就無法完成
 Timing Constraint 的分析。

由於 RC 萃取的重要性，各家公司都有提供 RC 萃取的解決方案，包括：
* Synopsys [StarRC](https://www.synopsys.com/implementation-and-signoff/signoff/starrc.html)
* Cadence [Quantus QRC](https://www.cadence.com/en_US/home/tools/digital-design-and-signoff/silicon-signoff/quantus-extraction-solution.html)
* Mentor [Calibre xACT](https://eda.sw.siemens.com/en-US/ic/calibre-design/circuit-verification/xact/)，或叫 xCalibrate

基本上這部分我沒那麼熟，不確定是哪一家佔了最大的比例，總之，故事就從這裡開始。

會影響 RC 值的參數如走線材料(通常是銅)的阻值與厚度；走線之間填充的介電質是什麼？要用的製程有幾層金屬？  
真正知道的人是晶圓廠，因此要做晶片要先跟晶圓廠取得製程的 PDK，PDK 內就會有製程 RC 萃取所需的參數檔。  
而 EDA 三巨頭間三國鼎立（誰是魏、誰是吳、誰是漢呢XD），三家互無法一統天下，晶圓廠也不是家家都口袋麥可麥可，自然不會每家工具的資料都支援。

以上篇 [1P3M]({{< relref "1P3M" >}}) 的狀況來說，我拿到的是由 Synopsys 用的 itf 檔，但我熟悉的工具是 
Cadence 的 INNOVUS，整合了 QRC 的 INNOVUS 在 mmmc 設定需要 .tech 檔和 .CapTbl 
檔，於是就有了這篇，先介紹一下 RC extraction 中所需的各種檔案，以及沒有的話要如何在不同家工具間轉換。

當然啦，我自然也不是全部的工具都用過，只能記錄我跑過的流程，或是參考網路上的筆記進行整理，如果有沒記錄的流程就歡迎大家補充了。

# 原始格式

叫原始格式其實有點怪怪的，因為內容其實不原始，這裡是指：晶圓廠如何提供製程資訊給 EDA 工具？

這類檔案記錄的如：
* 層間填充物的介電系數、厚度與層數
* 電容隨溫度變化的模型
* 製程如何影響電容值
* 不同寬度與厚度的單位電阻
* 電阻值隨密度與寬度的變化參數
等等。

各家用的格式如下：
* Synopsys .itf 格式 (Interconnect Technology Format)
* Cadence .ict 格式 (InterConnect Technology file)
* Mentor .mipt 格式 (Mentor Interconnect Process Technology )

目前網上只有 itf 的檔案格式有解析 [understanding ITF](https://ileonsun.github.io/understanding-itf/)
，ict 與 mipt 檔案格式目前沒有公開。  
但是，如果你手上有 ict 或 mipt 檔的話，可以用文字編輯器打開，明碼呈現應該是滿好懂的。

# 原始格式互轉

由於晶圓廠可能只提供一家的檔案（例如我這次拿到的製程就只有 .itf 檔），為了搶市佔，三家 EDA 
廠多少都有一些提供一些工具，能把一家的原始格式轉成另一種。  
查詢的結果，都只找到從 itf 變 ict 與 mipt 的方法，反向則沒有。  
如果依照我問 AI 工具的整理結果：

> 最早出現 / 商用化最早的：Avanti 的 Star-RC（後來成為 Synopsys StarRC）。  
> Avanti 在 1990s 就已經有 Star-RC 產品（1999 年可見到 Star-RCXT 的公開報導），後來 Avanti 被
> Synopsys 收購（交易在 2001–2002 年間完成），StarRC 成為 Synopsys 的產品線之一。
> [EDN+1](https://www.edn.com/avantis-new-star-rcxt-engine-speeds-time-to-market-and-ensures-timing-convergence-for-vdsm-designs/)

那麼的確有可能 StarRC 在這方面最早建立了競爭優勢成為 de facto standard，以致於晶圓廠普遍支援 StarRC 
訂的 itf 格式，但我沒有證據就是。

## Synopsys itf to Cadence ict

使用 innovus 下 voltus/gift 內的執行檔 `itf_to_ict`，路徑在 `INNOVUS/share/voltus/gift/bin/itf_to_ict`：
```bash
itf_to_ict *.itf *.ict
```

## Synopsys itf to Mentor Mipt

參考討論區 [mipt文件如何转化为itf文件](https://bbs.eetop.cn/thread-967787-1-1.html)
```
xcalibrate -itf2mipt2 itf_file 
```
會生成 out.mipt。

# 查表檔案與 RC extraction

上述介紹的是原始格式，一般工具在計算 RC 的時候不會直接使用這類檔案，因為每看到一條線都要重新解析如 M1-M2 
中間有多少層介電質，重新計算太費工。

在實際的 RC extraction 中，工具會先將資料轉為表格，依照執行條件先算完 RC 值，RC extraction tool 
會利用查表的方式計算設計中的寄生電容、電阻，就能省去大量的計算時間。

下面整理各家的查表格式，以及如何從原始格式轉換為查表格式；這個轉換比較花時間，
而且愈先進的製程檔案就愈複雜會轉愈久，因此有兩點建議：
1. 各工具或多或少都有多核心選項，人生苦短能開多少就開多少，電腦能換多核心的就換多核心的，~~公司不讓換電腦的就換掉公司~~
2. 接到工作請立即檢查所需的檔案是否提供，沒有就趕快轉，不然這裡變瓶頸會卡死後面的 layout 工作。

作為參考，下面的測試我用的機器記憶體 32 GB，CPU 是 Xeon Platinum 8268 @ 2.9 GHz 共 16 
核心，轉換的都是 3 層金屬的製程。

## Synopsys

### 1 .nxtgrd

StarRC 抽取寄生參數所用的查表檔案，用 StarRC grdgenxo 從 itf 生
```bash
grdgenxo *.itf
```
這步很花時間，可參考[讓 grdgenxo 使用多核心](https://blog.csdn.net/m0_61544122/article/details/146949384) 新增 config file。
```bash
$ cat config
NUM_CORES: 16
GRD_DP_STRING: list ssh localhost:16
$ grdgenxo -dp_config config *.itf
```
**耗時 7 分 50 秒**。

### 2 .tluplus

Synopsys APR 工具 ICC2 用的電阻電容查表檔案，也使用 StarRC 工具 grdgenxo 生成。

```bash
grdgenxo -itf2TLUPlus -i *.itf -o *.tluplus
```
使用這個選項的時候不能用 dp_config，不過在上步轉 .nxtgrd 檔時，會同步轉出 tluplus 
的前置檔，下列的指令就只是匯出檔案，毫秒內就做完了。  
就算沒有先跑過 .nxtgrd，itf 轉換 tluplus 的時間也相對快，**需 30 秒左右**。

### 3 反轉 .itf 檔

grdgenxo 有能力把轉換 nxtgrd 檔反轉回 .itf 檔~~反轉術式~~，原因是 itf 轉
 nxtgrd 的時候會把原始的 itf 用註解的方式寫在 nxtgrd header 內：
```bash
grdgenxo -nxtgrd2itf -i *.nxtgrd -o *.itf
```

## Cadence

Cadence 的查表檔案有兩個

### 1 .tch

Quantus technology files，一般副檔名用 .tch，
從 ict 生出 .tch 和 .CapTbl，使用 Cadence Quantus Extraction (EXT191) 下的 Techgen：

```bash
Techgen -cell -multi_cpu 16 -plan *.ict
Techgen -cell -parallel -autoconcat *.ict *.tch
```
這個爆幹久而且還不支援多核心，三層金屬轉檔就要**6-7 小時**，難以想像先進製程要轉多久。  
本設定參考 [how to genrate .tch file](https://www.edaboard.com/threads/how-to-genrate-tch-file.249128/)

### 2 .CapTbl

使用 innovus 下的 generateCapTbl，也是要花一點時間計算外插的 capacitance table
，一樣不支援多核心大概需時 **1 小時**

另外，這個轉換需要製程基礎參數的 .lef 檔：
```bash
generateCapTbl -lef *.lef -ict *.ict  -output *.CapTbl
```

## Mentor

### rules.R rules.C

Mentor 所用的參數檔為 rules.R 和 rules.C 兩種，看名字就知道分別對應電阻與電容的萃取，使用 xcalibrate 生成
```bash
xcalibrate -exec -turbo 16 *.mipt
```
實際轉換**4 分鐘**。

# 總結

如果使用了多核心，基本上準備檔案都是分鐘等級的事，除了 Cadence 家的 Techgen 與 
generateCapTbl 無法用多核心，會需要數小時不等的時間來進行轉檔。  
老實說都 2025 年了還不支援多核心實在是有一點點落漆呀~~Cadence你加油好嗎~~。

我想就用一個表與一張圖總結一下吧。

| 廠商 | 原始格式 | 查表格式 |
|-|-|-|
| Synopsys (StarRC)       | .itf           | .nxtgrd <br /> .tluplus   |
| Cadence (QRC/Quantus)   | .ict           | .capTbl, .tch      |
| Mentor (Calibre xRC/xACT)| .mipt         | rules.C rules.R    |

轉換示意圖：

![RC format and the translate tools](/images/ICdesign/RCmaterial.png)