---
title: "使用dbench 進行硬碟效能測試"
date: 2017-02-24
categories:
- simple setup
tags:
- linux
series: null
---

最近遇到需要大量進行儲存系統讀寫的要求，因為包含了samba 硬碟，查了一下發現了dbench 這個測試程式，就試用了一下，它支援本機的測試，也支援samba, iscsi跟nfs 測試：  
<!--more-->

本測試需安裝 dbench 進行測試，在Linux 主機上使用下列指令取得dbench。  
```bash
git clone https://github.com/sahlberg/dbench   
```
先安裝要測試網路硬碟所需的library：  
```bash
sudo apt-get install libiscsi-dev  
sudo apt-get install smbclient  
sudo apt-get install libsmbclient-dev  
sudo apt-get install samba-dev  
sudo apt-get install libnfs-dev
```

在dbench 中使用下列指令編譯，configure 要加的參數來自[這個gist](https://gist.github.com//6d94b7db13b08be586ce)，才能找到samba client library：  

```bash
./autogen.sh  
./configure CFLAGS="-I/usr/include/samba-4.0/"  
make  
make install   
```
完成編譯dbench，在測試機上，可以使用dbench來進行測試，簡單的如：  
```bash
./dbench --loadfile=loadfiles/client.txt -t <TIME> <THREAD>
```

或是想要測試遠端的samba server：  
```bash
./dbench -B smb --smb-share=//<IP>/<DIR> --smb-user=<USER>%<PASS> --loadfile=loadfiles/smb_1.txt -t <TIME> <THREAD>   
```

各欄位說明如下：  

| | |
|:-|:-|
| IP | samba IP |
| DIR | samba 資料夾名稱 |
| USER | samba使用者帳號 |
| PASS | samba使用者密碼 |
| TIME | 測試時間 |
| THREAD | 使用多少 thread 進行測試 |

如果是nfs 或iscsi 的話，應該會需要其他的參數以設定登入，不過手邊沒有nfs 或iscsi 可以測試，只好先跳過。  

loadfile 是dbench 的測試檔案，裡面可以描述想要dbench 執行的讀寫動作，例如開檔、寫檔等等，如果寫得好，它應該可以重現一般使用者真實的讀寫狀況，不過我都直接用它在loadfiles 資料夾中預設的檔案，如上面的smb\_1.txt。  
自己試過在超過50 個thread 的時候，samba很容易出現寫入錯誤，所以保守一點就用50 個thread 就是了，
如果是本機測試的話，就不用這麼保守；不過話說回來一般本機上也不會有這麼多人一起用你的電腦就是了。  
執行之後，dbench 就會印出測試的報表：  
```txt
Operation                Count    AvgLat    MaxLat
--------------------------------------------------
Flush                      849   117.384   207.657
Close                     9000     0.003     0.117
LockX                       40     0.006     0.019
Rename                     520     0.078     3.887
ReadX                    19240     0.007     1.723
WriteX                    6039     0.056    11.209
Unlink                    2480     0.058     3.291
UnlockX                     40     0.003     0.005
FIND_FIRST                4300     0.035     0.162
SET_FILE_INFORMATION       990     0.090    10.150
QUERY_FILE_INFORMATION    1940     0.002     0.017
QUERY_PATH_INFORMATION   11350     0.013     8.822
QUERY_FS_INFORMATION      2040     0.004     0.048
NTCreateX                12260     0.020     8.160

Throughput 42.255 MB/sec  10 clients  10 procs  max_latency=207.669 ms
```

## 參考資料：  
[dbench](http://kongll.github.io/2015/04/24/dbench)  
[man page](https://dbench.samba.org/doc/dbench.1.html)