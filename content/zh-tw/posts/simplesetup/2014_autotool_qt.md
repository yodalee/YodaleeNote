---
title: "使用autotool 編譯qt project"
date: 2014-11-17
categories:
- Setup Guide
tags:
- cpp
- qt
- makefile
series: null
---

在寫這篇，我發現我曾經寫過類似的內容：[使用gnu make編譯Qt 專案](http://yodalee.blogspot.tw/2013/08/gnu-makeqt.html)  
總之，這次又是在qucs專案上遇到的問題，之前專案裡的使用者介面，不知道是哪根筋不對，竟然全部都是用手爆的啊啊啊！
正好這個project現在進入巨量refactor階段，在改其中一個部分時，順手把其中一個使用者介面換用Qt的Designer來做。  

結果，還要改編譯的autotool，讓它使用UIC解決才行，網路上找找沒什麼資料，只好印autotool的文件下來看，以下是我最後弄出來的Makefile.am設定：  
<!--more-->

首先，定義目標：此資料夾的靜態函式庫及它的原始碼：  
```txt
noinst_LIBRARIES = libdialogs.a
libdialogs_a_SOURCES = xxxxx.cpp
```

原始碼後面可能有一大串，一般來說autotool有這樣有夠了，不過對Qt project，
首先我們需要MOC: Meta object compiler將標頭檔編譯為moc.cpp原始碼，並把它們加到靜態函式庫的原始碼中：  
```txt
MOCHEADERS = xxxxx.h
MOCFILES = $(MOCHEADERS:.h=.moc.cpp)
.h.moc.cpp:
$(MOC) -o $@ lt;
nodist_libdialogs_a_SOURCES = $(MOCFILES)
```
這會讓編譯器去編譯MOCFILES，找不到就用副檔名規則呼叫MOC產生.moc.cpp檔。  

UIC比較麻煩一點，因為標頭檔不像原始碼一樣，會被加到編譯時的相依規則中，
若像原始碼在相依規則裡，相依性不符時，Makefile會自動去尋找有沒有可以產生此相依的規則，如上面的.h.moc.cpp；
但標頭檔就算全不見了，不設定的話Makefile也不會做什麼。  
這裡我們使用autotool的 [BUILT_SOURCES](http://www.gnu.org/savannah-checkouts/gnu/automake/manual/html_node/Sources.html)來解，被加到這個變數的內容會優先被編譯：  

```txt
UICFILES = ui_yyyy.h
BUILT_SOURCES = $(UICFILES)
ui_%.h: %.ui
$(UIC) -o $@ lt;
noinst_HEADERS = $(MOCHEADERS) $(UIHEADERS)
```
如此一來就能順利的呼叫UIC幫我們產生標題檔了；不過含有%這種寫法是Makefile.am使用Gnu Extension達成的，
因此在產生Makefile.in時會收到警告，如果不用這種寫法就只能寫明所有*.ui轉成ui\_*.h的規則了。  

rcc的話我是沒有用，不過它是將qrc檔轉成原始碼檔，因此估計使用方法跟moc比較像。  