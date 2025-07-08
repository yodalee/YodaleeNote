---
title: "git partial add"
date: 2013-10-29
categories:
- git
tags:
- git
series: null
---

Git 是一款極為強大的工具，雖然說過於強大的功能有時會讓人感到卻步，我也是一項功能一項功能慢慢學，不會的時候就抓著會的同學問，好不容易才變得比較會一些。  
最近新學會的功能是git的partial add功能，在這裡做個簡單的介紹：  

使用 partial add 的功能，可以讓我們每次只 commit 一部分的東西上去，假設我在某程式開發了讀取、寫入兩樣功能，比較好的做法是讀取部分和寫入部分可以分開commit。  
有一部分原因應該是這樣比較分得清楚，如果之後要從這個commit中取出修改內容，或是再修改時都更清楚一點，雖然說筆者到現在也沒有做過這樣的事，不過養成一個好習慣也是好事。  
<!--more-->

要partial commit，第一步是先partial add：  
假設今天我對一個main.c的檔案，新加上兩個function foo1, foo2，這時候使用git add -p main.c，git顯示出main.c裡面有差異的部分，這時候可選選項：  
![partialadd1](/images/git/partialadd1.png)

y,n,q,a,d,/,s,e,?  
* y/n: 加入/不加入這個區段  
* q/a: 不加入/加入整個檔案  
* d: 不加入這個區段，跟之後所有的區段；我得承認不確定它跟q的差別...  
* /: 尋找regular expression；啊老實說我也沒用過OAO  
* j/k: 跳到後/前一個undecided 區段  
* J/K: 跳到後/前一個區段  
* s: 分開這個區段  
* e: 手爆編輯這個區段  

一般來說，git 會把相近的修改區間放到同一個區段裡面，下 (s)plit 指令，git 會用原檔案中「未修改的部分」把修改區間切開，例如圖中 fun1-fun3 是同一個區間，下 s 的話 fun1, fun2 會被切成一個區間，fun3 切成另一個區間，但 s 並不會切開 fun1 和 fun2。  

![partialadd2](/images/git/partialadd2.png)
如果fun1, fun2要分開commit的話，就要用(e)dit，跳出編輯器介面。  
新加入的修改會有 '+' 在行首，不加入的話刪掉即可。  
刪除的則是 '-' 在行首，不加入的話把 '-' 替換成 ' '，這個用 vim的 ctrl+v 很容易就可以做到。  
筆者試過一次在這個狀態下去修改原始碼，git 會叫說 patch 產生錯誤，大概是不能這麼做，只能把你加上去的內容刪掉，或是刪掉的內容 mark 成 ' ' ，不要把這個刪除簽進這個修改。   

commit 時，直接 git commit 就可以把 add 過（正式名字應該是 staged）的內容 commit 上去。  
這時不要使用 git commit main.c，這會將檔案內容全部 staged 然後 commit 上去，有一次筆者先 partial add 後下了 commit file，再下 git status 就發現這個檔案已經全部 stage 進去了，沒什麼修改可 stage…。  

另外一個要注意的是用 partial add 的話，在回復的時候一定要非常小心，例如在上例中我們add了fun1 這時候原始碼的狀況是：  

* main() → 上一個commit  
* fun1() → staged  
* fun2() → unstaged  

注意到fun2是unstaged，如果你亂改到什麼想要回復，而下：  
```shell
git checkout main.c
```
回復到上一個狀態，fun2 的原始碼（該說它從來沒被記錄下來）也會整個被消掉。