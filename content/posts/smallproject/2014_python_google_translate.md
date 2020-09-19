---
title: "使用python 與Google Translate進行程式翻譯"
date: 2014-12-01
categories:
- small project
- python
tags:
- python
- qt
series: null
---

最近Qucs Project有個德國佬加入，這個……一加入就做了不少苦力的工作，像換掉一些Qt3才支援的function，換個Qt4相對應的名字，
他說他是用Xcode的取代功能寫的，老實說這個東西不是用sed就可以解決嗎(.\_.)，不過算了，有人幫忙總是好事。  
他後來又貢獻了一個PR，內容是把整個程式的德文翻譯加了一千多個翻譯，根本巨量苦力；同時他又開了一個issue，想要把德文的翻譯給補完，
我覺得這樣一個一個翻譯有點太累了，雖然Qt 有linguist幫忙，可是其實還是很累，遇到沒翻過的，還是要自行輸入。  
當下靈機一動，想到之前看過有人用Google Translate來自動進行Gnu Po檔的繁簡轉換，那一樣我能不能用Google Translate進行Qt 的翻譯呢？  
<!--more-->

為了這個我寫了一個PyLinguist的script，輔助工具選用的是Python的package [goslate](http://pythonhosted.org/goslate/)，
使用方法很簡單，產生一個goslate的物件後，叫個function 即可：  
```python
import goslate
go=goslate.Goslate()  
go.translate("worship", "zh_tw")   
'崇拜'   
```
同樣的，qt的翻譯檔就是一個xml 檔，python要對付xml也是小菜一碟，用xml.etree.Element即可，每個要翻譯的文字會以這樣的格式記錄：  
```xml
<message>  
<source>Hu&amp;e:</source>  
<translation type="unfinished"></translation>  
</message> 
```

Source是原始文字，Translation則是翻譯文，如果還沒翻譯，就會在translation tag加上type="unfinished"的屬性。  

## 整體程式流程：  

把整個xml 讀到一個xml tree 物件裡，用的是 python xml 的 [ElementTree](https://docs.python.org/2/library/xml.etree.elementtree.html)：  
```python
import xml.etree.ElementTree as ET
self.tree = ET.parse(XXX.ts)  
root = self.tree.getroot()    
```
開始翻譯，這裡我設定self.maplist這個dict物件，記錄所有翻過的內容，這樣只要以後再次出現就取用之前的結果，省下網路回應的時間；
之所以要在translate的外面加上try, except，是我發現goslate在翻譯OK這個字時，不知為何會出現錯誤，為了讓程式跑下去只好出此下策；
如果找到翻譯文，就替代掉之前的文字並拿掉unfinished的屬性。  
```python
for msg in root.iter('message'):
  source = msg.find('source').text
  isTranslated = not (msg.find('translation').attrib.get('type') == "unfinished")
  if not isTranslated:
    if source in self.maplist:
      msg.find('translation').text = self.maplist[source]
      del msg.find('translation').attrib['type']
    else:
      try:
        text = self.gs.translate(source, target_lang)
        msg.find('translation').text = text
        self.maplist[source] = text
        del msg.find('translation').attrib['type']
      except Exception:
        pass
```
最後把程式寫出去即可，也是一行搞定：  

```python
self.tree.write(filename, xml\_declaration=True, encoding="UTF-8", method="html")   
```
## 結果：

目前除了輸出時如xml 的DOCTYPE宣告會消失，大致上的功能是可接受的，翻譯800行約100到200個翻譯文的檔案，大約30秒就翻完了，
這之中可能還有一些是google translate回應的時間，這已經比人工還要快了不少。  
老話一句：working hard, after you know you are working smart，翻譯這種事多無聊，丟給google做就好啦。  
~~感恩python，讚嘆python~~  

本程式(毫無反應，其實就只是個腳本XDD) [原始碼在此](https://github.com/yodalee/PyLinguist)，不過這年頭 qt 的程式感覺已經沒多少人在寫了吧，
大家都去寫網頁了。