---
title: "跨年好寂寞？使用 Google Assistant 跟你對話"
date: 2020-01-04
categories:
- GoogleAssistant
tags:
- GoogleAssistant
- dialogflow
series:
- GoogleAssistant
---

故事是這樣子的，2019-2020 的跨年，小弟邊緣人沒地方去，後來就自己回家當紅白難民，然後還沒聽到 Lisa 唱紅蓮華QQQQ。
不過幸好宅宅有宅宅的做法，沒聽到紅蓮華我們可以看 Youtube [別人上傳的影片](https://www.youtube.com/watch?v=tnIHWvf-vgE)，沒有朋友跨年我們可以自幹朋友，也就是我們今天的主角：Google Assistant。  
<!--more-->

如果平常有用 Google Pixel 手機，或是家裡有 Google Home 裝置的，應該就會知道它上面附的 Google Assistant ~~Christina~~，雖然說我覺得還是滿沒用的啦，我自己只會拿它來查天氣，有 Google Home 的同學只用它來開關燈，但反正，都有這麼好的工具了為什麼不來好好玩一下？就趁著跨年的假日做點不一樣的事來玩。  

下面是一個基礎的流程，跟 [codelabs](https://codelabs.developers.google.com/) 的課程（搜尋 google assistant 有三級課程可以上）一樣，做一個會回應你的小程式，我們想做到的就是：它會問你最喜歡的顏色，然後會重複你的話：你最喜歡的顏色是XXX。  

## 建立專案

首先來到 [google action](https://console.actions.google.com/) 的頁面，~~雖然是 Google Assistant 卻叫 Google Action 呵呵~~。
先建立一個新的 project，類型選擇對話 Conversational，語言我是建議先選英文，之後應該會試著做做看中文的助手，但英文比較萬無一失。  
建立之後要設定一個發語詞，平常在手機上呼叫 Google Assistant 是用 OK google，另外也可以用 talk to my "發語詞" 來呼叫你寫的程式，或者是打開某個 App，這裡我們沒決定名字就叫它 TestApp 就好。  

![quicksetup](/images/assistant/dialogflow/01_actiondevelop_quicksetup.png)

## 連接 dialogflow
下一步要產生一個 Action，選擇 Custom Intent 再點 Build ，這會連結你的 action 到 dialogflow 建立一個新的 Agent，可以想像一個 Agent 就是回話的機器人，這裡一樣語言建議選擇英文，時后就選擇 +8 時區（不知道為什麼只有香港可選）。  

![dialogflow](/images/assistant/dialogflow/02_dialogflow.png)   

這個背後流程是這樣子的，你跟 Google Assistant 講話之後，Google Assistant 會把這段話送到 Google Action，那 Google Action 又要怎麼理解這段話？就是靠 dialogflow 服務，算是一個簡化版本的自然語言理解框架，可以理解說話的意圖，解析出關鍵字送出回應，而中間這些關鍵字跟回應是可以由設計者設定的；其他家類似的服務像是 Amazon Lex、IBM Watson 等。  
dialogflow 由許多的 Intent（意圖）所構成，dialogflow 會從 google assistant 來的輸入辨識出現在要選擇哪個意圖，然後照著意圖的設定去回應；可以把google assistant 想像成一個狀態機，意圖想成一個狀態，照使用者的輸入進到不同狀態，依狀態決定輸出內容，以及下一個可能的狀態。  

預設一定有的意圖就是 Default Welcome Intent，也就是一啟動 google assistant 時的的狀態，我們在它的 Response 裡面加上回應："What is your favorite color?"，這樣程式一開就會把問題丟給使用者。  
這句話非常的重要，**設計 chatbot 最重要的就是把使用者限制在一個小框框裡面，讓使用者針對只有有限選項或是只能答 yes/no 的問題做回答**，否則使用者天馬行空，<請你跟我結婚>、<誰是世界上最美麗的女人>這種問題滿天飛，結果你的 chatbot 完全聽不懂，畢竟人人都以為人工智慧可以做到穿熱褲黑絲襪又會拌嘴的傲嬌助手，實際上還不是血汗工程師在後面拉線設定的人工智障，隨便一問就被看破手腳。  

![default](/images/assistant/dialogflow/04_default.png)   

## 新增 intent

另外我們要新增一個 Intent ，命名為 favorite color，注意這個命名在未來連接 webhook 時非常重要，命名跟大小寫都要注意。  
在 training phrase 的地方，試著打入一些使用者可能會說的話，最好是上一句問句的回話：  
* blue  
* my favorite color is red  
* orange is my favorite  
* ruby is the best

邊打的時候 dialogflow 就會自動的把顏色部分給標起來，接著往下拉到 Action and parameters ，系統應該會自動加上一個 color 的 parameter，我們設定 entity 為 @sys.color，value 為 $color。  

![training](/images/assistant/dialogflow/05_training.png)   
![response](/images/assistant/dialogflow/06_response.png)   

這裡就能看出 dialogflow 服務的功力了，在我們打上例句的時候 dialogflow 就透過事先分類好的 entity，分析出我們現在想要知道使用者回話的什麼內容（這裡是顏色），再幫我們把這個內容存到變數裡。  
最後在 response 的地方，我們使用剛剛萃取出來的內容：  
> OK. Your favorite color is $color

## 測試
這樣就完成我們的回話機器人了，當然我們要測試一下，在 Integration 選擇 integration setting，記得打開 Auto-preview changes 後再點 test，就可以在 google action 測試頁面中測試了：  
![test](/images/assistant/dialogflow/07_test.png)   

短短小文祝大家新年快樂，希望大家都有個機器人陪你過年(欸