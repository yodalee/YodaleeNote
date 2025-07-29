---
title: "進行arm 開發時遇到的各種狀況"
date: 2016-10-09
categories:
- embedded system
tags:
- archlinux
- arm
- embedded system
series: null
---

約一週前重灌了電腦，重灌這檔事最麻煩的就是一些開發環境會消失不見，平常用得順手的東西突然不見了，例如我的arm 開發環境就是一例：  
<!--more-->
首先在archlinux 上面，跟 [之前這篇 LLVM 編譯]({{< relref "2015_llvm_embedded.md">}})不同，現在只剩下gcc49, gcc53跟gdb 還在  
```txt
arm-none-eabi-gcc53-linaro
arm-none-eabi-gdb-linaro
```
替代品是AUR中下面這些套件（順帶一提，安裝這幾個套件之前，請先去/etc/makepkg.conf 把 MAKEFLAGS 改成 -jn，不然用單核心編譯這幾個近100 MB的程式會編譯到想翻桌）：  
```txt
arm-linux-gnueabihf-binutils
arm-linux-gnueabihf-gcc
arm-linux-gnueabihf-glibc
arm-linux-gnueabihf-linux-api-headers
arm-linux-gnueabihf-gdb
```
安裝完之後當然就來用一下了，測試當然就用最簡單的helloworld.c 去測：  
```txt
$ arm-linux-gnueabihf-gcc helloworld.c -o hello
exec format error: ./hello
```
這是當然的囉，因為我的機器是x86\_64，而arm-gcc 編出來的執行檔要在arm 架構上執行，幸好這年頭我們有qemu-arm 可以用（老實說，悲劇就是從這裡開始的= =）：  
```bash
qemu-arm hello
/lib/ld-linux-armhf.so.3: No such file or directory
```
這又是為什麼呢？我們可以file 它一下，可以看到它的interpreter 是/lib/ld-linux-armhf.so.3，而這個檔案是不存在的。  
```txt
file hello
hello: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), dynamically linked,
interpreter /lib/ld-linux-armhf.so.3, for GNU/Linux 2.6.32,
BuildID[sha1]=716a92a4985090baa83f8b762c5f9844e197ed83, not stripped
```
它真正的位置在arm-gcc 的安裝位置：/usr/arm-linux-gnueabihf/lib，創個symbolic link過去  
```txt
ln -s /usr/arm-linux-gnueabihf/lib/ld-linux-armhf.so.3 /lib/ld-linux-armhf.so.3
ll ld-linux-armhf.so.3
lrwxrwxrwx 1 root root 48 Oct 5 19:10 ld-linux-armhf.so.3 ->
   /usr/arm-linux-gnueabihf/lib/ld-linux-armhf.so.3
```
這時候就不會有No such file or directory，雖然會換成另一個錯誤  
```txt
hello: error while loading shared libraries: libc.so.6: wrong ELF class: ELFCLASS64
```
參考了[這篇文章](http://blog.csdn.net/sahusoft/article/details/7388617)：  
原因是dynamic linker 在連結動態函式庫時，找到的libc.so.6 是錯誤的格式，它找不到它要的arm 格式的函式庫，這步有時會有其他的錯誤像是：  
```txt
cannot open shared object file: No such file or directory
```

這就是電腦上沒有安裝相對應的函式庫，可以用ldd 來確認這件事，沒有就要安裝該函式庫；或者函式庫安裝在/usr/lib 以外的特殊路徑，就要利用ld.so.conf去設定，像我的/etc/ld.so.conf.d裡面就有：  
```txt
android-sdk.conf
cuda.conf
fakeroot.conf
ffmpeg2.8.conf
lib32-glibc.conf
octave.conf
openmpi.conf
```

不過我們的狀況比較複雜一點，在這之前試著把 /usr/arm-linux-gnueabihf/lib 加到ld.so.conf 裡面，執行ldconfig 時就出問題了  
```txt
$ ldconfig
ldconfig: /usr/lib/ld-linux-armhf.so.3 is for unknown machine 40.
```
我們x86\_64 的ldconfig 壓根不認arm 的函式庫，這些函式庫也沒加到ld.conf.cache，自然也不會在執行時被 ld-linux-armhf.so.3 連結，所以上面的執行還是失敗了。  

所以說了這麼多，我們到底要怎麼樣才能把我們的hello world 跑起來？  

## 設定 [rpath](http://stackoverflow.com/questions/2728552/how-to-link-to-a-different-libc-file)

在呼叫gcc 的時候使用  
```
arm-linux-gnueabihf-gcc -Xlinker -rpath=/usr/arm-linux-gnueabihf/lib hello.c
```
這樣編譯出來的執行檔就會以/usr/arm-linux-gnueabihf/lib 為第一優先，就能夠直接以qemu-arm 去執行。  

## 設定LD_LIBRARY_PATH

LD\_LIBRARY\_PATH 的優先順序高過 ldconfig 設定的路徑，也能讓qemu-arm 跑起來：  
```txt
export LD_LIBRARY_PATH=/usr/arm-linux-gnueabihf/lib/
```
當然這不是一個好方法，也是[老話題](http://xahlee.info/UnixResource_dir/_/ldpath.html)了，請見：  

## 設定 qemu -L flag
或者是利用qemu-arm 的-L flag，這個的位階低於LD\_LIBRARY\_PATH，因此用這個要確定LD\_LIBRARY\_PATH沒有設值。  
```txt
qemu-arm -L /usr/arm-linux-gnueabihf hello
```
試了這麼多方法，最後一種其實才是最有效的做法，也是我忘掉的方法(yay  

---

寫文的同時我大概整理一下 man ld 裡面，在選項 -rpath=dir 跟 -rpath-link=dir 的說明：  
首先是rpath ，這是設定runtime 時期的library search path，這些字串會完整的被複製到runtime linker (也就是ld.so）
用來尋找共享函式庫；如果rpath 沒有設定，則 linker 會使用環境變數 LD\_RUN\_PATH 的值。  
因此透過rpath 我們有兩招：  

1. 是上面寫的，用 rpath 設定搜尋路徑：  
```txt
arm-linux-gnueabihf-gcc -Xlinker -rpath=/usr/arm-linux-gnueabihf/lib hello.c
arm-linux-gnueabihf-gcc -Wl,-rpath=/usr/arm-linux-gnueabihf/lib hello.c
```
2. 是直接編譯，但先設定LD\_RUN\_PATH的值：  
```txt
export LD_RUN_PATH=/usr/arm-linux/gnueabihf/lib
arm-linux-gnueabihf-gcc hello.c
```
我們可以用readelf -d 把dynamic sections 給讀出來，就能看到我們設定的rpath 了：  
```txt
readelf -d hello
0x0000000f (RPATH) 函式庫路徑：[/usr/arm-linux-gnueabihf/lib]
```

另外還有一種是 -L，它會設定連接時搜尋共享函式庫的目錄，這裡只給一個最粗淺的例子：  
```txt
arm-linux-gnueabihf-gcc -c hello.c -o hello.o
arm-linux-gnueabihf-ld hell.o -o hello
```
會發生undefined reference to puts 的錯誤，因為我們沒有連接所需要的 c library，另外我們也沒有指定程式的進入點為何，要能連結通過至少要：  
```txt
arm-linux-gnueabihf-ld hell.o -o -lc -L/usr/arm-linux-gnueabihf/lib hello –entry main
```
當然這樣不代表可以執行，試著執行會發現dynamic linker 並沒有正確設定，除此之外還有各種runtime 的library 需要連結進去才會動；
要看到可運作的呼叫方式，可以用gcc -v (-verbose) 來觀察。  

-rpath-link 則只指定link 時搜尋shared library的路徑，這個路徑不會包含到executable 裡面，這個我一時之間給不出例子，
但在這裡有找到，利用 -rpath-link=. 在編譯時指定在編譯時目錄尋找 shared library，另外關鍵的差別都寫在這幾句話了：  
[在 gcc 中使用 rpath/rpath-link 指定 shared library 搜尋路徑](https://ephrain.net/linux-%E5%9C%A8-gcc-%E4%B8%AD%E4%BD%BF%E7%94%A8-rpathrpath-link-%E6%8C%87%E5%AE%9A-shared-library-%E6%90%9C%E5%B0%8B%E8%B7%AF%E5%BE%91/)  

> 在 -rpath-link 裡指定 "." (當前目錄) 還算正常，因為我們可以控制現在的工作目錄，  
> 但是在 -rpath 裡指定 "." 就有點奇怪，因為你不知道別人會在哪個目錄執行你的程式...    

使用-rpath-link 須知它也會蓋掉原本的搜尋路徑，因此用-rpath-link有個危害是：
link time linker(ld)跟runtime linker (ld.so) 可能會使用不同的shared library，因為後者並沒有設定這個路徑，而是去預設的路徑尋找。   

man ld 有列出 [link time linker 的搜尋路徑](https://my.oschina.net/shelllife/blog/115958)，它未寫明有沒有先後關係，但以-rpath 來說顯然是有的：  

1. 透過 -rpath-link 指定的資料夾  
2. 透過 -rpath 指定的路徑，如上所說，這跟 -rpath-link的差別是它會被包括到runtime linker中  
3. 如果前兩者都沒有指定，尋找LD\_RUN\_PATH環境變數的值  
4. 在SunOS，如果 -rpath 未指定，尋找 -L 選項設定的值  
5. 尋找LD\_LIBRARY\_PATH 設定之路徑，這裡有句 For a native linker，不確定native linker是在指什麼特別的linker  
6. For a native ELF linker，會查找現在引入的共享函式庫中設定的DT\_RUNPATH 跟DT\_RPATH section，後者的優先度高於前者（其實這就是在編譯shared library 時，以rpath 編進去的路徑：）  
7. 預設路徑 /lib, /usr/lib  
8. /etc/ld.so.conf 設定的路徑、  

整體大概就是這樣，從編譯到執行，有許許多多的地方都能讓我們有各種方法對執行檔「上下其手」，去改動裡面連結、動態連結引入的東西  
不過說老實話，其實這篇文…是呃…我忘了 qemu-arm 使用上就是用 -L 去指定library path 的產物，花了我一堆時間… 這真的是：

> Hello World 年年都會寫，每一年都有不同的體會呢XD。