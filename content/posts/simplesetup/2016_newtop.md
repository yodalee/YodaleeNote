---
title: "新Top 介紹"
date: 2016-08-13
categories:
- simple setup
tags:
- shell
series: null
---

top 一直是command line 上相當重要的工具，一打開就列出幾個高消耗的行程，等著kill (X，有時候不小心把電腦給炸掉的時候還滿好用的。  
不過不知啥時更新後，新版的top 介面大改之後，我就不會用了OAO  
<!--more-->

最近決定把top 的用法給好好研究一遍，其實也就是把manpage 看過一遍啦，這裡做點筆記：  

進到top 後，主要分成
1. Summary Area
2. Fields/Columns Header
3. Task Area  

幾個沒變的命令：
* h是help
* q是quit
* 上下左右，page up/down, home, end，調位置  

Summary Area 沒啥好說，顯示uptime, load average, Task 和CPU 的狀態  
CPU 的狀態可用 t 來toggle顯示方式，可以

* 關掉CPU 顯示
* 下面資料全部顯示
* 只顯示 us+ni / sy total  

用 1 來toggle 顯示全部的CPU 亦或合成一個  

顯示的縮寫意思：  

| field | meaning  |
|-------|--------------|
| us, user | time running un-niced user processes |
| sy, system | time running kernel processes |
| ni, nice | time running niced user processes |
| id, idle | time spent in the kernel idle handler |
| wa, IO-wait | time waiting for I/O completion |
| hi | time spent servicing hardware interrupts |
| si | time spent servicing software interrupts |
| st | time stolen from this vm by the hypervisor |

Memory 的狀態用 m 來選擇顯示方式 Used/Avail graph 或都純文字顯示    

Field/Column 大概是跟舊版比起來變最多的，這裡可以用 f 進到managing fields來設定要顯示的欄位，
按 f 後在想要的資訊用 space 或 d 來選擇要不要印出，用s 來設定用哪個欄位排序。  

欄位基本上都有註解，我預設沒特別設定印出的欄位會是：  

| ID | USER | PR | NI | VIRT | RES | %CPU | %MEM | TIME+ | S | COMMAND |
|----|------|----|----|------|-----|------|------|-------|---|---------|

事實上可以印的東西很多，可以自行看manpage的介紹，不過我覺得實際上需要的其實也就預設這幾個。  

其實寫這篇最主要的目的就是 sort 了，因為開了top 都不知道要kill 誰了；現在自行設定用CPU 來sort，之後新的top 就像舊的top 一樣，把佔用最多CPU 的行程放在最上面，等著我們kill (X  

另外也有些快捷鍵能設定排序欄位：  

| Key | Sort Field |
|------|--------------|
| M | %MEM |
| N | PID |
| P | %CPU |
| T | TIME+ |

另外還有一些有趣的global command:  

| Key | Function |
|------|-------------|
| d | 設定更新的頻率  |
| E/e | 設定Summary Area/Task Window記憶體的單位，從KiB 到EiB (真的有人有這麼多記憶體嗎XD)都行  |
| g | 新的top 可以開四個不同的顯示視窗，可以有各自設定，用g 來選擇  |
| k | 大殺四方行程，這跟原本的top 是一樣的  |
| r | renice, 就…就是renice  |
| L | 定位字串，如果要highlight 某個關鍵字可用，類似vim 裡面的 '/'，找下一個則是 &  |

如果要改變畫面的顏色mapping，可以用Z 進到互動設定  
* b/B toggle粗體顯示
* z 設定是否彩色顯示

另外能設定各欄位的顏色：  
* S = Summary Data
* M = Messages/Prompts,  
* H = Column Heads
* T = Task Information  

不過我是沒什麼美感的人，去改配色大概只會悲劇，所以就放著讓它用預設顏色就好。  

初看新版的top ，應該是舊的top 功能不夠了，所以整個大翻修，還有許多功能本篇沒有介紹，
剩下的大概都是平常用不太到的功能吧，就留給有興趣的人去研究了。 