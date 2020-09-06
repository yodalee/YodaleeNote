---
title: "我的vim設定"
date: 2012-09-22
categories:
- vim
tags:
- linux
- vim
series: null
---

最近梗比較少，寫不出什麼有用的東西  
整理了一下自己的vim設定，就把自己的設定跟plugin分享一下好了  
<!--more-->

## plugin  
裝的plugin主要有幾個：  
* [autoComlPop](http://www.vim.org/scripts/script.php?script_id=1879): 輔助omnicomplete的文件單字補齊  
* [LargeFile](http://www.vim.org/scripts/script.php?script_id=1506): 開大檔用，其實比較少用到  
* [surround](http://www.vim.org/scripts/script.php?script_id=1697): 快速修改相對應的標籤  
* [NERDtree](http://www.vim.org/scripts/script.php?script_id=1658): 快速瀏覽目錄  
* [snipMate](http://www.vim.org/scripts/script.php?script_id=2540): 自訂關鍵字補齊功能，缺點是會變笨  
* [taglist](http://www.vim.org/scripts/script.php?script_id=273): 程式碼概略瀏覽  

附帶一提，這些plugins全部都裝在~/.vim裡面  
我發現可以用dropbox，建一個setting的資料夾  
把.vim sync到dropbox上，這樣以後重裝電腦  
只要把這個資料夾再複製回來，這些plugin就都裝好了  

## vimrc  
我的vimrc如下：  
```vimrc
"=================================================="
" encoding setting
"=================================================="
set encoding=utf8
set fileencodings=utf8,gbk,cp936,gb18030,big5

"=================================================="
" filetype setting
"=================================================="
syntax on
filetype on
filetype plugin on
filetype plugin indent on

"=================================================="
" editor layout
"=================================================="
set nocompatible
set shiftwidth=4
set tabstop=4
set softtabstop=4
set background=dark
set cindent
set ruler
set hls
set ic
set nu
set ai

"=================================================="
" plugin mapping and setting
"=================================================="
" taglist mapping
nnoremap <F12> :TlistToggle<CR>
" NERDtree mapping
nmap <F6> :NERDTreeToggle<CR>
" quickfix mapping
map <F7> :make<CR>
map <F8> <ESC>:call QFSwitch()<CR>
map <S-F8> <ESC>:colder<CR>
map <C-F8> <ESC>:cnewer<CR>
map <C-n> <ESC>:cnext<CR>
map <C-p> <ESC>:cprev<CR>
function! QFSwitch()
redir => ls_output
execute ':silent! ls'
redir END
let exists = match(ls_output, "[Quickfix List")
if exists == -1
execute ':copen'
else
execute ':cclose'
endif
endfunction
" code complete popout color setting
highlight Pmenu ctermfg=0 ctermbg=2
highlight PmenuSel ctermfg=0 ctermbg=7
highlight PmenuSbar ctermfg=7 ctermbg=0
highlight PmenuThumb ctermfg=0 ctermbg=7

"=================================================="
" omnicomplete omnifunc setting
"=================================================="
autocmd FileType ruby,eruby set omnifunc=rubycomplete#Complete
autocmd FileType python set omnifunc=pythoncomplete#Complete
autocmd FileType javascript set omnifunc=javascriptcomplete#CompleteJS
autocmd FileType html set omnifunc=htmlcomplete#CompleteTags
autocmd FileType css set omnifunc=csscomplete#CompleteCSS
autocmd FileType xml set omnifunc=xmlcomplete#CompleteTags
autocmd FileType java set omnifunc=javacomplete#Complete
if has("autocmd") && exists("+omnifunc")
autocmd Filetype *
\ if &omnifunc == "" |
\ setlocal omnifunc=syntaxcomplete#Complete |
\ endif
endif
let g:rubycomplete_buffer_loading = 1
let g:rubycomplete_classes_in_global = 1
let g:rubycomplete_rails = 1

"=================================================="
" syntax and snipMate filetype setting
"=================================================="
" cross link between php and html
augroup php
autocmd BufRead,BufNewFile *.php set filetype=php.html
autocmd BufRead,BufNewFile *.html set filetype=html.php
augroup END
" link lex to c
augroup lex
autocmd BufRead,BufNewFile *.l set filetype=lex.c
augroup END
" cuda to cpp
augroup cuda
autocmd BufRead,BufNewFile *.cu set filetype=c.cpp
augroup END
```

一開始是編碼和layout的設定，然後是各個plugin的設定  

* 用F12可以開taglist  
* 用F7可以用當前的makefile進行make  
* 之後可以用F8列出quickfix所有的錯誤編譯訊息  
* Ctrl+n Ctrl+p在錯誤內容進行跳躍  

omnicomplete的部分是針對各種檔案格式，去設定omnifunc要用哪一種  
比較奇怪的是，在vim73上面，omnicomplete的功能被嚴重限縮了  
目前還不知道原因Orz  

最後就是一些filetype的link  
比如說把php, html的filegype交互設定，這樣在php檔裡面也可以使用html 的snipMate快速補齊；cuda 和lex也是相同的道理  

## 結論  
這是一篇廢文  
其實vim功能相當的強大，能安裝的plugin也多的很  
這個設定只是分享，使用習慣還是大家平時用習慣最重要  
