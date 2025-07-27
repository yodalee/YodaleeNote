---
title: "用python讀入agilent (keysight) binary file"
date: 2014-12-25
categories:
- small project
- python
tags:
- python
- keysight
- agilent
series: null
forkme: keysightBin
---

故事是這樣子的，最近拿到一些透過Agilent示波器（好啦你喜歡叫他Keysight也可以）讀到的資料，要對裡面的數字做分析，
由於資料極大時他們會用自家的binary格式存檔案，要讀出資料分析就比較麻煩。  
他們自家網站是有提供……程式來分析，可惜是用matlab寫的…  
What The F.. Emmm, Ahhh, Ahhh, 沒事  
總之我看到這個東西就不爽了，俗話說人活著好好的為什麼要用matlab。恁北想用python沒有怎麼辦，只好自幹啦。  
<!--more-->

其實整體來說滿簡單的，只是把matlab code 用python 寫一篇，python又比matlab 好寫很多。  

比較值得提的只有一個，分析binary就不能不用 [python的struct]({{< relref "2014_python_struct.md" >}})，
這次我再加上用namedtuple來處理，整體會變得很乾淨；例如它一個波型的header格式是這樣：  

```c
int32 headerSize
int16 bufferType
int16 bytesPerPoint
int32 bufferSize
```
那我就先定義好namedtuple跟struct的format string:  
```python
from collections import namedtuple
bufHeaderfmt = "ihhi"
bufHeaderSiz = struct.calcsize(bufHeaderfmt)
bufHeader = namedtuple("bufHeader", "headerSize bufferType bytesPerPoint bufferSize")
```

再來我們讀入檔案，直接寫到tuple裡，就可以用名字直接存取值，例如我們要跳過header：  
```python
bufHdr = bufHeader._make(struct.unpack(bufHeaderFmt, fd.read(bufHeaderSiz)))
fd.seek(bufHdr.bufferSize, 1)
```

是不是超簡潔的？一個晚上就寫完了=w=  

人生苦短，請用python。  

* [原matlab 網址](http://www.keysight.com/main/editorial.jspx?cc=TW&lc=cht&ckey=1185953&nid=-11143.0.00&id=1185953)  
* [原始碼在此](https://github.com/yodalee/agilentBin)，不過我覺得是沒什麼人會用啦orz  