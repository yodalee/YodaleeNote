---
title: "使用 ctags 增強vim 的功能"
date: 2016-09-05
categories:
- vim
tags:
- vim
- ctags
- vundle
series: null
---

vim 搭配 ctags 是一款生猛的工具組，可以快速在trace 專案尋找定義和實作，大幅增加vim 瀏覽程式碼的效率。  
<!--more-->

## 安裝方法

安裝ctags ，archlinux 的話是ctags，ubuntu 的話是exuberant-ctags，其他的就…自己找。  

## 設定
在專案的根目錄中使用：  
```shell
ctags -R
```

產生tags 檔，在瀏覽原始碼的時候，就能用：  

* Ctrl + ] 跳到該名稱的定義  
* Ctrl + t 跳回到剛離開的位置   

另外在搜尋的時候，找到了一個taglist 的替代品 [tagbar](https://github.com/majutsushi/tagbar)，可以使用Vundle 安裝：  
在 .vimrc 裡面加上：  
```vimrc
Plugin 'majutsushi/tagbar'
map <F12> :TagbarToggle<CR>
```
就能用F12 開關Tagbar 的視窗，第一眼看來還不錯，比taglist 還要漂亮跟清楚很多，據說相對taglist 對Cpp 的支援也更好；
雖然以個人之前的經驗，taglist 沒有想像中的好用…也可能是我不會用吧。  

![tagbar](/images/vim/tagbar.png)

有關Vundle 的相關資訊，請參考[之前的文章]({{< relref "vundle_vim.md">}})  

其實ctags 上使用一直有個問題，導致我之前都不太使用它：一般稍大一點專案都不會是一層，而是程式碼分到樹狀的資料夾中，
用ctags -R 只會在根目錄上產生tags 檔，而通常寫code 的時候都不會在根目標上作業，否則要開檔的時候光打目錄就飽了；
但如此一來vim 就抓不到tags 檔了。  

後來查了一下[vim wiki](http://vim.wikia.com/wiki/Single_tags_file_for_a_source_tree)，發現只需要在.vimrc 裡面加上一行文就可以解決這個問題……  

```vimrc
set tags=tags;
```

這樣vim 就會一路往上找tags 檔。  

ps. 這樣就能修掉也太詭異了吧… 