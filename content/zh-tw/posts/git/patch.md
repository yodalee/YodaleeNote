---
title: "使用 git patch 來搬移工作內容"
date: 2017-03-09
categories:
- git
tags:
- git
- patch
series: null
---

前幾天在改一個專案，因為筆電的設備不夠強大，只能到桌電上開發，兩邊都是開發機，也就沒有用remote 的方式來同步專案。今天，要把那時候的commit 搬回筆電，只好使用git 的patch 移動工作內容，這裡記錄一下整體工作流程和解決衝突的方法。  
<!--more-->

## 生成 patch
首先是生成 patch，git 本身有兩種 patch 的功能，
1. 使用常見的diff  
2. git 專屬的patch system  

常見的 diff 其實也就是git diff 生成的 patch，內容就是：這幾行刪掉，這幾行加上去，用 git diff > commit1.patch 就能輕鬆生成。  
git patch system 則是用 git format-patch 來產生，它提供比 diff 更豐富的資訊，他的使用有幾種方式：  

1. git format-patch <commit>  
從某一個 commit 開始往後生成patch  
2. git format-patch -n <commit>  
從某一個 commit 開始從前先成 n 個patch   

使用format-patch的好處是，它可以一次對大量的commit 各產生一個patch，之後就能用git 把這些commit 訊息原封不重放到另一個 repository 裡面。  
我自己的習慣，是開發一個 features 就開一個新的branch，這樣在生成 patch的時候只要使用format-patch master，就會把這條分枝的 commit 都做成patch，git 會自動在檔案前綴 0001, 0002，這樣用 wildcard patch 時就會自動排序好。  

你說如果 patch 的數量超過10000 個怎麼辦……好問題，我從來沒試過這麼多patch，搞不好我到目前為止的 commit 都沒這麼多呢，一般project 超過 10000 個commit ，還要用patch system 來搬動工作內容也是滿悲劇的啦  

## patch 內容
細看 patch 的內容，開頭是這個commit 的概略訊息，修改的檔案小結，後面就是同樣的diff 內容。  
```txt
From commit-hash Mon Sep 17 00:00:00 2001
From: author <email>
Date: Mon, 6 Mar 2017 14:07:42 +0800
Subject: [PATCH] fix getDates function

---
database.py  | 9 +++++----
viewer.py      | 5 +++++
2 files changed, 10 insertions(+), 4 deletions(-)
```

## apply patch
現在我們來使用 patch ，把這些patch檔拿到要apply 的repository裡  
針對常見的diff，其實用shell 的patch 指令就能apply 上去，但它出問題的風險比較高，也不能把 commit 訊息帶上，所以我都不用這招。

對format-patch產生的 patch，我們就能用 git apply 的指令來用這個 patch，首先先用  
```shell
git apply --check patch
```
來檢查 patch 能不能無縫補上，只要打下去沒噴訊息就是正常。  

接著就是用 git apply patch 把patch 補上，然後記得自己commit 檔案。  

這樣還是太慢，我們可以用  
```shell
git am *.patch
```
把所有的 patch 一口氣送上，運氣好的話，會看到一整排的 `Applying: xxxxx`，所有的commit 立即無縫接軌。  

## patch conflict
如果運氣不好，patch 有衝突的話，apply 就會什麼都不做。  
衝突其實很常見，只要你產生patch 跟apply patch 的地方有些許不同就會發生，因為patch 裡只記載了刪掉哪些內容、加上哪些內容，一旦要刪掉的內容不同，apply就會判斷為衝突。  

這跟merge 的狀況不同，merge 的時候雙方有一個 base作為基準點，可以顯示 `<<<<<< ====== >>>>>>` 的差異比較，apply 的資訊就少很多。  

在 apply patch 的時候，也可以使用 `git apply -3` 來使用3方衍合，但若你的repository 中沒有patch 的祖先，這個apply 一樣會失效。  
衝突時am 會跳出類似這樣的訊息：  
```txt
Applying: <commit message>
error: xxxxxxxxxxxxxxxxxxx
Patch failed at 0001 <commit message>
The copy of the patch that failed is found in: .git/rebase-apply/patch
When you have resolved this problem, run "git am --continue".
If you prefer to skip this patch, run "git am --skip" instead.
To restore the original branch and stop patching, run "git am --abort".
```

這裡我們只能手動解決，在apply 的指令加上：  
```
git apply --reject patch
```
這樣會補上那些沒有問題的patch， 然後把無法補上的地方寫入 .rej 檔案中。  

下一步我們要用編輯器，打開原始檔跟 .rej 檔，把檔案編輯成應該變成的樣子，把該加的檔案變化都git add add 之後，使用 git am --continue 完成commit。  
後悔了，直接用 git am --abort 停掉 am 即可。  

以上是git patch system 的簡介，我的心得是，能用git remote 就用git remote，merge 起來資訊豐富很多，解決衝突也有git-mergetool 如vimdiff 可以用，省得在那邊 format-patch 然後apply 起來機機歪歪，每個commit 都要手動解衝突是會死人的。  

## 參考資料  
<https://git-scm.com/book/en/v2/Distributed-Git-Maintaining-a-Project>  
<http://aknow-work.blogspot.tw/2013/08/patch-conflict.html>