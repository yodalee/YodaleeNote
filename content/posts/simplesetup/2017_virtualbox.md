---
title: "如何調整 virtualbox 虛擬硬碟檔案的大小"
date: 2017-05-16
categories:
- simple setup
tags:
- virtualbox
series: null
---

故事是這樣子的，一直以來我都是用 Archlinux 作為我的作業系統，因為在碩士班要跑的模擬用的是 windows 版的ADS，做投影片要用到 M$ Office，於是就裝了一個 Virtualbox ，裡面跑 Win 7。  
最近wannacry 勒索軟體肆虐，我才驚覺原來我 virtual box 裡的 win 7 已經超級久沒有更新了，結果是卡到 win 7 的一個 update bug，
一更新它就卡在check update 上出不來了，後面搜尋了一段時間，先手動裝了幾個 update 才開始更新，這部分用 windows 7 check update stuck 當關鍵字還不少搜尋結果。 
因為累積的一籮筐的更新，要下載的檔案大小超過1 GB，然後…嗯…我的 virtualbox 劃給 windows 的磁碟就滿了(.\_.)，幸好我用的是vdi格式可以動態調整磁碟大小，之前就有調整過一次，這次做個筆記方便下次查找。  
<!--more-->

[參考文件](https://forums.virtualbox.org/viewtopic.php?f=35&t=50661)
開頭就有說了，一定要是 vdi 的虛擬硬碟檔案，首先要先備份一下 vdi 檔，以免調整用量的時候出錯，把整個虛擬磁碟毀了，
備份完之後，使用下面的指令，vdi 檔的路徑建議用絕對路徑，size 的單位是 MB，我多劃 5 GB 的空間給它，總共是 40 GB。  
```bash
vboxmanage modifyhd /media/datadisk/win7.vdi --resize 40960
```
要注意這個指令似乎只能調大不能調小，所以不要不小心劃太多。  

[window 設定](https://www.lifewire.com/how-to-open-disk-management-2626080)  
vdi 檔案加大之後，只是從 guest 那邊看到的磁碟變大，windows 內還沒有對應的調整，這裡要使用 windows 的 disk management：
1. 控制台
2. 系統及安全性
3. 系統管理工具
4. 建立及格式化硬碟分割

可以把它想成 windows 版的 gparted。  
打開之後的畫面大概像這樣（這張是網路上抓的）
![diskmanagement](/images/posts/diskmanagement.png)

這是已經擴大分割之後的畫面，剛擴大完應該會在 C碟的後面看到另一個未使用的分區。  
這時只需要在 C 碟上右鍵，選擇延伸磁碟區，把新加的空間劃給它即可，如此一來就完成了擴大磁碟的工作了。  

話說 35 GB 都不夠用，win 7真的肥肥。  
更新又這麼久，真的是珍惜生命，遠離 windows。 