---
title: "數位電路設計系列 - 晶片的物理架構"
date: 2024-06-02
categories:
- ICdesign
tags:
- ICdesign
images:
- /images/ICdesign/M4.png
---

談到 APR 之前，我們先來說一下晶片內部的物理架構，pad、鎊線、memory、power ring、power strip 等，
讓大家對平常看到的晶片有個認識，後面實際操作軟體的寫文章才好寫。

<!--more-->

# 封裝
平常生活中最常看到的 chip，大概就是那種黑黑有腳的晶片，不然就是放在主機板上面的 CPU 晶片，這時候腳位是在背面的針腳或是接點，這是晶片的封裝。

視電路設計的針腳數，可以選用不同的封裝，我查到最完整的列表來自[德州儀器](https://www.ti.com/zh-tw/support-packaging/packaging-terminology.html)，
我比較知道在幹嘛的封裝包括：
* SB：Side-Braze
* CQFJ：Ceramic Quad Flat
* J-leaded CLCC：Ceramic Leadless Chip Carrier
* CQFP：Ceramic Quad Flatpack

等等， 目前這些封裝似乎都沒有個統一的中文譯名，各封裝的外觀可以自己搜尋圖片，用它的名字加上 packages 查到。

封裝是晶片與外面電路板的中介層，例如 Side Braze 的封裝就可以直接插在麵包板上進行量測，CQFJ, CLCC, CQFP 等等就比較適合自己洗電路板出來做連線。  
不同的封裝都有不同的尺寸、接腳數，例如 SB 封裝可能到 48 支腳就接近上限了，CQFP 到幾百支都沒問題。  
各封裝的成本與訊號頻率上限也有不同，可依照自身需求選取，個人現在是都選 SB，反正接腳數沒那麼高，頻率也沒要求。

如果我們使用物理的方式破壞封裝（開蓋），就會看到下面的裸晶，實際上晶片的尺寸都比我們想得小非常多，會這麼大都是因為封裝的限制。  
以 Intel 最新的 14900K 為例，網路上就可以找到 14900K 用的 LGA1700 的[腳位定義圖](https://www.reddit.com/r/intel/comments/15n9jpn/lga_1700_pinout_problem/)，中間白色那塊就是晶片要放的位置：
![LGA1700](/images/ICdesign/LGA1700.png)
這個 CPU 外觀尺寸大約是 45.0 mm x 37.5 mm ，但開蓋後的裸晶尺寸只有 257 mm²，大約是 1.6 cm x 1.6 cm，跟你大拇指的指甲差不多大。  

以下是我跟強者我同學求到的鎊線圖，這顆好像本來就沒封裝是直接量測裸晶，所以嚴格來說也不算開蓋圖就是了，
中間的裸晶由晶圓代工廠做完後，透過鎊線 (bond wire) 連接到周邊的封裝上，封裝上的接腳將外界的電源、接地、訊號接入晶片中：

![Bond wire](/images/ICdesign/bondwire.png)

大多數的製程，晶片會利用最上層的金屬，在晶片最外一圈製作 bonding pad，鎊線就會由這圈 pad 接到封裝上。  
由於這圈鎊線等於是一條長長的導線，帶來額外的電感等效應，在晶片愈加高速化的今天，這種寄生效應帶來額外的限制，
因此也出現覆晶 (Flip Chip) 等封裝技術，但這有點扯遠了，等我做到這個程度再說，有興趣的話我把資訊附在參考資料。

# 標準元件庫
進到晶片內部，整個晶片從橫切面來看，由底層往上依序是：

* 矽晶圓基板，從砂子提煉出來矽基板。
* 電晶體晶片的最底層，包含晶圓上的 OD oxide diffusion (drain source)，PO Poly oxide (gate) 構成
* Contact，形成電晶體的接點，連接到上層的金屬。
* Metal Connect，由銅製成的金屬導線，看製程可能有 5 層、7 層甚至超過 10 層的金屬做為連結使用，一般會依序稱 M1, M2, M3, … M9。
* 最上層的 Top Metal 就會是上述 bonding pad 的所在，在製作晶片時 bonding pad 的位置會打開以供鎊線。

當然會直接用電晶體的，大概只有類比、微波或是 MEMS 等特殊的應用，在數位晶片的領域，我們會使用晶圓廠或是 IP 廠如 Arm 提供的標準元件庫來進行設計。  
我搜 google 找到的網頁，有找到一個[標準元件庫的範例](https://www.vlsitechnology.org/html/cells/vsclib013/lib_gif_index.html)，網頁最後更新於 2008 年。  
標準元件庫會提供各種基本的邏輯閘，以及他們的時序特性、電氣特性等，每個邏輯閘都有各自的邏輯，如 AOI21 就代表一個 And 配上 NOR gate，這樣的組合用 CMOS 實現起來，會比只做 AND, OR gate 再連接起來更快速，面積又更小。  
為了簡化 layout 的功夫，各個邏輯閘會依照一定的規範在設計，諸如：
* 每個邏輯閘的高度都是一樣的
* 上面的節點接電源 VDD，下面的節點接地 VSS
* 每個邏輯閘使用 PMOS 與 NMOS 的寬度是一樣的

注意這只適用在一般製程，愈是高階的製程愈可能因為製程限制或是效能、省電等要求，使標準元件有各類特殊設計。

# followpin
有了這樣格式固定的邏輯閘，我們會在最底層的金屬 M1，在晶片上放上一條一條的橫條 followpin，
一條接正電 VDD，一條接地 VSS (GND)， 在 layout 中邏輯閘就會延著橫向的 VDD VSS 排成一列，就像貨架一樣，邏輯閘就能這樣連接上 VDD VSS。  

下面我們用 Minecraft 舖了 33x33 的晶片出來（這己經是我找到最能重現 3D 的東西了），
大概就像這個樣子，紅石代表 VDD，黑羊毛代表 VSS，灰色的則是邏輯閘的接點。
![M1](/images/ICdesign/M1.png)

這樣的設計能大幅減少晶片的複雜度，畢竟晶片要連結的東西包括訊號走線、時脈、VDD、VSS，全部都要繞線還要顧及線寬以控制壓降，
變數太多難以處理，用這樣的接線立刻少 VDD VSS 兩個變數要處理。

# Metal

再往上的 Metal 2 到 Top Metal，大致上會有幾個任務：
1. Metal 2 - Metal3 有時用到 Metal 4 會用來繞線讓信號連接到各邏輯閘的接點。
2. 由 Top Metal 往下幾層，會在晶片四面畫上 Power Ring。
3. 從 Metal 2 到 Top Metal，會在晶片中加上 Metal Strip。

第一點因為太複雜，我們沒辦法在 minecrfat 裡面重現，以下我們就展示 2, 3 是在做什麼，與其他圖相同，紅石方塊是 VDD，
其他顏色是 VSS；M2, M3, M4 的 VSS 依序為棕色、藍色、綠色。  

下面是加上 M2 Power strip 的圖，為了不要妨礙到繞線，M2 的 VDD, VSS 都還比較細一些，
M1 因為要接邏輯閘電源所以會走水平方向，M2 就會走垂直方向。
![M2](/images/ICdesign/M2.png)

再加一層 M3，到了上層金屬走線就會更寬一點，以導通更多的電流，Metal Strip 與 Metal Ring 一樣，M3 又輪到水平走向；每組 Power strip 都是 VDD/VSS 一組畫在一起。
![M3](/images/ICdesign/M3.png)

最後再來一層 M4，四角的原木標示了晶片的四角，我們在 M3, M4 加上外層的 Power Ring，這層 Ring 會連結更外面的 Pad。
![M4](/images/ICdesign/M4.png)

每層 Strip 都會跟上線層的 Strip 透過 Via 相連，這樣才能把 VDD, VSS 由上而下導到最底層的邏輯閘，
Via 的部分來個特寫，看看上下兩組 VDD/VSS 是如何連接的，來導播放大(X
![Via](/images/ICdesign/M34via.png)

後來想說好人做到底，我們就來畫個 Pad 吧。
![Pad](/images/ICdesign/Pad.png)

大體上來說 Pad 就是用黃色的 Top Metal，畫一個可以打鎊線的平板，可能 50 μm x 50 μm，同時一路走 Via 到下層的金屬，就我的經驗會一路下到 M1，
但我們這邊先畫到藍色的 M3 就好；Power Ring 的 VDD/VSS (這裡是 VSS) 就會往外連到 Pad 上面。  

當然這裡只是示意，和實際上的 Pad 還是會有差，畢竟標準元件庫中提供的 Pad 會是機密，跟邏輯閘一樣只畫個外框給你，細節是看不到的。

# 結語

晶片當然是很複雜的東西，但其實我們（人類）為了讓設計可行，已經大量簡化過內部的結構了。  
例如為了供電我們會畫 Power Strip 和 Power Ring，為了實現複雜邏輯我們會使用標準元件庫的邏輯閘，
為了要連接邏輯閘，我們設計晶片要加 followpin 來供電。

到了下一篇的 APR 實際操作，我們又會看到連這些 APR 軟體也是針對上述結構進行設計，所以你可能會問，
我們能不能設計一款電路，不要接 followpin 或 Power Strip，把 VDD VSS 當成像繞線一樣進行 layout？  
答案我會說是可以但也不行，可以是物理上的確可以這樣做；不行是因為你沒工具幫你這樣做，所有的 APR 軟體大概都只會繞訊號線，不會去管 VDD/VSS 要怎麼連；
能生成的結構也己經寫死就是 Power Ring, Power Strip, followpin 等，不會有其他結構給你選。  

APR 就像 AlphaGO 一樣，是針對一個特定問題設計的工具，而不是某種通用的圖論演算法大集合，它就跟數位晶片一樣，說穿了就沒那麼神奇了。
總之這樣的假設也沒必要，市面上各種晶片，大抵也是依循同一套結構設計，也都能正常運作，除非你是什麼學術單位想試著挑戰晶片設計的基礎結構，不然照做就是了。

# 參考資料
有關 Flip chip 可參考：[Flip Chip技術簡介與應用](https://www.moneydj.com/kmdj/report/reportviewer.aspx?a=f83cb156-6be4-40ba-9193-d828d6663dc6)  
有關封裝可參考：[IC封裝與測試](https://www.macsayssd.com/ic-packaging-and-testing)  
