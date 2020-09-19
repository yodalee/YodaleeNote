---
title: "使用 python自動回應網頁"
date: 2012-12-14
categories:
- web
- python
tags:
- python
series: null
---

##  緣起：

這篇文的緣起是這樣的：  
修了一門課要交作業，要從server上把資料下載下來，剖析資料之後建立模型，把模型回傳給server，server會再產生資料。  
以上的上傳下載要重複幾次，server的介面是利用php寫的。  
手動下載、建模型、上傳，這並不是個 smart 的工作方式：  
1. 來回數次用人做本來就慢
2. 也是最重要的一點，人做容易出錯，出錯就會GG要重做。
<!--more-->

## 解決方案：

經過一些調查，我使用的是python [urllib module](http://docs.python.org/3/howto/urllib2.html)，
這是個超完整的 python web module，於是就用這個來寫寫看。  

### 用python來取得 html?  
這部分urllib老早就寫好了，用如下的code，下面一行就可以把整個html以bytes的方式取出來：   
```python
import urllib
html = urllib.request.urlopen(hw_url).read()  
```
如果要寫入檔案，在開檔的時候指定為 'wb' 就可以直接將html 寫到檔案中而不怕格式錯誤。 
否則就要呼叫.decode(“utf-8”)的方式先轉換html的格式。  
針對form filling的部分也有相對應的方式，可以用下面的方式把POST的訊息編碼，在urlopen的時候附加在後面。  
```python
data = {}  
data['id'] = ID  
form_data = urllib.parse.urlencode(data)  
form_data = form_data.encode('utf-8') # data should be bytes  
response = urllib.request.urlopen(php_url, form\_data)
```
得到相同可以用read()取得資料的方式，實地驗證過，會得到一個相同的html file。  

### 取得最新的資料 - 使用正規表示法：  
現在有了取得的html檔之後，要怎麼找出其中的連結？   
這裡用上了regular expression module re的方式，這大概是地表上最強大的字串比對工具。 該網頁中的檔案下載連結類似這樣的格式  
```html
<a href=\'LOL/XD.txt\'>
```

只要parse <a href>的標籤，很容易就能找到所有的連結檔了  
```python
links = re.findall("<a\s+href\s*=\s*'(.*)'", data, re.DOTALL)
```
其中()就是我們要尋找的目標，會被存入links之中，成為一個list object，取出最後一個連結，就是我們要的最新版本的檔案了。  

另一方面，當使用者要使用這個程式時，會需要輸入他們的學號以供使用，這部分也是使用re module來進行檢查：  
```python
re.match(“\s*[A-Za-z][0-9]{8,8}\s*”, string)
```
不match的話就會回傳None，讓程式再進行一次問話。  

### 如何執行本地程式？  
這個倒比較簡單，使用python subprocess即可簡單完成：  
```python
command = "./{0}".format(program\_name)  
stdout = subprocess.check\_output(command.split())   
```
j
### 如何透過php上傳檔案？

這地方問題就頭大了，查了很久一直不知道該怎麼寫比較好。後來是經強者我同學的提示，用的解決方案是 [httplib](http://stackoverflow.com/questions/1270518/python-standard-library-to-post-multipart-form-data-encoded-data)：  

很有趣的是，httplib的運作是先讀入根目錄，再由selector去要求根目錄下的某個檔案。  

fields的部分為二元tuple組成的 list：  
tuple 第一個元素為要填入form的name attribute，請愛用「觀看原始碼」自行找出對應的name attribute；  
tuple 第二個元素為要填入的值：
例如：
```python
fields = [(“name”,”yodalee”),(“nickname”,”garbage”)]  
```

files的部分則是三元的tuple，依序為form的 name attribute、filename、file的binary；第三個用open(file, 'rb')傳入即可；例如：  
```python
files = [(“model”, “test.txt”, open(“test.txt”, “rb”))]   
```

當個例子的code如下：  
```python
fields = [("id",ID), ("model\_submit","")]  
files = [("model", filename, open(filename, "rb").read())]  

content\_type, body = encode\_multipart\_formdata(fields, files)  
h = httplib.HTTP(host)  
h.putrequest('POST', selector)  
h.putheader('content-type', content\_type)  
h.putheader('content-length', str(len(body)))  
h.endheaders()  
h.send(body)  
errcode, errmsg, headers = h.getreply()  
return h.file.read()
```
在id的欄位填入ID，model\_submit欄位填入空白，檔案則上傳 filename 所指的檔案。   
上傳檔案，並取得結果存入h之中。  

## 結論：   

我只需要下個指令，就能把作業所有需要的檔案都準備完成，打包一下，作業就被秒殺了。
雖然說我寫python code的時間其實遠超過我手動執行的時間，但整體而言輕鬆很多，這才是working smart！  

## 致謝：

有關python httplib的使用，感謝AZ Huang同學的提點。  
作業的部分，感謝Godgodmouse同學的指導。