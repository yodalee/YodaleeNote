---
title: "從指定 commit 生成全新的 git 倉儲"
date: 2025-11-11
categories:
- git
tags:
- git
- filter-branch
- filter-repo
series: null
---

故事是這樣子的，最近用了 git filter-branch 把手邊一個 repository 
整理了一遍，因為中途一度碰觸到搜尋引擎也很難搜到的東西~~AI 的邊界~~，
所以就來記錄一下。

<!--more-->

# 問題描述

首先我們先定義好專案狀態，可以先好好看一下情境描述，如果相同的話再往下看下去。  
小弟公司裡面有一個絕贊開發中的 repository，叫 Repo-old。  
有一天我從 master 往外長出一個 dev 的 branch，因為專案架構的關係 dev 很難匯回 master。  
dev 開始加上 commits 以及更多的分枝，例如 dev-faster，dev-faster 與 dev 
之間也是水乳交融，彼此互相都有 merge；這時候 dev 本身儼然就是另一個 master 了。

理論上啦，當初決定分出 dev 的時候，就應該直接分家生出另一個 repository 
了，但總之我們沒這麼做，導致現在 Repo-old 裡面亂成一鍋粥。  
因此，公司決定從 dev 與 master 分家的那一個 commit 分歧點~~分歧路口前途漫漫~~，把過去的 commit 
全部壓扁成一個 commit，未來的把 dev 及 dev-faster 整根剪下來移到新的 repository Repo-new 上面。

這篇就來記錄一下我整個操作的過程，如果以上的情境跟你符合的話就歡迎你參考看看了。

# 名詞定義

以下為了避免混淆與節省描述 commit 的用詞，先定義好操作的對象：
* 舊的 repository： Repo-old
* 要搬去新的 repository： Repo-new
* 工作的資料夾：Repo-migration
* 要搬去 Repo-new 的 branch：dev, dev-faster，其他都不用過去
* 整個 repository 的第一個 commit：ROOT
* dev 與 master 的分歧 commit，即搬的基點：BASE
* 把 ROOT 到 BASE 整個壓扁之後新的 commit：NEWBASE

# 為什麼不能 rebase

比較不那麼破壞性的做法，會是用 git rebase：
1. 在 BASE 上進行 rebase 生成 NEWBASE
2. 把 dev rebase 到 NEWBASE 上就完工了

但這招這次不行，如上所述總共有 dev, dev-faster 兩個 branch 要處理，如果 dev, 
dev-faster 分頭 rebase 到 NEWBASE 上，會導致中間開發過程完全混亂掉。  
另一種選擇是以 dev 為主，dev-faster 只保留最後一次從 dev 中分出來的短 branch
，這個選擇會破壞 dev-faster 的開發過程，因此也不考w慮。

針對這個問題要採取比較**破壞型**的工具，也就是 filter-branch 或 filter-repo。  
注意我上面已經標註破壞型了，所以請千萬小心，確認完再 force push，只要 remote 沒被
 force push 蓋掉就沒問題，本地的隨時都可以刪掉重來。

# 使用 filter-branch 的操作方式

先從比較原始的 filter-branch 開始，以下是操作步驟與解說：

## 1. clone Repo-old

```bash
git clone <Repo-old url> Repo-migration
cd Repo-migration
```

## 2. 建立本地環境

git clone 的時候在本地端只會簽出 master branch，由於 filter-branch 
執行的時候只會改動本地簽出的 branch，因此先把所有要保留的 branch 都簽出：
```bash
git branch dev origin/dev
git branch dev-fater origin/dev-faster
```

做到這一步就可以把 origin 給刪了，以免一不小心就推到遠端去造成問題；因為 master 
沒有要移去 Repo-new 所以也可以刪了。
```
git remote remove origin
git branch -D master
```

## 3. 壓縮歷史

把 BASE 先標出來：
```bash
BASE=$(git merge-base master dev)
git branch BASE $BASE
git branch NEWBASE $BASE

git checkout NEWBASE
git rebase -i --root
```

這裡就看你用什麼編輯器，把 root 至今的 commit 用 squash 或 fixup 壓成一個，
這個新生的 commit 就是 NEWBASE 了。

## 4. filter-branch

以下是我某次實作時的 commit hash：
```txt
BASE = 22c4cb6d3b09c9ccd433083c8cd977f538605034
NEWBASE = 8bf02baa7f0867707722a93febc075a8c9c2a58e
```

執行 filter-branch 指令如下：

```bash
git filter-branch --prune-empty --parent-filter
  'test $GIT_COMMIT = 22c4cb6d3b09c9ccd433083c8cd977f538605034
     && echo "-p 8bf02baa7f0867707722a93febc075a8c9c2a58e"
     || cat' 
     -- --all
```

