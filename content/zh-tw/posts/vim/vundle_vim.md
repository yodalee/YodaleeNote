---
title: "使用Vundle 維護的新vim 設定"
date: 2015-03-21
categories:
- vim
tags:
- vim
- vundle
series: null
---

離上一篇 [我的vim設定]({{< relref "vimsetting.md">}}) 已經過了一段時間  
其實這個設定已經過時，大約去年九月左右就已經整個換掉了。  

現在的設定是由阿蹦大神推薦的，包括：  
* [Vundle](https://github.com/gmarik/Vundle.vim)  自動安裝插件的插件  
* [ultisnips](https://github.com/SirVer/ultisnips)  強大的原始碼片段展開  
* [vim-snippets](https://github.com/honza/vim-snippets)  各種snippets的集合  
* [YouCompleteMe](https://github.com/Valloric/YouCompleteMe)
補齊插件，包括C語言、Java(雖然我沒寫)跟python 的補齊  
* [Cscope](https://github.com/steffanc/cscopemaps.vim)  Cscope，利用Ctags 幫助原始碼查找的工具  
* [vim-better-whitespace](https://github.com/ntpeters/vim-better-whitespace)
自動幫你把trailing whitespace 給幹掉的插件  
* [tagbar](https://github.com/majutsushi/tagbar) 顯示檔案內的 tag 和整體架構
<!--more-->

另外還有一堆各種程式語言的插件，就只列語言不附連結了：
* haskell
* sml
* rust
* go
* glsl
* sage

用上Vundle 的好處是，安裝plugin 變得簡單很多，不像以前要用dropbox同步所有設定檔，同時Vundle 可以透過github 安裝，
能直接update plugin，像我剛裝的時候還沒有Rustlang 的snippets，後來update 一下就有了。  

## Vundle

首先設定Vundle，照著Vundle 的設定打就行了，先用git 把Vundle.vim 載到~/.vim/bundle 資料  
夾裡：  
```shell
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
```

然後在設定檔加入   
```vimrc
filetype off
set runtimepath+=~/.vim/bundle/Vundle.vim
call vundle#begin()
Plugin 'gmarik/Vundle.vim'
Plugin 'SirVer/ultisnips'
Plugin 'honza/vim-snippets'
Plugin 'Valloric/YouCompleteMe'
Plugin 'steffanc/cscopemaps'
Plugin 'wting/rust.vim'
Plugin 'ntpeters/vim-better-whitespace'
call vundle#end()
```

想要裝的plugin就像這樣，在vimrc 裡面插入Plugin，後接git repository 的url 或是author/pluginname；
接著在vim 裡面下達 `:PluginInstall` 讓Vundle 猛攪一陣就可以了。  

## Ultisnips

這個比較簡單，因為我們vim-snippets 裡的檔案會存在  
```txt
.vim/bundle/vim-snippets
```

裡面；另外是觸發snippet 的按鍵，設定Ultisnips的參數，xxxxxxx請改自己的家目錄：  
```vimrc
let g:UltiSnipsSnippetsDir=["/home/xxxxxxx/.vim/bundle/vim-snippets/UltiSnips"]
let g:UltiSnipsExpandTrigger="<c-j>"
let g:UltiSnipsJumpForwardTrigger="<tab>"
let g:UltiSnipsJumpBackwardTrigger="<s-tab>"
```
## youcompleteme

這比較麻煩，在C語言系統它要先編過一些東西，先設定vimrc：  

```vimrc
let g:ycm_global_ycm_extra_conf = '/home/xxxxxxx/.vim/plugin/.ycm_extra_conf.py'
let g:ycm_extra_conf_vim_data = ['&filetype']
```

上面這個 `.ycm_extra_conf.py` 可以在 `.vim/bundle/YouCompleteMe/third_party/ycmd/cpp/ycm/`  
裡面找到（講到這裡我就要靠北一下，我記得這個py檔不設定的話YouCompleteMe會跟我一直叫叫叫，然後一堆人都遇到這個問題丟去github 上問，作者只會回「去看文件」啊你文件就沒有講吼！）  
這裡面是YouCompleteMe 的設定檔，我只有把裡面的 `-Wc++98-compat` 改成 `-Wno-c++98-compat`，使用一些 C++11 的語法時才不會一直警告和 C++98不相容。  

然後YouCompleteMe需要編譯，需要安裝編譯工具、Cmake跟python-dev，然後：  

```shell
cd ~/.vim/bundle/YouCompleteMe
./install.sh --clang-completer
```

## Cscope

要安裝ctags 跟cscope，在Linux 用套件管理程式都可以安裝。  
接著在原始碼根目錄的地方，先用ctags -R 產生tag 檔，之後打開vim後，在關鍵字上使用Ctrl + ] 就可以進行跳躍，用Ctrl + t跳回。   

---

大概就是這樣，現在你的Vim 應該已經變成相當強大的工具了，Happy Vim。