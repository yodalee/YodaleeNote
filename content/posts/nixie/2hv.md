---
title: "自幹世界線變動率探測儀（Nixie Tube Clock）：自組高壓電路"
date: 2018-10-20
categories:
- hardware
tags:
- Hardware
- NixieClock
series:
- 自幹世界線變動率探測儀(Nixie Tube Clock)
---

一般自組輝光管時鐘都要配高壓電源，當然從 110V 變壓到 180V 再經過整流、穩壓也是一招，但這樣很難調整電壓，自己繞變壓器其實也比直流升壓麻煩，體積跟重量也都大得多。  
<!--more-->
我們之前買的高壓電板板，要直接用也是 OK，只要在最後 layout 的時候，依照板子的規格在上面鑽洞來接銅柱，接線的地方預留接腳即可。  
我的設計是自己接 MC34063 的直流升壓電路（因為好玩），MC34063 算是非常…古老的晶片，它年紀可能足夠當我老爸，網路上一搜可以搜到許多不同人的實作，不過通常蠻簡略的，也會用到一些比較不常見的元件。  
<!--more-->
這裡是參考強者我同學小新大大所找到的[復古咖啡（一）](https://fugu.cafe/talks/7517)的內容，自己接一個 MC34063 的高壓電路。  

這是電路圖：  
![schematic](/images/nixie/HV.png)
Boost Converter 的原理請大家自己上 [Wiki 說明頁](https://en.wikipedia.org/wiki/Boost_converter#Circuit_analysis)（當初好像是在電機機械實驗遇到這玩意兒），簡單來說我們在電路上加上一個開關，開關接通的時候會對電感充電，關閉的時候則由電感放電到負載，利用電感釋放能量把電壓飆上去，利用二極體把高壓鎖在負載，輸出放一個電容在開關打開的時候維持電壓。  

這個開關必須的高速開關，與 boost converter 搭配的，就是 555 或是我們所用的 MC34063 晶片，其實 MC34063 的設計非常簡單：
![MC34063](/images/nixie/MC34063.png)

它做的事情也很簡單，MC 34063 內部會產生 1.25 V 的電源，不斷和 5 腳位的輸入比較，如果輸入低於 1.25 V，就會將內部震盪訊號送出去，使開關不斷開關（這什麼饒口的說法）。  
震盪訊號的頻率是由 3 腳位接的電容決定，可以從幾 10 KHz 可以到最高 100 KHz 左右，我接 2.2n 的電容，頻率大約是 20 kHz。  
MC 34063 有一個安全機制，因為對電感充電的時候，當電感充電完成時電流會急遽增大（電感變導線了，等於電源直接接地），MC34063 （推測）會用 7 腳位去偵測電壓，如果電壓相比 6 腳位的 VCC 掉太多的時候，表示電感已經飽和，MC34063 就會提早結束充電；這個偵測電壓是 330 mV，使用 330 mV 除以限流就能得到限流電阻值，規格書上的建議最小電阻是 0.2 歐姆（意即限流是 1.65 A），因為市面上買不到小於 1 的電阻，我在這裡就用並聯五個 1 歐姆做到 0.2 歐姆，如果希望限流小一點，可以不要並聯這麼多個電阻。    

與 MC34063 搭配的是 MOS 外部開關，讓 MC34063 壓力不會這麼大，這邊就是照復古咖啡的建議選元件，MOS 開關選 IRF840，往高壓的二極體用 FR104；開關 MOS 的二極體要選速度快的，例如 1N914；輸出電容用 250V, 10u 的電解電容。  
復古咖啡有提到，增加一路 PNP 2N2907 放電路徑的重要性，我在電路板上驗證的時候有測試過，在輸出 170 V, 1.7 mA 在狀況下，有放電路徑的電路只需要 12V, 62 mA 的輸入，沒放電路徑的電路卻需要 100 mA。    

這裡使用的電感千萬不能用色碼電感（電阻式電感），我曾經試過結果它就冒煙了XDD，一定要選銅線繞的電感，在光華也只有一家地下室的源達有在賣，或者也有人用軸向的電感（？），我最後是選銅線繞的電感，感覺比較保險（光華商場買不到參考設計的大顆軸向電感，工字電感有點小顆怕怕的）。  
感值的部分應該用 68 - 100 uH 的電感，就可以推動兩到三支管子（沒實際測試過，至少 68 uH 是 OK 的），和直覺相反的，如果這裡要推更大的電流，其實電感要用更小，利用小電感快速放電的特性跟高頻率的振盪把電流逼上去，但因為 MC34063 100 kHz 的振盪頻率不算太快，用太小顆的電感沒事就會飽和，因此 MC34063 的升壓跟輸出電流都有一定限度。  

回授電路的部分就是用 511K 和 3.3K 電阻分壓，加上 2k 的可變電阻，這樣分壓的可調範圍是 511K/3.3K -> 511K/5.3K，也就是 193V - 120V，這裡對電阻值比較敏感，因此選用誤差值 1% 的五環精密電阻。    
最後在電路板上的完成照，其實我 lay 得滿稀鬆的，外購的高壓板同樣的 48 x 41 mm^2 裡，在麵包板上測試的版本則是忘了照了XDD：
![HV](/images/nixie/DSC_1173.jpg "opt title")
除了 MC34063 之外，下面[這個連結](http://www.mobile01.com/topicdetail.php?f=348&t=3398723)也有人有其他效率更高的設計，不過因為他沒有提到更詳細的設計內容，只能當個參考；當然裡面提到的一些 Layout 技巧還是用得上。  
我在插麵包板測試的時候，我的電路效率不知道為什麼一直上不去，大約卡在 40 %，外購的高壓板效率可以到 68% 左右；雖然有點懷疑是不是電感品質的問題，或者是 layout 的問題，只要到 PCB 上就解決了？但我在 PCB 上沒有預留量電流的地方，也因此無從驗證了。 