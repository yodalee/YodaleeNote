---
title: "使用sed取代ADS檔案路徑"
date: 2014-08-07
categories:
- microwave
tags:
- ADS
series: null
---

最近實驗室正在畢業潮（已羨慕），學長們約定俗成要把自己的設計燒成一片光碟傳給學弟……喔或是學妹。   
一般習慣不好的話，在ADS 的設計檔裡，會包含很多絕對路徑的內容，這樣這個設計project就變得難以移植。   

以我隔壁超強的同學「瓦哥」為例，過去的電磁模擬記錄會這樣寫   
```txt
D:\Program Files (x86)\Sonnet\0.18um\_m\transformer\PA\sonnet\Stack\_PA\XXX.snp  
```
移到別的電腦就找不到這些電磁模擬檔。   

比較好的做法是把電磁模擬放到ADS的project資料夾內，例如新建一個EM的資料夾，然後用相對路徑去存取：   
```txt
EM\Stack\_PA\XXX.snp  
```
就能確保模擬檔的可移動性。   

那如果已經做完了，難道要一個一個改嗎？   
ADS的設計是記錄在dsn文字檔裡面，這類文字檔的操作其實也很簡單，在ADS project的networks資料夾，改掉dsn裡面的檔案即可：   
用 sed 一行解決，加上for loop 輕鬆寫意，就跟喝水一樣輕鬆：   

```bash
for i in *.dsn;
do
   sed -i 's/XXX/yyy/g' $i;
done   
```

缺點：Unix 限定……，windows我還真想不出解法，可能要用python, mingw，不然powershell可能有類似的功能？   
當然要一個檔案一個檔案打開來改也不是不行，只是很不smart就是。 