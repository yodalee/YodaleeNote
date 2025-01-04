---
title: "使用python struct 實作Dex file parser "
date: 2014-03-17
categories:
- Setup Guide
- python
tags:
- python
- android
- dex
series: null
---

最近因為學校作業的關係，開始碰一些android的相關內容；有一個作業要我們寫一個程式去改android dex file的opCode，
不過我實力不足，最後用smali/baksmali+shell來實作，一整個就不是熟練的程式人該作的事O\_O。  
<!--more-->
不過，為了補一下實力不足，還是用python 寫了一個Dex file parser：  

因為Dex file已經包成binary的形式，要去parse其中的內容，最方便的套件就是python struct了，在這裡以Dex為例，來介紹python struct的使用：  

要使用python struct，首先要寫出format string，struct 會依照format string對資料進行處理。  
基本的格式是包含幾個組成：
1. endian 字元
2. 重複次數
3. 型別代碼

詳細請參考[官方文件](https://docs.python.org/3/library/struct.html)

有了format string就可以呼叫struct的function: pack, unpack，它們會照format string，把資料寫到binary或從binary讀成一個tuple。  

例如：我們可以看到dex 35的header為：  

```c
typedefstructDexHeader {
    u1 magic[8]; /*includes version number */
    u4 checksum; /*adler32 checksum */
    u1 signature[kSHA1DigestLen]; /*SHA-1 hash */
    u4 fileSize; /*length of entire file */
    u4 headerSize; /*offset to start of next section */
    u4 endianTag;
    u4 linkSize;
    u4 linkOff;
    u4 mapOff;
    u4 stringIdsSize;
    u4 stringIdsOff;
    u4 typeIdsSize;
    u4 typeIdsOff;
    u4 protoIdsSize;
    u4 protoIdsOff;
    u4 fieldIdsSize;
    u4 fieldIdsOff;
    u4 methodIdsSize;
    u4 methodIdsOff;
    u4 classDefsSize;
    u4 classDefsOff;
    u4 dataSize;
    u4 dataOff;
}DexHeader;
```

對這個我們可以寫出v35 format string為：`8sI20s20I`，就這麼簡單。 接著我們可以呼叫unpack來取得header的內容。  
```python
infile = self.open("yay.dex", "rb")
header = struct.unpack(self.v35fmt, infile.read(struct.calcsize(self.v35fmt)))
```
比較麻煩的一點是，unpack的資料長度必須和format string會處理到的長度一樣，這裡struct提供了calcsize來處理這個問題，它會回傳format string代表的長度。  
```python
print(header)
(b'dex\n035\x00', 3615126987, b'A\x89\xd9Y\xd8mm\xe4\xfe\x9d8\x0c\xc25\xbc\xcc\x9b\x86\xbd)',
912, 112, 305419896, 0, 0, 752, 16, 112, 8, 176, 4, 208, 1, 256, 5, 264, 1, 304, 576, 336)
```
可以看見資料已經寫入tuple中了，之後再一個一個轉出即可。