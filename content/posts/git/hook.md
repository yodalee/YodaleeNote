---
title: "使用git hook在commit 前進行unittest"
date: 2016-12-30
categories:
- git
tags:
- git
series: null
---

使用 git 做為版本控制系統已經有一段時間了，最近在寫Facebook message viewer 的時候，就想到能不能在本地端建一個 CI，每次 git commit 的時候都會時自動執行寫好的測試？  
查了一下就查到[這一個網頁](https://www.atlassian.com/continuous-delivery/git-hooks-continuous-integration) 裡面有相關的教學：  
在這裡記錄一下相關的設定。  
<!--more-->

Git hook 可以想成git 的plugin system，在某些特定的指令像是commit, merge的時候觸發一個script。  
Hook 可分為 client side 和server side，又有 pre-hook 跟 post-hook 的分別

* pre-hook 在指令執行前觸發，並可取消行為  
* post-hook 得是在指令結束後執行，它無法取消行為只能做其他自動化的設定。  

網頁中有給一些使用範例：  

* Client-side + Pre-hook: 檢查coding style  
* Client-side + Post-hook: 檢查repository 的狀態  
* Server-side + Pre-hook: 保護master  
* Server-side + Post-hook: broadcast 訊息  

所有的hook 會放在.git/hook 資料夾裡面，在開啟專案時就有預設的一些範例，只要拿掉檔名的 .sample就能執行，它們是從 /usr/share/git-core/templates/hooks/ 複製而來。  
望檔名生義，這些檔名大多直接了當的指名它們的功用；有些script 如 pre-commit 在回傳非零值時，能阻止git 接受這次commit；詳細的使用方法跟觸發時機請見參考資料。  

這裡我想做的是用 Client-side + Pre-hook ，在每次commit 前都先跑過一次測試，如果測試不過就拒絕此次commit，所以我們用到的是 pre-commit。  
首先先在project 裡面加上一個test.py，用來統整所有的test script，這樣就可以用 python test.py 跑過所有測試，可以先在command line 測一下：  
```shell
python test.py || echo $?   
```
pre-commit script 就很簡單：  
```shell
#!/bin/sh

python test.py || exit 1
```
這個 || exit 1 是要確保pre-commit script 一定以錯誤結束，如果這個測試之後就沒有其它測試就不需要這段，因為script 會回傳最後一行command 的回傳值。  

另外，如果不想在打下commit 的時候出現 unittest 的輸出，可以改寫成：  
```shell
#!/bin/sh

python test.py 2>/dev/null
if [[ $? -ne 0 ]]; 
then
  echo "> Unit tests DID NOT pass !" exit 1
fi
```

注意後面的判斷跟echo 是必要的，否則python 輸出導向null之後，使用者打git commit 會變成完全沒有反應，這顯然不是個好狀況；完成之後，試著下git commit，就會發現test 不過，而不像正常流程一樣跳出commit message編輯器：  
```txt
Garbage@GarbageLaptop $ git commit  
.F  
======================================================================  
FAIL: test\_zh\_tw (\_\_main\_\_.REdictParseTest)  
----------------------------------------------------------------------  
Traceback (most recent call last):  
File "test.py", line 17, in test  
assert(ans == parse)  
AssertionError  

----------------------------------------------------------------------  
Ran 2 tests in 0.007s  

FAILED (failures=1)    
```

我的建議是在 test case 有一定規摸的時候，足以進行TDD 的時候才引入此流程，或者要先把test 裡都加上expected failure ，否則有test 不過就會讓git 根本commit 進不去，如果又因為過不了就每次都下git commit --no-verify，就失去TDD 的意義了  

另外，請記得所有要跑的 script 一定要有執行權限，之前試了一段時間，每次commit 還是都commit 進去，後來發現是 pre-commit 沒有執行權限lol。  
hook 內的東西clone 的時候也不會複製到 client side，要把它們包到repository 裡面，再由使用者自己把script 加到.git/hook 裡。  

這裡大致介紹 git hook 的簡單用法，網路上能輕易找到許多亂七八糟的script 來做各種事，例如用autopep8, cppcheck 檢查語法是否合標準，自動跑npm test 等等。  

## 參考資料  
* [git hook in gitbook](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)  
* [stackoverflow](http://stackoverflow.com/questions/2087216/commit-in-git-only-if-tests-pass)