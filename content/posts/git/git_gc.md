---
title: "自己犯的錯自己刪，使用git-gc"
date: 2014-06-28
categories:
- git
tags:
- git
series: null
---

最近我修改了我的ADS2Origin，因為使用者回饋表示，有時候資料區塊長度不同是無可避免的，比如說遇到loadpull的圖形，因此我把輸出改為csv格式，程式只會提醒使用者資料區塊長度不同，而不會自動切掉長度過長的部分；這個東西其實也不難改，反正資料就在那裡，只是改一下寫出的方式。  
倒是寫這個讓我想起data mining的名言：「做data mining的，用了70%的時間在處理資料，30%的時間在靠北處理資料」  

與此同時，很高興6/25號晚上我又推了一位同學當使用者，使用者人數++。  
為了方便使用者，把[下載連結](/download/ADS2Origin.zip) 放在這裡讓大家下載。

---

另外，最近我發現到一個問題，因為我的git project把windows下的執行檔都包進去，git又是每記錄一個版本就把檔案都複製一份，看一下我的git repository已經14 MB（唔…跟某些project用幾十G在算的比起來其實還是很小），
不過恁爸保留exe的commit好像也沒啥用，就趁這個機會研究一下怎麼刪掉舊記錄裡面的執行檔。  
不能用git rm ，這是不夠的，git歷史資料還是會保留著，因此需要一些特別的方法，主要的參考資料是 ProGit 的 10.7 的 [Git-Internals-Maintenance-and-Data-Recovery](https://git-scm.com/book/zh-tw/v2/Git-Internals-Maintenance-and-Data-Recovery) ，
還有一篇 [gitready](http://gitready.com/beginner/2009/03/06/ignoring-doesnt-remove-a-file.html) 的文章，其實大部分的內容它們都講完了，我只是照做而已。  
<!--more-->

其實理論上是不能這麼做的啦，這樣的行為會改變整個有大檔案存在的歷史，在有協作時需要你的團隊重新拉你的commit，會如此麻煩是因為git的設計理念就是不讓你輕易的丟失資料。  
不過不管啦，我有幾個理由：  
1. 這個project根本沒人理  
2. 恁北我看windows不爽，就是要把windows的執行檔幹掉  
3. ~~跳脫舒適圈~~  

首先看一下project的狀況，在執行完git gc後，再用 `git count-objects -v` 看看project有多大：  
得到size-pack為: 3350 KB  

我們的目標是一個名為dist的資料夾，裡面放滿了py2exe產生的巨量檔案。  
用git log找出所有有加入該檔的歷史資料：  
```shell
git log --pretty=oneline --branches --abbrev-commit -- dist
```

這個的會列出所有head下，match到dist 這個路徑裡的log，使用縮短的sha來顯示，結果如下：  

```txt
5f9f3dc output in csv format, allow various length data   
23f8633 windows executable file of 0.3.1 version   
bb1107f Merge branch 'master' of github.com:lc85301/ADSToOrigin   
e891091 update ADSToOrigin.exe version   
acbeb1d fix duplicate tital bug   
5343e5c add data length different detect, multifile sup   
9ff12b9 multi variable parser support add   
c989cc4 allow drag in windows   
b21d5c1 windows distribution
```

的確，第一次把dist這個資料夾加進來就是從這個windows distribution開始的，這個commit的SHA值為b21d5c1。  

好的，讓我們動手，這個要使用git filter-branch的命令，基本上這是一個…破壞性有點高的指令，建議是把manpage好好讀過一遍之後再來使用，不然GG了我不負責。  
Filter-branch可以傳入一個filter，然後基於這個filter上，把所有的commit重寫一篇  
這裡要用的是--index-filter或--tree-filter，這個會改變commit的內容，另外還有像--env-filter改寫每個commit的環境設定，msg-filter用來改寫commit message等等。  

每一個filter後面要接一個command，用來操作你的git倉庫，拿最簡單的來說，msg-filter會把目前的commit message送到你的command的stdin，然後以command stdout的內容當作新的commit message，例如我有一個倉庫依序加入abc三個檔案，現在長這樣：  
```txt
b0b79d5 add c   
f09a9d6 add b   
2eee4d4 add a
```

如果我下：git filter-branch --msg-filter 'echo XDD' -- master  
結果就會變成這樣：  
```txt
075cdd6 XDD   
44fe70f XDD   
ec1e435 XDD
```
所有的commit message都被改寫成XDD，這簡直比改歷史教科書還要簡單。  

現在我們要移除掉dist資料夾，就使用--index-filter  
```shell
git filter-branch --index-filter 'git rm -r --cached dist' -- b21d5c1^..
```
最後這個-- b21d5c1^..，是送到git rev-list的內容  

git rev-list會把從某個branch往前回溯(嚴格來說是reachable)的每個branch寫出來，然後可以加上各種條件對這個群集進行操作，這裡我用例子來說明：  

* git rev-list master //master往前的所有commit  
* git rev-list master ^branch //master 往前，但不是branch往前的commit  
* git rev-list branch..master //  
與上一行等價 另外還有...的用法，只是那個我還沒搞懂，搞懂了再另外寫一篇XDD  

前面提到，windows的東西第一次是出現在 b21d5c1這個commit  
因此我們做的，就是從master往前所有commit裡面，把 b21d5c1前一個commit再往前的排除掉，因此只會更改到 b21d5c1這個commit之後的東西，不然filter-branch就會重寫整個歷史，會花比較多的時間（這個垃圾project算了，請想像你有幾千個commit要修正的話？）。  
 指令是移除掉dist下的東西，就是個 rm。  

output大概會像這樣：  
```txt
Rewrite b21d5c1abbaf39e02b817b0ccb7efdc54dbf6090 (1/14)rm 'dist/ADSToOrigin\_win.exe'   
rm 'dist/\_hashlib.pyd'   
rm 'dist/bz2.pyd'   
rm 'dist/library.zip'   
rm 'dist/python27.dll'   
rm 'dist/select.pyd'   
rm 'dist/unicodedata.pyd'   
rm 'dist/w9xpopen.exe'    
```
以下類似的東西重複14次，無非就是刪掉exe, pyd 巴啦巴啦，可以看見我到底存了多少exe垃圾在我的project裡面lol。  

另外，我有些commit是針對windows distribution去commit的，這個指令一下這個commit就變成empty commits，因此我們再來：  
```shell
git filter-branch --prune-empty -- b21d5c1^..
# 這裡的SHA應該要換掉，只是我忘了是多少了。  
```
這個參數可以在上面就下，一次做完比較痛快，這時候像windows distribution這個commit就不見了。  

這樣我們已經讓記錄中不再記錄這個檔案，最後把它從.git裡面記錄刪掉，因為git reflog跟branch-filter本身都有對它的引用（你看看從git裡面刪東西是有多機車……）。  
```shell
rm -Rf .git/refs/original # 刪除branch-filter的引用  
rm -Rf .git/logs/ # 刪除reflog  
git gc   
```

最後，強制把你修改的分枝樹，把遠端的東西蓋掉。  
```shell
git push origin master -f   
```

這樣應該就差不多了，雖然說我弄完之後好像沒變小很多，不過我不是很清楚問題在哪...  