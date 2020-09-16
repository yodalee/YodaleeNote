---
title: "Linker script 簡介"
date: 2015-04-26
categories:
- embedded system
tags:
- linker
- embedded system
- c
series: null
---

Linker script，就是給Linker 看的script。  

## Linker  
當然這樣是在講廢話，首先要先知道Linker 是什麼：  
在程式編譯成物件檔之後，會把所有的物件檔集合起來交給連結器(linker)，Linker 會把裡面的符號位址解析出來，定下真正的位址之後，連結成可執行檔。  
<!--more-->
例如我們在一個簡單的C 程式裡，include 一個標頭檔並使用裡面的函數，或者用extern 宣告一個外部的變數，在編譯成標頭檔的時候，
編譯器並不清楚最終函數和變數的真正位址，只會留下一個符號參照。  
待我們把這些東西送進linker，linker就會把所有的標頭檔整理起來，把程式碼的部分整理起來、變數的部分整理起來，
然後知道位址了就把位址都定上去，如果有任何無法解析的符號，就會丟出undefined reference error。  

我們可以試試：  
外部函數，在一個foo.h 裡宣告，並在foo.c 裡面定義：  
```c
// foo.c
int foo();   
```
外部變數，在var.c 裡面定義  
```c
// var.c
int var;   
```
在main.c 裡面引用它們：  
```c
// main.c
#include “foo.h”  
extern int var;  
int main(){  
    var = 10000;  
    foo();  
    return 0;  
}   
```
開始編譯  
```bash
gcc -c main.c  
gcc -c foo.c   
```
這樣我們就得到兩個物件檔 main.o跟foo.o，我們可以用objdump -x 把物件檔main.o的內容倒出來看看，其中有趣的就是這個：  
```txt
SYMBOL TABLE:  
0000000000000000 g F .text 000000000000002a main  
0000000000000000 *UND* 0000000000000000 var  
0000000000000000 *UND* 0000000000000000 foo RELOCATION RECORDS FOR [.text]:  
OFFSET TYPE VALUE   
0000000000000011 R\_X86\_64\_PC32 var-0x0000000000000008  
000000000000001f R\_X86\_64\_PC32 foo-0x0000000000000004   
```
可以看到var, foo 這兩個符號還是未定(UND, undefined)，若我們此時強行連結，就會得到：  
```txt
$ ld main.o
main.c:(.text+0x11): undefined reference to 'var'  
main.c:(.text+0x1f): undefined reference to'foo'   
```
必須把foo.o 跟var.o 兩個檔案一起連結才行。  

## Linker script
好了Linker講了這麼多，那linker script 呢？  

Linker script 可以讓我們對 linker 下達指示，把程式、變數放在我們想要的地方，一般的gcc 都有內建的linker script，
平常我們開發x86系統跟arm系統，會使用不同的gcc，就是在這些預設的設定上有所不同，要是把這團亂七八糟的東西每key一次gcc 都要重輸入就太麻煩了；
可以用ld --verbose 輸出，這裡看到的是支援x86 系統的linker script ，講下去又另一段故事，先跳過不提。  

