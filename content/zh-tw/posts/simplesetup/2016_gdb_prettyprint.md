---
title: "不為人知的gdb 使用方式系統-gdb pretty printer"
date: 2016-09-14
categories:
- Setup Guide
tags:
- python
- gdb
- qt
series: null
---

前言：  
最近因為jserv 大神的關係，看了下面這部Become a GDB Power User  

{{< youtube 713ay4bZUrw>}}

覺得裡面還不少生猛的用法之前都不會用，決定把它整理一下，寫個介紹文。  
這篇來介紹 gdb 的 [pretty printer](https://sourceware.org/gdb/onlinedocs/gdb/Pretty-Printing.html#Pretty-Printing)  
<!--more-->

假設我們有一個客製的struct 或是class，例如Qt4 的QString，如果我們用原本gdb 的print 去印出QString的話：  
```cpp
QString s("Hello World");
```
```txt
(gdb) p s
$2 = {static null = {<No data fields>}, static shared_null = {ref = {_q_value = 2}, alloc = 0, size = 0,
data = 0x7ffff7dd70fa <QString::shared_null+26>, clean = 0, simpletext = 0, righttoleft = 0,
asciiCache = 0, capacity = 0, reserved = 0, array = {0}},
static shared_empty = {ref = {_q_value = 1}, alloc = 0, size = 0, data = 0x7ffff7dd70da
<QString::shared_empty+26>, clean = 0, simpletext = 0, righttoleft = 0, asciiCache = 0, capacity = 0,
reserved = 0, array = {0}}, d = 0x603dc0, static codecForCStrings = 0x0}
```
因為QString 是個結構的關係，我們無法單純印個char array ，反而會印出裡面所有的資訊，它真的資訊是存在那個 d 裡面，要真的印字串就要從那個d 裡面去印。  
之前在寫Qt 專案的時候有遇到類似的問題，那時有查到一個printqstring 的自訂函式，把下面這段加到 ~/.gdbinit 裡面：  
```bash
define printqstring
  printf "(QString)0x%x (length=%i): \"",&$arg0,$arg0.d->size
  set $i=0
  while $i < $arg0.d->size
    set $c=$arg0.d->data[$i++]
    if $c < 32 || $c > 127
      printf "\\u0x%04x", $c
    else
      printf "%c", (char)$c
    end
  end
  printf "\"\n"
end
```
就可以在debug 時使用printqstring來印出QString  
```txt
(gdb) printqstring s
(QString)0xffffe650 (length=12): "Hello World!"
```

當然我們可以用gdb 的pretty printer 來做到類似的事，而且不需要自訂函式，單純用p s 也能做到一樣的效果。  
gdb v7 開始加入對python的支援，可以讓我們透過python和gdb 互動，在python 之中import gdb 之後，
就可以利用一連串定義完善的介面去跟gdb 互動，詳細上用法還不少，這裡我們只先試著寫個pretty\_printer。  
Python 的pretty printer 就是實作一個class，至少要實作 `__init__` 跟 `to_string()` 兩個介面，其他的函式可以參考 
[API  文件](https://sourceware.org/gdb/onlinedocs/gdb/Pretty-Printing-API.html#Pretty-Printing-API)  

之後使用 gdb.printing 的 RegexpCollectionPrettyPrinter，產生一個叫 QString 的printer，利用add\_printer，
只要型態名稱符合^QString$ 的物件，就用QStringPrinter來處理，
最後用regeister\_pretty\_printer把這個RegexpCollectionPrettyPrinter 塞進去：  
```python
# qstring.py
import gdb.printing

class QStringPrinter(object):
  def __init__(self, val):
    self.val = val
  def to_string(self):
    return "I'm Qstring"
  def display_hint(self):
    return 'string'

pp = gdb.printing.RegexpCollectionPrettyPrinter('QString')
pp.add_printer('QString', '^QString$', QStringPrinter)
gdb.printing.register_pretty_printer(gdb.current_objfile(), pp)
```
進到gdb 之後，首先source qstring.py ，print 一個QString 時，gdb 就會呼叫我們寫的QStringPrinter 的to\_string 來處理，就會得到垃圾訊息：I'm QString。  

to\_string 回傳的規則如下：  
python 的integer, float, boolean, string 都是gdb 可處理的(可轉換為gdb.Value)，會由gdb 直接印出；回傳None的話則不會印東西。  
傳回其他的gdb.Value，那gdb 會接續處理這個value，處理中也會呼叫其他註冊的pretty printer；真的無法處理，gdb就會丟出exception。  
另外我們可以實作display\_hint 的介面，告知gdb 要如何處理這個值的輸出，這會影響到gdb 如何接續處理這個值；這裡我們表示這個輸出是個字串。  

上面只是舉例，要印出同樣的結果，我們的to\_string 要稍微改寫：  
```python
addr = self.val.address
size = self.val['d']['size']
i = 0
content = []
while i < length:
  c = self.val['d']['data'][i]
  if c > 127:
    content.append("\\u%x" % (int(c)))
  else:
    content.append(chr(c))
  i = i + 1
return '(QString)%s (length=%d): "%s"' % (addr, size, "".join(content))
```

我在查這個的時候，發現有[另一個人的實作](http://nikosams.blogspot.tw/2009/10/gdb-qt-pretty-printers.html)生猛得多：  
```python
dataAsCharPointer = self.val['d']['data'].cast(gdb.lookup_type("char").pointer())
content = dataAsCharPointer.string(encoding='utf-16', length=size*2)
```

他直接用cast 得到一個新的gdb.Value()，型態為char pointer；再呼叫string()方法用utf-16 的方式encoding，就把字串給拿出來了，
更多用法可以參考[文件](https://sourceware.org/gdb/onlinedocs/gdb/Values-From-Inferior.html)，這裡暫時不詳細說明：  

不過，這樣的pretty printer 其實有個問題的，因為它寫死了一定會去讀取self.val['d']裡面的值，
但這個值未必是有初始化的，這時使用pretty printer 就會出錯：  
```txt
<error reading variable: Cannot access memory at address 0xa>
```

其實要用pretty printer 的話，在.gdbinit 裡面加上 set print pretty on 就是個不錯的開始，光這樣就能讓一些輸出漂亮很多
（其實也就是塞在一行裡跟自動換行的差別XDDD），相對開了這個print 也會佔掉比較多行數。  
一般除非是客製的資料結構又有大量debug 的需求，才會需要客製化pretty printer，像是gdb 內應該已內建C++ std 的pretty printer，
Qt 的開發套件應該也有提供Qt 的；寫rust時所用的rust-gdb也只是對gdb 進行擴展，在開始時先引入設定檔，裡面也有Rust 的pretty printer。  
```bash
# Run GDB with the additional arguments that load the pretty printers
PYTHONPATH="$PYTHONPATH:$GDB_PYTHON_MODULE_DIRECTORY" gdb \
  -d "$GDB_PYTHON_MODULE_DIRECTORY" \
  -iex "add-auto-load-safe-path $GDB_PYTHON_MODULE_DIRECTORY" \
  "$@"
```
但一般人似乎不太用得到這個功能，所以這篇其實是廢文一篇(蓋章，感謝大家貢獻兩分鐘的時間給小弟的blog (炸。  