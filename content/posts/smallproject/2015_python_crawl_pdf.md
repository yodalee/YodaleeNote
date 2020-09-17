---
title: "使用 python 爬蟲與 pdf 函式庫產生網頁 pdf 檔"
date: 2015-11-09
categories:
- small project
- python
tags:
- python
series: null
---

之前聽傳說中的jserv大神演講，發現了一本 [Learn C the hard way](http://c.learncodethehardway.org/book/)，  
簡而言之就是…呃…自虐…應該說用常人不會走的路來學C  
不過呢這東西目前來說只有html file，如果要印成一本可以看的文件，畢竟還是pdf檔比較方便，該怎麼辦呢？  
這時候用python 就對了。  
<!--more-->

概念很簡單，用一隻爬蟲爬過網頁，然後轉成pdf檔：  
爬蟲的部分我是選用強者我同學，現在在Google Taipei大殺四方的AZ大大所寫的 [Creepy](https://github.com/Aitjcize/creepy)，
雖然好像沒在維護，不過我們要爬的頁數很少，不需要太複雜的爬蟲程式。  
Html轉pdf選用 [pdfkit](https://pypi.python.org/pypi/pdfkit)，
這需要ruby的 [wkhtmltopdf](https://wkhtmltopdf.org/)，可以用
```bash
gem install wkhtmltopdf
```
安裝；再用 [pypdf2](https://pythonhosted.org/PyPDF2/)將文件全合併起來，兩個程式寫起來40行就了結了，輕鬆寫意，內容如下：  

### 爬網頁：   
```python
from creepy import Crawler
import pdfkit

class C_Hard_Way_Crawler(Crawler):
  def process_document(self, doc):
    if doc.status == 200:
      filename = doc.url.split('/')[-1].replace('html', 'pdf')
      print("%d %s" % (doc.status, filename))
      pdfkit.from_string(doc.text, filename)
    else:
      pass

crawler = C_Hard_Way_Crawler()
crawler.set_follow_mode(Crawler.F_SAME_HOST)
crawler.crawl('http://c.learncodethehardway.org/book/')
```
### 合併檔案：   
```python
from PyPDF2 import PdfFileMerger

names = ['index', 'preface', 'introduction']
for i in range(53):
  names.append("ex%d" % (i))

merger = PdfFileMerger()
for name in names:
  f = open("%s.pdf" % (name), 'r')
  merger.append(f, name, None, False)
  f.close()

f = open("Learn_C_the_hard_way.pdf", 'w')
merger.write(f)
f.close()
```
我承認我code 沒寫得很好，各種可能噴射的點，不過至少會動啦，~~信 Python 教得永生~~。  

轉出來的pdf檔超醜的，感覺跟之前一些在網路上找的pdf風格有點像，每頁的標頭有些重複的內容應該要去掉，連結也全壞了，就…有空檢討並改進XD  