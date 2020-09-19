---
title: "字幕產生器 Subtitle Generator"
date: 2016-06-06
categories:
- small project
tags:
- javascript
series: null
---

六月初參加PyCon ，因為第一天開幕睡過頭了，用 One Punch Man 超商大特賣的畫面做了兩張搞笑圖，
用gimp 做不熟練，花了不少時間，決定來寫個字幕產生器   

### [成品在此](http://yodalee.github.io/subtitle-gen.html)   
<!--more-->

這個網頁基於之前qcl 大神所寫的[大師語錄產生器](http://qcl.github.io/master-quote-gen.html)，大體架構沒什麼改   

同時我還參考了以下的stack overflow，老實說要是沒有網路跟stack overflow，我應該寫得出一點C跟python，
可是html 和javascript 我大概會完全卡住，一行都寫不出來：   

* [上傳圖片到canvas裡面](http://stackoverflow.com/questions/22255580/javascript-upload-image-file-and-draw-it-into-a-canvas)   
* [canvas 裡面大圖縮小](http://stackoverflow.com/questions/2303690/resizing-an-image-in-an-html5-canvas)  
* [canvas裡寫字有邊框](http://stackoverflow.com/questions/13627111/drawing-text-with-an-outer-stroke-with-html5s-canvas)   
* [指定 input/color 預設顏色](http://stackoverflow.com/questions/14943074/html5-input-colors-default-color)   

其實寫出來覺得有點對不起qcl 大神，其實就是「大師語錄產生器」的變種，應該要貢獻回qcl 大神的github 的，
只是我不知道怎麼調和自行上傳圖片和預設圖片的衝突，也不知道要怎麼處理使用者決定文字在圖內或圖下時，canvas要怎麼處理，乾脆算了。  

不過既然做出來了，表示好處多多，可以好好利用：   
除了本來PyCon 兩張可以快速做出來

![demo1](/images/posts/subtitlegen/demo1.png)
![demo2](/images/posts/subtitlegen/demo2.png)

還可以玩一些其他的：
![demo3](/images/posts/subtitlegen/demo3.png)
![demo4](/images/posts/subtitlegen/demo4.png)