---
title: "使用GAE python自幹Facebook Bot"
date: 2016-05-22
categories:
- small project
- python
tags:
- python
- facebook
- bot
series: null
---

話說最近各種Bot 的傳聞，又看到有人弄了[一個建在Flask 上面的Facebook Bot](http://enginebai.logdown.com/posts/733000/python-facebook-bot)，
強者我同學qcl 也弄了傳說中的libGirlfriendFramework，就想來弄一個回應產生器，以下是大概的開發流程：  
<!--more-->

首先先在Facebook 頁面上申請一個粉絲專頁，可以先使用「未發佈專頁」大家就不會搜到這個專頁；
另外要申請應用程式，其實Facebook messenger 的[說明文件](https://developers.facebook.com/docs/messenger-platform/quickstart)
已經寫得滿清楚了，申請的部分照著做就是了  

1. 進到應用程式主控板，選左列 **+新增產品** 並選擇 messenger，使用Facebook messenger platform。  
2. 在messenger 裡，粉絲專頁選擇自己的粉絲專頁，拿到粉絲專頁的token，記起來下面會用
3. 下方設定 webhook-edit event，回呼網址是你伺服器的網址，必須透過https 連線，驗證權杖則隨你喜好設定一段字串。  

在上面的[使用Flask開發Facebook Message Bot](http://enginebai.logdown.com/posts/733000/python-facebook-bot)，  
因為它的server 看來是買自己網域建在自家主機上面，所以在https 的部分比較麻煩，要自己用Let's encrypt 去生一個CA出來，
因為我是用 Google Compute Platform，網域直接走Google 的CA，所以這步可以省下來。  
這步卡了我卡超久，Let's encrypt 跟GAE 不太合，怎麼裝都裝不上去；經強者我同學qcl 大神提醒才發現根本不用理這個，這時上午已經過去了，當下覺得蠢。  

## webhook
第一步就是把webhook 裝上去，首先連接webhook 的route：  
```python
app = webapp2.WSGIApplication([
    ('/webhook', FBwebhook),
], debug=True)
```
並實作 get handler，所謂 verificaion token就是上面寫驗證權杖，寫到這裡可以用Postman去檢驗是否有問題：  
```python
class FBwebhook(webapp2.RequestHandler):
  def get(self):
    verification_code = "Verification Token Here"
    verify_token = self.request.get('hub.verify_token')
    verify_challenge = self.request.get('hub.challenge')
    if verification_code == verify_token:
      self.response.write(verify_challenge)
```
背後的流程是這樣子的，Facebook 會依照上面設定的 verification\_code 來問你設定的 webhook 位址，

實作完成後連接webhook 的地方應該就能通過了，四個選項依自己的需要選擇： 
* messages：接收訊息的callback，最基本都有這個，這個都沒勾你連接messenger 幹嘛XD
* message\_deliveries：傳送訊息的callback
* messaging\_optins：連接Send-to-Messenger plugin
* messaging\_postbacks：連接postback button的事件

上面四個我只勾了messages 可是也可以正常接受、發送訊息，其他三個光看說明看不懂是要幹嘛，有人知道的話歡迎解惑。  

## 註冊應用程式
連接了webhook 就能向Facebook 註冊你的應用程式了，依照getting started 的頁面指示發送要求，token請換成你粉絲專頁的token：  
```bash
curl -ik -X POST "https://graph.facebook.com/v2.6/me/subscribed_apps?access_token=<token>
```
理應會收到  
```json
{"success": true}
```

## 接收訊息
現在可以真的在facebook粉絲頁丟訊息了，它會向webhook設定的回呼網址發送Post，
[webhook reference 的頁面](https://developers.facebook.com/docs/messenger-platform/reference/webhook-events/)有介紹傳來的json 格式，
可在webhook中建post handler然後 `print(self.request.body)`，就能從google cloud platform 的紀錄中撈到：  

以下是撈到的內容：  
```json
{
"object":"page",
"entry":[
  {
  "id":"page id",
  "time":1463907808653,
  "messaging":[
    {
    "sender":{"id":"sender id"},
    "recipient":{"id":"recipient id"},
    "timestamp":1463907808591,
    "message":{
      "mid":"mid.1463907808584:503df60b4ad4529365",
      "seq":7,
      "text":"XDDD"}
    }
  ]}
]}
```
處理訊息用python json 就行了：   
```python
message_entry = json.loads(self.request.body)['entry']
for entry in message_entry:
    messagings = entry['messaging']
    for message in messagings:
        sender = message['sender']['id']
        if message.get('message'):
            text = message['message']['text']
            print(u"{} says {}".format(sender, text))
```

## 回應訊息
到這裡應該可以在你的google cloud platform 紀錄中找到你發送訊息的內容，下一步就是回訊息，只要向粉絲專頁的網址，
搭配token發送post 訊息即可，很容易…個頭：  
```python
def send_fb_message(self, to, message):
  post_url = "https://graph.facebook.com/v2.6/me/messages?access_token={token}"
    .format(token=FBtoken)
  response_message = json.dumps(
    {"recipient": {"id": to},
     "message": {"text": message}})
  result = urlfetch.fetch(
    url=post_url,
    headers={"Content-Type": "application/json"},
    payload=response_message,
    method=urlfetch.POST)

  print("[{}] reply to {}: {}".format(result, to.encode('utf-8'), message))
```

要注意的一個是，因為google appengin python 一直停留在python2.7 ，所以unicode handler不若python3 這麼完整，
上面很多encode('utf-8')都是不斷錯誤後加上去的，也曾經發送訊息 **太強啦** 結果GAE 整個當掉，因為這三個字一直引發handler crash，
handler沒有回音導致Facebook又發送一次「太強啦」過來，然後就無限loop 了，
這時要用上面的curl 命令，把你註冊的程式重整一下，讓Facebook 不要再發訊息過來。  

為了這堆unicode 又花掉一個下午，寫這個簡單的Bot 一天就用掉了…寫到這裡我突然想到那篇傳奇文章
[軟體工程師的鄙視鏈](https://vinta.ws/blog/695)裡面那句：  

> 用 Python 3 的工程師鄙視還在用 Python 2 的工程師
> 用 Python 2 的工程師鄙視遇到 UnicodeEncodeError 的工程師。  

完了我要被鄙視了QAQ  

總之最後結果像這樣：  
![facebook bog](/images/posts/facebook_bot.png)

我曾經很認真地想過這個功能到底有什麼用，後來我想到，例如中央氣象局的粉絲頁就能加入註冊跟發送訊息的功能，
我們可以發送訊息給該粉絲頁：「註冊/台北」或「註冊/高雄」  
後端的handler 在接受這樣的訊息時，將發送者的ID跟地點加入後端的資料庫中，如地震通報或是每日當地的氣象預報就能自動發訊息給每位註冊的使用者。   

不過目前沒看到非常印象深刻的應用就是了。  

## [Project 放在這裡](https://github.com/yodalee/IPban-bot)