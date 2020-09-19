---
title: "安裝Minecraft Shader"
date: 2015-12-14
categories:
- minecraft
tags:
- minecraft
- shader
series: null
---

這次放假回家，試著在Minecraft 上面安裝Shader，這裡記一下過程與結果。   
試了之後發現，原本要裝GLSL Shader MOD 現在都不用了，1.8 的 [Optfine](http://minecraftsix.com/optifine-hd-mod/) 已經把Shader 選項整合進去，只要安裝Optifine 即可開啟Shader 選項  
<!--more-->
而且Optfine 的安裝也變簡單了，直接執行載下來的jar 檔就能安裝完成，跟以前手動把jar 檔拆開，把檔案複製進去，刪掉Meta-inf一堆步驟，不小心還會爆開要刪掉重裝的過程根本天壤之別。  

裝完optfine再來就可以去載Shader 來玩了，[這邊](http://minecraftsix.com/glsl-shaders-mod/)  有三個shader可以載，列表打開也有一排shader任君選擇，不過我覺得看多了其實大同小異，通常還是用Sonic Ether's Unbelievable Shaders medium  

不過Shader 開了，為求效果通常把亮暗對比調得很高，這其實很妨礙建築跟探險，所以只限於拍照用。  

另外是一個插曲，一開始裝好的時候，不管是哪個shader，打開畫面都會一片漆黑，下面出現類似：  
```
Invalid program: final  
Cannot create FrameBuffer  
```
之類的錯誤，後來發現我沒用Optirun開，使用的顯卡是Intel 的HD Graphics 4000，可能是程式不相容不然就是顯卡不夠力，總之顯示不出來；後來用了Optirun 用筆電的nVidia GT 640M才一切正常，這是顯示結果：  
![shader](/images/minecraft/shader.png)
世界變得好漂亮lol。  

話說回來，這根本是在虐待顯示卡，用Ultra 的shader fps 都會降到 24左右，移動時畫面看得出頓點，用medium才能回到50 fps。
以下個人意見：打minecraft 最好玩的還是徒手打造理想世界的那股衝勁，還有完成它的成就感，shader充其量只是裝飾的工具，真正強大的顯示卡，其實是你我的想像力呀。  

