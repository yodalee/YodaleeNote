---
title: "ADS Export to Origin converter"
date: 2013-10-08
categories:
- microwave
- python
tags:
- ADS
- origin
- python
series: null
forkme: ADSToOrigin
---

最近在準備一些學校報告用的投影片，在學長主持的小咪報告之後，學長表示

> 你這幾頁的圖，如果之後要放論文的話，就乾脆用Origin重畫  

好吧學長都這樣說了，就來畫畫Origin的圖wwww  
不過秉持著用開源軟體的精神，還是找了一下，結果就在的[作敏學長的blog](http://zuomin.blogspot.com/2010/05/linux-origin.html)
裡面找到 [qtiplot 這個開源繪圖軟體](https://www.qtiplot.com/)，跟Origin的功能幾乎差不多。  
<!--more-->

## 問題簡述：

這裡遇到一個有點機車的問題：  
平常我們在ADS這套軟體畫好圖之後，如果用ADS再export成txt file，就會變成類似下面的格式：  
```txt
freq S(1,1)
1e9 -1E1
2e9 -1E1
3e9 -1E1
4e9 -1E1

freq S(2,1)
1e9 1E1
2e9 1E1
3e9 1E1
4e9 1E1
```

註：隨便選個數字表示一下。 但如果要用Origin匯入文字檔的話，理當是這個格式比較好：   
```txt
freq S(1,1) S(2,1)
1e9 -1E1 1E1
2e9 -1E1 1E1
3e9 -1E1 1E1
4e9 -1E1 1E1
```
俗話說得好：科技始終始於惰性，與其用Excel打開檔案然後一欄一欄複製貼上，不如寫個script來解決 =b。  

## 解決方案：

最後還是用我們的老朋友python，實際譔寫時間約30分，超快der；會慢主要是在查zip的寫法；實際內容大概也只有zip比較有趣。  

首先先把資料一行一行讀進來，寫入list裡面。讀檔結束就會有一堆list，分別存著freq裡所有的資料，然後是S(1,1), S(2,1)，我在讀檔時就先把這些list存到一個大list裡。  
假設我的大list為data，data 的長相大概像這樣：  
```txt
data = [[S(1,1)],[S(2,1),....]]
```
於是我們可以先展開data list為所有list，然後透過python 強大的zip函式，直接iterate所有的list。   

```python
for line in zip(*data):
    outfile.write("%s\n" %("\t".join(line)))
```

很快速的就完成檔案格式化寫出的工作。  

## 多變數處理
之前的版本只支援單變數的狀況，這次則加入多變數的狀況，ADS記錄多變數的狀況如下：  
```txt
sweepvar1 ... sweepvar_n-1 sweepvarn ... data
var1_1 ... varn-1_1 varn_1 ... data_1_1
var1_1 ... varn-1_1 varn_2 ... data_1_2
var1_1 ... varn-1_1 varn_3 ... data_1_3
...
var1_1 ... varn-1_1 varn_m ... data_1_m

sweepvar1 ... sweepvar_n-1 sweepvarn ... data
var1_1 ... varn-1_2 varn_1 ... data_2_1
var1_1 ... varn-1_2 varn_2 ... data_2_2
var1_1 ... varn-1_2 varn_3 ... data_2_3
...
var1_1 ... varn-1_2 varn_m ... data_2_m
```

新版的會以前幾個變數產生title name，例如在上述狀況，最主要的index是sweepvarn，不斷重複的則是data，上述的狀況會產生為：  
```txt
sweepvarn title1 title2 …
varn_1 data_1_1 data_2_1 …
varn_2 data_1_2 data_2_2 …
varn_3 data_1_3 data_2_3 …
...
varn_m data_1_m data_2_m ...
```

產生的第一個title會是：  
sweepvarn 之後則是  
```txt
sweepvar1=var1_1,sweepvar2=var2_1, …sweepvar_n-1=varn-1_1
```
好像不好看懂，總之就是 title 會是第二到第 n 個變數的數值。  

目前有一個已知難防的bug是，顯示的變數名稱不能有空白在裡面，因為斷詞是以空白為基準(好像也沒有更好的斷詞方試)，
有空白的變數名稱會造成tital產生錯誤，目前無解。只能要使用者不用掃有空白的變數名稱，例如： `I_Proble[0, ::]`  

## windows版本：

在改windows版本的部分，則是把本來要吃參數的script改成吃使用者輸入的內容。  
照著的幫助，首先先安裝python和 [py2exe](http://www.py2exe.org/)，利用py2exe把python script轉成exe檔。  
先寫一個setup.py：  
```python
from distutils.core import setup
import py2exe

setup(console=['ADSToOrigin.py'])
```
然後在cmd用  
```bash
python setup.py py2exe
```
就會自動產生dist這個資料夾，裡面會包括ADSToOrigin.exe，打開就會開console，像linux一樣正常使用。  

原本是進入一個 prompt 讓使用者輸入檔名，使用者試用的經驗表示這實在是太弱了，
在windows下最好的使用方式：把要轉換的檔案拖到exe檔上面。  
測試之後發現，在windows上把檔案拖到exe檔上面，等同將被拖的檔案路徑當成argv參數傳入，因此程式改為輸入參數為要修改的檔名即可。  

## 原始碼公開：
這個script已經公開在[我的github](https://github.com/lc85301/ADSToOrigin)上，歡迎大家給feedback或來pull request。  

## 執行檔下載：

剛好建了自己的網站，就順便把下載連結丟到網站上來：
[ADS2Origin](/download/ADS2Origin.zip)