---
title: "blogger 搬到 hugo 全記錄"
date: 2020-09-19
categories:
- Setup Guide
- LifeRecord
tags:
- blog
- hugo
- google cloud platform
series: null
latex: true
---

工程師如何搬家，~~給工程師一個死線，時間到了家就搬好了~~。

簡單來說，搬家基本上來說可以分成三步驟：
1. 找到新家
2. 把舊家的東西搬出來
3. 把東西放到~~冰箱~~新家
<!--more-->

## 找新家

### 主機：Firebase
我聽從強者我學長 David 大大的建議，放在同樣是 Google 旗下的 [firebase](https://console.firebase.google.com/)，
結果變成從 google blogger 跳到 google firebase，逃得了和尚逃不了廟。

在 firebase 申請的步驟：

1. 建立新專案
2. 選擇連接 google analytics
3. 建立新的 google analytics 帳號

結束，等等就可以把 hugo 的內容傳到這裡。

### DNS：Gandi
網域透過強者我同學 qcl 大神推薦我申請了 [gandi 的服務](https://www.gandi.net/zh-Hant)，一年的費用是 545 NTD，
三年以上到十年會有 85.3 折優惠， 反正都是 85 折就先買個三年，註冊了 yodalee.me 這個簡單好記的網域名稱。

Gandi 的申請畫面應該不用多加介紹，該填的資料填一填，魔法小卡準備好刷下去就能擁有自己的網域了。

### 連接主機和 DNS

這應該是唯一比較麻煩的步驟，申請完 firebase ，在 hosting 的地方可以看到自己的主機名稱，現在我們要讓 yodalee.me 的請求都轉到這裡處理。
1. 在 firebase點下<新增自訂網域>：
2. 輸入在 gandi 申請的網域名稱，我的狀況是 yodalee.me

![firebase](/images/blog/firebase.png)

3. firebase 生成一大串字串
4. 在 Gandi 的頁面將這個字串加入 DNS Records 的 txt 項目

![gandi](/images/blog/gandi.png)
最下面那欄 txt 就是我的驗證字串，firebase 會要求 yodalee.me 的 DNS 回應這串文字，驗證你真的是這個網域的所有人。

Firebase 驗證過就會把主機的 IP 給你（不知道為什麼還是 IPv4），這時就把 Gandi 內的 A 項目跟 AAAA 項目全部刪掉，
改成 firebase 給的 IP，如果是 IP4 就建 A，IP6 就建 AAAA。

完成，現在連接 yodalee.me 就會由 firebase 主機接手請求了。

### 連接 www

上一步連結完網域之後，在網址打入網址就可以存取網頁，例如我的網域是 [yodalee.me](http://yodalee.me)。  
不過機靈一點的讀者，可能會注意到，為什麼 `www.yodalee.me` 這個子網域不會連到上面的網頁？  

這部分要另外做兩個設定，firebase 跟 gandi 都要：  
Firebase 跟上面一樣，新增一個自訂網域，這次打入 www.{your.domain} 並勾選下面的 **將「www.{your.domain」重新導向至現有的網站**。  
這樣有一個針對 www 子網域的請求，firebase 才知道要怎麼回應。  
Gandi 則是在 DNS 另外新建一個 cname 的項目，名稱為 www，更新時間可以久一點沒差 43200，值則是 `yodalee.me.` **注意後面的 . 一定要打**。  
這是讓 Gandi 知道，有 www 的子網域要求就回給他跟網域一樣的 IP 即可。  

設定完這些訪問 www.{your.domain} 應該就能看到和主網域一樣的網頁了。  

### 架站工具

如上一篇所述，架站工具選定為靜態網頁生成，
[ruby/jekyll](https://jekyllrb.com/)、
[go/hugo](https://gohugo.io/)、
[python/pelican](https://blog.getpelican.com/)、
[rust/zola](https://www.getzola.org/)

應該都不會差太多，最後選定是 go/hugo。

下面羅列幾個我覺得重要的步驟：

#### 前進到下一步之前，最好先選定好工具，並且先用一些廢文試一下想要的主題 (theme)，看看合不合自己的需求。

我一路試過大概 3-4 個主題跟設定，從寫書用的 [book](https://themes.gohugo.io/hugo-book/) 到複雜異常足夠做企業網站的主題，
最後選定的 theme 是 [slick](https://www.getzola.org/)，屬極簡風的設計，完全沒有多餘雜訊的主題。  

之所以要先試一下，是因為主題通常會有一些獨特的設定要寫在每篇的文章的標頭，以 slick 為例是 tags, categories, series 等，
決定好之後依照這個設定改寫下面搬舊家的 script，會讓搬家輕鬆一些些。

#### 主題也不用決定太久

記住主題只是花妝，blog 的文章有沒有料比較重要，主題也不是絕對，未來都還能修改。

#### config 的 permalinks 一定要設
[permalinks](https://gohugo.io/content-management/urls/#permalinks) 設定是 hugo 用來產生文章連結的， 我的設定是 `/:year/:month/:filename/`。  
故事是這樣子的，未設定的話 hugo 產生網頁的網址可能會受到你放的位置影響，這樣你一但公佈網站後就不能再任意改變檔案位置了，
否則網址不斷跑掉會影響到搜尋引擎的評分，而寫了一大串同類型的文章之後，很自然的就是歸到一個資料夾下，這樣就會改變位置了。
有設定 permalinks ，只要不改變檔案名稱就沒什麼關係了，為了網站的瀏覽量著想，這步請務必要做。

#### Latex 的解決方案
我融合了兩個不同的步驟，分別是這篇 [katex 文章的設定方式](https://eankeen.github.io/blog/posts/render-latex-with-katex-in-hugo-blog/)，
但 render 用的是 [MathJex 的設定](https://geoffruddock.com/math-typesetting-in-hugo/)，主要是我 katex 設定了還是跑不出來。
需要 latex 的文章只要在標頭的設定加上 `latex: true` 就可以使用了，幾個 render 測試：

* [關於費式數列的那些事]({{< relref "2019_fibonacci.md">}})

$$ fib(n) = \frac{1}{\sqrt{5}}(\frac{1+\sqrt{5}}{2})^n-\frac{1}{\sqrt{5}}(\frac{1-\sqrt{5}}{2})^n $$  

* [放大器的級間穩定]({{< relref "2012_stage_stability.md">}})

$$r = \frac{ad-bc}{a^2-c^2} = |\frac{S_{12}S_{21}}{1-|S22|^2}|$$  


## 把舊家的東西搬出來

如何把舊家的東西全搬出來？

### 文字內容
很不幸的，如果你照著 [google 備份指南](https://support.google.com/blogger/answer/41387?hl=zh-Hant)做下載網誌備份，
只會得到一大團 xml 嘔吐物，當然可以用 python lxml 寫一個工具從嘔吐物裡面萃取出文章內容，但實在是有點…嘔嘔嘔的方法。

後來決定用 [google blogger API](https://developers.google.com/blogger) 把文章內容爬出來。
使用 API 要先到 [google developer console](https://console.developers.google.com/) 建立 Oauth2 憑證

* 在<API 和服務>裡啟用 blogger API V3
* 在<憑證>頁面選擇<建立憑證>
* 選擇 Oauth 用戶端，電腦版應用程式

建立完成的 Oauth2 client ID 可以下載 json 檔，內含等等要用到的 client_id 和 client_secret。

程式碼直接修改自 [google 提供的範例](https://github.com/googleapis/google-api-python-client/tree/master/samples/blogger)，
呼叫 API 部分修改如下，oauth2client 會自動去讀取下載的 client.json，並開啟 oauth2 取得權限：

```python
from datetime import datetime
from markdownify import markdownify as md

import sys

from oauth2client import client
from googleapiclient import sample_tools

def main(argv):
  # Authenticate and construct service.
  service, flags = sample_tools.init(
    argv, 'blogger', 'v3', __doc__, __file__,
    scope='https://www.googleapis.com/auth/blogger')

  blogs = service.blogs()
  posts = service.posts()

  thisusersblogs = blogs.listByUser(userId='self').execute()

  # List the posts for each blog this user has
  for blog in thisusersblogs['items']:

  request = posts.list(blogId=blog['id'])

  while request != None:
    posts_doc = request.execute()
    if 'items' in posts_doc and not (posts_doc['items'] is None):
      for post in posts_doc['items']:
        write_post(post)
    request = posts.list_next(request, posts_doc)
```

拿到 post 之後就能把裡面的東西寫出來，post 內含的資料結構可以參考 [API reference](https://developers.google.com/blogger/docs/3.0/reference/posts#resource)：
```python
def write_post(post):
  title = post['title'].replace('/', '')

  date = post['published']
  date = datetime.fromisoformat(date)
  date = date.strftime("%Y-%m-%d")

  content = md(post['content'])
  tags = post['labels']

  fname = "posts/{}-{}.md".format(date, title)
  with open(fname, 'w') as f:
    f.write("---\n")
    f.write("title: \"{}\"\n".format(title))
    f.write("date: {}\n".format(date))
    f.write("tags:\n")
    for tag in tags:
      f.write("- {}\n".format(tag))
    f.write("series: null\n")
    f.write("---\n\n")
    f.write(content)
```

基本上是個一次性的 code ，不用太認真，就是把每篇文都載下來，用 markdownify 將 content 的 html 轉成 markdown，多少可以減輕一些未來編輯的負擔。  
如果平常就有玩 google API，google console 裡有 project 可以隨時使用，用這招應該比處理 xml 嘔吐物還要快。

### 圖片內容
所有在 blogger 上面的圖片可以在 [google album 的 archive](https://get.google.com/albumarchive/) 裡面下載，
反過來說你誤上傳的圖片也都要到這裡才能刪掉，而這個 archive 用正常管道似乎很難找到…
總共有 185 張圖 100 多 MB，小 case。

## 把東西放到冰箱新家

後續就是整理文章了，我全部 246 篇文章總共有 1.7 MB，大概六十多萬字。   
有些很舊過時的文章，像是 "M5641 ubuntu無法進入的解法" 這種，
或是當初寫的時候就只是記錄一些開發失敗的過程，事後看根本沒價值的文，都直接砍了不重發，大概砍了 25 篇廢文，損耗率大概 10% 上下。  
慢慢整理到新網站上，有些文章在 blogger 上面看起來會太長的，在 hugo 上面也不用客氣，整理的時候順便融合成一篇。

下面整理一些好用的指令：

* `sed -i -e 's/^[ \t]*//'`   
把 bloggger API 抓下來開頭的空白都取代掉

* `sed -i '3 a categories:\n- git' *.md`  
同一類的文章都抓出來之後，用 sed 全部插入 categories。

* `find . -type f -exec sed -i 's/“/"/g' {} \;`  
應該是當初我用 libreoffice 寫文的關係，滿多文的單引號跟雙引號被改成這種四不像的全形符號 `“”‘’`，用 sed 輕鬆解決

另外，因為我用了 markdownify 的關係，所有 \_ 都被自動修改成 \\\_ 了，但在程式區塊 ``` 裡面的 _ 是不用跳脫的，
這部分我是寫了個 python script 來處理這件事，正好複習一下 python XD。
```python
def process(self, line: str) -> str:
  if line.startswith("```"):
    self.inCode = not self.inCode

  if self.inCode:
    line = line.replace("\\_", "_").rstrip() + os.linesep
  return line
```

文章內容的不同註定沒辦法用自動工具自動將 blogger 的文章轉換到 SSG 上，用了 markdownify 的確可以先做完一些工作，但也只有一些。  
比起 blogger 編輯器，無論要用什麼格式很麻煩也不好看，這讓我養成幾乎不用諸如標題、表格等特殊的格式，頂多用編號或是條列。  
在 markdown 裡面就不用顧慮這麼多，小標、表格、code block 等想加就加，自由很多，就是要花點時間調整。  

我自己是預訂九月開始的兩個星期，不做其他的就是瘋狂搬文，先對舊文做些大致的分類，再從整理好的系列文開始一團一團搬，
兩個星期大約搬了 200 篇文章，該搬的都差不多了。
只能說搬家真得好累啊，不論是實體的或是虛擬的…

## 全新的工作流程

在使用軟體與服務上面則大幅改變，也幫助我重新梳理我的數位工作型態，以往習慣寫好後用 Blogger 透過 HTML 完整編輯的方式，有了全新的套路。  
1. 在 google doc 上面完成大致寫作，圖片直接收集到本地的資料夾內。
2. 內容複製到 vscode，在 vscode 內部完成插入連結、圖片、程式碼上色，全新的程式碼上色只需要加上 ``` 真的很爽，rust 的 lifetime 也能正常顯示。
3. 透過 hugo 轉譯為靜態網頁，上傳 firebase。
```bash
hugo & firebase deploy
```

## 結語

如上例所述，使用 hugo 也更容易用 shell 工具進行管理，如果是在 blogger 下我根本無心把文章一篇一篇打開來修正錯字，
用了 SSG 之後就做得到了。  
用 SSG 完成的比較像一個個人網站，更有一種作品集的感覺，本來分成 10 篇文章的輝光管時鐘，現在可以獨立到一個作品資料夾下，
零散的文章才會分到未分類的 posts 下面，比起 blogger 更有組織；文章內容全部用 git 備份，達到跟 blogger 一樣雲端備份的效果。

我自己的體驗是比 blogger 還要好，發佈文章也更加迅速，就是還要再花點心思調整版型就是，目前預計還要：
* 加上討論留言的 disqus
* 放 adsense (欸
* 連接 google analytics
