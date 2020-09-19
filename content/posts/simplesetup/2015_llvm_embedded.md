---
title: "用llvm 編譯嵌入式程式"
date: 2015-04-13
categories:
- simple setup
tags:
- embedded system
series: null
---

最近幾天在研究嵌入式系統，玩一玩也有一些心得。  
課程上所用的編譯工具是arm-none-linux-gnu toolchain，在Archlinux 下可以用如下的方式安裝：  
```bash
yaourt -S gcc-linaro-arm-linux-gnueabihf
yaourt -S qemu-linaro
yaourt -S arm-none-eabi-gcc49-linaro
yaourt -S arm-none-eabi-gdb-linaro
ln -s /opt/gcc-linaro-arm-linux-gnueabihf/libc /usr/arm-linux-gnueabihf
```
不過最近心血來潮，想來試試如果用另一套編譯器 LLVM 來編譯看看，至於為什麼…好玩嘛(炸)，總之這裡是設定筆記：  
<!--more-->

主要參考網址：  
<http://clang.llvm.org/docs/CrossCompilation.html>  
[https://github.com/dwelch67/mbed\_samples/](https://github.com/dwelch67/mbed_samples/)  

用上LLVM 的優勢是，它在編譯時會將程式碼轉換成與平台無關的中間表示碼(Intermediate Reprsentation, IR)，再透過轉換器轉成平台相關的組合語言或是底層的機械器。不像gcc 針對不同的Host/Target的組合就是不同的執行檔和標頭檔，在編譯到不同平台時，都要先取得針對該平台的gcc 版本。  
註：上面這段是譯自上面的參考網址，雖然我有點懷疑這段話，不然gcc 命令列參數那些平台相關的選項是放好看的嗎？  

我嘗試的對象是mini-arm-os 00-helloworld，目標device 是STM32  
<https://github.com/embedded2015/mini-arm-os>  

前端的 c 我們先用clang 編譯為llvm IR code，用llvm 的llc 編譯為 object file，因為目前LLVM 的linker [lld](http://lld.llvm.org/)還在開發中，只能link x86上的elf 檔，要連結ARM 我們在link 階段還是只能用biutils 的ld，以及biutils 的objcopy，這樣看起來有點詭異，有點像換褲子結果褲子只脫一半就穿新褲子的感覺。  

最後的Makefile 大概長這樣：  

CC := clang  
ASM := llc  
LINKER := arm-none-eabi-ld  
OBJCOPY := arm-none-eabi-objcopy  

CCFLAGS = -Wall -target armv7m-arm-none-eabi  
LLCFLAGS = -filetype=obj  
LINKERSCRIPT = hello.ld  

TARGET = hello.bin  
all: $(TARGET)  

$(TARGET): hello.c startup.c  
$(CC) $(CCFLAGS) -c hello.c -o hello.bc  
$(CC) $(CCFLAGS) -c startup.c -o startup.bc  
$(ASM) $(LLCFLAGS) hello.bc -o hello.o  
$(ASM) $(LLCFLAGS) startup.bc -o startup.o  

$(LINKER) -T hello.ld startup.o hello.o -o hello.elf  
$(OBJCOPY) -Obinary hello.elf hello.bin   
其實重點只有在target 指定的地方，其他的就沒啥，只是這樣一看好像沒有比較方便，而且這樣根本就不是用 llvm 編譯，最重要的Link 階段還不是被 gcc 做去了= =  
在lld 完成前也許還是乖乖用 gcc 吧？  

對LLVM 相關介紹可以見：  
[http://elinux.org/images/d/d2/Elc2011\_lopes.pdf](http://elinux.org/images/d/d2/Elc2011_lopes.pdf)  
各種biutils 的替代品列表：  
<http://marshall.calepin.co/binutils-replacements-for-llvm.html>  