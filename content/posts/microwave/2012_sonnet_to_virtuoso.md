---
title: "將sonnet檔轉換到virtuoso上"
date: 2012-11-25
categories:
- microwave
tags:
- sonnet
- virtuoso
- microwave
series: null
---

做高頻電路討厭的就是，頻率太高的情況下，寄生的電容電感會在電路各處藏汙納垢(XD)。  
所以在設計的過程，就需要跑很多電磁模擬，把這些寄生的效應一併考慮到模擬之中。  
（會吃你一堆電腦的記憶體跟花一堆時間，這也是我為什麼有時間打這篇文章的原因，哈哈）  
麻煩就在於，每次在電磁模擬軟體(實驗室用Sonnet)上畫完架構，然後開始跑，確定結果沒錯之後，又要在電路下線的軟體(實驗室用Virtuoso)上畫一遍。
最近學到，該怎麼把sonnet上的檔案匯到virtuoso上面，在這裡記錄一下。  
<!--more-->

理論上，我們只要把sonnet檔案匯出到GDSII檔，這是IC layout通用格式，幾乎所有的工具都支援；之後再從virtuoso讀入GDSII檔案即可。  
遇到的麻煩是，在進行電磁模擬時，我們會在sonnet裡面建好電路一層一層的架構，但Virtuoso的環境卻是依所用的製程而定，它完全看不懂我們是在講什麼？  
所以如果直接匯入的話，就會變成有些層 virtuoso 不知道該對應給誰，變得完全無法編輯，總之會出現各式各樣的問題。  
幸好Virtuoso並沒有這麼笨，在匯入檔案的選項中，可以自行指定層與層的Map file，透過這個，理當能「無損的」將sonnet檔案匯入virtuoso中。  

## sonnet to GDSII：  
在sonnet中，是將電路板切成一層一層不同的介質，然後可以在每層介質中填入金屬，去摸擬其中的電磁效應，我們要的就是這金屬的pattern。  
下面是一個sonnet層數設定的截圖，從最上面的空氣……到最底層的substrate  

![sige](/images/posts/sonnet2virtuoso/sige.jpg)

合理的推斷，GDSII也是將一層一層的資料給記錄下來，但要怎麼知道？  
我用的是開源的 [klayout](https://www.klayout.de) 打開gds下去看，得到如下的畫面：  

![klayout1](/images/posts/sonnet2virtuoso/kl1.png)
![klayout2](/images/posts/sonnet2virtuoso/kl2.png)

發現到sonnet轉gds的規則很簡單，原本在sonnet設在第幾層的金屬，就會被轉到gds第幾層；
很可惜的，sonnet中層與層間連接的via的資訊全都消失了，不過很多金屬不用重畫還是可以省下很多時間。  

## GDSII to Virtuoso：  
有了上面的資料之後，再來就是編寫map file: 一個map file 的格式如下：  
```txt
#Cadence layer name Cadence layer purpose Stream layer number Stream data type
#
TopMetal2 drawing 0-63 0-63
```

每一行分為四個子資料，分別是：

1. 在此製程中的某層的名稱
2. 該層的用途
3. 對應在stream檔中的層數
4. 該層的資料  

像上面這種寫法，會把0-63層的資料都變成TopMetal2。  
purpose的部分，大概有drawing, pin, net三種可以選擇，但從sonnet過來的話大概都是要要轉成drawing的。  
stream layer number就是方才用klayout看到的layer編號；stream data type這部分則不是很清楚，但sonnet轉出來好像也不會特別去設定。  
根據上面的轉出來的資料，可以自行編寫對應的map，data type不清楚就用0-63全部截下來：  
```txt
#Cadence layer name Cadence layer purpose Stream layer number Stream data type
#
TopMetal2 drawing 2 0-63
TopMetal1 drawing 3 0-63
MIM drawing 4 0-63
Metal5 drawing 6 0-63
Metal1 drawing 10 0-63
```
這樣各層就能夠轉換成功了：  
![virtuoso](/images/posts/sonnet2virtuoso/virtuoso.png)

不過另一方面，據說從sonnet匯入virtuoso時，有機會發生一些off-grid的問題，這就是一時之間無法解決的問題了。  

## 結語
這篇介紹了如何將電磁模擬軟體Sonnet上的繪圖，直接轉換到Cadence Virtuoso上面，
我很喜歡 「work hard, after you know you are working smart」類似的話，  
如果可以直接匯入圖形(work smart)，就不要花時間重畫(work hard)了。  

如果你用的是Sonnect V13以上的話，已經內建含有[和 Virtuoso的介面](http://www.sonnetsoftware.com/products/sonnet-suites/ef_translators_cvbridge.html)了。

## 參考資料：  
* [GDSII format](http://www.buchanan1.net/stream_description.shtml)
* [Lyaermap format](http://www-bsac.eecs.berkeley.edu/~cadence/tools/layermap.html)