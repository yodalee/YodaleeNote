---
title: "使用Expect進行大量修改密碼"
date: 2013-09-20
categories:
- Setup Guide
tags:
- expect
- bash
series: null
---

最近稍微研究了一下expect這個工具，簡單來說，它可以作為使用者對shell的代言人，本來需要大量使用者回應的工作，可以交由expect來處理，
能做到非常多事情，多到值得寫一本書，也是本篇的參考資料：  
[Exploring Expect A Tcl-based Toolkit for Automating Interactive Programs](https://itbook.store/books/9781565920903)  
看書還是吸收技術最快的方法。  
<!--more-->

最簡單的工作，就是由expect來幫我們輸入密碼，例如我們要改帳號，都需要輸入舊密碼和兩次新密碼，如果有1000個帳號要修改時，等於要輸入3000次密碼，如果兩次新密碼打錯的話還會吃屎重來，真是讓人感到絕望…。  
再更簡單一點就是管工作站時，要向其他電腦下命令，如果有10台電腦要執行一樣的命令，而且要用 su 執行？  
結果書上還出現用expect來控制gdb的除錯程序，好像有一點猛…  

expect最基本的指令大概是：  
1. spawn
2. expect
3. send

有了這三個就能做不少事情惹。 例如我想從工作站上載東西下來：   
```shell
#!/usr/bin/expect

set password "mypassword"

spawn scp account@workstation:/etc/hosts .
match_max 1000
expect "*?assword: "
send "$password\r"
expect eof
```
首先我們設定password變數，利用spawn叫shell執行scp指令，當scp要求輸入密碼時，由expect承接，scp輸出內容是：  
```
txtaccount@workstation 's password:
```
用*整個接下來；用send把密碼傳給shell，就完成一個自動下載檔案的程式了。  
唯一要注意的大概只有那個\r回車鍵，沒打那個就相當於打完password後沒按enter，你會看到程式停在螢幕上對你微笑，等你按enter。  

上面只是個簡單的例子，回應很單純，不過稍微擴展一下，我們就可以完成一個自動改nis密碼的script   
```shell
#!/usr/bin/expect

set rootpwd "wwww"
set newpwd [lindex $argv 1]

spawn yppasswd [lindex $argv 0]
expect "*?root password:"
send "$rootpwd\r"
expect "*?new password:"
send "$newpwd\r"
expect "*?new password:"
send "$newpwd\r"
expect eof
```

使用./script account newpasswd，即可自動修改密碼，只要事先把account跟newpasswd打好，一瞬間密碼就改完了，有幾千人都不用怕。  

雖一的缺點大概是要把root password明文寫在script裡面，這個script一定要保護好，用root擁有然後權限設成700吧。  