---
title: "使用gnu make編譯Qt 專案"
date: 2013-08-08
categories:
- Setup Guide
tags:
- cpp
- qt
- makefile
series: null
---

最近白天跑EM，夜深寫QT。  
當然這完全沒什麼，其他同學至少兩年前就寫過了LOL。  

只能說Qt 真是相當強大的工具，最基本的signal & slot的概念，如果對GTK的callback熟悉的話，很快就能上手。   
一般在寫Qt時，最常用的還是用qmake來產生Makefile，畢竟qmake寫得還不賴，打一次就會產生好Makefile，接著make即可；
不過有時個人習慣還是偏好用gnu-make，可以自己編寫Makefile，做一些細部的調整，用qmake的話只要重新產生一次Makefile，這些細部調整就要重新再修改一次。  
這篇就是說明一下，要如何使用gnu-make來處理Qt專案。  
<!--more-->

基本上Qt的運作原理，是對原有的C++進行擴展，然後透過Qt提供的解析程式，產生額外的原始碼檔。  
少了這些額外的原始碼，在編譯的時候會產生一堆可怕的錯誤資訊，要用gnu-make編譯Qt專案，其實只要呼叫這些解析程式來產生原始碼即可；總共會用到的程式有三個：
* moc：產生meta object(故名Meta-Object Compiler)
* rcc：處理resource(resource compiler)檔
* uic：產生介面檔(User Interface Compiler)

一般Makefile裡面會有這些東西，用來把所有的source轉換成object file。  
```makefile
SOURCE_FILE = main.cpp
OBJECT_FILE += $(addsuffix .o, $(basename $(SOURCE_FILE)))
```
為了Qt，我們加上下列的變數定義：  
```makefile
#==================================================
# Qt special function
#==================================================
QT_LIBS = -lQtCore -lQtGui -lQtOpenGL
QT_PATH = /usr/lib/qt4/bin
QT_MOCFILE = mainwindow.h
QT_RCCFILE = resource.qrc
QT_UICFILE = first.ui
QT_MOCSOURCE = $(addprefix moc_, $(addsuffix .cpp, $(basename $(QT_MOCFILE))))
QT_RCCSOURCE = $(addprefix qrc_, $(addsuffix .cpp, $(basename $(QT_RCCFILE))))
QT_UICSOURCE = $(addprefix ui_, $(addsuffix .h, $(basename $(QT_UICFILE))))
```

這一整個區塊與QT有關，所有參數都加上QT為標示。   
QT\_PATH設定Qt的執行檔位置，如果安裝在其他地方、或要用其他版本就要自己換地方。  
QT\_*FILE是先定義，moc, rcc, uic分別要處理的檔案：
moc會處理所有.h檔，產生含meta object的cpp檔  
rcc會處理qrc file，產生相對應的cpp檔  
uic則會處理ui，產生可包入的header file  

透過makefile的suffix, prefix，轉成我們需要轉出的檔案名稱，個人的習慣是在這些檔名前加上關鍵字moc\_, qrc\_, ui\_。  

接著是利用implicit rules來compile所有的物件檔：  
```makefile
TARGET = program
BIN_DIR = bin
LIBRARY_DIR = library
SOURCE_FILE = main.cpp $(QT_MOCSOURCE) $(QT_RCCSOURCE)
OBJECT_FILE += $(addsuffix .o, $(basename $(SOURCE_FILE)))
```

由於moc和rcc會產生新的cpp檔，因此需要將它們列入；然後就可以用implicit rules執行：  

```makefile
%.o:%.c
  $(CC) -c lt; -o $@ $(CFLAGS) $(INCLUDE)
  @$(MOVE) $@ $(LIBRARY_DIR)

%.o:%.cpp
  $(CXX) -c lt; -o $@ $(CXXFLAGS) $(INCLUDE)
  @$(MOVE) $@ $(LIBRARY_DIR)

moc_%.cpp: %.h
  $(QT_PATH)moc $(DEFINES) $(INCLUDE) lt; -o $@

qrc_%.cpp: %.qrc
  $(QT_PATH)rcc lt; -o $@

ui_%.h: %.ui
  $(QT_PATH)uic lt; -o $@
```

前兩項是將c/cpp-編成 .o檔，當遇到QT\_MOCSOURCE, QT\_RCCSOURCE的檔案，就會由moc, rcc產生。   
另外在編譯主程式的相依性中，原本我們只要它編譯所有的OBJECT\_FILE，現在還要加上由uic產生的header file：   
```makefile
$(TARGET): $(OBJECT_FILE) $(QT_UICSOURCE)
  cd $(LIBRARY_DIR); \
  $(LINKER) -o $@ $(OBJECT_FILE) $(LIBS); \
  cd ..
  mv $(LIBRARY_DIR)/$@ $(BIN_DIR)
```

如此一來，就會觸發uic產生出header file。   

透過以上的設定，即可完成Qt專案的編譯，不過最後還是要說，雖然我這裡是這麼寫，但其實真的用的時候還是用qmake來產生Makefile =w=，
套句AZ大神的話

> 它寫得這麼好幹嘛不用？你白痴嗎。