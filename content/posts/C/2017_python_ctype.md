---
title: "用Python ctypes 建立與C的介面"
date: 2017-03-21
categories:
- c
- python
tags:
- c
- python
series: null
---

故事是這樣子的，最近小弟接觸一項工作，主要是開發一套C 的API，實作大程式底層的介面，
以前只有改過別人的介面，這次自己從頭到尾把介面建起來，git repository 提交100多個commit，說實在蠻有成就感的。  
寫Project的過程中也發現自己對測試的經驗實在不夠，本來想說該把unit test set 建起來然後做個 regression test，
結果unit test 寫一寫最後都變成behavior test 了，啊啊啊啊我根本不會寫測試啊，測試好難QQQQ  
<!--more-->

寫測試時也發現一個問題，用C 寫測試實在有點痛苦，陸續看了幾個例如 [CMocka](https://cmocka.org/) 的testing framework，實作起來還是挺麻煩的；
有些要測試的功能，例如檔案parser，都需要另外找library來支援，而C 的library 卻未必合用，要放入project 的Makefile 系統也很麻煩；
C 需要編譯也讓有彈性的測試較難達成。  
這時我們的救星：Python 又出現了，是否能利用python上面豐富的模組跟套件，還有簡單易用的 testing framework，可以彈性修改的直譯執行來幫助測試呢？  

一開始我看了一下Python C/C++ extension，這是將C的程式包成函式庫，並對它增加一層 Python 呼叫的介面，變成 Python 可以 import 的module。  
但是這個方法有點太殺雞用牛刀了，這是要用在python 極需性能的部分，可以寫C 進行加速，而不是單純想 call C function 來測試。  
比較好的解法是利用python 的 [ctypes](https://docs.python.org/2/library/ctypes.html)，
可以直接載入編譯好的 shared library，直接操作C 函式。  
引用參考資料[程式設計遇上小提琴](http://blog.ez2learn.com/2009/03/21/python-evolution-ctypes/)的話：

> 與其做出pyd來給python使用這種多此一舉的事情，東西就在那裡，dll就在那裡，為何不能直接使用呢？  

所以我們的救星：ctypes 登場了。  

首先是要引用的對象，使用ctypes 前要先把要引用的project 編成單一的動態函式庫，下面以 libcoffee.so 為例，
如此一來，我們可以用下列的方式，將 .so 檔載入python 中：  

```python
filepath = os.path.dirname(os.path.abspath(__file__))
libname = "libcoffee.so"
libcoffee = ctypes.cdll.LoadLibrary(os.path.join(filepath, libname))
```

ctypes 有數種不同的載入方式，差別在於不同的 call convention
* cdll 用的是cdecl
* windll 跟 oledll 則是 stdcall

載入之後就可以直接call 了，有沒有這麼猛(yay)  

## 參數處理：

ctypes 中定義了幾乎所有 C 中出現的基本型別，可[參考說明文件表格](https://docs.python.org/2/library/ctypes.html#fundamental-data-types)，
None 對應 C 的NULL
所有產生出來的值都是可變的，可以透過 .value 去修改。例外是利用Python string 來初始化 `c_char_p()`，再用 value 修改其值，
原本的Python string 也不會被修改，這是因為Python string 本身就是不可修改的。  

如果要初始化一塊記憶體，丟進C 函式中修改的話，上面的 `c_char_p` 就不能使用，要改用 `create_string_buffer` 來產生一塊記憶體，
可以代入字串做初始化，並指定預留的大小，爾後可以用 .value 來取用 NULL terminated string，.raw 來取用 memory block。  
如果要傳入 reference ，除了 `create_string_buffer` 產生的資料型態本身就是 pointer 之外，可以用 byref() 函式將資料轉成 pointer。  
使用 ctypes 呼叫C 函式，如果參數處理不好，會導致 Python 直接crash，所以這點上要格外小心。  

我們可以為函式加一層 argtypes 的保護，任何不是正確參數的型態想進入都會被擋下，例如：  
```python
libcoffee.foo.argtypes = [c_int]
# 之前這樣會過，C function 也很高興的call 下去
libcoffee.foo(ctypes.c_float(0))
# 設定之後就會出現錯誤
ctypes.ArgumentError: argument 1: <type 'exceptions.TypeError'>: wrong type
```

這部分採 strict type check ，甚至比C 本身嚴格，如果設定argtypes 為：  
```python
POINTER(c_int)
```
那用 `c_char_p` 這種在C 中可以轉型過去的型態也無法被接受。  

## 回傳值：

restype 則是定義 C 函式的 return type，因為我的函式都回傳預設的 c\_int ，所以這部分不需要特別設定。  
比較令我驚豔的是，ctypes 另外有 errcheck 的屬性，這部分同restype 屬性，只是在檢查上比較建議使用errcheck。  
errcheck 可以設定為 Python callable (可呼叫物件，無論class 或function )，這個callable 會接受以下參數：  
```python
callable(result, func, args)
```
* result 會是從C 函式傳回來的結果
* func 為 callable 函式本身
* args 則是本來呼叫C 函式時代進去的參數

在這個callable 中我們就能進行進一步的檢查，在必要的時候發出例外事件。  
```python
def errcheck(result, func, args):
 if result != 0:
   raise Exception #最好自己定義 exception 別都用預設的
 return 0
libcoffee.errcheck = errcheck
```

## 衍生型別：

ctypes 另外提供四種衍生型別

* Structure: C struct
* Union: C union
* Array: C array
* Pointer: C pointer

### Struct, Union
每個繼承 Structure 跟Union 的 subclass 都要定義 `_filed_`，型態為 2-tuples 的 list，
2-tuple 定義 field name 跟 field type，型態當然要是 ctypes 的基本型別或是衍生的 Structure, Union, Pointer 。  

Struct 的align 跟byte order 請參考[文件描述](https://docs.python.org/2/library/ctypes.html#structure-union-alignment-and-byte-order)，
一般是不需要特別設定：  

### Array
Array 就簡單多了，直接某個 ctypes 型態加上 * n 就是Array 型態，然後就能如class 般直接初始化：  
```python
TenInt = ctypes.c_int * 10
arr = TenInt()
```

## Pointer
Pointer 就如上面所說，利用 pointer() 將 ctypes 型別直接變成 pointer，它實際上是先呼叫 POINTER(c\_int) 產生一個型別，然後代入參數值。  
爾後可以用 .contents 來取用內容的副本（注意是副本，每次呼叫 .contents 的回傳值都不一樣）和 C 一樣，
pointer 可以用 python 取值的 `[n]` slice，並且修改 `[n]` 的內容即會修改原本指向的內容，
取用 slice 的時候也要注意out of range 的問題，任何會把C 炸掉的錯誤，通常也都會在執行時把 python 虛擬機炸了。  
同樣惡名昭彰的Null pointer dereference：  
```python
 null_ptr = POINTER(c_int)()
```
產生NULL pointer，對它 index 也會導致 Python crash。  

## Callback

ctypes 也可以產生一個 callback function，這裡一樣有兩種不同的型式：

* CFUNCTYPE：cdecl
* WINFUNCTYPE：stdcall

以第一個參數為 callback 的return type，其餘參數為 callback 參數。  
這部分我這裡沒有用到先跳過，不過下面[文件連結](https://docs.python.org/2/library/ctypes.html#callback-functions)
有示範怎麼用ctypes 寫一個可被 qsort 接受的 callback 函式，真的 sort 一個buffer 給你看。

## 實際案例

上面我們把ctypes 的文件整個看過了，現在我們來看看實際的使用案例。  
這裡示範三個 C function，示範用ctypes 接上它們，前情提要一下project 的狀況，
因為寫project 的時候消耗了太多咖啡了，所以project 的範例名稱就稱為 coffee，我們會實作下面這幾個函式的介面：  
```c
// 由int pointer回傳一個隨機的數字
int coffee_genNum(int *randnum, int numtype);
// 在buf 中填充API version string
int coffee_getAPIVersion (char *buf)
// 對src1, src2 作些處理之後，結果塞回到dest 裡面
int coffee_processBuf (char *src1, char *src2, char *dest, int len)
```

針對我要測試的 c header，就對它寫一個 class 把該包的函式都包進去，init 的部分先將 shared library 載入：  
```python
import ctypes
import os.path

class Coffee(object):
  """libcoffee function wrapper"""

  def __init__(self):
    filepath = os.path.dirname(os.path.abspath(__file__))
    libname = "libcoffeeapi.so"
    self.lib = ctypes.cdll.LoadLibrary(os.path.join(filepath, libname))
```
所有 header 檔裡面的自訂型別，都能很容易直接寫成 ctypes Structure，舉個例本來有個叫counter 的 Union，比對一下C 跟Python 版本：  
#### C 版本：   
```c
typedef union Counter {
  unsigned char counter[16];
  unsigned int counter32[4];
} Counter;
```

#### Python ctypes 版本：   
```python
class Counter(Union):
  _fileds_ = [
    ("counter", c_uint8 * 16),
    ("counter32", c_uint32 * 4)]
```

針對 C 裡面的函式，我們把它們寫成各別的 Python 函式對應，同時為了保險起見，每個函式都設定 argstype，
這樣在參數錯誤時就會直接丟出 exception；又因為函式都依照回傳非零為錯誤的規則，所以可以對它們設定 errcheck 函式，
在return 非零時也會拋出例外事件。  

這裡的作法是在 `class __init__` 裡面把該設定的都寫成一個dict，這樣有必要修改的時候只要改這裡就好了：  
```python
def errcheck(result, func, args):
    if result != 0:
        raise Exception
    return 0

# in __init__ function
argstable = [
  (self.lib.coffee_genNum,          [POINTER(c_int), c_int]),
  (self.lib.coffee_getAPIVersion,   [c_char_p]),
  (self.lib.coffee_processBuf,      [c_char_p, c_char_p, c_char_p, c_int])]

  for (foo, larg) in argstable:
    foo.argtypes = larg
    foo.errcheck = errcheck
```

然後實作各函式，這部分就是苦力，想要測的函式都拉出來，介面的參數我就用Python 的物件，在內部轉成ctypes 的物件然後往下呼叫，
如 getNum 的轉化型式就會長這個樣子，pointer 的參數，可以使用 ctypes 的byref 。  
```python
# int coffee_genNum(int *randnum, int numtype);
def genNum(self, numtype):
  _arg = c_int(numtype)
  _ret = c_int(0)
  self.lib.coffee_genNum(byref(_ret), _arg)
  return _ret.value
```

getAPIVersion 是類似的，這次我們用 `create_string_buffer` 產生一個 char pointer，然後直接代入函式，就可以用value 取值了。  
```python
# int coffee_getAPIVersion (char *buf)
def getAPIVersion(self):
  buf = create_string_buffer(16)
  self.lib.coffee_getAPIVersion(buf)
  return buf.value
```

最後這個的概念其實是一樣的，我把它寫進來只是要火力展示XD，上面提到的processBuf，實際上可以把它們跟Python unittest 結合在一起，
利用python os.urandom來產生完全隨機的string buffer，答案也可以從python 的函式中產生，
再用unittest 的assertEqual 來比較buffer 內容：  
```python
l = 4096
src1 = create_string_buffer(os.urandom(l-1))
src2 = create_string_buffer(os.urandom(l-1))
dest = create_string_buffer(l)
ans  = generateAns(src1, src2)
self.lib.coffee_processBuf(src1, src2, dest, l)
self.assertEqual(dest.raw, ans)
```

一個本來在C 裡面要花一堆本事產生的測試函式就完成啦owo  
如能將這個class 加以完善，等於要測哪些函式都能拉出來測試，搭配python unittest 更能顯得火力強大。  

## 後記：  
趁這個機會把ctype的文件整個看過一遍，覺得Python 的 ctypes 真的滿完整的，完全可以把 C 函式用 ctypes 開一個完整的 Python 介面，
然後動態的用 Python 執行，真的是生命苦短，請用python。  