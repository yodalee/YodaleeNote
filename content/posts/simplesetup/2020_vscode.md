---
title: "第一次跳槽 vscode 就上手"
date: 2020-05-16
categories:
- simple setup
tags:
- git
- linux
- rust
- c
- cpp
series: null
---

故事是這樣子的，小弟第一次學寫 code 的時候，是在大一修計算機程式（嚴格來說是高三下學期上了幾個小時的 C，不過那實在稱不上是"學"）的時候，第一個使用編輯器是破舊破舊的 Dev C++ ，我打這篇的時候差點都忘了它叫 Dev C++ 了。  
當然那時候的功力跟現在實在是天差地遠，淨寫一些垃圾，啊雖然現在也是淨寫一堆垃圾…。  
總之後來應該是大二，被同學們拉去演算法課上當砲灰，第一次接觸了工作站 + vim，從那時候把 Dev C++ 給丟了跳槽到 vim，就一直用到現在，
之中當然也會用一下其他的編輯器，像是改 windows 的 .NET 程式用到 Visual Studio，但大體還是以 vim 為主力，算算也是超過 10 年的 vimer 了。  

不過這兩三年在工作上、日常 project 上面，多多少少都見識到 vim 的不足之處，例如
* 新語言（主要是 rust）支援不足
* 跟編譯除錯工具整合不佳
* 跟 GUI 整合不佳
* 跟 Git 整合不佳要另外開終端機跟 gitg
* 自動格式化/排版操作麻煩而且通常排不好

