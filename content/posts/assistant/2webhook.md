---
title: "連接 Google Assistant Webhook"
date: 2020-01-11
categories:
- GoogleAssistant
tags:
- GoogleAssistant
- dialogflow
- ngrok
series:
- GoogleAssistant
---

上一篇可以看到，我們的 action 可以從我們說的話裡面萃取出關鍵字詞，一般簡單的回應可以在 Intent 裡面剖析、回應，但 dialogflow 也僅止於判斷語意跟萃取關鍵字，如果使用者要使用外部服務，像是訂車票之類，一定要連接到外部訂票網站，這個時候就需要借助 webhook 的力量了。  
<!--more-->

dialogflow 可以讓一個 Intent 的 fulfillment，也就是完成回應，送到另一個 server 的 webhook 來處理，由伺服器回應使用者的需求，同時間伺服器也能去呼叫其他的 API 服務，完成 Google Assistant 幫助使用者完成某件事情。
這個做法的優先權比較高，我試過用了 webhook ，它的回應會蓋過 Intent 裡面設定的回應，完整的介紹可以參考 [Google 的文件](https://cloud.google.com/dialogflow/docs/fulfillment-overview)。  

如果有看 codelab 的課程，裡面使用的回應是用 dialogflow 內建的 server 或是連接到 firebase 上面的 server，兩個都是用 nodejs 實作，這是我們第一個要解的問題：我不想寫 nodejs 看到 nodejs 就會傷風感冒頭痛發燒上吐下瀉四肢無力，所以我們不能用 nodejs。  
幸好隨手拜 google 大神，就找到有人[用 python 架 server](https://medium.com/zenofai/creating-chatbot-using-python-flask-d6947d8ef805)，
之前在 MOPCON 講 COSCUP chatbot 的講者大大也是[用 golang 架 server](https://hackmd.io/@mopcon/2019/%2F%40mopcon%2FryFCOLxYB)，所以要擺脫 nodejs 一定是沒問題。  

我們這篇的目標是做一個把 python server 給架起來，然後把歡迎訊息改成用 webhook來回應，都是 google 的服務，伺服器可以用同專案開 GAE 放在上面，但測試時用 ngrok 本地測試會比較方便。  
首先是先設定 webhook，在 dialogflow 裡面把 `Default Welcome Intent` 最下面 fulfillment 的 `Enable webhook call for this intent` 打開：
![webhook](/images/assistant/webhook/03_openwebhook.png)   

在 fulfillment 裡面打開 webhook，在 URL 裡面填上 webhook 的位址，這部分等等寫好服務之後再來填：]
![fulfillment](/images/assistant/webhook/02_fulfillment.png)   

下面開始寫我們首先開一個新的 python 專案，建立 pip requirements.txt：  
```txt
# requirements.txt  
Flask==1.1.1   
```
使用 pip 跟 virtualenv 建立環境：  
```bash
python -m venv env  
source env/bin/activate  
pip install -r requirements.txt   
```
接著建立 flask 實作的 webhook：  
```python
from flask import Flask, request, jsonify, make_response
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
  data = request.get_json(silent=True, force=True)
  print("Request:{}".format(json.dumps(data, indent=2)))
  action_name = data.get("queryResult").get("intent").get("displayName")
  if action_name == "Default Welcome Intent":
    text = "Welcome to my google assistant"
    reply = { "fulfillmentText": text }
    return jsonify(reply)
```
下面是一個 Default Welcome Intent 的 webhook request，要看這個內容可以使用 dialogflow 右手邊的 Try it now 搭配 diagnostic info，可以確認 dialogflow 在判斷 Intent 有沒有錯誤，還有 fulfillment request ，也就是送到 webhook 的內容。  
![dialoginfo](/images/assistant/webhook/00_dialoginfo.png)   
![diagnosticinfo](/images/assistant/webhook/01_diagnosticinfo.png)   

下面節錄我 welcome 訊息的 request：  

* session：一個對話的 id，每一輪的話都會是同一個 id，作為對話的識別：
* queryResult queryText：對話的內容
* queryResult intent displayName：目前 dialogflow 判定使用者的意圖

dialogflow 接受的回應內容是 json 格式，可以填充的內容請見[參考文件](https://cloud.google.com/dialogflow/docs/reference/rpc/google.cloud.dialogflow.v2?hl=zh-tw#webhookresponse)，最簡單的一個回應就是設定 key 為 fulfillmentText 的內容，這個內容就會是 Google Assistant 要顯示給使用者的回應。  

最後我們使用 [ngrok](https://ngrok.com/) 來進行測試，ngrok 是一個網路服務，幫你把連接到 ngrok 的連線重導向到 localhost。在使用 ngrok 之前，測試架在雲端的網路服務流程會像這樣：  

1. 寫程式
2. 在 local 進行有限的測試
3. 上傳到雲端（等等等）
4. 跑了之後發現 server 炸掉
5. 去雲端上面撈 log 檔（等等等）
6. 改完之後所有步驟重複一次。  

用了 ngrok 之後，程式在本地、log 檔也在本地，上述耗時又麻煩的上傳雲端、撈 log 檔都省下來，真的是瞬間人生變成彩色的。  

使用 ngrok 也非常簡單，安裝好 ngrok 之後照著網頁的指示先註冊金鑰：  
```bash
>> ngrok authtoken <token>  
>> ngrok http 8080  
Forwarding https://wwwwww.ngrok.io -> http://localhost:8080   
```
也就是 wwwwww.ngrok.io 已經被映射到我們的 localhost:8080 由 flask 執行的伺服器，因此我們可以在 webhook 的地方填入 wwwwww.ngrok.io/webhook。  

我們來測試一下：  

![test](/images/assistant/webhook/04_test.png)   

看到我們的 Assistant 回應了我們在 webhook 設定的回應。 