---
title: "使用 ccache 加速編譯"
date: 2021-03-25
categories:
- c
- cpp
tags:
- c
- cpp
- ccache
- distcc
series: null
---

故事是這樣子的，小弟在公司工作內容，要維護公司產品核心的engine，要維護當然會需要把程式碼從版本控制裡簽出來，
修改、編譯後測試修正有沒有問題，而編譯一直以來都非常花時間。  
本文介紹的 [ccache](https://ccache.dev/) 是 compiler cache 的簡稱，會在編譯時存下檔案內容的 hash 與編譯結果，在未來如果有相同的檔案要編譯的時候，就不用再次呼叫 gcc/g++ 進行耗時的編譯，只要把存下的 object 檔從 cache 裡面抓出來就行了。

<!--more-->

在編譯加速上，小弟的公司已經做了許多努力，包括：
* prebuilt library：因為公司有很多共用的 library，每天某個時間點，電腦會自動簽出當天的程式碼並編譯所有 library，
如果你沒改到 library，不簽出這個 library 就不用重編譯，連結定期建好的 library 即可。
* 公司也自幹了一套編譯工具，可以幫你把 code 灑到許多（一般預設是80台）機器上平行編譯，
有點類似 [distcc](https://distcc.github.io/)，可以大幅減少編譯時間。

話雖如此，分散式編譯從零開始編譯到產生執行檔仍然需要 11 分 33 秒；如果不用分散式編譯用單機編譯則需要 23 分 36 秒；
目前程式碼裡，有一些 cpp 檔不知道是不是寫太長或太複雜，光編譯單一檔案都要編超久，即使有分散式編譯也會卡住整個編譯流程。  

最糟的是，隨著簽出的 library 數量愈多，編譯時間也會愈長，某個極度複雜用程式寫程式的元件，單機編譯可能要花上兩個小時，
讓人不禁回憶起以前在用 Altera quartus II 編譯 verilog project 的時候，差不多也是耗時那麼久。  
後來忘了我在哪個場合，聽到強者我同學在 Google 大殺四方的小新大大提到 ccache，就決定來試試看能加速多少？  

## 安裝
不是管理員無權動工作站的內容，我在工作站上只有找到一款 ccache-swig，版本是 1.2.4，這版本實在有點太老了，因此我決定自己去 [github](https://github.com/ccache/ccache) 載最新的 code 回來自己編譯，建議至少要用到 ccache 3，才有支援下面會提到的 hash_dir 的功能。

ccache 採用的是 Cmake，載下來之後照[安裝步驟](https://github.com/ccache/ccache/blob/master/doc/INSTALL.md)進行編譯即可：
```bash
mkdir build
cd build
cmake -DZSTD_FROM_INTERNET=ON ..
make
make install
```

ccache 背後採用 facebook 的 [libzstd](https://github.com/facebook/zstd) 來壓縮、儲存快取的 .o 目的檔，
同樣因為我的機器沒裝 libzstd，所以讓 cmake 去網路上抓。

## 設定

裝完之後 ccache 會需要一些設定，這裡只列出我有設定的，其他的就請[參閱文件](https://ccache.dev/manual/4.2.html)。  
每個 ccache 的設定都有兩種設定方式，一種是用環境變數，一種是寫到 ccache.conf 檔案中；ccache 有一套設定[優先權的順序](https://ccache.dev/manual/4.2.html#_location_of_the_primary_configuration_file)。

### ccache directory
ccache 快取儲存的位置，我用 CCACHE_DIR 環境變數來設定，一般預設會使用 $HOME/.cache 作為儲存位置，
但我們工作站有限制家目錄的容量，因此我用 softlink 從 $HOME/.cache 連到大容量磁碟另一個 .cache 資料夾。  
我不清楚 cache directory 放在硬碟、固態硬碟、Ramdisk 會不會對效能有影響，以速度、頻繁讀寫又可以限制容量的性質來看，
ccache 放在 Ramdisk 上應該滿合理的，可惜在工作站上權限不夠沒辦法自建掛載  ramdisk QQ。  

ccache directory 下的 ccache.conf 則是我們的設定檔。

### 最大容量
執行 `ccache -M 2G` 或在設定檔中留下
```txt
max_size = 2G
```
來設定 ccache 可使用的最大容量，因為使用了 zstd 的關係，ccache 用的 cache 空間不會很大，我編譯了應該有幾百 MB 的執行檔，debug/release 各一套近 1000 個目的檔，也只用掉 250 MB 的 cache 空間，2G 對一般人來說應該很夠用了。

### hash_dir
```txt
hash_dir = false
```
在寫程式難免需要 debug build，而 debug build 會在目的檔內留下編譯時資料夾的絕對路徑，這會讓 ccache 失效，
因為在不同資料夾內的同一個檔案，會被 ccache 視為不同檔案而重編譯，而工作上為了修正不同的問題，在不同地方同時簽出 code 司空見慣。  
設定 hash_dir = false 可以讓 ccache 忽視掉檔案的絕對路徑資訊，即使不同資料夾內的編譯也能共享 cache，
這也是為什麼上面說一定要用 >3 的版本，因為沒有 hash_dir ccache 的效率會大幅下降。  

對這個問題有其他的解決方式，請參考[Compiling in different directories](https://ccache.dev/manual/4.2.html#_compiling_in_different_directories)

## 測試

ccache 的使用方式很簡單，把 gcc/g++ 呼叫改成 ccache gcc/g++。如果用的是 Makefile，最簡單的就是設定 CC, CXX 兩個變數，讓 Makefile 替換掉編譯的指令。  

小弟因為公司自幹一套編譯系統，還花一點時間跟整合 team 問了該如何設定自己的編譯器；
而且因為上述的分散式編譯，會把工作丟到其他機器去執行，而遠端機器的函式庫舊到無法執行我用最新函式庫編譯的 ccache，
導致我下面的測試都是把分散式編譯關掉改用單機編譯，測試結果可能會比用分散式編譯還要好。  

### 測試步驟
以下測試流程：
1. 用 ccache -Cz 清空快取與 ccache 統計資料
2. 簽出 baseline 進行 debug build
3. 簽出 enhance 進行 debug build
4. 在 baseline 進行 opt build
5. 在 enhance 進行 opt build
6. ccache -s 觀看統計資料

我們的程式在 build 的時候，除了編譯各個檔案外，還有一些時間花在**從程式裡剖析 prototype** 以及最後**連結執行檔**的時間，
這些都不是 ccache 可以加速的步驟；4. 5 步時，因為 2.3 步 debug build 已經做過**從程式裡剖析 prototype**這件事，
編譯 c/cpp 檔案的時間佔比會更高。  

### 測試結果

| | Baseline Build | Enhance | Gain |
|-|-|-|-|
| Debug Build | 29 min 39 sec | 11 min 51 sec | 2.3x |
| Opt Build | 23 min 36 sec | 4 min 47 sec | 4.9x |

看這個結果我們應該可以推估從程式裡剖析 prototype 這件事大概耗時六分鐘（而且這步沒有平行化處理）。  
這個結果比我想得還要厲害一點，編譯佔比高的 Opt build 幾乎快了五倍。  
當然，這裡並沒有測試分散式編譯下 ccache 的影響，因為分散式編譯下編譯佔的時間會少很多，想必效能增長不會這麼大。

統計結果當個參考就好 ccache -s
```txt
cache directory                     /home/ipban/.ccache
primary config                      /home/ipban/ccache.conf
secondary config (readonly)         /home/ipban/myinstall/etc/ccache.conf
stats updated                       Wed Mar 24 12:46:34 2021
stats zeroed                        Wed Mar 24 11:48:15 2021
cache hit (direct)                  459
cache hit (preprocessed)            2
cache miss                          465
cache hit rate                      49.78 %
called for link                     4
cleanups performed                  0
files in cache                      928
cache size                          246.8 MB
max cache size                      2.0 GB
```

## 結語

導入 ccache 對編譯速度改進比預想還要好，目前小弟應該會跟公司的整合 team 連絡看看，看能不能將 ccache 導入我們的編譯流程中。
畢竟如果在每天定期的編譯時，也能把 ccache 的結果一併建出來，放在共用的磁碟內，
大家把 cache dir 設到那裡去，很可能可以省下巨量的編譯時間，應該是滿值得的。

本文感謝強者我同學在 Google 大殺四方的小新大大指導