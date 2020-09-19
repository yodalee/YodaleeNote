---
title: "用makefile來編譯安裝android apps"
date: 2013-04-17
categories:
- simple setup
tags:
- android
- makefile
series: null
---

因為一些關係，最近正在寫Android上的Apps。  
寫Android，大部分人可能都會用Eclipse來寫，Eclipse主要是整合了很多功能，用起來滿方便的，不過個人還是偏好用terminal+vim來寫code。  
雖然這樣會比較不那麼自動一點，但也不是沒有解，在終端機下，如果有什麼要自動化的話，就要用makefile啦。  
<!--more-->

以下就是自己寫個簡單的makefile，在projectname和packagename裡面分別填入build.xml裡的`<project name=""/>`，跟AndroidManifest.xml裡面的`<manifest package=""/>`，這樣就可以用：  
```bash
make debug  
make install  
make uninstall  
```
來完成編譯、安裝和解除安裝的工作。  
```makefile
.PHONY : clean install uninstall   
#=========================================  
# MACRO DEFINE  
#=========================================  

ADB = adb  
DEL_FILE = rm -f  
DEL_DIR = rm -rf  
MKDIR = mkdir -p  
MOVE = mv -u  
BIN_DIR = bin  
projectname = MyFirstApp  
packagename = example.opengles.hellotriangle  

#================================   
# Build function  
#================================  
debug:  
    ant debug  
install:  
    adb install ${BIN\_DIR}/${projectname}-debug.apk  
uninstall:  
    adb uninstall ${packagename}  
clean:  
    adb uninstall ${packagename}  
    ${DEL\_DIR} ${BIN\_DIR}   
```