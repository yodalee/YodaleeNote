---
title: "Google App Engine 使用taskqueue 在背景處理工作"
date: 2016-10-27
categories:
- web
tags:
- google cloud platform
series: null
---

最近小弟在用Google App Engine 開發一個網頁的服務，大體的內容是讓使用者上傳一個檔案，伺服器處理過後，讓使用者可以瀏覽處理後的內容。  
因為檔案的大小一般都滿大的，處理起來一定會有延遲，如果handler 直接開始處理的話使用這一定會感受到網頁沒有回應，
最後請教了強者我同學 NNNN 大大，經大大指點，才知道Google App Engine其實有提供 [taskqueue](https://cloud.google.com/appengine/docs/standard/python/taskqueue)
來達成我要的功能。  
<!--more-->

簡單來說 task queue可以讓我們在背景執行耗時的工作，不影響到其他的服務，這篇是個簡單的範例，情境如下：
1. 使用者上傳要處理的檔案，處理過後會把處理的結果送到 ndb 的資料庫中儲存
2. 使用者的 ndb model 中，加上一個 isReady 的boolean，用來記錄資料是否已經處理好
3. taskqueue 處理
4. 處理完之後就會把這一個boolean設為 True
5. 如果他還是 false，前端就會顯示處理中的畫面（例如一個圓圈一直轉）。  

GAE 的taskqueue 分為 push 跟 pull 兩種  

* Push：你push 工作到queue 之後，你設定多久釋放一個工作，時間到了那個工作就會開始執行，push 的工作限定要在 10 分鐘內結束。
* Pull：這讓你決定何時從queue 中釋放工作出來執行，但你也要負擔更多管理queue 的工作。

## Create queue
一切都先從呯叫開始，在一般的get/post handler 中，[taskqueue.add](https://cloud.google.com/appengine/docs/standard/python/taskqueue/push/creating-tasks)
把工作加到 taskqueue 裡面  
```python
from google.appengine.api import taskqueue
task = taskqueue.add(
  url='/parse',
  target='worker',
  params={'user_id':user_id})
```

Target 指要執行 task 的module 是誰，另外可以指定instance, version，這裡我是依著範例叫做 worker，如果未指定module 的話，就會是預設的app.yaml 這個module：  
文件是這麼寫：  
```txt
A string naming a module/version, a frontend version, or a backend, on which to execute all of the tasks enqueued onto this queue. … If target is unspecified, then tasks are invoked on the same version of the application where they were enqueued.
```
url 用來在服務中，選擇對應的handler。  
params 可帶入字典，指明要有哪些參數，亦可直接用 ?key=value 附加在/url 後，不過我喜歡用 params的帶入，比較清楚。  

## worker.yaml
接著我們加入 worker.yaml，跟 app.yaml 一樣，這個module 用來分配task 的執行，注意handler 的URL 要用login: admin設為secure：  
```yaml
runtime: python27
api_version: 1
threadsafe: true
module: worker

handlers:
- url: /.*
  script: worker.app
  login: admin
```

最後就可以寫真正的handler 了，我們寫在worker.py中，我們要操作使用者的資料，因此先把使用者資料庫的model UserMessage獨立到單獨檔案dbmodel.py 中：  
```python
# dbmodel.py
Class UserMessage(ndb.Model):
    user = ndb.StringProperty()
    isReady = ndb.BooleanProperty()
```

Worker.py 一樣用 wsgi ，將對 /parse的要求交給 ParseHandler 處理，ParseHandler 可以用 self.request.get('key') 拿到由caller 傳來的資料，
我們這裡沒做什麼事，就是取出使用者資料然後把isReady 改為 True 再存回去；為了模擬耗時工作我加了個 sleep(10)  
```python
from google.appengine.ext import ndb
import webapp2
import logging

from dbmodel import UserMessage

class ParseHandler(webapp2.RequestHandler):
    def post(self):
        time.sleep(10)
        user_id = str(self.request.get('user_id'))
        logging.info("user_id: {}".format(user_id))

        query = UserMessage.query(UserMessage.user == user_id)
        userdata = query.fetch()

        if len(userdata) != 0:
            userdata = userdata[0]
            userdata.isReady = True
            userdata.put()

app = webapp2.WSGIApplication([
    ('/parse', ParseHandler)
], debug=True)
```

執行是最關鍵的一步了，平常是要測試的話只要  dev\_appserver.py . 就好，因為我們多了一個 worker.yaml ，
所以要指定它把 worker.yaml 也考慮進來，又因為兩個yaml 在application ID上會衝突，會出現  
```
More than one application ID found: dev~None, dev~application_id
```

所以要明確指定ID：  
```bash
dev_appserver.py -A application_id app.yaml worker.yaml
```
這樣才能正常的執行，這花了我超多時間，最後是看了[google 範例code](https://github.com/GoogleCloudPlatform/python-docs-samples) 裡，
standard/taskqueue/counter 的readme 才知道要這樣執行…  

實際上來說，我們也可以在add taskqueue 的時候不指定target，然後在app.yaml 的handler 把/parse 交由 worker.app 處理，這樣就不需要分兩個yaml 了。  
驗證有沒有動的話，我是有個 /view 的頁面，會去監看那個資料庫裡isReady 的狀態，並顯示這個狀態，在發動taskqueue 之後，重新整理一下網頁，就會看到狀態更新了。  

另外taskqueue 也可以透過 [queue.yaml](https://cloud.google.com/appengine/docs/python/config/queueref) 
來設定queue 的名稱、update rate、每個task 可以使用的空間上限等屬性，不過我們還是個小服務所以沒用上這個設定，這裡就不細講了。  

以上大概就是taskqueue 的小小整理，之後就是把 sleep(10) 換成真正重要的工作了。  

本文感謝強者我同學 NNNN 大大的指導。