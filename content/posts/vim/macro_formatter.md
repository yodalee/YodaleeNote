---
title: "用vim 巨集整理文件格式"
date: 2017-02-22
categories:
- vim
tags:
- vim
series: null
---

曾經有一次，從外面匯入一個project 的程式碼，林林總總大概 10 幾個C 的source跟header，每個檔案幾十行到幾百行不等。  
打開一看，關掉，哎呀我的眼睛業障重呀  
唔…是沒這麼誇張，但裡面充斥著行末空白、排版有點糟糕，然後有些tab 跟空白混用，研究了一下，可以用vim 把這些程式都整理整理。  
<!--more-->

## trailing space
在刪掉trailing space 的部分用 [vim-better-whitespace](https://github.com/ntpeters/vim-better-whitespace)。
這樣就能在文件中使用StripWhitespace 指令刪掉所有行末空白。  

## 排版
排版用vim 本身的排版功能，一般文件可以用 = 就會排好了，不過如果是python 的話就沒辦法，
它不像C 有明確的分號跟大括號來表示縮排結束，所以這招對python 是沒用的，用了只會一直不斷的縮排下去。  

## tab
把tab 換掉的部分，我基本上是space 派的(戰，這也可以用vim 的取代功能很快做完，不過我們要用ge 來suppress error ，以免文件中不存在tab 的狀況停掉巨集執行。  

## 巨集
我們利用vim 的巨集功能，把上面幾個結果串在一塊，選一個喜歡的英文字母 (這裡用y，因為我最喜歡y了)，依序輸入下面的指令，打完一行就按一下enter，#後面的表示註解：  

```vim
q
y #將巨集存在 y 暫存區
:StripWhitespace  #清除trailing space
:%s/\t/ /ge  #全文件取代tab 為雙空白
=G  #全文件重新排版
:w  #記得存檔，神明保佑(X
:n  #編輯下一份文件
q
```

然後關鍵的一步來了，我們的巨集在執行完就會跳到vim 暫存區的下一個檔案，現在，我們在project 目錄裡面，可以用 vim *.h *.c 一次打開所有程式檔案到暫存區。  
接著只要 `100@y`，執行這個巨集100 次（好吧如果你檔案更多就選個更大的數字），巨集的執行會在 :n 沒有下一個檔案的時候停止，這樣就能把所有檔案的格式都整理得漂漂亮亮了。