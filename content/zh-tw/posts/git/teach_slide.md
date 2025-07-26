---
title: "Git 教學影片系列"
date: 2017-12-31
categories:
- git
tags:
- git
- tutorial
series: null
---

故事是這樣子的，自己大概三四年前開始使用git，一路用到現在，對 git 相關的功能算是相當熟悉，有時也會負責教其他人使用 git，自己的 blog 上其實也留了不少 [git 相關的文章]({{< ref "/categories/git" >}})：  
大約兩個禮拜前突發奇想，反正都要教，乾脆就錄個影片，以後只要貼影片給別人看，不只教認識的，還能教虛擬世界中「沉默的多數」（誤），想著想著稍微規劃了一下，好像還真的有點模樣，於是就開始了我變身網（ㄈㄟˊ）紅（ㄓㄞˊ）的第一步。  
<!--more-->

最後確定的版本有以下幾集的影片，一部是相關的功能，順便還會介紹一些社群習慣或是我自己的習慣，講得滿雜的，也有些出錯的地方：  

1. 安裝與設定  
2. Add, commit：50/72 rule, gitignore, commit hash, DAG  
3. 如何指定一個 commit：hash, HEAD, ^ ~, reference, show, log, diff, diff --staged  
4. patch add and amend  
5. branch, checkout, merge：解衝突  
6. Rebase：rebase -i，解衝突  
7. 遠端開發，使用 github：用 gitgraph.js 的開發經驗，來說明如何使用 github  
8. stash  
9. format-patch, apply, am, cherry-pick 各種搬移工作的方法  
10. bisect, blame  
11. Ending：講一下一些沒提的東西  

自己做起來就發現，想當 youtuber 要費的功夫真的超級大，除了初期收集資料跟準備材料，投影片跟 demo 用的 project，還要確認要講的內容沒有錯誤；
真正錄的時候可能還要多錄幾遍，確定哪裡說不好要改進，如果不小心說錯了，要重頭再錄一次，事後還要上傳 Youtube 修改影片資訊等等。  

像後來，就發現我在安裝的那章其實有個錯誤，Windows系統不能只安裝 Tortoise git，還要安裝 git 才行…不過暫時還沒想到怎麼去修正它(yay；如果像那些網紅一樣還要加後製，那成本真的超級大，我猜不組個小團隊其實是很難撐起來的  

總之這些是最後的成品，收到一個 youtube 播放清單中：  
[youtube 播放清單](https://www.youtube.com/playlist?list=PLlyOkSAh6TwcvJQ1UtvkSwhZWCaM_S07d)  

或者下面是嵌入式的第一部影片：  
{{< rawhtml >}}
<iframe width="560" height="315" src="https://www.youtube.com/embed/videoseries?list=PLlyOkSAh6TwcvJQ1UtvkSwhZWCaM_S07d" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
{{< /rawhtml >}}

自己回想起來其實花了非常多時間在錄這些教學影片，還去買了新的麥克風，錄製跟剪輯影片分別使用 obs 跟 ffmpeg 剪輯指令，因為加特效太麻煩，所以就沒加特效 =w=，希望這些影片能對大家有所幫助。  

雖然本人比較喜歡低調路線，不過想想，既然都花了這麼多時間，這些影片要是沒有人看就太可惜了，因此來學一下農場的做法，希望大家覺得影片有你幫助的話，就幫小弟分享一下，無論是這篇文章或是上面 youtube 播放清單的連結都可以。  

ps. 也能透過blog 旁邊的連結，用 Paypal 給點賞，鼓勵一下小弟，不過這不強求啦，畢竟 Paypal 手續費抽滿貴的。