我們這裡拿燒錄在 [STM32 硬體上的linker script](https://github.com/yodalee/mini-arm-os/blob/master/02-ContextSwitch-1/os.ld) 來講，linker script 可見：  

Linker 的作用，就是把輸入物件檔的section整理成到輸出檔的section，最簡單的linker script 就是用SECTIONS指令去定義section 的分佈：  
```txt
SECTIONS  
{  
    . = 0x10000;  
    .text : { *(.text) }  
    . = 0x8000000;  
    .data : { *(.data) }  
    .bss : { *(.bss) }  
}   
```
在Linker script 裡面，最要緊的就是這個符號 '.' location counter，你可以想像這是一個探針，從最終執行檔的頭掃到尾，
而 '.' 這個符號就指向現在掃到的位址，你可以讀取現在這個探針的位址，也可以移動探針。  

不指定的話location counter 預設會從0的位置開始放置，而這段script，先把location counter 移到0x10000，在這裡寫入.text section，再來移到0x8000000放.data 跟.bss。  
這裡檔名的match 支援適度的正規表示式，像 `*, ?, [a-z]` 都可以使用，在這裡用wildcard直接對應到所有輸入檔案的sections。  
光是SECTION 就講不清的用法：
* 把指定某檔案的Section (file.o(.data))
* 排除某些檔案的section (EXCLUDE\_FILE)  

幸運的是，通常我們都不會想不開亂改linker script，這些位置的放法要看最終執行的硬體而定，亂放不會有什麼好下場。   

另外linker script 也定義一些指令，這裡列一些比較常用的：  

### ENTRY:  
另外我們可以用ENTRY指定程式進入點的符號，不設定的話linker會試圖用預設.text 的起始點，或者用位址0的地方；
在x86 預設的linker script 倒是可以看到這個預設的程式進入點：  
```txt
ENTRY(_start)  
```

### Symbol
既然linker script 是用來解析所有符號的，那它裡面能不能有符號，當然可以，但有一點不同，
一般在C 語言裡寫一個變數的話，它會在symbol table 裡面指明一個位址，指向一個記憶體空間，可以對該位址讀值或賦值；
而在linker script 裡的符號，就只是將該符號加入symbol table內，指向一個位址，但位址裡沒有內容，在 linker script 裡定義這個符號就是要操作記憶體特定位址：  
以上面的STM32 硬體為例，因為FLASH 記憶體被map 到0x00000000，RAM的資料被指向0x20000000，
為了把資料從FLASH 搬到RAM 裡，在linker script 的RAM 兩端，加上了：  
```txt
\_sidata = .;  
//in FLASH \_sdata = .;  
\_edata = .;   
```
等於是把當前 location counter 這根探針指向的位址，放到\_sdata 這個符號裡面，所以在主程式中，就能向這樣取用RAM 的位址：  
```c
extern uint32\_t \_sidata;  
extern uint32\_t \_sdata;  
extern uint32\_t \_edata;  

uint32\_t *idata\_begin = &\_sidata;   
uint32\_t *data\_begin = &\_sdata;   
uint32\_t *data\_end = &\_edata;   
while (data\_begin < data\_end) *data\_begin++ = *idata\_begin++;    
```
注意我們用reference 去取\_sdata, \_edata 的位址，這是正確用法。  

### PROVIDE
Linker script 還定義了PROVIDE 指令，來避免linker script 的符號跟C中相衝突，上面如果在C程式裡有\_sdata的變數，linker 會丟出雙重定義錯誤，但如果是  
```txt
PROVIDE(\_sdata = .)
```
就不會有這個問題。  

### KEEP
KEEP 指令保留某個符號不要被最佳化掉，在script 裡面isr\_vector是exception handler table，如果不指定的話它會被寫到其他區段，
可是它必須放在0x0的地方，因此我們用KEEP 把它保留在0x0上。  

### MEMORY:

Linker 預設會取用全部的記憶體，我們可以用MEMORY指令指定記憶體大小，例子中我們指定了FLASH跟RAM的輸出位置與大小：  
```txt
MEMORY {
    FLASH (rx) : ORIGIN = 0x00000000, LENGTH = 128K  
    RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 40K    
}
```
接著我們在上面的SECTION部分，就能用 > 符號把資料寫到指定的位置  
也就是例子裡，把 .text section全塞進 FLASH位址的寫法，如果整體程式碼大於指定的記憶體，linker 也會回報錯誤。  

## 結語：

Linker 其實是個古老而複雜的東西，Linker script 裡面甚至有OVERLAY這個指令，來處理overlay 的執行檔連結，
但一般來說，除非是要寫嵌入式系統，需要對執行檔的擺放位置做特別處理，否則大部分的程式都不會去改linker script，都直接用預設的組態檔下去跑就好了。  

這篇只介紹了極限基本的linker script，完整內容還是請看[文件](https://sourceware.org/binutils/docs/ld/Scripts.html) 吧。  