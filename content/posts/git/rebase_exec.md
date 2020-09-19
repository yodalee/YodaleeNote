---
title: "使用git rebase 進行Pull Request 檢測"
date: 2014-11-24
categories:
- git
tags:
- git
series: null
---

故事是這樣子的，自從我被加到Qucs project的專案小組，原本的管理員又因為博班進到最忙的時間開始比較少管事，變成我在管專案的Pull Request(PR，拉取要求)。  
其實管就管，反正這個project 沒人鳥，平常也沒什麼PR進來；不過有PR進來的時候，還是要做適當的檢查，以下提一下幾個檢查PR的流程：  
<!--more-->

首先是把PR拉到本地資料夾，這部分參考 [github 的支援文件](https://help.github.com/articles/checking-out-pull-requests-locally/)  

```shell
$ git fetch origin pull/ID/head:BRANCHNAME
```
其中 ID 是github上Pull request 的編號，branchname則是你隨便取；這樣就會把網路上的提交全部拉下來，並創建一個新的分枝。  

接著就要做點檢測工作，最重要的是所謂的阿蹦大神規則：**每個提交都必須能編譯成功**。  

這裡我會選用git rebase 搭配execute：  
```shell
git rebase -i master –exec "make -C path"
```
git 就會在每個提交間插入一個執行make 的command，要注意git 在rebase 時的目錄位置是在專案最頂層的目錄（.git資料夾的所在），所以make 的路徑必須設好，不然 rebase 會找不到make檔案，直接出錯；git會輸出下列的文件，在提交間插入執行命令，如果有提交不想要執行，可以手動移除掉。  
```txt
pick 92c96a8 Add Xcode support to gitignore  
exec make -C qucs/build  
pick 0cdd379 Bugfix: LANGUAGEDIR  
exec make -C qucs/build  
pick 9a695b0 Skip Qt3 support for qucs-help  
exec make -C qucs/build execute的規則如下：  
```
執行的指令如果回傳值非零，表示執行出錯，rebase 即會暫停在當前的提交，讓你有機會修正錯誤，可以使用git rev-parse HEAD來抓到當前的提交雜湊。  

這樣就能放著電腦一直跑，反正出錯了就會停下來，表示這個Pull Request是有問題的，還不能合併到主線內。  