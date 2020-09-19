---
title: "使用git bisect 搜尋災難發生點 "
date: 2014-08-27
categories:
- git
tags:
- git
series: null
---

之前因為強者我同學阿蹦大神的關係，接觸了neovim這個大型專案，光星星數就有9300多顆，是我星星最多的project的9300多倍lol。   
雖然說看了幾個issue，大部分都插不上話－－討論的層次太高了，偶爾有個好像比較看得懂的，trace下去之後提出解法，沒想到是個不徹底的解法，pull request就被拒絕了TAT，要參加這個超過9000顆星星的project，像我這種花盆果然還是「垃圾請再加油」   

雖然說是這樣，但我還是趁這個機會，研究一下如何使用 [git bisect](http://git-scm.com/docs/git-bisect) 在project裡面找到洞洞。   
基本上project無論用了多少test，多少還是跟我的腦袋一樣有一些洞，要如何找到洞洞就是一門學問了，git 提供了git bisect這個指令幫助開發者找到出錯的地方   
<!--more-->

我們用一個比較小的project: [pyquery](https://github.com/gawel/pyquery)來實驗這個功能，這是強者我同學JJL大神參與的專案   

我們trace 一下 issue74 [Behavior of PyQuery.is_() is different from jquery](https://github.com/gawel/pyquery/issues/74)
因為這個issue 發生在v1.2.4，但到了v1.2.9已經消失了，那我想知道這從哪裡發生的（這種狀況比較少見，一般都是有錯要找哪裡出錯了），就用bisect 來找吧。   

首先是bisect 的基本設定，步驟大概是：
1. 啟動bisect
2. 指定一個good commit 
3. 指定一個bad commit  
bad commit 在歷史上要比good commit 來得晚
4. bisect 會從bad commit 一路回溯到good commit 為止。

可以透過checkout tag的方式作大範圍的搜尋，以免bisect檢查太多commit，在這個例子中，我們發現v1.2.8->v1.2.9的過程中這個bug 被修掉了。   
因此我們設定：   
```shell
$ git bisect start   
$ git bisect bad 1.2.9   
$ git bisect good 1.2.8   
Bisecting: 11 revisions left to test after this (roughly 4 steps)   
[bc1b16509cec70de7a32354026443fca777f4d7d] created a .gitignore file
(which is almost a copy of .hgignore with some minor changes and comments)    
```

這時候我們已經進入bisect 狀態，用git branch的話會看到現在是(no branch)狀態。  
要說明一下這裡的good, bad只是bisect上的一個概念，對應到 bisect 的用途：找到是哪個 checkout 把 good 的程式變成 bad 的程式，它會從 good 開始找到 bad，至於裡面是不是真的 good/bad，這由開發者決定。  
這時bisect會checkout 處在good/bad 中間位置的版本，我們執行事先寫好的一個測試檔test.py，它會自動測試這個 issue 的狀態  

```python
from pyquery import PyQuery as pq   
x = pq("<div></div>")  
y = pq("<div><table></table></div>")  
print(x.is\_("table"))  
print(y.is\_("table"))   
```
執行發現它還是回傳False/False，因此我們輸入   
```shell
$ git bisect bad  
Bisecting: 5 revisions left to test after this (roughly 3 steps)  
[b81a9e8a2b0d48ec0c64d6de14293dd4a680a20b] fixed issue #9   
```
bisect 會以binary search的方式checkout 一個更舊的版本，然後你再測試一次。  
經過五次的bad/good的測試結果，bisect回傳：  

```shell
300cd0822505a4bd308acd1520ff3ef0f20f8635 is the first bad commit  
commit 300cd0822505a4bd308acd1520ff3ef0f20f8635  
Author: Gael Pasgrimaud <gael@gawel.org>  
Date: Fri Jan 3 10:35:30 2014 +0100  

fixed issue #19  

:040000 040000 1d9cb3b170a8fdb2846e3c0e0fb6d2be9a9538d5 07d3a40ff73dda078d7543be2fab2f9f927b0c1f M pyquery    
```

這樣就抓到這個 fixed issue #19 的commit 就是修好這個issue 的commit 了，最後要用  
```shell
$ git bisect reset
```
結束bisect狀態。  

---

上面這個方法好像還是不夠方便，理論上bisect 支援git bisect run這個方法，可以送一個script 給它，它會自動執行，

* 回傳值0表示這個commit 是good
* 回傳值1表示這個commit 是bad
* 回傳值125表示這個commit 要skip掉。   

所以我改了上面這個script 為：  
```python
import sys  
from pyquery import PyQuery as pq  
x = pq("<div></div>")  
y = pq("<div><table></table></div>")  
if x.is\_("table") == False and y.is\_("table") == False:  
sys.exit(1)  
else:   
sys.exit(0)
```

可是不知道為啥，bisect run ./test.py的結果，每個commit 都會是bad的輸出…這真的是太奇怪了，我猜有可能會是git bisect的問題也說不定，有空再來詳加研究。  

---

8/28增補：  

後來經過阿蹦大神的指出，問題可能是出在*.pyc上面，因為python要是看到現在的pyc跟現在的時間相同，就不會更新pyc而是直接跑pyc。  
git bisect run會極速的checkout 舊分枝，跑python script，看結果跑下一步；而pyc的檢定大概是用秒在算的，就變成python並沒有更新pyc檔，反而是用pyc跑出同樣的結果，bisect 自然出錯了。  

解決方法有兩個：  

第一個是寫一個shell script test.sh，先刪掉所有pyc檔之後，再執行python script:  
```shell
find . -name "*.pyc" -exec rm {} \;  
./test.py
```
然後執行 `git bisect run ./test.sh`  

第二個是讓python script 跑慢一點，讓python能察覺到python 的版本變化：  
```python
import time   
time.sleep(1)
```

第三個應該才是根本的解法：  
在python 的shebang上面加上 -B的參數就好了
```shell
#!/use/bin/env python -B
```
  執行結果就跟手動的一樣了，去你的pyc。  

## 結論：

bisect很好用？不是，我認為從這個案例中最重要的概念，其實是自動測試的重要性，如果程式能保持一個自動測試的script，在除錯上可以透過script 自動找到錯誤點，不需要人工手動介入。  
試想若每個commit都需要手動10步驟的測試，兩個版本間有10個commit ，測試步驟立刻變成100步，但用script只要一個指令就能知道是好是壞，搭配bisect才能事半功倍。  