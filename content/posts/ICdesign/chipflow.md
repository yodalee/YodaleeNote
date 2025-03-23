---
title: "數位電路設計系列 - 下線流程概述"
date: 2024-04-29
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
---

接續我們上一篇的[前言]({{< relref "introduction" >}})，今天我們就先來看看整個下線流程概述，
這篇文的目標是讓大家對下線流程有一定的了解，後面的文章才好懂。  
本來計劃是前言打完就趕快發這篇，但我想在 11 月下線的晶片回來，確定下線成功符合當初設計再來繼寫後面的文，
這樣底氣才夠講話才能大聲……沒錯一定是這樣，絕對不是我下班之後回家都在耍廢的關係。

<!--more-->

首先要了解晶片設計，首推的就是阿嬤都能懂的晶片設計，不但有[線上 pdf](https://m105.nthu.edu.tw/~s105062901/ppt/RMaKnowsICDesignFlow.pdf)
文件還錄了 Youtube 影片，真是貼心，~~他都講完了我要講什麼~~。

{{< youtube kYUhk6FQwBc >}}

這篇文我們就再把這個流程概述一次，同時加註一些我個人所知的產業概況，大家就加減看一下，
如果有錯誤的話煩請不吝更正（就我的經驗是沒有人會更正就是了）：

大方向來看，我大致把下線的流程分為下列幾個階段：
* HDL
* simulation
* synthesis
* post-synthesis simulation/LEC
* APR
* Post-layout simulation
* DRC/LVS verification

每個階段都是大量的軟體工作，沒錯，以數位電路的複雜度來說，每一個階段都必須要電腦輔助設計，
所謂的硬體工作其實是軟體工作，硬體工程師也是一種軟體工程師。  
據說早年 EDA/CAD 還沒開始發展時，最早的 Intel 處理器的 layout 是用手繪的，就跟當年登陸月球的火箭一樣，
想想也很自然，畢竟你根本就沒電腦是要跑什麼 EDA？  
但現在時代不同了，沒電腦你什麼東西都做不出來，主要的電子設計自動化軟體都掌握在三家廠商：
Synopsys、Cadence、Siemens 手裡，下面各個工序會不斷提到這三家，也是台灣許多硬體廠每年必付軟體稅的對象。

各階段詳述如下：

# HDL
首先是從要做的 spec 開始設計 HDL，現在業界流行的就只有兩個 VHDL 和 verilog，兩派各有流行的地區和擁護者，
大致上來說 VHDL 在國防和航太用得比較多，流行地區是歐洲；
verilog 則在產業界上用比較多，流行地區是美國（可能因此還有亞洲）。  
身為 implementer 的我們不用想太多，選自己熟悉的就可以了。

# Simulation
模擬工具我所知比較知名的有 Synopsys 的 vcs 及 Cadence 的 ncverilog 與 xcelium，
我自己測過 vcs 與 xcelium 都支援 systemverilog，在工具上已經沒有理由不用 systemverilog 了。

值得提到的是在後續的 layout 流程中，Cadence Innovus 為了拉抬自家的軟體，
在功耗模擬上會使用 xcelium 才能夠生成的 toggle counter format TCF 檔案格式，我還沒找到 vcs 能產生此設定的方式，
如果後續選用 Innovus 作為 layout 軟體，可以將這點納入考量。

開源工具上測試過 iverilog 與 verilator 兩款，iverilog 使用簡單，verilator 則是安裝和使用都更麻煩一些，
但兩者的模擬速度就不是同一個檔次的，verilator 在模擬至少比 iverilog 快 10x 到 100x，同時也支援 systemverilog。  
此外 iverilog 是模擬 Verilog 的實作，如 Verilog 的 #1 #0.1 等實際時間的 delay 是可以模擬的。  
相對的 verilator 是去分析 Verilog 中 register 與 combinational circuit 的邏輯，將它轉換為模擬的 C code，
產生的模擬是以 Verilog 的 clock 為基礎，clock 的賦值會觸發更新的邏輯，但 #1 等實際時間的 delay 就無法模擬了。  

# Synthesis

synthesis 這步會把我們寫的 HDL 合成為實際電路使用的各式邏輯閘，在使用 FPGA 驗證我們的設計時，所做的步驟也是 synthesis。  
先來說 FPGA，目前市場上就 Xilinx 和 Altera 兩家市佔最高，Xilinx 吃肉、Altera 喝湯，剩下的舔碗療飢，
分別被 AMD 和 Intel 收購。  
使用 FPGA 必要的就是各製造商獨門的軟體，Xilinx 是 Vivado，Altera 是 Quartus，
這類的合成是將 HDL 轉為 FPGA 中提供的 look up table (LUTs) 與 flip-flip (FF)，還有如 BRAM, DSP 等元件。

在製作晶片的時候使用的合成則是將 HDL 轉為晶圓廠提供的邏輯閘，我下線時使用的是 Synopsys 的 Design Compiler，
這是 Synopsys 的起家厝，應該也是目前市佔最高的 synthesis tool；Cadence 則有 Genus Synthesis tool 打對台。

# post-synthesis simulation/LEC

轉為邏輯閘後，可以選擇要不要過 post-synthesis simulation 及 logic equivalence check (LEC) ，
目前我這步沒做 LEC，只靠 verilog 的 testing。  
由於已經轉為邏輯閘了，這步的模擬除了 synthesis 產出的 verilog 之外，還要配上 synthesis 產出的
standard delay format (.sdf) 檔，兩者一起模擬才會得到正確結果。

# APR

完成 synthesis 後就可以準備 layout 了，APR 指的就是 Auto Place and Route，主要工作包括：
* 安放晶片的 pad，如果電源、接地、信號線等的 IO pad。
* 把電源與接地從晶片的 pad 連接到晶片核心 core。
* 把邏輯閘放到實際的位置。
* 依照合成結果連接邏輯閘的信號線。
* 合成 Clock Tree，讓每個邏輯閘如模擬般可以接近同時收到 clock。

這些工作現下都有專用的 EDA 軟體來完成，我下線時使用的是 Cadence 的 Innovus；Synopsys 則有 ICC2。

# Chip verification

layout 後，整個電路的物理架構也就完成了，為了確保製作晶片的巨大成本不會打水漂，還會有很多工作可以做，包括但不限於：

## Design Rule Check DRC：
檢查 layout 是否符合晶圓廠定義的 design rule，例如線寬是否太細？太粗？兩條線是不是太近？  
隨著製程的進步，Design Rule 也愈變愈麻煩，就我個人所知，從基本製程到先進製程，規則數量可能從幾百上升到數千，
各種亂七八糟混來混去的規則，檢查的時間也大幅的拉長。如果你覺得你的電腦很快，
那就試著跑跑看 DRC，你就會想換最新的旗艦 CPU 了。  
如果 APR 做得好的話，其實 DRC 不太會有大問題，個人是遇過出現幾個個位數的線繞不出來，最後要用手修 layout 解的，
但通常這不會發生，畢竟數位 IC 都是幾萬個電晶體，真亂畫幾千個 error 怎麼可能手動解？

## Layout Versus Schematic LVS：
比對 Layout 與邏輯閘的 schematic，兩者是否符合，背後的問題簡單說起來就是：
從 schematic 建出一張圖，與 layout 與的另一張圖，兩者是否為同構 isomorphism。

和上面的 DRC 一樣，就數位 IC 的角度來說，APR 工具已經幫你畫好 layout 了，
跟我做類比電路的時候辛辛苦苦畫 LVS 比起來，數位的 LVS 都是秒過的程度，不用擔心。  
那能不能跳過這個檢查呢？  
還是不行，就算 APR 畫完，還是可能做一些細微的修改，例如把一件元件的文字拉進晶片內部，
畫一些標記等等，如果一不小心把線接在一起，就有賴 LVS 來檢查了。

以上 DRC 與 LVS，就個人所知領導品牌是 Siemens 的 Calibre，signoff 都是用 Calibre 做最終檢查；
其他如 Synopsys, Cadence 雖然都有在推自己的 DRC, LVS 工具，但都無法取代 Calibre 成為最後一步。

## Parasite EXtraction PEX 與 Gate-level simulation
PEX 是在完成 layout 之後，使用工具抓出元件與接線中間的寄生電阻與電容，生成含寄生元件的 spice 檔。  
這個 spice 檔以使用模擬器進行 Gate-level simulation，一般來說這步非常的花時間，
本來以小時計的模擬可能變成以天計，我個人到目前為止是還沒執行過 Gate-level simulation，這部分就跳過。  

## Timing analysis：

layout 完之後，所有走線的延遲都確定了，再次產生 sdf 檔確認晶片的時序都有達到要求。  
這塊業界的標竿應該是 Synopsys 的 PrimeTime，我因為 layout 使用的 Cadence INNOVUS 已整合 Cadence 的 Tempus，
最後晶片也有量到，就不用 PrimeTime 了。  
套用一下水星的魔女的話就是：

> 晶片不只靠製程的性能，不是只靠 EDA 與設計者的技巧，但是，結果本身就是唯一的真相！

## Power Simulation：
同樣在走線都擺好之後，也能依照模擬時的資訊，計算出晶片整體的功耗，並搭配 layout 的走線寬度等等，
確認電源從 pad 一路下到電晶體，壓降都不會高到無法承受。  
這步我同樣是使用 INNOVUS 整合的功耗分析，搭配模擬產生的 vcd 或 tcf 檔進行功耗分析；
競爭工具有 Synopsys 的 PrimePower ，但我沒用過無從評論。  

# PDK

上述所有下線的步驟，都有賴委託下線的半導體製造商 foundry 提供的 Process Design Kit (PDK) 來完成，
PDK 會提供各步驟軟體所需要的資訊，包括諸如：

* 標準元件庫提供的邏輯閘列表，供合成使用
* 電晶體的電氣特性、SPICE 模型
* 各邏輯閘含延遲的 Verilog 檔，供 post-synthesis 模擬使用

這在晶圓廠內都有專門的團隊在維護，定期下線量測它的性質；供 APR 使用的資訊諸如：

* 各元件的 GDSII layout，由 APR 將元件直接擺放在 layout 中
* 各金屬層的定義與電氣特性，線寬資訊
* Layout 中各層的定義，金屬、文字、Dummy 層等

Post-Layout 的部分則有：
* DRC/LVS/PEX 規則，DRC 除了給軟體開的設定，也有文件詳細解釋每一條規則的意義，通常還會有圖片解說

設計者（也就是我們）會把這套製程的文件送入各 EDA 軟體中，進行設計，可以說 PDK 沒到手線就不用下了，
連晶片都做不出來。

# 結語

說真的現在能完全掌握整顆晶片生產所有細節幾乎是不可能的，外面的公司可能一步就有一個部門在執行，
甚至是外包給其他的代工企業，想想就覺得市面上的數位電路能跑起來根本是奇蹟。  
而我們現下的文明生活，正是這些奇蹟的加總，感謝每一位曾經在暗夜埋頭苦幹的 IC 設計人員，
也感謝每一位在晶圓廠上班的輪班星人。

下一篇，我們就來看看這一小塊人類文明集大成的晶片的物理架構吧。  
