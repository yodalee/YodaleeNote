---
title: "使用 git-svn 和 svn 遠端協同開發"
date: 2017-07-03
categories:
- git
tags:
- git
- svn
series: null
---

最近因為跟人協作，共同開了一個版本控制資料夾。  
對方使用的版本控制是 svn ，而我則是用 git，重新學 svn 實在太麻煩了，有沒有一個好的解決方案呢？經過強者我同學 AZ 大神跟 qcl 大神的推薦，決定使用 git-svn 來解決。  
<!--more-->

git-svn 是 git 提供的一個…橋接工具？可以在遠端保持 svn 的狀態，本地則用 git 的管理，享受 git 那些branch 開很大開不用錢，git stash之類，種種我們再熟悉不過的使用方式；另外用了 git 也不用每次都跟遠端目錄同步，可以在自己家裡亂搞，最後有網路時再一次同步。  
畢竟在 git 出世前，svn 才是世界上版本控制的霸主，有不少早期知名的 project ，例如LLVM, apache software；用了 git svn ，不需重新熟習 svn 也能用 git 參與這些 project 的開發。  

## 簽出

第一步，在拉下 svn repository 的時候，直接使用 git svn 的指令，所有跟 svn 相關的指令都是 git svn xxx：  
```shell
git svn clone http://SERVER/svn/trunk/ TARGET_DIR
```
這樣就會把整個svn給抓下來，它同等於執行 `git svn init` 跟 `git svn fetch`。  

要注意的是因為 git 設計的邏輯就是「所有的機器裡面都有完全一樣的內容」，所以 git svn clone 的時候，它會把遠端的內容逐個載下來，如果遠端 svn 很大的話，這個動作可能會花上非常久的時間。  
抓下來的 repository會產生一個叫 git-svn 的 remote ，這個 remote 只有用 git svn 的時候會動到；
要注意一點，因為 svn 只能維持一條線性的歷史，同時也沒辦法修改歷史，所以在使用 git-svn 的repository 裡面，不要和其他的 git 遠端同時使用，保持所有使用者都用一個 svn 遠端，git svn 設計上也假定你只有一個遠端。  

## 修改
再來我們就能做些修改，一樣就是git add, git commit，這時提交的內容只會在本地中，可以用：  
```shell
git svn dcommit
```
把內容送到 svn 遠端去。  

git 在推送到遠端 svn 的時候，會把一個一個 commit 取出，並提交到 svn，然後最重要的，它會依照svn 的提交結果，重新在 git repository 裡面 commit 這些結果，整個 dcommit 的結果，最終效果更像是 git rebase，這跟一般的 git push 完全不同。  
```txt
commit aea3964417e62759dadf9e1769d927623e0f5a1b
Author: yodalee <garbage@mail.com>
Date:   Fri Jun 30 16:31:30 2017 +0800

    add debug message to every function call

commit 2531676d1d1b81f898e9965c0e46f28e92e02c82
Author: yoda <yoda@59464745-af19-4556-b8ec-ef3a2794439b>
Date:   Fri Jun 30 08:00:23 2017 +0000

    fix description in sensor function

    git-svn-id: http://SERVER/svn/trunk@2345 59464745-af19-4556-b8ec-ef3a2794439b
```

上面的 git log ，包含一個已經推到遠端的 commit 跟一個還未推送的 commit，推送到 svn 上的 commit 會出現 git-svn-id 的遠端資訊，同時它的作者資訊跟雜湊值也會變化。  
這也是為何不建議同一個 repository 中同時使用 git跟svn的遠端，git-svn 修改雜湊值會讓 git 遠端天下大亂。  
就算要有 SVN 跟 git 兩個遠端也要先向svn dcommit ，得到最終雜湊值後，再推送到 git 遠端上。  

## 衝突

svn 身為版本控制，也是允許其他人共同協作，只要有協作就會有衝突要解決，如果發生衝突，svn dcommit 會無法推送到遠端。  

為了解決該問題，可以執行 git svn rebase ，它和 git pull 很像，首先它會用 git svn fetch ，把 svn 遠端上的內容拉下來，沿著 git-svn 往前長，之後再用 git rebase ，把現在 git HEAD 指向的目標，rebase 到 git-svn 上。  
如果沒有更新的內容，在 git svn rebase 時會看到：  
```txt
Current branch master is up to date.
```
此時就能放心進行 git svn dcommit  

## 差異

這裡會牽涉到一些 git 跟 svn 設計不同的地方，在 git 裡面，假設 remote/master 跟本地的 master 有所不同，在 push master 的時候即會發生衝突，git 會要求你解決衝突後才能 push。  
svn 在這點上，只有檔案有所衝突的時候才會要求，所以當遠端修改 A 檔案，本地修改 B 檔案，在 dcommit 的時候是完全沒有問題－－只是遠端專案會進到一個 A, B 檔案都修改過，而本地檔案卻沒看到 A 檔被修改的狀態。  
直接引用 git 文件的話：「如果做出的修改無法相容但沒有產生衝突，則可能造成一些很難確診的難題。」所以，誠心建議還是在 dcommit 前都 svn rebase 一下，確保跟遠端保持隨時同步。  

其實有了 dcommit 跟 rebase，大概也就差不多了，有關 svn branch 的部分我就不太想看了，畢竟 git branch 比較強大；唯一要注意的，大概就是要送到 svn 伺服器之前，儘量用 rebase ，把 git 的各 branch 收整成一條線性，再進行 dcommit 。  
另外有個小技巧是，git svn dcommit/rebase 在操作的時候不允許任何 uncommit 的內容，所以在 svn 操作的前後，可以利用 git stash push/pop ，把未commit 的內容塞進stash，svn 操作結束後再取出來。  

## 參考資料  
<https://git-scm.com/book/en/v2/Git-and-Other-Systems-Git-as-a-Client>