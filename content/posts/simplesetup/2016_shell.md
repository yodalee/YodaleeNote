---
title: "整理一些增進效率的shell 工具"
date: 2016-11-09
categories:
- simple setup
tags:
- autojump
- fzf
series: null
---

最近整理了一下自己工作上有在用的一些shell 工具或指令，在這裡分享一下，也許能讓大家工作更有效率。  
<!--more-->

## shell:

沒錯不要懷疑，就是shell，[shell 本身就有不少快捷鍵](https://blog.longwin.com.tw/2006/09/bash_hot_key_2006/)可用  
不過其實不少快捷鍵都有更好記的單鍵可代替，例如到行首尾可以用Home 跟End，平常比較常會用到的其實只有：  

* Ctrl + W 刪除一個詞
* Ctrl + R 後打關鍵字，可以找上一個拿關鍵字的命令
    * 按 Ctrl + R 持續找，光是用Ctrl + R 就海放只用↑↓在找指令的了(X，不過用了下面的fzf ，它會用fzf 代替單純的 Ctrl + R搜尋
* Ctrl + L 可以清除畫面，跟下clear 是一樣的效果，而且clear 打起來超級快，最近還在習慣用Ctrl+L；
我覺得這個重要的是在gdb 裡面沒有clear 指令，要用Ctrl+L來清除畫面。

## [autojump](https://github.com/wting/autojump)

本指令感謝AZ 大神的推薦，一個記錄你cd 過的地方，以後可以直接 jump 過去的指令  
主流的linux 都有套件支援了，安裝後在shellrc 裡面source 它即可  
```bash
if [[ -e /usr/share/autojump/autojump.zsh ]]; then
  source /usr/share/autojump/autojump.zsh
fi
```

接著它需要一點時間train 一下，平常cd 的時候它就會把cd 的資料夾記下來，之後就能用  
```bash
j foo  
jo foo
```
前者cd到名稱含有或近似foo 的資料夾，後者直接開視窗的file manager檢視該資料夾。  
也可以下多個參數，例如：  
```txt
victim/alice/data  
victim/bob/data
```
如果只下j data 可能會跳去alice的資料，但下了 j bob data 就能跳到後者  

我記得我在寫minecraft plugin 的時候，差點沒被java 氣死，為啥source code 一定要藏這麼多層勒，光cd ../../../ 就累死了，
那時沒用autojump 深感相見恨晚；後來寫一些包含不少小專案，還要source sdk 的android project ，這個指令也幫了大忙。  

## fzf

本指令感謝士銘大神推薦，[fzf](https://github.com/junegunn/fzf) 是一個模糊搜尋工具，讓你列出很多的東西，然後模糊查找目標：  

目前還在習慣中，安裝的話透過它github 頁面上的script 安裝即可：  
```bash
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install
```

archlinux 則有收到repository 中，安裝repository 之後在shellrc 裡面加上  
```bash
source /usr/share/fzf/completion.zsh  
source /usr/share/fzf/key-bindings.zsh
```
最一般的使用方式，是把其他會吐出一堆東西的指令當作fzf 指令的輸入，fzf 會把輸出全列出來，然後讓你打字進行模糊搜尋，
或者用上下選取，用一下就覺得快若閃電，絲毫沒有延遲，例如：  
```bash
locate servo | fzf  
find -type f | fzf
```
加了key-bindings.zsh 之後就連上面的Ctrl+R 也會變成fzf 模式，潮爽der；
fzf 也有跟vim 綁定，不過這部分我沒試用，暫時先持保留意見。