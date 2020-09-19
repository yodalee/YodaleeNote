---
title: "應用git stash 於多分枝之版本控制"
date: 2013-12-19
categories:
- git
tags:
- git
series: null
---

本文是要說明git中stash指令的應用，基本需要先知道git 基本的add, commit，以及branch的功能。  

使用git進行版本控制，branch是相當重要的功能，一般會建議要開發一個新的功能，就要先分出一個新的branch，開發好新的功能後再merge到master的版本內。  
編按：雖然話是這麼說啦，可是筆者在實作時通常還是一個master branch一直commit下去XD。  
當分枝一多的時候，就會出現一些問題，例如在一個分枝中修改到一半的內容，例如：「雷射彈幕」，這時有些點子想要切到另一個分枝中修改其他內容，但這個「雷射彈幕」的功能還沒達到可以commit的等級，就需要stash來暫存目前修改的內容。  
<!--more-->

下面是git stash的相關操作環境範例： 我們有個master branch跟開發中的feature branch，現在在feature branch中開發一個新的feature，加入並commit "featurefile"這個檔案  
```shell
$ git checkout feature  
$ git commit featurefile # 注意一般是不這麼寫的，這裡是為了說明方便。  
some modification on featurefile  
$ git checkout master  
```
這時候我們會得到一個：  
```txt
error:  
Your local changes to the following files would be overwritten by checkout: featurefile
Please, commit your changes or stash them before you can switch branches.
Aborting
```
因為切到master branch會清掉已修改的內容，而git不會輕易讓你這麼做。  

這時候就要先stash(暫存)它，stash有點像commit，不過沒有commit這麼正式，使用：  

* git stash (save)  : 存入一個暫存，可以不打，git stash預設  
* git stash list  : 列出目前有的stash  
* git stash pop  : 取出暫存  
* git stash drop : 刪掉暫存  

在這裡我們就直接git stash，這時候會看到所有還沒commit的修改都已經消失，用 `git stash list`會看到：  

```txt
stash@{0}: WIP on feature: ef9d050 feature initial commit
```

這裡重要的是“０”這個數字，這是stash的index；另外 `feature initial commit` 則是這個stash是這在哪個commit中分支出來的。  

Git stash時還可以加上message來取代上面的ef9d050 feature initial commit這段  
```shell
git stash save "this is temporary stash of master commit"
```
不過這在stash量很少的時候大概不太需要用到。  

現在我們已經可以切回master的branch了。  
在master進行修改後，同樣不想commit的內容也可以用stash進行暫存，這時候git stash list會變成  
```txt
stash@{0}: WIP on master: e194f69 master initial commit  
stash@{1}: WIP on feature: ef9d050 feature initial commit
```
分別標示了從 master 和 feature commit中暫存的內容。  

---

要取出stash的內容，我們用 `git stash pop`，這預設會取出 stash index 0 的內容，如果要取出其他stash的內容，就要用例如：  
```shell
git stash pop stash@{1}
```
在後面打上stash完整名稱。  

取出其他index的內容相當重要，像在例子中，如果我們先切回feature branch，再pop出在master branch中記錄的stash，這個效果和pull是類似的，若是有衝突的檔案就會要求merge，會很麻煩，個人是不建議在這種狀況下進行merge，畢竟當初就是不想記錄下來才用stash，現在要是merge就記錄進去了。  

如果要刪掉已經存入的暫存就用 drop 刪掉即可。  
```shell
git stash drop
```

祝大家git stash愉快