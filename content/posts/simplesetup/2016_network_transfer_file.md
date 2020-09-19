---
title: "使用網路線直接連線進行資料傳輸"
date: 2016-10-02
categories:
- simple setup
tags:
- ssh
series: null
---

這篇講的其實不是什麼大不了的事情  
總之先前重灌電腦的時候，筆電裡面的平常放著不少動畫檔，為了求備份方便（時間與空間考量）我沒將它們備份到隨身硬碟上，而是把它們全部刪掉了。   
反正我桌機上還有同樣的動畫資料夾，想說重灌過後再把它們複製一份就是了。  
<!--more-->

在複製一份的時候，試了一下用網路線的方式來傳檔案，查一些文件，有說2002 之後的網路卡，配合網路跳線都能連得上，
也有[相關文章](http://askubuntu.com/questions/22835/how-to-network-two-ubuntu-computers-using-ethernet-without-a-router)在做這件事，於是就來試試看：   

我有一台筆電跟一台桌電，大致的設定如下： 首先是在兩端都接上網路線，分別在筆電和桌電的eth0（也可能是其他名字，反正就乙太網路介面）上設定不同的static ip：  

* 我筆電設定為：192.168.66.99/24 gateway:192.168.66.254   
* 桌電設定為：192.168.66.100/24 gateway:192.168.66.254   

在筆電上用ifconfig 就會看到介面ip 已設定：   
```txt
enp2s0f0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST> mtu 1500
inet 192.168.66.99 netmask 255.255.255.0 broadcast 192.168.66.255
```
連接上網路線的話，也會看到雙方的有線網路都顯示連線，這時候可以先用ping 去測一下，確定已連線  
```bash
ping 192.168.66.100 -c 3
PING 192.168.66.100 (192.168.66.100) 56(84) bytes of data.
64 bytes from 192.168.66.100: icmp_seq=1 ttl=64 time=12.4 ms
64 bytes from 192.168.66.100: icmp_seq=2 ttl=64 time=7.74 ms
64 bytes from 192.168.66.100: icmp_seq=3 ttl=64 time=2.46 ms

--- 192.168.66.100 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
rtt min/avg/max/mdev = 2.468/7.566/12.488/4.092 ms
```

接著在筆電上設定ssh，我在archlinux 上是用openSSH，[相關的設定](http://smalldd.pixnet.net/blog/post/24627330-arch-linux-%E5%AE%89%E8%A3%9D-openssh)。

最後開啟服務：  
```bash
systemctl start sshd
```
就能透過該ip ，從桌電ssh 進入筆電了：  
```bash
ssh username@192.168.66.99
```

確認連線之後，就能用任何你想得到的方法，透過網路備份，像什麼sftp, fillzilla 的，我最後同樣用rsync 來處理，這應該會要求目標電腦上也有安裝rsync，它會透過一個rsync --server來接收檔案：  
```bash
rsync -av --progress -e ssh /media/data/Animate 192.168.66.99:/media/data
```

log 我就不貼了，反正就一直傳一直傳一直傳，均速大概是 50 MB/s，雖然連線資訊寫的速度是1000 Mb/s，不過也算相當快了，一集動畫100M 在1-2 秒間就會傳完。  

我自己用隨身硬碟的經驗是，雖然usb2.0 速度理論上有 30 MB/s，3.0 當然更快，但是實際在複製的時候，通常都達不到這麼快，甚至有時會降到3-5 MB/s，
這點我懷疑有可能是我隨身硬碟用的格式是ntfs，而linux 上的driver ntfs-3g 有時效能不太好，相對來說網路傳輸反而穩定得多。  
另一方面，隨身硬碟備份要來回複製跟貼上，不像rsync按下去就行了；相對網路讀寫能同時進行就可以一次複製完，
外接硬碟再怎麼快，讀跟寫還是分開，外接硬碟要能相匹敵，讀寫均速至少要是網路速度的兩倍才行，
問題是現下可能連網路的1/5 都不一定達得到，網路的優勢實在太過顯著。  

附一張連線的實際照片，隱約可見的藍色線就是網路線，桌電遠端進入筆電，正在用rsync 上傳資料：   
![networkssh](/images/posts/DSC_0119.jpg) 