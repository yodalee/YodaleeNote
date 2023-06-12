---
title: "跨年不寂寞，讓 Google Assistant 陪你猜數字"
date: 2020-01-22
categories:
- GoogleAssistant
tags:
- GoogleAssistant
series:
- GoogleAssistant
---

有了我們上次的 webhook 之後，我們可以真的來挑戰一些更複雜的助理智障功能，這次就來做跟你猜數字的助理，這樣就算跨年沒有朋友，還是有助理跟你玩有趣的猜數字遊戲，從螢幕感受到滿滿的溫暖（欸。  
<!--more-->

其實做猜數字要做的事，在上篇的 webhook 中都差不多了。  

我們可以簡單畫一下流程圖，從開頭的 default welcome intent 開始：  
![workflow](/images/assistant/guessnumber/1workflow.png)   

畫個簡單的流程圖是很重要的，特別是當設計的助理功能複雜到一定程度的時候，直接徒手下去硬幹很容易迷失在 intent 海洋中，特別是 dialogflow 的介面設計，在個別 Intent 中只能看到這個 Intent 會處理什麼輸入，給出什麼輸出，
列出全體 Intent 的介面又看不出各 Intent 之間的關係，一下子就會迷失做亂掉，有了流程圖就能在編輯各 Intent 的時候，照著流程圖一一設定好。  
Webhook 也是，要在單一的 webhook 裡面處理所有的 Intent 該怎麼回應，當 Intent 數量一多的時候就會亂掉，所以都要事先做好規劃。  

簡單說一下上面的流程圖：

1. default welcome intent 進來會產生一個數字
2. 使用者輸入數字（猜數字）
    1. 如果數字不對，會顯示更新的區間
    2. 對了就會顯示一句稱讚的話然後離開對話

讓我們開始實作：  

## 設定 Default Welcome Intent

這裡我們要回應一句請使用者猜數字的話，這句話簡單可以讓 dialogflow 自己回應就好，不過我們還是要打開 webhook，讓後端的伺服器產生一個亂數出來。  
在 webhook 的部分，如果偵測到 Intent 是 Default Welcome Intent，就用 random 產生一個亂數出來；另外要把這個 session id 跟亂數寫到資料庫裡，這個 session id 是固定的，同樣的 session id 就會對應到同一組對話。  

* 新增一個 Intent GuessNumber

這個 Intent 裡面可以設定一些例句，像是：  

> I guess it is 11.  
> Let me think. 25.  
> 38.  
> Maybe 0.

在 parameter 的地方把這個數字抽取出來，設定型別是 sys.number-integer，變數名number，這個 Intent 也要打開 webhook 讓伺服器處理使用者猜數字的行為。  
![guessintent](/images/assistant/guessnumber/2guessintent.png)   

## 新增一個 Intent GuessEnd

這個 Intent 不會由使用者的輸入進入，而是我們在 GuessNumber 的 webhook 設定 assistant 進入的狀態，在這裡要新增一個 Event，我叫它 `User_number_match`，在回應的部分設定一些恭禧使用者的話，然後設定這個 Intent 結束對話 End of Conversation。  
之所以要新增這個 event，是要讓 webhook 有能力讓 dialogflow 判定要進到這個 Intent，一般 Intent 的判定都是透過使用者的輸入來決定，但在猜數字裡面使用者輸入數字判定的 Intent 一定是 GuessNumber 不會是 GuessEnd，那對話就無法結束了。因此我們自定義這個 `User_number_match` 事件，只要 webhook 發出這個事件 dialogflow 就會判定為 GuessEnd Intent 了。  

![guessendintent](/images/assistant/guessnumber/3guessendintent.png)   

## 寫 code

如上篇文所述，可以從送來的 json 中，從 queryResult -> intent -> displayName 拿到 Intent 的名字，用這個名字就能分派到不同的函式來處理；另外一個就是 json 的 session 可以拿到 session id。  
```python
session = data.get("session")
action_name = data.get("queryResult").get("intent").get("displayName")
```
我的處理函式就是對三個出現的 Intent 去處理：  

### Default Welcome Intent 產生亂數並寫入資料庫

這裡我是偷懶用 python 的 pickledb，雖然這樣推到 gae 上面可能會沒辦法用，但光為了這種小應用就要動用 gae 的 datastore 實在是有點大砲打小鳥，用 pickledb 展示一下概念就好了：  
```python
target = random.randint(low, high)
db.set(session, (low, target, high))
text = "I have a number between {} and {}. Can you guess it?".format(low, high)
reply = { "fulfillmentText": text }
return jsonify(reply)
```

### GuessNumber 的 webhook 
從資料庫裡面把存起來的數字拿出來，並從 queryResult/parameters/number 拿到使用者輸入的數字，雖然我的型別選擇 number-integer 了，dialogflow 還是塞了個 number float 給我，只能用 int 轉成 integer。  
後面就可以拿 guessnum 去跟 target 做比較，如果一樣的話就不會回覆 fulfillment 而是發送之前設定好的事件 `User_number_match` ，讓 dialogflow 進到 GuessEnd 並結束對話；不一樣的話就縮小可以猜的區間，設定回覆訊息給使用者。  
```python
minnum, target, maxnum = db.get(session)
guessnum = int(data.get("queryResult").get("parameters").get("number"))
if guessnum == target:
  event = "User_number_match"
  reply = { "followup_event_input" : { "name" : "User_number_match" } }
  return jsonify(reply)
else:
  # update minnum, maxnum here
  db.set(session, (minnum, target, maxnum))
  text = "A number between {} and {}. Keep guess.".format(minnum, maxnum)
  reply = { "fulfillmentText": text }
  return jsonify(reply)
```

### GuessEnd
GuessEnd Intent 的 webhook 就很簡單，把 session id 對應的條目庫裡面刪掉就可以了。  

## 測試

讓我們來測試一下：  

![test1](/images/assistant/guessnumber/4test.png)   
![test2](/images/assistant/guessnumber/5test2.png)   