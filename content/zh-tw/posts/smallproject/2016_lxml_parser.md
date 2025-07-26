---
title: "利用lxml 實作高效率的parser"
date: 2016-11-21
categories:
- small project
- python
tags:
- python
- xml
series: null
---

最近實作facebook message viewer 的時候，需要去處理相當大的html 檔案，原始檔案大小約50 MB，beautify 之後會加到近80 MB。  
<!--more-->
實作上我用lxml 來實作，用了最基本的寫法，最直覺而簡單的寫法：  
```python
from lxml import etree
parser = etree.HTMLParser(encoding='UTF-8')
root = etree.parse("largefile.htm", parser)
```
問題是什麼呢，這樣lxml 一開場就把整個htm 給載到記憶體裡面，消耗一堆記憶體。  

我們執行一下，看到的結果是這樣：  
```txt
group count 525
parse 280895 entries
./parser.py   25.80s  user 0.21s system 99% cpu 26.017 total
  avg shared (code):         0 KB
  avg unshared (data/stack): 0 KB
  total (sum):               0 KB
  max memory:                710 KB
  page faults from disk:     0
  other page faults:         181328
```
710KB！根本記憶體不用錢一樣在浪費…，我把這個丟到網路服務上，光記憶體就害自己被砍了。  

要打造節省記憶體的 xml parser，參考了[一些相關的文章](http://www.ibm.com/developerworks/xml/library/x-hiperfparse/)，
文中提供了兩種方式，

##  target class
在parse 中指定我們的target class，我們要實作一個class 包含下列四個method：  

1. start(self, tag, attrib)： 有tag open的時候會呼叫這個method，這時只有 tag name跟attribute 是可用的  
2. end(self, tag)： tag close 時呼叫，此時這個 elem 的child, text都可以取用了  
3. data(self, data)： 在parser 收到這個tag 中的text child的時候，會將text 變為作為參數呼叫這個method   
4. close： 當parse 結束時呼叫，這個method 應該回傳parse 的結果：  

之後取用  
```python
results = etree.parse(target=TargetClass)
```
results 就會是close method return 的結果，這個方法不會消耗大量記憶體，不過它的問題是每一個遇到的tag 都會觸發一次事件，
如果大檔中之有少量elements 是想剖析的，這個方法就會比較花時間；我的案例比較沒這個問題，因為我要剖析的內容幾乎橫跨整份文件。  

## iterparse

另一個方法是用lxml 本身提供的 iterparse，可是傳入指定events的tuple跟一個有興趣的tag name的list，它就只會關注這些tags 的events：  
```python
context = etree.iterparse(infile, events=('end',), tag='div')
for events, element in context:
  print(elem.text)
  ```
文中並有說，iterparse 雖然不會把整個檔案載入，為了加速整份檔案可能被多次讀取的狀況，它會保留過去element 的reference，
因此剖析會愈跑愈慢；解決方法是在iterparse 中，取完element 的資料就把它給刪除，同時還有element已經剖析過的sibiling，在iteration 最後加上這段：
```python
element.clear()
while element.getprevious() is not None:
  del element.getparent()[0]
```
要注意的一個是，使用iterparse 的時候，要避免使用如getnext() 方法，我用這個方法，有機會在剖析的時候遇到它回傳None，
應該是iterparse 在處理的時候，next element 還沒有被載入，因此getnext 還拿不到結果；
從上面的end 事件來說，每個iteration，就只能取用element 裡面的元素。

改寫過之後的parse 的執行結果：
```txt
group count 525
parse 280895 entries
./parser.py   22.59s  user 0.07s system 99% cpu 22.669 total 
  avg shared (code):         0 KB
  avg unshared (data/stack): 0 KB
  total (sum):               0 KB
  max memory:                68 KB
  page faults from disk:     0
  other page faults:         21457
```
跟文中不同，因為我有興趣的tag 比例較高，執行時間沒有下降太多，但記憶體用量大幅下降。

另外文中也有提到其他技巧，像是不要用find, findall，它們會用XPath-like expression language called ElementPath。

##
lxml 提供iterchildren/iterdescendents 跟XPath，前兩者相較 ElementPath速度會更快一些；
對於複雜的模式，XPath可以經過事先compile，比起每次呼叫元素的xpath() method，經過precompile 的XPath在頻繁取用下會快很多，
兩種寫法分別是：
```
# non-precompile:
xpathContent = "//div[@class='contents']"
content = root.xpath(xpathContent)
# precompile:
xpathContent = etree.XPath("//div[@class='contents']")
content = xpathContent(root)
```
下面是我實測的結果，在都是完全載入記憶體下，有無precompile 的速度差接近兩倍，不過這也表示我用了iterparse 其實速度是下降的，因為我iterparse 其實是有使用precompile 的：
```txt
./parser.py 14.99s user 0.35s system 99% cpu 15.344 total   
./parser.py 25.82s user 0.40s system 99% cpu 26.232 total    
```
以上大概是使用lxml 時，一些減少記憶體用量的技巧，記錄一下希望對大家有幫助。

## 題外話：
在寫這篇的過程中，我發現Shell script 的time 其實是一個相當強大的指令，除了時間之外它還能記錄其他有用的數值，像是 memory usage, I/O, IPC call 等等的資訊。
我的time 是用zsh 下的版本，我也不確定它是哪裡來的，用whereis 找不到，用time --version 也看不到相關資訊，
但man time 有相關的說明，總之copy and paste from stack overflow，把我的TIMEFMT 變數設定為：
```bash
export TIMEFMT='%J   %U  user %S system %P cpu %*E total'$' \
  avg shared (code):         %X KB'$'\
  avg unshared (data/stack): %D KB'$'\
  total (sum):               %K KB'$'\
  max memory:                %M KB'$'\
  page faults from disk:     %F'$'\
  other page faults:         %R'
```
其他的變數選項可以在man time 的format string 一節找到，這裡就不細講了，算是寫code 的一個小小收穫吧。