正好此時 Microsoft 回心轉意擁抱開源，推出了 vscode，隔壁棚的 emacs 有大神跳槽[鬧得風風雨雨]( https://gist.github.com/kuanyui/11be51ee7894a9f01ce438a97dcffcb6)，
台灣 CUDA 第一把交椅強者我同學 JJL 也跳槽 vscode 惹還來傳教。  
<!--more-->

正好最近寫 code 沒什麼靈感，而且最近正好武漢肺炎的關係時機歹歹，就來試著跳槽一下吧（？，
到目前為止用 vscode 對最近碰的一個 ncollide package 做了一些除錯的工作，筆記一下到目前為止的設定還有使用方式的筆記。  

# 擴充功能

vscode 基本上的優勢就是是它編輯/建構/除錯三位一體的編輯介面；還有它的擴充功能，用過的都說讚。  
擴充方面主要參考的文件有兩個：

1. [VSCode 如何提高我的寫扣效率](https://larrylu.blog/vscode-tips-fe3320f9032a)
2. [小克的 Visual Studio Code 必裝擴充套件](https://blog.goodjack.tw/2018/03/visual-studio-code-extensions.html)

另外台灣 CUDA 第一把交椅強者我同學 JJL 大大也有推薦一些：  

擴充的安裝方式是從左邊的選單選 Extension，再搜尋你想要找的擴充名字：

* [vim 擴充]( https://marketplace.visualstudio.com/items?itemName=vscodevim.vim)  

## 語言相關：  
* [C/C++](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools)：
* [Clang-Format](https://marketplace.visualstudio.com/items?itemName=xaver.clang-format)
C/C++ 語言擴充，包括文字上色、定義跳轉等等都需要。
Clang-format 需要另外安裝 clang 的執行檔，~~終結宗教戰爭的好工具~~。
* [Python 擴充](https://marketplace.visualstudio.com/items?itemName=ms-python.python)：
* [autopep8](https://marketplace.visualstudio.com/items?itemName=ms-python.autopep8)
Python 語言擴充，autopep8 也是排版工具
* [Rust Analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)：
可以直接在寫程式的時候幫你自動附注型別等資訊，讓 vscode 變 rust 神器。
* [VerilogHDL](https://marketplace.visualstudio.com/items?itemName=mshr-h.VerilogHDL)
verilog 與 SystemVerilog 上色工具

## 工具類
* [Vim](https://open-vsx.org/extension/vscodevim/vim)：
整合 vim 編輯器，畢竟習慣了這樣打字效率才會高，想要手跟鍵盤黏踢踢就一定要裝  
* [Git Graph]( https://marketplace.visualstudio.com/items?itemName=mhutchie.git-graph)：
整合 gitg 類似的圖形化顯示工具到介面，git 管理上當然可以靠打字，但看歷史還是看圖方便  
* [GitLens]( https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)：
還沒試過，強者我同學 JJL 推薦的  
* [CMake](https://marketplace.visualstudio.com/items?itemName=twxs.cmake)
可以直接用 Ctrl + Shift + P 執行 Cmake configure, build, test 等指令，非常方便
* [Docker](https://open-vsx.org/extension/ms-azuretools/vscode-docker)
最近開始試用 docker 管理所有的開發環境，可以在 vscode 裡面新增/管理/連線所有 docker image，非常方便  

## 其他
* [TODO tree]( https://marketplace.visualstudio.com/items?itemName=Gruntfuggly.todo-tree)：
統一管理 project 內部的 TODO, FIXME, XXX  
* [Trailing Spaces]( https://marketplace.visualstudio.com/items?itemName=shardulm94.trailing-spaces)：
自動刪掉程式碼行尾的空白  
* [Markdown Github Style]( https://marketplace.visualstudio.com/items?itemName=bierner.markdown-preview-github-styles)：
編輯 markdown 文件時可以直接預覽輸出的格式，解決每次編輯 Github README.md 都要一直 push -f 直到格式完全改對為止，
這點很強烈的突顯出 vim 等純文字編輯器無法和圖形整合的弱項，以致在 markdown、LaTex 這類文字和顯示有相互關係的文件編輯會很吃虧
（好啦好啦我知道有人能人腦 render latex 的）。  

# 怎麼建構專案？  
在 vscode 裡面的建構叫 [task]( https://code.visualstudio.com/docs/editor/tasks)，
在選單 terminal 下面的 run Task 跟 run Build Task (Ctrl + Shift + B)，沒有 cargo 預設的話就要自行編輯 tasks.json，
以下是我這次 debug 時使用的 tasks.json  
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "cargo run",
      "type": "shell",
      "command": "cargo",
      "args": ["build"],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```
應該滿直覺的，就是呼叫 cargo build 幫我編譯整個專案；在寫完 code 之後使用快捷鍵 Ctrl + Shift + B 就能編譯專案了。  

# 如何除錯：  
[除錯](https://code.visualstudio.com/docs/editor/debugging)是 vscode 一項殺手級的功能，
vscode 公開一個 API 讓安裝的語言擴充使用，需要什麼語言的除錯安裝擴充就好，像我上面就安裝了 C/C++, Python, Rust 的擴充。  
如果我記憶沒錯的話，跟 visual studio 一樣，vscode 快捷鍵是也執行 Ctrl + F5 跟除錯 F5：  

## 用 Ctrl + Shift + D 展開 debug 介面。  
理論上用滑鼠在原始碼旁邊點一下就能加上 breakpoint，不知道是 Rust 還是 lldb 的問題，我用滑鼠加上去的 breakpoint 都煞不住，
至少一定要先在 debug console 裡下一個 b main 讓程式煞住之後，用滑鼠加的 breakpoint 才會有用，真的很奇怪。  
另外就是 debug console 的指令跟習慣的 gdb 有點不同要重新習慣，最奇怪的大概是按了 enter 竟然不會重複上個指令，
這樣要一直按 n + enter + n + enter 怪麻煩的，只能去習慣 vscode 的除錯指令：F10/next、F11/step、Shift+F11/finish 了。  

這次最主要的目的是要對 Rust 程式除錯，我參考的是下面[這篇文章](https://www.forrestthewoods.com/blog/how-to-debug-rust-with-visual-studio-code/)…不過試用之後沒有成功  

首先我們要加上一個 launch.json 告訴 vscode 要怎麼跑除錯的程式：  
```json
{
  "version": "0.2.0",
  "configurations": [
  {
    "name": "Debug example contact_query2d",
    "type": "lldb",
    "request": "launch",
    "program": "${workspaceRoot}/target/debug/examples/contact_query2d",
    "args": [],
    "cwd": "${workspaceRoot}",
  }]
}
```
再來用 F5 就能開始除錯了，但不知道為什麼我 step into 一個函式，瞬間都變成 assembly code，連 stack 資訊都爛掉了，根本無從 debug 起，
感覺是 vscode 哪裡跟 lldb 沒弄好，不是 vscode 的問題，畢竟我在終端機用 rust-gdb 一樣會有問題，
正好反過來如果下 b main 停下來的話，rust-gdb 下一步會停不下來，一口氣跑到 main 的尾巴…。  
這個問題一時之間好像無解，也許要等 rust 跟 codelldb/gdb 真的接好之後再來看看了。  

# 快捷鍵操作：  
Ctrl + KT 叫出 color theme 設定，我用的是 light 的 Solarized Light ，最近眼睛好像不太適合全黑的畫面了QQ。  
Ctrl + P 開檔案，這部分已經整合了 find 要用 wildcard 才能找的功能，方便不少。
Ctrl + Shift + F 全文搜尋，等於是有個 grep 帶著走，雖然沒有 regular expression 但已經十分夠用了
Ctrl + Shift + P 開始指令輸入框，一樣支援模糊比對
Ctrl + , 開啟設定，在安裝完模組之後可以快速做各種設定
Ctrl + ` 開啟整合式終端機
Ctrl + Shift + ` 開啟一個新的終端機分頁
Ctrl + PageUp/PageDown 在終端機分頁間切換

# 結語：
回頭一看怎麼一堆快捷鍵，不過算啦，跟 vim 的快捷鍵比起來這還是算少的吧XD；話說大概是「把手留在核心區」這個哲學的關係，
vim 大部分的按鍵都少有用 Ctrl/Alt 開頭的，剛好一般的圖形應用程式包括 vscode ，大部分的快捷鍵都是 Ctrl/Alt 開頭，
也因此在操作上面，vim 很容易就能跟桌面應用程式整在一起，就像是瀏覽器的 vimium 跟 vscode vim 擴充。  

