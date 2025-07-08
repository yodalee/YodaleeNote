---
title: "使用vimdiff來解決git merge conflict"
date: 2013-03-29
categories:
- git
tags:
- git
- linux
- vim
- vimdiff
series: null
---

最近同時家裡用筆電跟辦公室用桌電，在兩個地方使用 git/github 來管理程式作業，這兩個東西加起來根本神物，本來要用隨身碟同步的東西，現在可以用 git 直接完成。  
關於git的基本介紹我就不解釋了，網路上隨便一找就有一堆資源，我當初是看 [progit](http://git-scm.com/book)來學git。    
用 git 會遇到的問題是：有時候檔案在github上的檔案已經更新，本地的檔案也有修改過，這時候若想要 git pull 的話會產生conflict，這時候就需要把~~本地的檔案刪掉重新clone~~使用merge來解決衝突，偏偏作者手殘常常把檔案 merge 成連<<<, >>>都保留下來的檔案，相當麻煩；這次好好的研究一下怎麼用vimdiff作為merge的工具，在這裡記錄一下。    
<!--more-->

首先呢，我們可以先設定vimdiff為git default的mergetool
```shell
git config --global merge.tool vimdiff
```
為什麼？沒辦法，用vim就是潮(誤)    

那麼來merge吧，輸入
```shell
git mergetool
```
這時候應該會打開vimdiff，然後產生左上角、中上、右上、下四個視窗，如下圖所示：
![vimdiff1](/images/git/vimdiff1.png)

* 左上：local 顯示本機的檔案內容，現在這個git資料夾的版本
* 右上：remote：顯示遠端，你要merge的分枝
* 中上：base：顯示上面兩個分枝共同基礎的內容
* 下：merged：顯示merge的內容  

下方的版本會是包含了那堆<<<<<<, >>>>>> 的版本，我們的目標就是把下面視窗修到 merge 完成後我們希望的版本。

到了這裡就開始解衝突啦，事實上不單是git，平時如果有兩個很像的檔案要合併，也可以用 vimdiff 開啟來解，使用的指令是這些：

* [c：跳到上一個衝突點
* ]c：跳到下一個衝突點
* :diffget，從某個視窗取得內容
* :diffput，把內容丟去某個視窗  

可以用:help do, :help dp查怎麼用，不過兩個指令的基本格式是： `:[range]dp|do bufspec`   

如果是雙方比較，那就沒什麼好說的，do/dp的對象就是另一個視窗的內容，這時候只要在衝突點在一般模式下用dp,do即可。  

但如果是現在這種3方比較時，就沒辦法這麼方便，而是要直接輸入 `:diffget/put bufspec` 來操作（可以打diffg, diffpu來少打幾個字，不過差不了太多=w=）。  

以上圖為例，我們游標停在下面的衝突點上，要使用remote的視窗內容。  
這裡 bufspec （用哪個視窗的內容）有兩種指定方式：  

1. 先用 `:buffes`，確認remote那個視窗編號，我是4號，因此用 `:diffget 4`
2. 用關鍵字，這個超強，用 `:diffget REMOTE`（因為git自動命名暫時檔名為 XXXX.REMOTE.yyy, XXXX.BASE.yyy, XXXX.LOCAL.yyy）即可。 

如此就會套用 remote 的內容了，經過幾次套用之後，畫面可能會變得有點亂，這時候可以用 `:diffupdate` 來重新產生diff的格式。  
![vimdiff2](/images/git/vimdiff2.png)

用上面的步驟，就可以快速的完成解衝突的工作，做完之後，在下面的合併檔存個檔離開吧。    

## 參考資料：
1. [vim wiki about git vimdiff](http://vim.wikia.com/wiki/A\_better\_Vimdiff\_Git\_mergetool)
3. vim help:  `:help diff` 