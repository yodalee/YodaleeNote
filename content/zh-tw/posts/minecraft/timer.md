---
title: "使用差動雙投擲計時器應用於時鐘製作之研製"
date: 2013-05-25
categories:
- minecraft
tags:
- minecraft
- timer
series: null
---

minecraft是一款我認為設計得相當好的遊戲，透過簡單方塊的堆積，讓你組出任何你想要的內容；而紅石又是其中最有變化的物件，可以模擬出許多數位電路的行為，老實說基本的邏輯設計課程應該可以用minecraft當作輔助教材(XD)。  

minecraft升級到1.5之後，多了很多新的紅石元件，其中包括可以測定日光強度的日光sensor，讓我們有機會在minecraft當中，實現時鐘的功能。   
之前已經有相當多相關的設計，包括直接用 sensor 輸出信號接在 redstone lamp [(1)]({{< relref "#reference" >}})，及用長線分離出各時段的信號[(2)]({{< relref "#reference" >}} 等。  
因為sensor輸出信號在白天呈現山形，第一種時鐘，共有上午和下午時會呈現相同的時間、計時非線性、晚上也只能顯示為晚上而非確切時間等問題；第二種則需要相當大的空間和電路，在一般server不用creative mode難以實現。  這裡我們就要設計的是，能夠線性計時，利用daylight sensor來校正，同時體積儘量小的設計。  
<!--more-->

最終設計的minecraft時鐘共有兩個主要部分，分別為：差動雙投擲計時器、雙比較器實現計數器(counter)．本文將分為以下幾個部分：   

## 1. minecraft 時間及sensor介紹：

minecraft 一天有現實的 20 分鐘，共分為 24000 個基本時間單位 ticks，ticks 設為0時相當於每日早上６點。
sensor 的部分，固定每天 22500 ticks 到 13500 ticks 會發出信號，其他時間則不發射，信號強度依日光強度有所不同。   
詳細資料請參考：[minecraft wiki daylight sensor]({{< relref "#reference" >}})。  

## 2. 差動雙投擲計時器之設計：

過去minecraft上常難以實現長時間的delayer，可行的辦法包括用rail+detect rail、dispensor+蜘蛛網、鐵路+流水回收[(4)]({{< relref "#reference" >}})等、活塞循環[(5)]({{< relref "#reference" >}})等；但一般 rail+detect rail 需要相當大的面積來達成長delay，一般大小下 delay 只有約10-20秒，且重登入時不容易reset；dispensor+蜘蛛網、鐵路+流水回收則不夠精確，delay時間的可調長度與可調精度不佳；活塞循環相較之下較為可行，但拉到四角的紅石信號容易造成信號線相當複雜，一般體積也較大。     
本文提出之差動雙投擲計時器，除了能精確計時外，還具有容易reset、停止、可調長度相當廣及所佔體積相當小等好處，主要的參考來源為[SCAMP全自動造山機]({{< relref "#reference" >}})。     

雙投擲器將兩個投擲器相對，驅動一個投鄭器即會將內容物送至另一個投擲器內，透過1.5版新增的比較器，偵測投擲器是否內含物品，驅動比較器製成的振盪器(圖左)，即可自動將一投擲器(下稱發射端)的物品送到另一側(下稱預備端)，調整投擲器內的物品數量和振盪器的頻率，可以調整輸出變化的時間，由於comparator的delay不明，粗估送完的時間方式為，投擲器內的物品數量*(Osc. Delay)，實測上兩個repeater調最長，17個物品送完的時間是30秒。  
![timer1](/images/minecraft/timer/timer1.jpg)
理論上可以在另一邊複製相同的振盪電路，將一側電路的輸出鎖住另一方向的repeater，達到來回振盪的功能，但如下圖，repeater要鎖住的方向不同，這樣的設計會讓電路變得相當大；同時兩邊都是相同的振盪頻率，實用上不容易做到校正的功能。   
![timer2](/images/minecraft/timer/timer2.jpg)

新架構加入另一套雙投擲計時器，兩計時器互鎖，當A方鎖住B方時(A方的Q值為1)，A方輸出和B方預備端是否含物品的信號通過AND閘，驅動高速振盪器，將物品送回發射端。    
![timer3](/images/minecraft/timer/timer3.jpg)
![timer4](/images/minecraft/timer/timer4.jpg)

運作包含五個相位：   
1. A方發射端將物品送入預備端，B方預備端高速送物品回發射端。  
2. B方預備端送完，高頻振盪器停止。  
3. A方發射端送完，B方發射端解鎖，使A方輸出鎖住，並啟動A方預備端高頻振盪器。  
4. A方預備端送完，高頻振盪器停止。  
5. B方發射端送完，A方發射端解鎖，使B方輸出鎖住，並啟動B方預備端高頻振盪器，回到相位一。  

最後則是控制信號的部分，可以透過強制將A/B方鎖住信號設在1來達成開關計時器的功能；但要注意的是，repeater的鎖住是鎖在 0或1，如果鎖在1的話，會使雙投擲器進入來回投擲的不穩定狀態；因此我們要在控制信號的輸入處，加入一個由輸出控制的鎖，以避免上述狀況的發生，詳細如下圖所示。   
完成之雙投擲計時器所佔面積為10*8*3，相當compact，理論上的最長delay時間估計為2032秒左右  

![compact_version](/images/minecraft/timer/compact_version.jpg)
![compact_version2](/images/minecraft/timer/compact_version2.jpg)

## 3. 雙比較器實現計數器之設計：

由於上述差動雙投擲計時器的輸出端，只能隨時間輸出長週期的1/0信號，因此輸出端先接入一個上升/下降緣檢測電路(edge detector)，產生短脈衝；再接入計數器計算短脈衝的數量，以達成隨不同時間輸出不同信號的能力。   

這裡狀態機的設定參考[(7)]({{< relref "#reference" >}})的設計，功能考量，我們只取其中的down counter跟重設的能力，同樣由雙比較器維持信號強度，每一個脈衝進來，經比較器產生強度一的信號，使狀態強度減小一，達到狀態記錄。   
實作上計數器記錄的是計時器發出多少次信號；在這裡我們用來記錄經過多少時間，在日間感測器開始運作之後，到日落的時間為15000ticks=12.5分，晚上感測器則是9000ticks=7.5分，分別需要記錄12, 7個狀態。  

![counter](/images/minecraft/timer/counter.jpg)
為了reset計數器，我們需要特定強度的信號，當然也可以用強度15的信號reset，但這樣會加大計數器的體積；這部分使用箱子+comparator產生，並利用另一個信號為15的信號相減，來產生所需的強度。   
以日間計數器需設到強度12的信號，箱子要放345－460個物品。  
以日間計數器需設到強度7的信號，箱子要放921－1036個物品。(雞蛋的話請除4)  
這個用骨粉來放最容易了。  
![level_generator](/images/minecraft/timer/level_generator.jpg)

## 4. 設計展示：

最終時鐘設計如下圖所示：   
![complete](/images/minecraft/timer/complete.jpg)
中央的日光偵測器為核心，左右各為一套雙投擲計時器，分別在日、夜時工作(左日右夜，不想看到紅石電路請自己拉到地底=w=)；計時器Q+輸出經edge detector進到計數器-1端，Q-經edge detector到對方計數器reset端；上方為夜間計數器，七個狀態；下方為日間計數器，12個狀態；有一些些調整是在鎖住sensor信號跟接到計數器的部分，都是為了讓體積更小。   

稍微提一下，因為在雙投擲計時器，鎖住控制信號的那一方(Q-)，在計時器被鎖住時，其輸出為0，如圖中左邊上半的狀態，因此在停止工作的瞬間，會有一個negative edge pulse，利用negative edge detector偵側這個信號幫另一方重設。   
開始計時的時候，Q-端會先變1，然後30秒後換Q+端變1，再30秒Q+變0；因此從Q+端接到計數器減一端的detector同樣是negative edge detector。  

這大概是整體時鐘的設計了，每個一紅石燈的信號可以自行拉線到想顯示的方式上；就我所知，這是目前能線性計時，同時體積最小的設計。  

## 5. 參考資料：{#reference}

1. [Basic Minecraft Clock Using 13w01a "Daylight Sensors"](http://www.youtube.com/watch?v=2x-l0owQGF0) 
2. [WORKING 12-HOUR CLOCK IN MINECRAFT](http://www.youtube.com/watch?v=1-ylYISMAck)
3. [daylight sensor](http://www.minecraftwiki.net/wiki/Daylight_Sensor)  
4. [Minecraft clocks](http://www.youtube.com/watch?v=Rz1Qxbh3_XI)  
5. [Minecraft : Piston clock for long delay](http://www.youtube.com/watch?v=M19UQ5Y_wzQ)  
6. [The SCAMP: How it Works, and How to Use It](http://www.youtube.com/watch?v=vBpPKVwIwP4>)  
7. [Decimal Counter with Comparators [Tutorial] Minecraft 1.5](http://www.youtube.com/watch?v=J7mRNZXshCQ)