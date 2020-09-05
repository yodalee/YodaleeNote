---
title: "如何在Pull request 被mergerevert 後再送 pull request"
date: 2016-12-31
categories:
- git
tags:
- git
series: null
---

自從換了智慧型手機，又搭配1.5G的網路之後，用手機上網的機會大增，在用Firefox 刷Facebook 的時候，很容易跑出廣告來，於是發想把「在Yahoo 台灣大殺四方驚動萬教的人生溫拿勝利組強者我同學 qcl 大神」所寫的神專案QClean 移植到Firefox Mobile 上面。  
<!--more-->

這部分後來還在努力中，目標是把QClean 的Add-On 移植到Mobile上，研究時，Mozilla 的網頁都跑出一直跑出提醒：Add-on 寫的 plugin 很快就會被淘汰，請改用 Web extension 來寫，想說就順便，在寫mobile version 前，先把本來用 add-on 寫的QClean for Firefox 搬移到 Web-extension 上面。  
總體來說是沒什麼難處，把原本用 Web-extension 寫的QClean for Google Chrome，複製一份，然後把裡面web extension 的API 從 chrome 取代為 Mozilla 所用的 browser ，結果就差不多會動了，真的是超級狂，整體來說沒什麼工作。  

到時再送出Pull Request 之後，發現寫的Makefile 裡面有typo，雖然緊急在Pull Request 下面留言<先不要merge>，但在作者看到之前已經被merge 了。  
接下來出現一個很有趣的狀況，直接幫我把 typo 修好並commit 之後，對上游的master branch送出新的 Pull request，github 卻顯示這個 Pull Request 有衝突，沒辦法像之前一樣直接合併。  

後來想了一下才發現問題在哪裡，目前repository 的狀況大概像這個樣子，主因就是對方已經搶先 revert 掉我剛送的 merge 了。  

![PRaftermerge1](/images/git/PRaftermerge1.png)

送出新的 Pull Request 的時候，github 會比較兩個 branch 最近的共同祖先，從那個 commit 開始算pull request，在上圖中會是那個”Add features 2” 的commit。  
這時我們從”fix some typo” 送了PR，github 會比較這個新的commit ，跟revert 過後的commit 作比較，因為revert 這個commit 修改的檔案（等同我們Pull Request的修改只是剛好反向），兩者因此有衝突；同時，之前的 commit “Add features 1, 2” 都不會算在這個Pull Request 裡面。  

要修正這個問題，我們必須讓 upstream 跟現在這個 develop branch完全沒有共同祖先，我所知的有兩個解法：  

一個是從開始的master branch開一個新的branch newDev，然後用cherry-pick 把develop 上面的 commit 都搬到這個branch 上，再重送 Pull Request；就如[這篇文](http://stackoverflow.com/questions/25484945/pull-request-merged-closed-then-reverted-now-cant-pull-the-branch-again)中所示：  

```shell
$ git checkout master  
$ git checkout -b newDev  
For every commit in develop branch do  
$ git cherry-pick commit-hash   
```

另外一個方法比較方便，直接在 develop branch 上面切換到 newDev branch，然後使用 interactive rebase ，然後把所有的commit 都重新commit 一篇，newDev 就會變成一個全新的分枝了：  
```shell
$ git checkout develop  
$ git checkout -b newDev  
$ git rebase -i master  
Mark every commits as reword (r) in interactive setting   
```

修正完之後的 repository 大概會長這樣：  
![PRaftermerge2](/images/git/PRaftermerge2.png)

這時候就能由 newDev branch 對上游的 master 送出Pull Request，把這次的修改都收進去了。  

題外話：  
寫這篇時發現了這個工具 [gitgraph.js](https://github.com/nicoespeon/gitgraph.js)，滿好用的，可以輕鬆畫各種git 的圖，雖然說試用一下也發現不少bugs XD，不過這篇文中的圖都是用這個工具畫的。  