---
title: "使用振盪器改善投擲器鏈之鎖死問題"
date: 2013-11-16
categories:
- minecraft
tags:
- minecraft
series: null
---

個人很常玩minecraft大概不用提，最近在建造分類工廠時，遇到「將物品向上傳送」的設計問題，因為一般的漏斗只能水平傳送或是向下傳送，如果不想要讓玩家自己把物品拿到高處，就要有自動化的機制才行。  
幸好在1.5版之後，新加入大量紅石元件，讓許多過去無法達成的自動化得以實現，本文設計一個利用振盪器驅動投擲器鏈，進而改善過去投擲器鏈常遇到的鎖死問題。
<!--more-->

## 過去向上運送法之介紹：  
過去常見的minecraft傳送物品向上有五種方法：向上水流運送、活塞運送、鐵路運送、投擲器鏈和玻璃傳送管。  
向上水流最大的問題是運送效率不佳，速度最慢還有可能會卡住，同時需要相當大的建造面積。活塞運送也有相同的問題，向上提升一格就要再將物品移動到另一格，也容易掉物品[(1)]({{< relref "#reference" >}})。  
玻璃管傳送法見[(2)]({{< relref "#reference" >}})，是利用minecraft 的bug feature，物品被由下向上擠壓時會向上移動尋找空間，藉此運送物品，最上方再以漏斗承接運送的物品，事實上不用玻璃亦可達到相同的效果，使用玻璃純粹是可以看到在運送什麼；在長距離傳送上，玻璃傳送管效益最高，使用極少量的紅石電路即可，但物品跑到傳送器外，未免讓人心理發毛，一不小心物品可能會落到管外而遺失。  
相較上述三種方式，鐵路運送和投擲器鏈不會將物品轉為實體，可靠性相對較高。  
鐵路運送[(3)]({{< relref "#reference" >}})相當有效率，要送高只要多蓋鐵軌即可，只有起迄點需要紅石電路設計，但使用方式是利用箱子一次運送一箱的物品，個人比較不喜歡。  
投擲器鏈相對可實現連續、可靠的運送，在過去已有幾件相關設計[4]-[5]({{< relref "#reference" >}})，這些設計都使用比較器偵測投擲器內的物品，經過回送驅動投擲器向上傳送；這樣的設計有個最大的問題，當投擲器內的東西超過一個時，投擲器發射後裡面還有物品，比較器將不會再更新，使得投擲器錄陷入鎖死，需要以人工手動移除多餘的物品才能再次運作。  
特別是一般自動化運送物品都會用漏斗將物品打入投擲器中，而漏斗的運作速率是每秒2.5個(4個redstone ticks)，這速率高於驅動投擲器向上的速率；因此兩個設計中都在漏斗旁放上一個紅石作為控制，一但投擲器有東西就停止漏斗的運作，無奈只要這個機制出小差錯，還是要人工介入移除多餘物品。  

## 改善投擲器鏈之設計：  
為了改善這個問題，本設計使用主動振盪器來驅動投擲器向上，雖然需要多一點的面積，不過這個機制保證投擲器會運作到整條投擲器鏈都沒有東西為止，主要分為三個部分：偵測器，Or gate，振盪器：  

偵測器：  
左右兩邊交互放置比較器偵測投擲器鏈內的內容，由於比較器輸出強驅動訊號，因此只有圖中紅色block上會放置紅石，上一層的比較器可透過白色方塊傳遞給下層紅色block，如圖所示：  
![deletector1](/images/minecraft/dropperchain/detector1.png)
Or gate ： 上一層的紅色block訊號，會經過兩次not，送給下一層的訊號；加入repeater的目的，是要防止自身紅色block的強訊號覆寫下一層not過的訊號，否則當整條鏈中只有紅色block該層投擲器有東西時，振盪器也不會驅動。  
![deletector2](/images/minecraft/dropperchain/detector2.png)
振盪器： 將訊號集中起來，驅動比較器制成的高頻振盪器，透過半板向上送給每一個投擲器，即完成本設計。  
![osc1](/images/minecraft/dropperchain/osc1.png)
本設計缺點有：
1. 振盪器的傳送距離為15格，大約只能送12層的高度  
可以在上層設置另一個振盪器來解決這個問題，但會佔掉一些樓板面積；或者不求速度的話，可以用比較慢一點的振盪器，就可以用「block-紅石火把」的組合將訊號向上傳送，如圖所示；不過若是超高層傳送，玻璃管傳送法會是比較有效率的做法。
2. 運作起來相當吵，這個是真的沒得解。  
![osc2](/images/minecraft/dropperchain/osc2.png)

## 設計展示：
在底部送入物品，都會送到頂部的箱子中，兩段式的版本也可以運作正常，前述的噪音問題在兩段式版上會更明顯，因為這裡用的是比較器振盪源，比較器只有1 ticks的延遲讓投擲器的運作快過漏斗的運作，一開啟就會聽到投擲器時停時開的嗒嗒聲，其實相當煩人。  

## 參考資料：{#reference}
1. [water](https://www.youtube.com/watch?v=z1rAiPsCj5Q)
2. [glass tube item lifter](https://www.youtube.com/watch?v=DtcSljfkMIw)
3. [railway item transport](https://www.youtube.com/watch?v=PLtqJ5gsO9E)
4. [dropper chain](https://www.youtube.com/watch?v=7OJUHyJfrQE)
5. [dropper chain](https://www.youtube.com/watch?v=_xu7e97_Qdo)