parent-filter 會執行 test 為首的 bash 指令，其中回傳 `-p hash` 可以修改當下 commit 的 parent
，並有 $GIT_COMMIT 這個環境變數指向現在處理中的 commit hash。  
* 如果 GIT_COMMIT 是 BASE，那就把 parent 指向 NEWBASE
* 反之則直接輸出原本的 parent commit hash

會加上 prune-empty 是因為在 fixup 之後，NEWBASE 已經包含 BASE 內容了，把 parent 改向 NEWBASE 
就會讓 BASE 變空包彈，用 prune-empty 把它移掉；當然如果你有其他的空 commit 就要小心了，他們也會一起被刪掉。

那為什麼我們不檢查 parent 是 BASE 把 parent 改寫為 NEWBASE？  
我也想但查了好像沒辦法這麼做，filter-branch 會提供的環境變數就只有 GIT_COMMIT，沒有 parent hash 
可以比對，而指向 BASE 的 commit 眾多，一一列舉也太麻煩。

## 5. 檢查與推送

到這步 repository 應該乾淨很多，把零星的一些 tag 給刪掉，就應該跟最終目標差不多了，
請仔細檢查一下有沒有預期外的錯誤，接著就能 push 到新的 repository 了。

```bash
git remote add <Repo-new url> origin
git push origin dev
```

## 6. 做錯了怎麼辦？

不用警慌，只要你沒有 push -f，在遠端的資料都會是安全的，把這個資料夾整個移除，再回到第一步開始做吧。

# 使用 filter-repo 的操作方式

上面使用的指令是 filter-branch，在執行的時候，應該會看到如下的內容：
```txt
WARNING: git-filter-branch has a glut of gotchas generating mangled history
         rewrites.  Hit Ctrl-C before proceeding to abort, then use an
         alternative filtering tool such as 'git filter-repo'
         (https://github.com/newren/git-filter-repo/) instead.  See the
         filter-branch manual page for more details; to squelch this warning,
         set FILTER_BRANCH_SQUELCH_WARNING=1.
```

filter-branch 開發用來就是要移除敏感資訊、不小心簽進 git 的二進位檔等等，大約在 2007 
年左右開發（我猜開發的原因一定是有人簽了什麼奇怪的東西），我在 2014 年第一次嘗試
[修改 git 歷史]({{< relref "git_gc" >}})的時候，也是使用 filter-branch。

但 filter-branch 的問題不少，它是使用 git command 在 shell 用一個一個執行，因為效率很差，
我過濾千個 commit 會耗用約莫十秒的時間，以現代電腦來看根本慢得不可思議。

filter-repo 是在 2019 年左右開發的新工具，它改用 python 直接操作 git 
內的資料結構，所以速度遠勝過 filter-branch；同時它精煉過的語法比 filter-branch 更乾淨更好懂。  
python 做為 scripting language 也允許更高的彈性，能對 repository 進行更精細的操作，相關的比較可以參考
[覺得 git filter-branch 很難用？試試看 git filter-repo！](https://ithelp.ithome.com.tw/articles/10257482)。

不過 filter-repo 還比較新參考文件還略顯不足，畢竟會有清洗 git repository 
的需求本來就少，解答散落各處不一定查得到。

以下是使用 filter-repo 來完成上述 filter-branch 的操作：

## 1. 安裝 filter-repo

ubuntu 可使用 apt 安裝 `apt install git-filter-repo`。

## 2. 使用 filter-repo 進行修改

以下這個是 AI 給出的答案，callback 中使用的 python code 是合邏輯的，檢查 commit.parents 
並把其中的 BASE 替換成 NEWBASE：
```bash
git filter-repo --force --commit-callback '
NEWBASE = b"8bf02baa7f0867707722a93febc075a8c9c2a58e"
BASE = b"22c4cb6d3b09c9ccd433083c8cd977f538605034"

commit.parents = [NEWBASE if p == BASE else p for p in commit.parents]
'
```

但這個指令沒有效果，有效的答案是下面這個，就 code 邏輯來看也會如 filter-branch 一樣出現一個空的
 commit，但 filter-repo 似乎自動處理了這個問題：
```bash
git filter-repo --force --commit-callback '
NEWBASE = b"8bf02baa7f0867707722a93febc075a8c9c2a58e"
BASE = b"22c4cb6d3b09c9ccd433083c8cd977f538605034"

if commit.original_id == BASE:
  commit.parents = [NEWBASE]
```

# 結論

其實這一切都很浪費時間與精力，我自己也是在 local 重複了無數次才得到一個令人滿意的結果，
還是勸大家非到必要的時候不要來這招，用正常的 git 操作來處理才是正途。  
也是托這次的福，知道 git filter-repo 這個全新修改歷史的工具，使用起來確實比
filter-branch 還有更有效率得多，以後有這類的需求一律推薦改用 filter-repo。

