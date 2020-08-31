---
title: "實作：minecraft 豬人農場"
date: 2014-01-21
categories:
- minecraft
tags:
- minecraft
series: null
---

直接進正題，總之看了youtube的設計：  
{{< youtube sEqKe10H6jo >}}
就決定也來蓋一個。  
<!--more-->
不過因為用venture mode很難抓ghast，就只好用裝trapdoor或sign的方式，讓豬人自己走下來；而豬人的出生頻率和傳送門block的數量正比，因此門自然是愈大愈好。  
和影片中的口字型設計相比，田字的設計可以讓傳送門/黑曜岩的比例更高，因此選用田字型的設計；高跟寬設定為3x3，這個高度為67格高，加上摔落距離20格高，差不多接近minecraft時間流動的極限，因此設定為田字型3x3的設計，有點像建一個魔術方塊的框。  

第一步是採集所需要的黑曜岩，所需要的量為：  
垂直：`21*3*16=1008`  
水平：`21*4*3*8=2016`  
總合：3024單位黑曜岩，正好有一枝 efficient V+unbreaking III 的鑽石鎬，就好好的利用它，一口氣挖掉一整個岩漿峽谷，結果如下圖，放一個木塊是本來岩漿池的高度，直接倒水後整塊挖掉，都要挖到基岩了：  
![obsidian](/images/minecraft/pigmanfarm/obsidian.png)
其他資源用量：  

* gravel: 5552單位  
反正gravel沒用處，就把我家的gravel全用在這，沒想到還不夠(我家只有3400多個)，還跟兩位朋友調了不少貨。
* stoneslab: 5446 單位  
這個其實不用，只是我覺得在下面一直滴水很討厭，就全部用一層stoneslab+一層gravel。
* Trapdoor: 2765 單位  
雖然說用sign比起來比較省木頭，不過trapdoor蓋起來比較快，木頭也不是什麼珍貴材料，就用trapdoor了。
* Cobblestone: 1092 單位  
主要是摔落塔跟底座。
* Stonebrick: 563單位  
這個是蓋四根支持柱，不是跟原PO一樣這麼求物理合理性的話可以不理這項。
* Netherbrick: 292單位  
用在黑曜岩間的填充跟走路的部分，純粹色調比較像。
* Ladder: 582單位  
* Fence: 450單位  
防凍架使用。

其他還有一些漏斗，repeater，比較器做分類器，南瓜燈等，就不列上來了。  

接著附幾張工程照片：  
雪人掉落部分，這地方設計跟影片內相同：  
![snowman](/images/minecraft/pigmanfarm/snowman.png)
建設中，因為我沒放很多光源，到了晚上就會變相撲競技場，被打到場外的話就會……：  
![work1](/images/minecraft/pigmanfarm/work1.png)
![work2](/images/minecraft/pigmanfarm/work2.png)

平面部分建設完成，可以看到有些地方會積雪，這是當初選址的錯，也是開始建設後才發現：  
![snow](/images/minecraft/pigmanfarm/snow.png)
因此加設防凍架，以防水結冰：  
![fence](/images/minecraft/pigmanfarm/fence.png)

黑曜岩矩陣：  
![obsidianarray](/images/minecraft/pigmanfarm/obsidianarray.png)

trapdoor鋪設完成：  
![trapdoor](/images/minecraft/pigmanfarm/trapdoor.png)
點火：  
![lightup](/images/minecraft/pigmanfarm/lightup.png)
放水，上述平面的坡度，除了最底層是八格寬外，上面四層都是七格寬，只要最上一個放水，整個廣場都會有水流(廣場大小：73x73)：  
![water](/images/minecraft/pigmanfarm/water.png)
測試一下，效果十分顯著，如果積了太多，可以用splash of healing，可以瞬殺一群。  
![collect](/images/minecraft/pigmanfarm/collect.png)
最後是一張全景照：  
![fullscene](/images/minecraft/pigmanfarm/fullscene.png)
謝謝大家收看。