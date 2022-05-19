---
title: "hugo 網頁內容調整"
date: 2021-03-02
categories:
- simple setup
- LifeRecord
tags:
- blog
- hugo
- google cloud platform
series: null
---

故事是這樣子的，從我上一篇[blogger 搬到 hugo 全記錄]({{< relref "2020_blogger_to_hugo.md" >}})
開始到現在，已經過了半年有了，這段時間寫了大概 7-8 篇的廢文之外，大部分狀況都是調調格式什麼的，
直到 228 紀念日我又花了點時間大調了一次格式，這篇文就用來記錄一下這半年做了什麼。
<!--more-->

## 版型 PaperMod：

最大的一個變化，當屬我又換了一次版型，從本來的 [silhouette-hugo](https://themes.gohugo.io/silhouette-hugo/) 換成
[PaperMod](https://themes.gohugo.io/hugo-papermod/)

PaperMod 是我在為 hugo 加上搜尋功能時搜到的，決定更換大概有下列幾個理由
1. sihouette 的版型真的不好用，自己後續做了超大量的修改，還不如改套一個更適合的版型。
2. sihouette 的 categories, tags 用的基底 list.html 也寫得不好，下面是一張截圖，可以看到每個 sihouette 裡面每個 categories/tags 竟然還是佔一個文章的高度，要找到 categories 看分頁每個看過去，對比 [PaperMod](https://yodalee.me/categories/) 則是把所有 categories 以類似文字雲的方式集中在一頁裡顯示。
![sihouette](/images/blog/sihouette.png)
3. PaperMod 內建我很喜歡的 Archive 跟 Search 的功能，下面敘述這塊。

我後來多看了幾次自己的 blog，還有看了在 Yahoo 台灣大殺四方前端加速 10dB 的 Jason 大神的[用 eleventy 架的網誌](https://jason-memo.dev/)，
更加體認到其實 blog 的 categories 跟 tags 通常沒有用，只是自己加爽的，一般才不會有人去點 categories 或 tag 跳轉到其他的文章。  
同樣 archive 通常也只是加爽的，只有一點點讀者會去點 archive 然後掃過整個網誌找有興趣的文章來讀。  
series 可能比上面幾個有點用，但也只限於同系列文，不管喜不喜歡，**blog 閱讀量的最大宗來源就是 google**，讓你的文章容易搜到才是真理；
而要方便讀者在站內找到文章，則需要站內搜尋的功能。

總之，大概花了 227 一天的時間調整版型，接著馬上就上線啦。

## Python script 檢查 code block：

hugo 的 code block (```) 會被轉成 html 的 pre tag，而這個 tag 裡面的底線 _ 是不需要跳脫的，
因為我先前是用 [markdownify](https://pypi.org/project/markdownify/) 把文字直接 markdown 化，
所以就連 code block 也會有跳脫，於是就寫了個小 script 來處理所有的文章。
```python
class CodeChecker(Checker):
  inCode = False

  def __init__(self):
    self.inCode = False
  def process(self, line: str) -> str:
    if line.startswith("```"):
      self.inCode = not self.inCode
    if self.inCode:
      line = line.replace("\\_", "_").rstrip() + os.linesep
    return line

def process(fpath):
  checker = CodeChecker()

  newcontents = []
  with open(fpath, "r") as fin:
    contents = fin.readlines()

  for line in contents:
    newcontents.append(checker.process(line))

  with open(fpath, "w") as fout:
    fout.writelines(newcontents)

def main():
  fs = walk()
  for f in fs:
    process(f)
```

## 自動生成系列文目錄與連結：
小弟喜歡系列文，這裡有兩個自幹出來的 code ，可以在有 series 分類的文章下面，自動產生目錄跟上/下篇文的連結：

* layouts/partials/series-toc.html
```go html template
{{ if .Params.series }}
  <div class="toc">
  {{ $title := .Params.Title }}
  {{ $same_series := where (where $.Site.Pages "Params.series" "!=" nil) 
                            "Params.series" "intersect" .Params.series }}
  <ol class="toc-content">
  {{ range $i, $e := $same_series.Reverse }}
    <li class="toc-li">
    {{ if eq $title $e.Params.title }}
      {{ $e.Params.title }}
    {{ else }}
      <a href="{{$e.Permalink}}">{{ $e.Params.title }}</a>
    {{ end }}
    </li>
  {{ end }}
  </ol>
  </div>
{{ end }}
```

* layouts/partials/series-link.html
```go html template
<div class="container mb-3">
  <div class="row">
  {{ if .Params.series }}
    {{ $title := .Params.Title }}
    {{ $same_series := where (where $.Site.Pages "Params.series" "!=" nil)
                              "Params.series" "intersect" .Params.series }}
    {{ range $i, $e := $same_series }}
      {{ if eq $title $e.Params.title }}
        {{ $prev := index $same_series (add $i 1) }}
        {{ if $prev }}
          <div class="col-md-6">
          <i class="fas fa-arrow-left" title="Left" aria-hidden="true"></i>&nbsp;
          <a href="{{$prev.Permalink}}">{{ $prev.Params.title }}</a>
          </div>
        {{ end }}

        {{ $next := index $same_series (sub $i 1) }}
        {{ if $next }}
          <div class="col-md-6">
          <a href="{{$next.Permalink}}">{{ $next.Params.title }}</a>
          <i class="fas fa-arrow-right" title="Right" aria-hidden="true"></i>&nbsp;
          </div>
        {{ end }}
      {{ end }}
    {{ end }}
  {{ end }}
  </div>
</div>
```

## 整合 Google analytics

這部分在 hugo 內已經有內建的 [internal template](https://gohugo.io/templates/internal/#google-analytics) 了，只要在設定檔中加上 google analytics 的編號，並使用內建的 partial code 即可，一般的 theme 應該都會幫你加好 partial code了。
```toml
# config.yaml
googleAnalytics = "UA-XXXXXXXX-X"
```

## 整合 Google Adsense
為了在網頁裡插入廣告，需要做下面三件事：
1. 建立 adsense partial code：
```javascript
// layouts/partials/adsense.html：
<script data-ad-client="wwwww"  
 async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
```
2. 把這段 partial code 插入 `<head></head>` 之間：
```go html template
{{ partial "adsense.html" }}
```
3. 從 adsense 取得 ads.txt 放到 static/ads.txt：
詳見[說明](https://support.google.com/adsense/answer/7532444?hl=zh-Hant)，讓 google 載得到 ads.txt。

這樣就完成廣告刊登了。
我覺得比較奇怪的一點是，在這個 blog 刊登的廣告位置都是不可選的，不像之前在 blogger 它會固定幾個位置顯示廣告；另外它預設的刊登頻率實在是高得嚇人，我試過幾乎每篇文章中間都會放一則廣告，預設就這樣了要是我把廣告頻率設到最大，會不會文章全部都被廣告覆蓋呀XD？

