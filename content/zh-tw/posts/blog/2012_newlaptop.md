---
title: "不正經，開箱文"
date: 2012-08-20
categories:
- LifeRecord
tags:
- Acer
- laptop
- linux
series: null
---

最近因為筆電快要解體，不開玩笑，像正面偵測螢幕的按鈕竟然掉下來了。  

就趁著八月台北資訊展時入手一台，因為平常要跑很多模擬的程式，需要的是運算力強的機種，本人又是個效能控XD，
也不想盯著太小的螢幕，經過綜合評估，最後入手的是這台 ACER Aspire V3-571G，近日解禁，於是來寫個不正經的開箱文：  
<!--more-->

算是這個系列的頂級機種了，買價是30.8k，pchome上是賣33.4k，差別在pchome有送 Diablo3，但那個東西對我價值是０元，如果有送minecraft 帳號或是東方全套我倒是可以考慮一下。  

## 規格

CPU：i7-3610QM，記憶體加到8G，整體而言不重，加上電池2.2kg，比我舊的Aspire 5633還要輕。  
這裡真的很想表一下…電池可以拆我是很高興啦，但你好歹設計一個備用電池，當我主電池拆下來，插頭又被拔的時候，可以撐個５分鐘；不要插頭一拔，螢幕就瞬間黑掉。  

## 外觀

外觀是所謂「鋼琴烤漆材質」，亮到會發光…，不過也超容易沾指紋，我甚至不用燻強力膠就看得到我的指紋了，所以千萬別拿這台筆電當兇器，光指紋就可以釘死你！
![surface](/images/blog/newlaptop/DSC03607.jpg)

15.6大尺寸的螢幕…毫無反應，就只是個螢幕。  
![screen](/images/blog/newlaptop/DSC03609.jpg)

鍵盤是所謂的「巧克力鍵盤」，雖然說我不知道為什麼叫巧克力鍵盤，也不能吃又沒味道，不過打起來還頗順手的，聲音有點大。  
![keyboard](/images/blog/newlaptop/DSC03611.jpg)

## 使用狀況：  

打開電腦，內建有預設的windows7，整體windows跑分有5.9，鎖在硬碟的讀取效率  
![windowsscore](/images/blog/newlaptop/score.png)

然後windows再見，再來大概很久不會再見了=w=。  

我選的linux是Archlinux x86\_64  
只看CPU的話，效能超讚，在archlinux下跑linux的pi指令，算到小數點下1000000位，用time來記時，用real來比較：  
```shell
$time pi 1000000 > /dev/null
```
這台i7只需要１秒啊！  

| CPU | time |
|:-----|:-----|
|舊筆電 Intel(R) Core(TM)2 CPU T5500 1.66GHz| 8.5s |
|桌電 core 2 quad | 5.6s |
| i7-3610QM | 1s |

![pi](/images/blog/newlaptop/pi.png)

電池也很強，從晚上７點到１２點，全程都在跑archlinux安裝，電池很夠，當然也可能是過程中都沒啟動X。  
在archlinux下，因為optimus的關係，顯示卡應該還沒連上，灌的時候X搞了很久，後來只用intel driver才進到X裡，真的超想說  
nVidia Fuck You！  

其實無線網卡也連不上，broadcom bcm57781的卡，自己編譯驅動還有一些錯誤要修…  
不過，只灌了Intel-dri就有了不錯的成績，minecraft視野調到far的fps還有50～60，拿來打東方打起來也很順，附個圖。  

![minecraft](/images/blog/newlaptop/minecraft.png)

![touhou](/images/blog/newlaptop/touhou.png)

另外網路上有說這台打Diablo3的時候會有過熱的問題，個人沒打Diablo3，但就算是安裝時，出來的風也沒有很熱。  

整體給分我給85/100，推薦給有高運算、高效能需求的人；小扣一些主要是三點：  

1. 電池設計：  
2. 對linux使用者來說，Optimus真的很崩潰…  
3. 這台比較新，無線網卡linux好像還沒有支援到，現在linux處於沒無線網路的狀態。  
當然如果你用windows就沒什麼差惹。 