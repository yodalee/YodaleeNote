---
title: "用 docker container 來編譯程式"
date: 2020-04-11
categories:
- Setup Guide
tags:
- archlinux
- docker
series: null
---

故事是這樣子的，最近受朋友之託研究一個套件，在編譯的時候…不知道為什麼我的 Archlinux 編不起來，有某個奇怪的 bug 蒙蔽了我的雙眼擋住了我而且一時之間解不掉，目前看起來像是 golang 那邊的鍋。  
總之目前看起來像是 Archlinux 限定的問題，如果裝一台 ubuntu 18.04 的虛擬機，在裡面 build 就沒這個問題，可以完成編譯。  
不過想想，現在都 2020 年了，怎麼連 docker 怎麼用都還沒學起來（查一下這玩意 2013 年就已經問世了耶…），
就本例來說沒事還要開一個巨大的 virtualbox ，建個巨大的虛擬磁碟再安裝作業系統真的有點划不來，就花了點時間學了一下 docker ，
然後順便記個筆記，不然這年頭發現自己學習能力低落，連 docker 這麼簡單的東西都學不好QQ。  
<!--more-->

其實網路上已經有 100 篇 docker 的教學文了，不過我還是來寫個 101 篇吧。  
首先是關於 docker，大抵上就是一個輕量化的容器，在主機作業系統之上為每個應用程式建立一個最小的執行環境，
每個 container 都是一個 user space process；相對的虛擬機則是把整個作業系統都包進去，每個虛擬機共用一個硬體。  

當然我們這裡只是要用，背後的原理要是我哪天學會的話再來寫文章記錄QQ。  
對比虛擬機 docker 具有小、快的優點，畢竟不用開一台機器就要裝一次作業系統，很適合像我這樣只是要用另一個作業系統做個測試，
或者寫網路服務的，可以讓程式跑在一個固定的環境裡面，不用一台一台虛擬機處理環境的問題。  

