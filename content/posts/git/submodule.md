---
title: "使用 git submodule 管理 project 所需的其他模組"
date: 2018-01-25
categories:
- git
tags:
- git
series: null
---

故事是這樣子的，最近在寫一些分析資料的程式，用的是 python 跟 numpy。  
一開始改寫的時候，發現一開始 load 資料的地方，Python 實在太慢了，載入 20000 筆資料耗時超過 150 秒，後來決定用 C++ 改寫載入數據的部分，同時利用別人寫好的 [cnpy](https://github.com/rogersce/cnpy) 這個 project，寫出 numpy 檔案作分析，結果載入速度竟然一口氣降到 4.5s，加速 15 dB，太可怕了(yay。  
為了要使用 cnpy 這個 project，順手研究了一下要如何給使用 git submodule，這篇文章就做個介紹。  
<!--more-->

基本上submodule 利用的場合，就如我上面說，我的 project 要用到其他 project 的程式碼，我希望讓我的使用者能直接拿到其他 project 的程式碼，這樣他們不用自己再去載，麻煩之外可能還會載到錯誤的版本。  
另一方面，我們又不想把對方的程式全部加到我的 repository 裡面，這樣會帶來不好的後果，上游的程式碼修改，要自己手動更新，沒辦法用 git 的方式更新，增加錯誤的機會。  

遇到 submodule 的時候通常有兩種狀況：  
第一種比較常見的，是載了一個別人的project，發現裡面有用到 submodule，例如知名的補齊工具 YouCompleteMe ，裡面針對各種語言的剖析工具都是 submodule，這些專案載下來的時候， submodule 裡面都還是空的，要先用下列指令把 submodule 載下來：  
```shell
git submodule init  
git submodule update  
```
或者可以用一行指令解決：  
```shell
git submodule update --init --recursive --recursive
```
會在 submodule 裡面還有 submodule 的時候，一口氣都設定好。  
又或者可以在 clone 專案的時候就指定要一齊複製 submodule（不過通常在 clone project 的時候還不知道裡面有 submodule，所以…通常不會這樣下）：  
```shell
git clone --recurse-submodules <url>  
```

第二種狀況如我上面所述，我們自己新增一個 submodule，我要做的就是新增 cnpy 為我的 submodule：  
```shell
git submodule add git@github.com:rogersce/cnpy.git cnpy
```
後面的 cnpy 是指定 submodule 要放在哪個資料夾裡面，通常名稱都跟 project 本來的名稱相同，才不會搞混；這時候 git 會把這個 project 下載下來，檢視 status 的話會看到下面的內容：  
```txt
new file: .gitmodules  
new file: cnpy .gitmodules
```
檔案裡面記錄了 submodule 的名字，現在的路徑以及遠端 url，這時用 add 及 commit 將這個 submodule 保存下來。  

在一個有 submodule 的專案裡面工作，會和一般的工作內容稍有不同，當進到 submodule 內部的時候；submodule 從外面來看只是一個參照，如果真的進到這個資料夾，用起來就會像另外一個 git repository 一樣，一樣會有 master 等等 branch，可以用 remote 拉別人的修改下來，或者自己送 commit 出去。  
比較讓人疑惑的通常是在外面的 project，當內部的內容有修改的時候，外面會出現一些讓人很疑惑的訊息，例如當我們對 cnpy 這個 project 新增一個 commit，從外面會看到這樣的訊息：  

```shell
$ git status  
modified: cnpy (new commits)
```

這則訊息的意思是，cnpy 這個 submodule 有了修改，修改的內容是新增了 commits；可以把git submodule 想成一個快照，現在 submodule 的狀態已經脫離這個快照，從 git diff 就會看出差別，最下面是 commit 的修改訊息：  
```txt
git diff  
diff --git a/cnpy b/cnpy  
index f19917f..8f997be 160000  
--- a/cnpy  
+++ b/cnpy  
@@ -1 +1 @@  
-Subproject commit f19917f6c442885dcf171de485ba8b17bd178da6  
+Subproject commit 8f997be1f87279f09054acbdb896162b1e9d3963   
```

這時對這個 submodule 做 add, commit，就會更新這個 submodule 的快照值；另外如果我們想要 submodule 維持在之前的快照上，用 git submodule update ，git 即會將 submodule 簽回到當初記錄的版本：  

```txt
git submodule update  
Submodule path 'cnpy': checked out 'f19917f6c442885dcf171de485ba8b17bd178da6'   
```

不過 update 之後會有一些不好的效果，因為這時 submodule 被強制簽出 `f19917` 這個 commit ，裡面就出現了一些沒有 commit 的修改，在這裡有內容未被 commit，所以它會顯示：  
```txt
git status modified: cnpy (untracked content)
```

從外面會看到 submodule 有修改，但要消掉這個 untracked content 的訊息，就要進到 submodule 資料夾裡面，用 checkout 或 clean 的方式，讓 submodule 的狀態回到 clean 才行。  
但同時也要注意的，這時候 submodule 就處在 detach HEAD 的狀態（在上面的例子，submodule 落後 master 一個 commit ），這時進到 submodule 做些 commit，這些 commit 並沒有 branch 參照，下一次再下 submodule update 的時候，所做的修改就會消失，如果有要修改的話，建議要先在 submodule 裡面生成一個 branch 來保留修改。  

另外一個比較需要注意的，大概就是在移動 submodule 的參照的時候，儘量可以用 git mv 的方式來移動，用 os 本身的 mv 似乎比較容易出問題。  

我想 submodule 我們就講到這裡，可以看看這篇[官方的參考資料](https://git-scm.com/book/en/v2/Git-Tools-Submodules)：  

裡面還有很多 git submodule 神奇的用法，例如從外面用 git submodule 指令一口氣更新所有 submodule 的狀態到最新，把所有 submodule 現下的狀態推送到遠端，等等。  

但我個人認為 submodule 相對來說是比較偏門的指令，自己也是用了這麼久，最近才第一次用到 submodule，大家還是用到再來查文件比較實在。  

而且我個人覺得，在一個有 submodule 的 git repository 裡面工作，很容易把這個 repository 給搞壞掉，而且壞掉之後都很難修，還是離 submodule 愈遠愈好。  
另外話又說回來， git submodule 能管理的相關 project 數量也是有個限度，數量多到一定程度，submodule 也會顯得捉襟見肘，因而 google android 才會另外推 repo 這樣大量 git repository 的管理工具吧。  
