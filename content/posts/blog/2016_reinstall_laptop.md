---
title: "筆電重灌全記錄"
date: 2016-09-27
categories:
- LifeRecord
tags:
- Acer
- laptop
- linux
series: null
---

最近家目錄 100 GB 的硬碟被我塞滿了。  

雖然後來刪掉一些東西，例如之前玩一些<資料>分析contest 的資料，還有之前玩虛擬貨幣primecoin載了整個區塊鏈，也全刪掉，清了大概30 GB 的空間出來。  
不過覺得還是不夠好，畢竟現在的電腦從2013年4月用到現在，硬碟分割不是很好，有太多長期留下來的東西，設定檔愈來愈亂，空間分配也不是很好；
覺得是時候重灌系統調整體質，以迎接下個十年，逆風高灰(X。  
<!--more-->

重灌系統，麻煩的就是要先備份系統，我選擇的是把家目錄備份出來，備份[使用 rsync](http://newsletter.ascc.sinica.edu.tw/news/read_news.php?nid=1742)，
用rsync 的好處是快，而且可以增量備份，隨時加一點東西上去也OK，例如週末有空的時候做全資料夾備份，直到重灌前一刻再增量備份：  

```shell
rsync -av --exclude=”.*” --exclude=”.*/” src_dir dest_dir
```

不過如果你的資料夾裡有 git 的話，就要小心，上面這個不會備份隱藏的資料夾，要把那個exclude 拿掉。  

硬碟分割的部分，這次決定採用激進的分割方式，雖然電腦上會保留Windows…用來……打遊戲，不過這次不分割所謂的D槽給Windows，資料分割區從NTFS 改為ext4。  

以下是這次的分割狀況，沒特別註明就是GB：  

* /boot 200 MB
* windows 150 之前的windows 被塞了不少acer 預設的程式在裡面，這回全部清得乾乾淨淨，給150 應該很夠用了。
* Linux root 75，現在是給50 GB，我也從來沒想過它會裝滿，直到有一天要燒FPGA裝了Xilinx Vivado，瞬間root 剩下零頭，每回開機都會警告空間不足…
* Linux /var 30 曾看archlinux 的wiki 頁面分12 G 給它，結果安裝一堆套件之後立刻就滿了
* Linux /home 200 一口氣倍增到200 G，應該絕對夠用了吧
* Linux /data 硬碟剩下的空間大概500 G就全分給data，之前用NTFS 現在改用ext4，用來放一些像是東方啦動畫之類的東西。


另外備份所有已裝套件：archlinux 使用
```shell
pacman -Q > allpackage
yay -Q > allpackage
```
把所有安裝的套件包都列出來  

然後就可以放心的把磁碟區全部clean 掉，然後先裝windows，再裝我的不敗開發環境：archlinux；颱風天一個人躲在房間，任窗外狂風暴雨，我的電腦也是狂風暴雨XD。  

不過我太久沒裝了，還是參考一下[強者我同學的安裝記錄](http://johnjohnlys.blogspot.tw/2016/06/archlinux.html)，大體上沒什麼不同，我是選用mate 作為我的桌面環境。  
小試一下，我的archlinux就回來啦，重裝套件的部分，就用剛剛上面的reinstall 文件，搭配vimdiff，很快就能把套件全部裝回來了…才怪。  

老實說，因為選用的是archlinux 的關係，有不少比較不那麼正式卻又很常用到的東西，都要從AUR 去裝；
而AUR 跟pacman相比就是很吃網路跟編譯時間，結果我整個裝下來，花的時間不比windows 的少，雖然說爽度還是有差，AUR 只要yaourt 裝好，指令打下去就是了；
windows 還要自己去找安裝檔，用滑鼠一個一個安裝，只能說重灌就是麻煩……希望這次轉骨完之後，下次可以等到很久很久之後再重灌了。  

ps. 後來發現在 /etc/makepkg 裡面的 -j 選項沒有開，等於是一直用單核心編譯，不知道速度上能差到多少  