---
title: "以pull request參與github專案開發"
date: 2014-05-09
categories:
- git
tags:
- git
series: null
---

本魯最近看到一個有趣的專案: [qucs](http://qucs.sourceforge.net/)  

目的是要打造一個類似ADS, AWR一樣的開源電磁模擬軟體，基本上是個野心勃勃，不過實際上沒多少人參與的專案，老實說還真令人擔心，我覺得還沒到一般人可用的階段應該就會腰斬了吧lol  
不過難得有個專案跟本科相關，就進去玩一下好了，看看bug report，爬爬程式碼還真的修掉幾個 bugs  

好啦都修掉了那就來送個Pull Request吧…這玩意要怎麼送來著？  
這時就只好自力救濟，問問旁邊的AZ大神跟QCL大神，QCL大神還很給力的直接殺到我房間教我；另外自己[查了一點資料](http://stackoverflow.com/questions/14680711/how-to-do-a-github-pull-request)：  
<!--more-->

對github的pull request 整理如下。  

## Step 1: get project

首先先在github網頁上，喜歡的project上按fork，把它複製到你的github上。  
接著用終端機clone你的github：  
```shell
git clone git@github.com:username/project
```
這樣會生成一個本地的git repository，它的 origin remote 設在你的github上。  
為了方便參與開發，建議連接上原project的github，才能隨時保持你跟project無時無刻處在同步狀態：  
```shell
git remote add upstream
git@github.com:mainuser/project
```
這樣你的本地git 的 upstream remote 就會連上原始 project 的 github  

## Step 2: Open branch

接著就來修改吧。  

通常新手使用git都會在來個「master大蜈蚣法」，一個master一路往前衝；不過project一大的時候還是建議開branch，改用「master大開花法」，每個branch只做一點點feature，然後再merge/rebase回master裡，反正 git 就是branch怎麼開都無所謂。  
參與pull request的時候更是如此，通常這時候project已經相當大了；儘量讓project manager看到少量的檔案變化，而不是整個project的檔案都變過；每個branch取個簡單易懂的名字：bug編號，feature編號都是不錯的選擇。  
```shell
git branch -b branchname
git checkout branchname
```
或是  
```shell
git checkout -b branchname
```
## Step 3: Make modification

修修補補。  

## Step 4: Send pull request

pull request會比較原始的 github(也就是upstream)的某個branch，跟你的github裡的某個branch，把相關的commit 列出來，讓管理人決定要不要把你的commit接到它的branch上。  
另外，如果你在master上面加點東西，然後原開發者接受pull request，也在他的master上面加一些東西，兩個master間就產生衝突，所以請務必確保你的master是乾淨的。  

```shell
Git push -u origin branchname
```
把你所做的修改，推到你的github 上面產生一個遠端的 branch。  
接著到對方的 github，按pull request，比較對方的 master branch跟自己剛產生的這個branch。  
第一個pull request就送出啦。  

同時，在對方表態之前，這個branch就不要再動了。  
如上所說，github會比較兩個branch的差異，所以如果送出pull request之後又有變化，這些內容只會算到一個pull request裡，而不是每個feature一個pull request出去。  

當然如果你被拒絕了，你也可以繼續在這個branch上做修改，改好了再pull request一次。  

## Step 5: Merge, clean up

等待對方merge你的branch，merge之後，github會自動問你這個feature的branch要不要刪掉。  
或者也可以用  
```shell
git push origin :branchname
```
來刪掉遠端的branch，另外要用  
```shell
git fetch origin -p
```
讓本地端更新遠端刪除掉的branch 的資訊。  

最後要保持你的project跟遠端是同步的：  
```shell
git fetch upstream
git checkout master
git rebase upstream/master
```

完成的畫面大概會像這樣：  
![afterPR](/images/git/afterPR.png)

整體的流程就是：
1. 在 origin/master 的地方 fork 對方的project
2. 在本地產生branch bug147
3. 修正bug
4. 推到我的github(origin)上。  
5. 對方merge我的pull request，更新了他的github(upstream)的master
6. 我再用rebase把我的master移到最新的狀態。  

如果你是高手，一次修 10 個 bugs 之類的，這時可以用rebase把其他應該修改的branch rebase到現在的master上。  

以上，祝大家pull request愉快，大家快點來開發各種open source project  

## 致謝：
本文感謝AZ大神及QCL大神的指導。