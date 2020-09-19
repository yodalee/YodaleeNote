---
title: "在Archlinux 上安裝mariadb筆記 (Install mariadb on Archlinux)"
date: 2017-02-14
categories:
- simple setup
tags:
- archlinux
series: null
---

最近在我的Archlinux 上面安裝MySQL，結果撞了一堆牆，在這裡筆記一下過程，希望有機會的話能幫到其他使用者。  
<!--more-->

步驟就是照著[wiki](https://wiki.archlinux.org/index.php/MySQL) 所講，一步一步往下做：  

首先因為Archlinux 已經改用mariadb ，MySQL 移去AUR，不過我試過，用yaourt -S mysql 也會裝mariadb ，一個由不得你的概念。  
```bash
sudo pacman -S mariadb
```
使用mysql\_install\_db 設定好/var/lib/mysql  
```bash
mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
```
用systemd 啟動mariadb service  
```bash
systemctl start mariadb
```
最後可以用mysql\_secure\_installation來進行安全設定  

我在start mariadb 這步遇上問題，service 總是起不來，出現類似這樣的訊息，要不就是start mariadb 直接hang住：  
```txt
Job for mariadb.service failed because the control process exited with error code.
See "systemctl status mariadb.service" and "journalctl -xe" for details."
```
使用systemctl status mariadb.service 之後，它會列出哪行指令出了錯，我記得沒錯的話是 /usr/sbin/mysqld，總之它開不了 /var/lib/mysql 中的某些檔案。  
後來發現原因是，在安裝mariadb 的時候，理論上它要加上mysql 這個使用者，但原因不明的沒有加上去，因此我們要手動幫它補上：  
```bash
groupadd -g 89 mysql
useradd -u 89 -g mysql -d /var/lib/mysql -s /bin/false mysql
chown mysql:mysql /var/lib/mysql
```
然後重跑上面的mysql\_install\_db，就能順利的把mariadb 跑起來了