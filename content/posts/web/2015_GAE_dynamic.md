---
title: "Google App Engine 回應動態內容"
date: 2015-12-17
categories:
- web
tags:
- google cloud platform
series: null
---
j
文章標題是照翻原來的內文：
[Dynamic Image](https://cloud.google.com/appengine/articles/python/serving_dynamic_images)，
這次試著處理聲音，發現一樣可以使用，就記錄一下。  
<!--more-->

找一下舊文章發現[上一篇類似主題]({{< relref "2015_GAE_ajax.md">}})竟然是七月的事：  
well，畢竟在陰間不好辦事，又遇到base64 decode的問題，弄了很久一直沒進度，這次放假問題解掉了，順利把資料送到後端；問題有兩個  

1. 我之前把資料放在url 裡面一起送，結果base64 string 的'+'全變成space，後端python base64 module decode不出來，
本來是用一種很蠢的解法，先讓資料經過data.replace(“ “, “+”)，結果 deploy 的時候遇到……
2. 資料放在url 裡面有長度限制，應該要放在send資料裡才對，連帶這樣也沒 '+' 被取代的問題

詳情寫在上面那篇文內。  

資料送到後端，寫入google app engine 的 [ndb 資料庫](https://cloud.google.com/appengine/docs/python/ndb/)
很直覺，先建一個class 把該有的資料庫項目填進去，不管影像或聲音都是ndb 的BlobProperty  
```python
class RecordFile(ndb.Model):  
    content = ndb.BlobProperty(indexed=False)  
    date = ndb.DateTimeProperty(auto_now_add=True)
```

這是prototype 的關係，只記了兩個欄位。  

在upload handler裡面，就可以用put()把資料寫到資料庫裡，用Key的get可以把資料再取出來：  
```python
recordFile = RecordFile(content=decoded)  
retrieveKey = recordFile.put()   
```

要怎麼把取出來的blob 塞進html 裡面？  
這裡首先要寫一個Handler負責取出資料庫裡的BlobProperty，然後把binary 直接寫出來：  
```python
class GetAudio(webapp2.RequestHandler):  
    def get(self):  
        recordFile = retrieveKey.get()  
        if recordFile.content:  
            self.response.headers['Content-Type'] = 'audio/wav'  
            self.response.write(recordFile.content)   
```

再來我們要把跟圖片/聲音的request 都轉給這個handler，這裡我是假定跟/wav有關的url 都轉給它，在handler register加上這行：  
```python
app = webapp2.WSGIApplication([  
    ('/wav', GetAudio),  
], debug=True)   
```

最後我們就能在圖片/聲音 tag 的src後面，直接寫上/wav, /img之類的網址：  
```html
<audio controls>  
    <source src="/wav?key=XXX” type="audio/wav">  
    Your browser does not support the audio element  
</audio>   
```
我這裡當然不是真的寫XXX，實際上的做法是{{ key }}，再用JINJA2的render把資料塞進去，一樣的方法也適用圖片上，
寫個/img 的handler 並把image 的blob 寫回去即可。