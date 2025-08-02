---
title: "幫 hugo blog 加上多語言支援"
date: 2025-07-29
categories:
- LifeRecord
tags:
- blog
series: null
---

故事是這樣子的，最近讀了一些商業相關的書，發現在經營上應該更有策略一些，加上觀察到強者我同學 [ShingLyu 的 blog](https://shinglyu.com/)
在單月瀏覽人次上整整比小弟多了 8 dB 左右，顯見英文內容和中文內容的引流能力還是天差地遠。  
有了這樣的結論，提供英文內容似乎就是~~大草原~~不可避的了，那麼要怎麼把我的 blog 快速轉成英文內容呢？
<!--more-->

# Hugo 對應的設定

目前首要是先支援英文內容，中文預設，英文第二。
在 config.yaml 中加入以下內容：
```yaml
defaultContentLanguage: zh-tw
defaultContentLanguageInSubdir: false
languages:
  zh-tw:
    languageName: "繁體中文"
    weight: 10
    contentDir: content/zh-tw
  en:
    languageName: "English"
    weight: 20
    contentDir: content/en
```
使用的主題 PaperMod 自動處理好語言選單。  
因為我沒有在一開始就設定多種語言，現有文章的 URL 並沒有 language code。如果設定 `defaultContentLanguageInSubdir: true`，那麼所有文章的 URL
都會多出 zh-tw 或 en 等 language code，算一個歷史遺留的問題，重設所有的 URL 對 SEO 很不好，因此我選擇設定為 false，這樣繁體中文的 URL 就不會變化。  
壞處是哪天我想把英文變預設的時候，可能還是會有一次 SEO 重建期。


# 免責聲明

下面提到我選用的翻譯軟體是 OpenAI API，因為是自動翻譯決定還是在文章開頭加上一段免責聲明。  

首先在文章內部加上
```go-html-template
{{- if (.Param "AITranslated") -}}
  <blockquote class="error">
    {{ T "disclaimer" }}
  </blockquote>
{{- end }}
```

`T "disclaimer"` 的內容要放在 i18n 資料夾下，我分別創了 `i18n/en.yaml` 和 `i18n/zh-tw.yaml`，內容就放上 
"disclaimer" 為 key 的對應內容：
```yaml
# en.yaml
disclaimer: This content is translated with AI. 
Please refer to the original Traditional Chinese version (zh-TW) for accuracy.
# zh-tw.yaml
disclaimer: 本內容由 AI 翻譯，如有疑問請以繁體中文原文為準。
```

只要文章有設定 AITranslated 就會自動顯示這段免責聲明。

把 content 的內容全部移到 zh-tw 下，接著就準備來翻譯啦。

# 請 AI 幫我翻譯

因為主要想翻的目標是晶片製作相關的 blog，因此先抽一些例句出來翻翻看，例如下面這句：

> 會想寫這篇文章，是因為在這次的下線過程中，我發現網路上相關記錄的文章相當少

包括 Google Translate 跟 DeepL 都把*下線* 翻成 *offline*，當然我是不排除我給的 Context 太少造成的。  
AWS Translate 則沒有公開測試介面。  
但經過適當的提詞，ChatGPT 跟 Claude 都能正確翻成 Tapeout，打爆這些專職做翻譯的，笑死。

既然如此，最後決定下訂 OpenAI API key，結果第一秒就犯了錯，我沒注意到 ChatGPT 跟 OpenAI API 兩個是不一樣的東西，不小心手滑就訂在 
ChatGPT Plus 上，立馬噴了 600 元出去QQ。  
要用的 penAI Key 的購買與設定畫面是[這裡](https://platform.openai.com/chat)，真的是 87 分不能再高了。

聽從朋友的建議，使用的 API 為 [Structured Output](https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses)
模式 ，請 ChatGPT 寫了一個 Python script translate.py。  
至於 function_schema 是在寫什麼…因為是 ChatGPT 寫的我其實也沒有特別肯定…；這就 AI 寫 code 的雙面刃，我幾乎沒查 API 怎麼用，也沒有自己動手，但 AI 就寫得特別快而且還會對。  
SystemPrompt 是嘗試幾次之後，把所有 markdown 有用到的東西都寫進去，這樣效果稍微好一些。  
UserPrompt 就簡單了，請它直接把輸入翻譯成輸出。

```python
def translate(text, source_lang, target_lang="English"):
  function_schema = {
    "name": "translate_text",
    "description": "Translate the input text to the target language.",
    "parameters": {
      "type": "object",
      "properties": {
        "translated_text": {
        "type": "string",
        "description": "The translated text in the target language."
      }
    },
    "required": ["translated_text"]
  }
}

system_prompt = f"""
  You are a precise and faithful translator, working in software and ICdesign territory.
  Translate articles from {source_lang} to {target_lang}.
  Note that the input is in markdown format, so keep following points in mind:
  1. Don't translate the code block, latex formula $$.
  2. Keep the notation like <!--more--> and the image path like 
     ![image](path/to/image.png) unchanged in the same place.
  3. Translate the table content and keep the table shape.
  4. Try your best to keep the format text like strikethrough ~~~~, 
     bold **** and italic ** to the corresponding text.
"""
user_prompt = f"Translate the following text from {source_lang} to {target_lang}:\n{text}"

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
  ],
  functions=[function_schema],
  function_call={"name": "translate_text"}
)

arguments = response.choices[0].message.function_call.arguments
result = json.loads(arguments)
```

嘗試的效果還不錯，沒特別設定 max_tokens 那些，機翻可以直接翻完。

翻譯了 IC Design 相關的八篇文章，共 26,000 字（有些文章因為出錯翻了多次，測試時也有拿測試文多跑幾次），
輸入 44,392 個 tokens，輸出 71,943 個 tokens，花費 0.38 USD 約合 11 塊多吧。  

照這個價格推算，把我所有 blog 總計約 1,000,000 字，全翻成英文大概要價 500 元左右，真的是感受到時代的進化，沒花多少時間寫 code，只是套個 AI 
模型，以前可能要花一堆時間翻譯的文章一分鐘內就搞定了，雖然還沒仔細看過翻譯品質，但就我使用 ChatGPT 的經驗應該是不會太差啦。  
當然，我是不排斥如果有人看到我的文章，覺得想推廣提交他們的翻譯然後把 AITranslated tag 移除掉，但那機會大概很低吧。

# 結語

這個 blog 前身自 2020 年從 blogger 遷移到 hugo，已經是五年前的事了呢，而最後一次重大維護則是 2021 年[改變版型](https://yodalee.me/2021/03/2021_hugo_decoration/)，之後都只有微幅調整而已。

前些日子因為 [Gandi 的網域訂閱](https://www.gandi.net/zh-Hant)快到期了，
看看價格也照著別人寫的[教學](https://www.sakamoto.blog/gandi-domain-transfer-cloudflare/) 
把網域供應商移到 [Cloudflare](https://www.cloudflare.com/zh-tw/) 上。  

這次心血來潮加上了多語言的支援，同時好好維護了一下，希望小弟累積十年多的 blog 能像強者我同學一樣讓更多非中文圈的人看到，千客萬來。  
如果你想許願看到這個 blog 多出什麼語言的支援，也歡迎留言告訴我，我完全不介意多花個 500 塊請 OpenAI 幫我再多翻一個語言。
