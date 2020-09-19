---
title: "使用GAE 回應fetch API"
date: 2016-11-18
categories:
- web
tags:
- google cloud platform
series: null
---

最近在寫GAE 上面的服務，把東西存進資料庫之後，開點API 讓使用者拿資料；這感覺就好像先蓋個大水槽裝滿水，然後在上面打洞讓水流出來讓使用者們喝(X  
因為都2016 年了，被人說別再用XMLHttpRequest，趕快用 [fetch API](https://developer.mozilla.org/en-US/docs/Web/API/WindowOrWorkerGlobalScope/fetch) 吧，
就來研究一下GAE 要怎麼服務fetch API。  
<!--more-->

fetch API 用起來很直覺，對著一個網址 fetch 下去就是了，我開了個API 叫fetch，就是這麼直覺，回來的東西會丟進then裡面處理：  
```js
fetch("/fetch?type=data").then(funciton(response) {
  console.log(response);
}
```

其實概念是一樣的，fetch 就是去取某一個位址，所以我們可以開一個fetch 的handler，然後把對fetch 的請求都導到那邊去，然後建一個handler：  
```python
app = webapp2.WSGIApplication([
  ('/fetch', MessageFetchHandler),
], debug=True)

class MessageFetchHandler(webapp2.RequestHandler):
  def get(self):
    reqType = self.request.get("type") # reqType == "data“
```

剩下的就是handler的事了，想回什麼就回什麼，文字就文字，binary 就把binary讀出來寫回去，像是：  
```python
self.response.write("response message") # return text
with open("img/servo.png") as f:
  img_content = f.read()
self.response.content_type = 'image.png'
self.response.write(img_content) # return binary
```

一開始的時候，因為我有用GAE 的user API，在寫fetch 的時候，我的fetch API都會被redirect 到login 的網址，
後來發現fetch API 預設不會包含必要的資訊，以致GAE 查不到已登入的資訊，要修好就是在fetch 時多加一點東西。  
fetch 提供了 Headers(), Request()函式來建立fetch，fetch 並可代入init 參數做更多設定。  
例如我這邊的狀況，使用自定義的Init 參數，設定credentials 為[same-origin](https://fetch.spec.whatwg.org/#concept-request-credentials-mode)，GAE 就不會再把我們導向login了。  
另外也可以設定如mode, cache 等設定，比使用XMLHttpRequest來得彈性。  
Header則可建立request的header，例如content-type，詳細的內容可以參考後面附的參考文件。  
```js
var userInit = {
  method: "GET",
  credentials: "same-origin" };
var userRequest = new Request('/fetch?type=user', userInit);
fetch(userRequest, userInit).then(function(response) {
  if (!response.ok) {
    console.log(response);
  }
}
```

以上大體就是關於GAE 回應fetch API 的寫法，再來就是寫各種API 了。  

相關資料：  
<https://developer.mozilla.org/zh-TW/docs/Web/API/GlobalFetch/fetch>  
[https://developer.mozilla.org/zh-TW/docs/HTTP/Access\_control\_CORS](https://developer.mozilla.org/zh-TW/docs/HTTP/Access_control_CORS)  
<https://fetch.spec.whatwg.org/#concept-request-credentials-mode>  

