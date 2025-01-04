---
title: "使用 doxygen 產生程式文件"
date: 2017-05-27
categories:
- Setup Guide
tags:
- doxygen
- c
- cpp
series: null
---

這應該是個過時的題目，相關的文件已經滿天飛了，不過最近程式寫得肥了，又是和其他人的合作項目，總不能老是這樣打開 Office Word 寫文件(掩面)，
然後程式跟文件老是不同步，還是把註解改好用 doxygen 產生文件省事些，順帶得就寫個文章記錄一下。  
[doxygen](http://www.stack.nl/~dimitri/doxygen/manual/index.html) 是一套文件產生程式，會自動 parse 原始碼、標頭檔等，搭配設定的模版，自動產生不同種類的文件，如 manpage, html , latex…。  
<!--more-->

要用 doxygen 第一步是先安裝 doxygen，這在 unix 下配上套件管理員應該跟喝水一樣簡單，略過不提。  

`doxygen -g <config-file>` 產生設定檔，預設的名字會是 Doxyfile  

下一步要編輯設定檔，我比較過預設設定，大概要改下面這些地方：  

* PROJECT\_NAME：當然要改成自己的名字
* OUTPUT\_DIRECTORY：我設定在 doc 資料夾，並且把 doc 資料夾加到 .git 中
* OUTPUT\_LANGUAGE：設定語言
* EXTRACT\_ALL：設成 YES，這樣才會解析所有的檔案，否則預設只會解析 .h 檔，必須要用 \file 或 @file 定義過的檔案才會被解析
* INPUT：用空白分隔的輸入檔案或資料夾，我是 src 資料夾
* FILE\_PATTERNS：設定要分析的檔案，這裡我只保留 .c 跟 .h
* EXCLUDE：把不需要的資料夾剔掉，因為我有一個測試的 test 資料夾，所以把它加上去
* GENERATE\_*：設定要輸出的格式，我只選擇輸出 html ，設定 GENERATE\_HTML 是 YES

為了在程式中加上更多資訊，可以在程式碼裡面為函式寫註解，我是使用下列的型式：  
```c
/*! * */
```
另外搭配以下幾個註解命令：  

* \brief 可以提供一行描述，簡短敘述這個函式的功能  
* \see 關鍵字，可以產生連結跳轉去其他的內容  
* \param 參數描述，有符合原始碼內的參數名稱，在排版上會自動上色並縮排  
* \return 對回傳值的描述  

在 \brief 之後空一行，其它的內容則會歸為長敘述中，如果沒空行的話這些內容都會被濃縮成一行歸在 brief 裡面，所以，一個完整的函式註解如下：  
```c
/*!
 *
 * \brief dest = src xor dest
 *
 * do xor on src buffer and dest buffer, store result in dest buffer
 * \param src, dest buffer to xor
 * \param len buffer size both buffer should have enough space for len
 * \return none
 *
 */
int32_t xor2(
  uint8_t *src,
  uint8_t *dest,
  uint32_t len)
```
接著就可以下  
```bash
doxygen config_file
```
產生文件，文件會在 doc/html 中  
話說新一代的程式語言好像都自帶文件產生器，如 golang 的 godoc，rust 也有 rustdoc，也許 doxygen 這樣的東西，未來也用不太到了？  
