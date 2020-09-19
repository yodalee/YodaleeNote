---
title: "不為人知的gdb 使用方式系統-gdb pretty printer auto load"
date: 2016-09-16
categories:
- simple setup
tags:
- gdb
- rust
series: null
---

前言：  
最近因為jserv 大神的關係，看了下面這部Become a GDB Power User  
{{< youtube 713ay4bZUrw>}}
覺得裡面還不少生猛的用法之前都不會用，決定把它整理一下，[上回]({{< relref "2016_gdb_prettyprint.md">}})
我們提到了gdb 的pretty printer，現在我們就來看個範例：寫Rust 用的Rust-gdb。  
<!--more-->

其實 rust-gdb 跟gdb 本質上沒什麼不同，裡面將python pretty printer 的路徑加到gdb source 的路徑，然後執行gdb…  
```bash
gdb -d "$GDB_PYTHON_MODULE_DIRECTORY" \
-iex "add-auto-load-safe-path $GDB_PYTHON_MODULE_DIRECTORY" \
"$@"
```
這樣感覺什麼都沒加進去呀，事實上，rust 是透過比較隱晦的機制，在編譯的時候將要引入的資料插在執行檔的 .debug\_gdb\_scripts 裡面，
這個section 會包含null-terminated 的條目(entry)指明gdb 要載入哪些script，
每個script 的開頭會有一個byte 指明這是哪一種entry，拿我之前寫的racer 來試試，把它的section 印出來：  
```txt
$ readelf -S racer
[17] .debug_gdb_script PROGBITS         0000000000743af8  00743af8
     0000000000000022  0000000000000000 AMS       0     0     1
```
然後我們把這個區段給印出來：  
```txt
$ readelf -x .debug_gdb_scripts racer
「.debug_gdb_scripts」區段的十六進位傾印：
0x00743af8 01676462 5f6c6f61 645f7275 73745f70 .gdb_load_rust_p
0x00743b08 72657474 795f7072 696e7465 72732e70 retty_printers.p
0x00743b18 7900                                y.
```
開頭的01，指明它是在script in python file，內容則指明要載入 `.gdb_load_rust_pretty_printers.py`，
一般我覺得是用不著這麼搞工啦，畢竟要用這招就要在編譯器上面動手腳，大概在自幹語言的時候用上這招比較方便，相關文件可見這兩個連結：  

* [Auto-loading extensions](https://sourceware.org/gdb/onlinedocs/gdb/Auto_002dloading-extensions.html#Auto_002dloading-extensions)
* [The .debug_gdb_scripts section](https://sourceware.org/gdb/onlinedocs/gdb/dotdebug_005fgdb_005fscripts-section.html#dotdebug_005fgdb_005fscripts-section)  

rust-gdb 所用的方法，如這份文件 [str_lookup_function](https://sourceware.org/gdb/onlinedocs/gdb/Writing-a-Pretty_002dPrinter.html#Writing-a-Pretty_002dPrinter)之後的部分所示  

把pretty printer 寫完之後，首先要先寫一個gdb 的lookup\_function，這個function 會負責回傳適當的pretty printer，不然就回傳None。  
文件建議這個pretty printer 放到單獨的python package 裡面，如果這個pretty\_printer是針對某個函式庫寫的，
那更建議package 的名字要加上函式庫的版本號，這樣gdb 能載入不同版本的pretty printer；
最後在auto load 的script 中import 這個pretty printer，用gdb.pretty\_printers.append ，把這個lookup\_function插入gdb的objfile 中即可。  

rust-gdb 就是這樣做的：  
1. auto load 的script `gdb_load_rust_pretty_printers.py` 中，引入 `gdb_rust_pretty_printing`
2. 呼叫它的 `register_printers`，把 `rust_pretty_printer_lookup_function` 插入目前的objfile 中。  

一個lookup\_function 會接受一個gdb Value，我們可以從中取得它的type的tag，從tag 中辨別它是什麼型別的資料，藉此回傳適當的pretty printer。  

我用之前的QString 做了個簡單的範例，首先我們要改造一下我們的qstring.py，加上lookup function 跟register\_printer，
lookup function 在型別為QString 時會將這個值傳入我們寫的QStringPrinter，並回傳它：  
```python
def qstring_lookup_function(val):
  lookup_tag = val.type.tag
  if lookup_tag is None:
    return None
  regex = re.compile("^QString$")
  if regex.match(lookup_tag):
    return QStringPrinter(val)
  return None

def register_printers(objfile):
  objfile.pretty_printers.append(qstring_lookup_function)
```

接著我們寫一個autoload script : hello-gdb.py，雖然我們用到了gdb，但gdb 內的python 會自動引入這個gdb 這個module，所以不引入也沒關係：  
```python
import qstring
qstring.register_printers(gdb.current_objfile())
```
另外要注意的是，一定要使用自動載入的方式，因為gdb.current\_objfile() 只有自動載入的時候才會設定為當前的objfile。  

之所以叫hello-gdb.py，是因為我們採用另一個機制：objfile-gdb.py的檔案會被自動載入，我執行檔名叫hello ，
hello-gdb.py會在gdb 開啟時自動載入，其他有用到的dynamic library ，檔名叫libXXX-gdb.py也可以用
[類似的方法](https://sourceware.org/gdb/onlinedocs/gdb/objfile_002dgdbdotext-file.html#objfile_002dgdbdotext-file)載入。  

當然故事不是這樣就完了

1. hello-gdb.py會用到qstring.py，所以我們必須把qstring的位置加到PYTHONPATH 變數之中
2. gdb 不會隨意自動載入第三方的script，以免造成危害（雖然說到底能有啥危害我也不知道……）

因此我們必須在gdb 開始自動載入script 前，把這個script 加到安全名單之中；因此，我們的gdb 呼叫會變成下列兩者擇一，也就跟rust-gdb 相差無幾了：  
```bash
PYTHONPATH="$PYTHONPATH:/tmp" gdb -iex "set auto-load safe-path /tmp" hello
PYTHONPATH="$PYTHONPATH:/tmp" gdb -iex "add-auto-load-safe-path /tmp/hello-gdb.py" hello
```

大概的故事就是這樣了，rust-gdb 當然是lookup function 那邊搞了很多，把型別什麼共同的部分獨立出來，以便支援gdb 跟lldb。  
一般的lookup function 就不用寫這麼多了。  
又說回來，要寫到大型的lookup function 應該也只有開發語言跟函式庫的時候需要，一般人更用不到這個功能，所以這篇比起上篇其實更是廢文一篇(蓋章，感謝大家又貢獻兩分鐘的時間給小弟的blog (炸。