---
title: "使用vim script 改進blogger 寫作流程"
date: 2016-10-22
categories:
- vim
tags:
- vim
- blogger
series: null
---

故事是這樣子的，今年不知道為什麼靈感大爆發，一直不斷的寫blog。  

用blogger 最麻煩的就是它的介面，不太能像 jekyll 之類的由文字檔轉成blog，要直接用它的編輯器介面寫文章，如果是一般的文章就很方便，插圖、連結都能一鍵完成，但要插入tag 就麻煩大了。  
像我的blog 常會有程式碼或一些執行結果要highlight，我通常會插入兩種不同的tag，一種是單純的highlight `<div class="hl"></div>`；
另一個是包住程式碼用的 `<pre class="prettyprint lang-xx">`，要在blogger 上面加上這兩個tag ，就必須切換到html 編輯模式，自己到適當的地方加上open tag，然後找到末尾加上close tag，這是一個很累人的過程。  
<!--more-->

特別像是上一篇rust helloworld 的文章，充滿許多程式碼跟執行結果，編輯起來要十幾分鐘，還要不斷的修稿，每每寫到這種文章就想要放棄blogger換到其他平台…
但想想還是不太想放棄blogger 平台，雖然有無痛轉移到其他平台wordpress，但其實blogger 上傳圖片等等還是滿好用的。  

那編輯耗時這點總不能這樣下去吧…最近死腦筋終於想到：可以利用vim script 改善這個流程。  
首先是HTML跳脫的部分，其實這個可以把文字貼去blogger 再從HTML 抓回來就行了，也可以用vim script 代勞，
例如這個[自動轉成 html 的指令](http://vim.wikia.com/wiki/HTML_entities)。  

於是我自幹一個 Make Blogger funciton，會用這個function對整份文件執行EscapeHTML 取代，並在每個行尾插入<br /> 換行tag：  
```vim
" Escape & < > HTML entities in range (default current line).
function! EscapeHTML(line1, line2)
  let search = @/
  let range = 'silent ' . a:line1 . ',' . a:line2
  execute range . 'sno/&/&amp;/eg'
  execute range . 'sno/</&lt;/eg'
  execute range . 'sno/>/&gt;/eg'
  nohl
  let @/ = search
endfunction

command! -range MakeHTML call EscapeHTML(<line1>, <line2>)

function! Blogger()
  let range = 'silent ' . 0 . ',' . line("$")
  call EscapeHTML(0, line("$"))
  execute range . 'sno/$/<br \/>/eg'
  endfunction

command! MakeBlogger call Blogger()
```

另外有兩個help funciton MakePre 跟MakeDiv，功用是可以用vim 執行range 指令，在前後加上tag，如果是Pre的話會把當中的`<br />` 給代換掉，利用vim 優秀的整行選取，方便加入各種tag。  
```vim
" Pre, add <pre class="prettyprint"> and </pre>
function! MakePre(line1, line2)
  call cursor(a:line2, 0)
  :normal o</pre><ESC>
  call cursor(a:line1, 0)
  :normal O<pre class="prettyprint">\r<ESC>
endfunction

command! -range Pre call MakePre(<line1>, <line2>)

" Div, add <div class="hl"> and </pre>
function! Div(line1, line2)
  call cursor(a:line2, 0)
  :normal o</div>
  call cursor(a:line1, 0)
  :normal O<div class="hl notranslate">
endfunction

command! -range MakeDiv call Div(<line1>, <line2>)
```
如此一來就能有效的加速blog 發文的流程了，使用時先把libreoffice 裡的文件貼到文字檔裡面，然後用vim script 編輯過，
就能整篇由blogger的文字介面中貼入，這篇文用這個方式發，不到十分鐘就發完了。  

話說在這個FB, LINE, HackMD 當道的年代，這樣一直寫blogger 感覺怪土裡土氣的，不知各位看倌怎麼想呢？ 
