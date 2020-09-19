---
title: "使用Google App Engine 處理前端ajax request"
date: 2015-07-12
categories:
- web
tags:
- google cloud platform
- javascript
series: null
---

最近在學用GAE寫一個簡單的服務，結果一直鬼打牆，這時候就要來跟我念一遍：前．端．超．難．   
這次是用了google app engine來處理ajax post，送一些base64 encode後的字串把資料送到server去，用的是ajax 來達成，
[ajax](http://www.w3schools.com/ajax/default.asp) 其實跟一般的post, get沒什麼兩樣，
只是它不需要重新整理網頁，可以做到網頁內容即時的變換。   
<!--more-->

使用時先產生一個XMLHttpRequest物件，如果是IE5跟IE6就直接放棄支援(其實要用舊語法，不過…算了管它去死)，
並用它開啟一個GET, POST的要求，指定server 的URL跟是否同步傳送，並用send()發送   

還可以用setReqeustHeader來指定post 的內容，總之有許多的設定可以選用，我用的就很直接，一個非同步的post 把資料送去server 就是  
```javascript
xmlhttp = new XMLHttpRequest()   
xmlhttp.open(“POST”, “upload?data=” + data, true);   
xmlhttp.send();    
```

建立python handler，其實就是post handler，GAE已經把post分解為request物件，直接取裡面的內容就好了:   

```python
class UploadHandler(webapp2.RequestHandler):   
def post(self):   
    data = self.request.get("data")    
```

後來發現這裡的內容有錯，這樣寫會動沒錯，但因為data 仍然在open() 的URL 裡面，因為GET method，會視瀏覽器遇到幾KB 的長度限制，
data 很長的話應該要放在send() 裡面，才是POST method ，理論上的長度上限是 GB 等級。  
上面應該要改成：  
```python
xmlhttp = new XMLHttpRequest()   
xmlhttp.open(“POST”, “upload", true);   
xmlhttp.send(data);  

class UploadHandler(webapp2.RequestHandler):   
def post(self):   
    data = self.request.body    
```
如果要回應什麼東西給ajax，用return送回去就是了，並在routing rule 建立對應的規則：   

```python
app = webapp2.WSGIApplication([   
    ('upload', UploadHandler),   
], debug=True)    
```
這樣一個極簡單的ajax post handler就完成了，雖然說我python後端無法解開前端javascript編碼的base64字串，不知道又是哪裡有問題，反正前端超難我什麼都不會   

本文感謝世恩大神的指導。