這次我的目標就是開一個 ubuntu 18.04 的作業系統，然後在裡面進行編譯。 以我的 archlinux 來說，第零步是先安裝並啟動 docker：  
```bash
pacman -S docker
systemctl start docker.service
```
為求方便的話可以把自己加入 docker group 裡面，不過這等同於給他 root 權限（這段警語只出現在英文 wiki 上面）：  
```bash
gpasswd -a user docker
```
第一步當然就是先把 ubuntu 18.04 的 image 給拉下來，不加版號的話會拉下最新的版本，這裡的 ubuntu image 是 ubuntu 官方準備好，
並且放到 [docker hub](https://hub.docker.com/) 上面供大家下載的版本，是一套非常純粹的 ubuntu，映像檔最小化連 python 都沒有；
大家可以視自己的需求選擇其他的版本，像是 node 官方也有出自己含 node.js 的映像檔，python、django、mysql …都有對應的映像檔可以選擇。  

如果自己註冊 docker hub 的帳號，也可以把自己建構的映像檔上傳到 docker hub 上讓大家下載，不過我這篇不會介紹，有興趣的請自己參考[其他人的文章](https://larrylu.blog/share-image-on-dockerhub-ccb7d9b26fa8)

```bash
docker pull ubuntu:18.04 docker pull ubuntu
```

載好之後就可以在 docker image ls 或 docker images 看到 ubuntu 了：   
```bash
$ docker image ls
REPOSITORY TAG IMAGE ID CREATED SIZE
ubuntu 18.04 4e5021d210f6 3 weeks ago 64.2MB
ubuntu latest 4e5021d210f6 3 weeks ago 64.2MB
```

有了 image 就可以把 container 給跑起來，可以想像 image 就是把需要的檔案都拿到手裡，把 image 放到 container 裡面跑起來就會變得像一個真的作業系統一樣。  
docker run 可能是 docker 最複雜的指令之一，選項多到不可理喻，我們先從簡單的開始：   
```bash
docker run -it ubuntu:18.04 bash
```

執行一個 ubuntu 18.04 的容器，-it 讓 docker 打開虛擬終端機，並執行 bash，這時候我們就會進到 ubuntu 的 bash，可以從 lsb-release 裡面看到這真的是一台 ubuntu 的機器。   
```bash
root@e98deb8ccdaf:/# ls
bin boot dev etc home lib lib64 media mnt opt proc root run sbin srv sys tmp usr var
root@e98deb8ccdaf:/# cat /etc/lsb-release
DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=18.04
DISTRIB_CODENAME=bionic
DISTRIB_DESCRIPTION="Ubuntu 18.04.4 LTS"
```

開另一個 host 的終端機，用 docker container ls 或是 docker ps 也能看到它在運作：   
```txt
CONTAINER ID IMAGE COMMAND CREATED STATUS PORTS NAMES
e98deb8ccdaf ubuntu:18.04 "bash" 59 minutes ago Up 59 minutes inspiring_feistel
```

但這個 container 在我們下 exit 離開的時候，它也會跟著不見，要用 docker container ls -a 把執行中跟已經被關掉的 container 都列出來才會看到它。  
這多少顯示了 docker 隨開隨用，不用隨關的特性，下個 run 就開了一個，不用了它就被關掉了。  

於是我們可以在 run 的時候，改成這樣下：   
```bash
docker run -itd --name blogger ubuntu:18.04
```
首先是 -d 這個參數，會讓 docker 在背景把這個機器給開起來；--name 則是給機器一個別名，
這樣就不需要去動到前面 docker container ls 裡面的 CONTAINER ID，畢竟打名字還是比打 hash 的 hex value 簡單多了。  
下完這行 docker 會給出新產生機器的 hash value，docker ps 也可以看到：   
```txt
CONTAINER ID IMAGE COMMAND CREATED STATUS PORTS NAMES
35f40d006a5f ubuntu:18.04 "/bin/bash" 1 second ago Up Less than a second blogger
```
這時候我們可以用 exec 進到這台 container，這樣跟 run -it 的效果是一樣的，只是這次離開 container 之後它還是會繼續執行，
blogger 的位置換成它的 container ID 35f4 也可以，以下同：   
```bash
docker exec -it blogger bash
```

把它停掉可以用 stop 正常關掉這個 container 或是 kill 直接砍了它：   
```bash
docker stop blogger docker kill blogger
```
就算是關掉的 container 在 docker ps -a 還是看得到它，可以用 restart 把它開回來   
```bash
docker restart blogger
```

為了要用 ubuntu 的機器編譯，我們還要將外部的檔案放到 container 內部，docker 對應的機制可以用 docker cp，有點像是 scp 的下法：   
```bash
docker cp ~/server.py blog:/server.py
docker cp blog:/server.py ~/server.py
```

或者我們想要簡單一點，可以用 volume 的方式，這有點像是 virtualbox 裡面的共享資料夾，平時 container 跟 host 之間可以用這個資料夾互通有無，
而且就算 container 被刪掉了，這個資料夾還是會留著；詳細的 volume 介紹可以看[這篇](https://larrylu.blog/using-volumn-to-persist-data-in-container-a3640cc92ce4)，
我這裡是直接用它的第二種方式，直接在 run 的時候指定一個資料夾給 container：  
```bash
docker run -v ~/docker:/docker -it ubuntu:18.04 bash
```
就能在內部的 /docker 裡面看到 host 那邊 ~/docker 的檔案了：   
```txt
root@c518b1b9fd7b:/# ls docker/
Dockerfile
```
如果要用 docker 當個編譯工具的話，差不多是這樣就夠了，連續的指令打起來就是：   
```bash
docker run -v ~/docker:/docker -itd --name compile ubuntu:18.04
docker exec -it compile bash
root@c518b1b9fd7b:/# apt update ...
```
全新的 18.04 ubuntu 真的是超級單純，該裝的東西都要自己裝好，連 apt 都要自己 update，但我編譯下去它還真的編譯過了 WTF……到底 archlinux 是出了什麼問題…。  

本篇文章感謝強者我同學在新加坡大殺四方稱霸麻六甲海峽的志賢大大多加指導。 