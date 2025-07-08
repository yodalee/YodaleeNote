---
title: "幫 Google Assistant 加上更多語言"
date: 2020-03-14
categories:
- GoogleAssistant
tags:
- GoogleAssistant
series:
- GoogleAssistant
---

[上一篇]({{< relref "3guessnumber.md">}}) 我們成功做出一個會跟我們猜數字的 Assistant，不過因為方便我開發的時候都是用英文在開發，自己玩玩當然 OK，但對非英文使用者就不行了，因此我們來試著加上中文的回應。  
<!--more-->

## assistant 設定
目前 google assistant 支援 20 種語言[（註）]({{< relref "#Note">}})，在 assistant 的開發頁面選擇 modify language setting 可以打開想要的語言，我這裡先開英文和繁體中文，兩個語言都要設定 assistant 的呼叫詞，中文的我們就叫它「猜數字程式」。  
![languagesetting](/images/assistant/multilanguage/languagesetting.png)

## dialogflow 設定
在連接的 dialogflow 的部分，點選 project 旁邊的小齒輪，language 分頁裡面也加上繁體中文的選項，在左側欄的 project 名稱下面就可以看到有兩個不同的語言。  

![dialogsetting](/images/assistant/multilanguage/dialogsetting.png)

加完語言之後，最麻煩的就是把整個設定複製一份了，所有的 intent 設定在新的語言都要再設定一遍，或者你在不同的語言想要採取不同的 flow 也可以，因為猜數字很簡單，我英文跟中文就用相同設定，training phrase 的部分，直接打上中文就可以了。  

![training](/images/assistant/multilanguage/training.png)

## i18n 設定
設定完 dialogflow 之後，下一步要設定我們的 webhook 讓它也能處理多國語言，我選用的套件是 python 的 [python-i18n](https://github.com/danhper/python-i18n)，可以用 yml 或 json 格式儲存想要翻譯的文字，這樣我們程式碼幾乎結構不用大修，只要在回應的地方呼叫 i18n 幫我們吐出翻譯過的文字就好。  
修改後的目錄長成這樣：  
```txt
main.py
locales
    guess.en.json
    guess.zh-tw.json
```

把文件檔都放在 locales 下面，檔案名稱為：{title}.{lang}.json，英文的 guess.en.json 內容如下：  
```json
{
  "en": {
    "test" : "test",
    "welcome" : "I have a number between %{low} and %{high}. Can you guess it?",
    "guess_out": "Are you sure? I said a number between %{low} and %{high}",
    "guess_unmatch" : "A number between %{low} and %{high}. Keep guess."
  }
}
```

對應的中文則是 guess.zh-tw.json：  
```json
{
  "zh-tw": {
    "test" : "測試字串",
    "welcome" : "我有一個介於 %{low} 到 %{high} 的數字，你能猜到嗎？",
    "guess_out": "你確定嗎？我說介於 %{low} 跟 %{high} 之間",
    "guess_unmatch" : "介於 %{low} 跟 %{high} 之間，再接再勵"
  }
}
```

開頭是 language code，這邊這個名字要跟檔案的 {lang} 是相同的，雖然說有點多此一舉的感覺，內容則是 key-value 的形式儲存文字內容。  

## 程式修改
主程式的部分也要對應的修改：  
```python
import i18n

i18n.load_path.append('locales')
i18n.set('file_format', 'json')
i18n.set('fallback', 'en')

language_code = data.get("queryResult").get("languageCode")
print(language_code)
i18n.set('locale', language_code)
text = i18n.t('guess.welcome', low = str(low), high = str(high))
```

因為我們把檔案都放在 locales 下面，在搜尋路徑上加上 locales；檔案格式為 json；預設的語言是英文。  
在 assistant 的 request 裡面，語言設定會放在 queryResult -> languageCode 下，用 i18n.set 設定 locale；這時呼叫 i18n.t(title.key) 就會找出在 {title}.{lang}.json 檔案裡，{lang} 下面 key 對應的字串了。  
i18n.t 的參數，則可以代入預先設定好的 placeholder 代換到字串裡。  

測試一下，在測試頁面可以選擇測試的語言，選擇繁體中文來試試：  
![test](/images/assistant/multilanguage/test.png)
現在我們的人工智障會講中文了。  

## 附註 {#Note}
在設定頁面全部可選的語言（依英文首字排序）有：繁中、粵、丹、荷、法、德、印度、印尼、義、日、韓、挪、波蘭、葡、俄、西、瑞典、泰、土；其中西、法、英三大家有口音選項。  
雖然在寫這篇的時候我有查到去年 12 月的新聞，說 google assistant [會支援 44 種語言](https://venturebeat.com/2019/12/12/google-assistant-can-now-interpret-44-languages-on-smartphones/)，
但截至我寫這個機器人的時候，還沒有這麼多的語言可以設定，可能是新聞跑得比開發工具快吧。  
另外 google assistant 的[說明文件](https://developers.google.com/assistant/sdk/reference/rpc/languages)上，則是沒有這麼多種語言，可能開發工具又跑得比文件快一點。  
結論：宣傳 > 開發工具 > 開發文件(欸