---
title: "用word寫論文的一些技巧"
date: 2014-06-25
categories:
- MSoffice
tags:
- office
- word
- essay
- tutorial
series: null
---

站長最近都在忙論文，blog就這樣荒廢了，不過今天心血來潮，把幾個寫論文時用word+mathtype寫的技巧整理一下，分享給大家。   
不過先聲明，個人還是認為用LaTeX寫才是真高手，只是站長小孬孬就用word寫，不像強者我同學們都用LaTeX。   
<!--more-->

其實我覺得大部分的技巧，我之前的 [word tutorial]({{< relref "word_tutorial.md">}}) 都整理的差不多了，主要就是：   

1. 設定好階層   
2. 使用樣式庫   
3. 弄懂段落   
4. 管理好參考資料   

~~文章到這邊就可以結束了~~當然，我還是把大略的流程整理一下，看情況隨機插入一些技巧，如果不想看文字的話，可以拉到最後搭配著我的投影片和解說影片一起看：   

## 設定樣式庫   

一開始就先把大部分的樣式設好，這樣以後比較方便，我遇到大部分要設定的樣式總計為：   

* 內文
* 標題
* 標題1-4（論文能寫到更多層我也覺得滿厲害的）
* 目錄1-4
* 圖片
* 表格系列，包括：
    * 標題列格式
    * 表格內文
    * 表格註記
* 圖片標號
* 表格標號
* reference 樣式   

一些細節的設定等等再談，這裡先把大略的字體、大小都設定好了。   

## 把文章的幾個標題都打好   
什麼大綱、Contents，chapter 1什麼的，套用好格式。   
接著，因為遇到標題、標題一應該要開新頁，因此在這兩個格式的「分行與分頁設定」中，選擇「段落前分頁」，沒事別亂加分頁符號，那會讓文件變得難以排版。   
這時候，基本的文章架構應該已經有了，頁數也變得至少十頁，雖然說內容都是空的   

## 建標號   
把該用的標號建好：兩個基本款應該是 Fig 跟 Table，在「參考資料」-「插入標號」裡新增它們。   
建立時可以選擇「編號方式」，讓標號的數字會依照章節數字跳動。   

## 打文章   
好啦這才是最花時間的地方，但這沒啥技巧，全是硬功夫，再好的排版軟體要是沒內容排也排不出東西。   

## 插圖片   
個人會在文件旁建立一個fig資料夾，依章節把圖片分好，就算圖片還沒畫，也可以先複製隨便一張圖片放著，在插入的視窗中選擇「插入與連結」，之後只要改動插入的圖片，選擇圖片按F9即會自動更新了。   
插入圖片之後，記得選取圖片該行，將樣式改為「圖片」樣式。   

## 插標號：   
每插入一張圖片、表格後就用參考資料-插入標號，選用已建好的標籤   
在內文的地方就選交互參照，選適當的標籤，插入參照類型的「段落編號(部分顯示)」   
內文就會自動變成Fig. xx   
插入新圖片後只要全選後按「更新功能變數」或 F9，所有編號都會自動更新。   
另外因為標號跟它的內容要在同一頁，因此在「圖片」樣式的落段「分行與分頁設定」中，選擇「與下段同樣」，表格標號也如此設定，這樣表格、圖片和它的標號才會在同一頁。   

## 表格：   
其實表格在 word 2007 後也有自己的樣式，不過我是覺得沒什麼設定的必要。   
不過表格是有不少需要設定的內容：   

* 在左上方M$的符號－「 word選項」－「進階」最後的「版面配置選項」，把「不要將跨頁的換行表格切斷」選起來，這樣一般大小的表格才不會在表格中間換頁，而是直接跳下一頁。   
註：藏這麼深誰找得到啦！（￣▽￣）╭∩╮   
* 如果有一個非常長的表格(依我的論文22列以上大概都會超出一頁)，那麼請把整個表格選起來，在「表格內容」－「列」－「允許列跨越頁分隔線」取消掉，才不會出現一列的內容被分到兩頁去。   
* 同時把「跨頁標題重複」勾起來，讓word自動重複標題。   
* 在「表格內容」的「表格」，設定為「文繞圖」，然後在「位置」中設定下方的邊界值，這樣表格後的文字才不會離表格太近。   

## 方程式   
好了我們說到word最WTF的地方了，基本上作者試了很多方式之後，還是無法自動的產生靠右的方程式編號，最後還是靠MathType來解決，反正word爛也不是一天兩天的事，同學說 LaTeX is the ultimate solution 或許真有幾分道理。   

補：後來強者我同學為中大神在 FB 上面嗆我說，用 word 也是能正常為方程式編號的，方法如影片所示：   
<https://www.youtube.com/watch?v=JcB4nQ2AYts>   
我是還沒試過啦，不過既然是為中大神開示，應該就是正確無誤了。   

## 插目錄   
差不多有點內容就可以插入目錄了，在該插入的地方選「參考資料」-「目錄」，要圖表目錄還是一般目錄就自己選。   
視狀況調整目錄1-4的樣式，只有一個靠右的定位點是必要的，如果發生目錄文字太長讓頁碼沒有靠右，請設定該樣式段落的「縮排」為「第一排」並設定適當縮排值。   

## 檢視技巧   
在上方的檢視裡：   

* 選用Web 版面配置：可以盡情放大文件，橫軸的捲軸會消失，文件的內文會自動換行，這在寫太久眼睛很累的時候很好用   
* 打開文件引導模式：左邊會有標題列的列表，點一下可以直接跳過去。   
* 開新視窗：同一份文件開一個新的視窗，我的習慣是多開一個，一個用來打內文，另一份停在 reference 的地方，要 reference 什麼 Alt+Tab 切到另一個視窗去找，就不需要用滑鼠一直滾來滾去。   

## 教學投影片

<https://www.slideshare.net/youtang5/office-word-44352616>  
不知道為什麼 hugo 只要一插入 embed 的 slideshare 投影片，就會瞬間變成下面 youtube 的影片…。

## 教學影片

{{< youtube t2QZ7q0xExg >}}

## 結論

常用 word，論文好寫；前程似錦，畢業快樂(欸