---
title: "bypass與測試線小技巧"
date: 2012-06-11
categories:
- microwave
tags:
- ADS
- microwave
series: null
---

無論是放大器、主動混頻器還是振盪器，都需要外加電線才能運作  這時候我們就面臨到一個問題：
當你接一個DC的電線到電源，這段線的長度非常長  即便DC電源是個理想的ground，經過這麼長的線，各頻率的阻抗會散開到smith chart的整個圓周上。  

因此需要有方法在DC的位置創造一個理想的 ground  方法很簡單，用並聯的電容即可，並聯的電容對RF信號來說，
就像直接short到ground一樣。  
也可以說，電容會隨信號充放電，達到穩定的效果，對於愈高頻的電路，電容就要愈小。    
<!--more-->

畫起來大概像這樣：

![bypass1](/images/posts/bypass1.png)

當然這只是示意圖，電容值是預設值沒有改，也不能直接接 ground，而是接back via的元件。
通常會用一路只有電容的把主要in-band 的頻率cover 住，另外一路會用大一點的電容跟串聯電阻，來cover較低的頻率，如此就能做到一個不錯的RF ground。   
為了看看這個bypass好不好，通常會加上測試線來試試，其實測試線說穿了就是用一段長線去模擬真實狀況的 DC長線，模擬上長這個樣子：

![bypass2](/images/posts/bypass2.png)

很簡單吧   

但是，平時模擬時不會把測試線打開，它會讓模擬跑得久一些些，等到大概模擬完，要開測試線，要一個一個打開又很麻煩。

最近發現ADS裡面也支援簡單的 script 這個小技巧，先拉出一個控制的 var，例如叫：`testline_valid` 好了，把上面測試線的Z改成
```matlab
if (testline_valid == "open")
then 20 Ohm
else 1e10 Ohm
endif
```
你不想叫"open"，要用什麼東西隨你便，總之只要把 testline\_valid 設成你要的值，就可以方便的加入測試線的模擬。  