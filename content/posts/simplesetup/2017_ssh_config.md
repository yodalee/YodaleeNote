---
title: "設定 ssh config 讓人生簡單一些"
date: 2017-07-29
categories:
- simple setup
tags:
- ssh
series: null
---

ssh 是工作上的重要工具之一，平時要連進其他電腦、傳送檔案、甚至是上 ptt 都可以用 ssh 達成，這篇文整理一些 ssh 的設定，可以讓 ssh 的使用更簡單一些。  
<!--more-->

## [免打密碼](https://blog.gtwang.org/linux/linux-ssh-public-key-authentication/)
這個如果有用 github 的話一定很清楚，簡單來說我們可以把電腦的公開金鑰放一份到遠端，登入的時候 ssh 就會不問密碼自動驗證。  

步驟如下：  
1. 在家目錄下的 .ssh 目錄中，鍵入 ssh-keygen 指令
    1. 預設是使用 rsa，如果覺得 rsa 不夠安全可能會被心算解開（誤，可以用 -t dsa | ecdsa | ed25519 | rsa 選擇要用哪種公開金鑰加密法
    2. 用 -b 來選擇生成的金鑰長度（不過我下了 ssh-keygen -b 16384 然後它金鑰生不出來…）  
2. 金鑰生成後，會詢問檔案要存在哪，預設就是 .ssh 資料夾
3. 問 pass phrase，我們都用上 public key 就是不想打密碼，除非有安全性考量否則留空即可  

```txt
Enter file in which to save the key (/home/garbage/.ssh/id_rsa): /tmp/id_rsa
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
```
會產生兩個檔案，`id\_[algorithm]` `id\_[algorithm].pub`，從檔名看 pub 自然是公開金鑰了。  

接著將 .pub 檔案的內容，複製到伺服器上 .ssh/authorized\_keys 裡面，如此一來 ssh 就能免密碼登入了  

## ssh config
ssh config 有點像 ssh 專用的 /etc/hosts，可以幫常連的機器設定別名，甚至是連線時要用什麼動作，以下來看看：  

首先，假設我們要連線一台電腦，remotemachine.com 或者是 ip，帳號名稱是 yolo，開的 port 為 9453，要連線要打入這樣的指令：  
```bash
ssh yolo@remotemachine.com -p 9453
```
當然如果照[這篇文章]({{< relref "2016_shell.md">}})安裝了 fzf ，某種程度上能大幅緩解連一台機器要打很多字的問題－－
連機器的指令不會變，用fzf 找出來就是了，但每次都用 fzf 來找還是會花一些時間，這時可以改用 ssh config  

在家目錄的 ~/.ssh/config 檔案中，加上以下內容：  
```txt
Host MyMachine
 HostName remotemachine.com
 User yolo
 Port 9453
```

ssh MyMachine 就會直接連上 yolo@remotemachine.com -p 9453  

這些規則不是寫死的，ssh 的設定優先次序是命令列、.ssh/config、/etc/ssh/ssh\_config，
設定後照樣可以用 another@MyMachine 來使用其他使用者登入，或者用 -p 來改變連線的埠。  

設定檔就是許多 Host 為開頭的區塊，內容為針對該 Host 的設定，上面展示的就是設定預設主機、使用者跟埠，還有許多其他設定可用，
像是認證檔的位置、選擇加密方式，詳細可以看 [man ssh_config](https://linux.die.net/man/5/ssh_config)。  

下面是我查到 ssh config 的契機，平常工作的地方開了一個新的工作室，但平常測試的主機A放在工作室A，兩個工作室的網段不一樣，沒辦法透過 ip 直接連線；
為了連線所以在 router 上面鑽一個洞，開一個 ip 會直接進到工作室A的另一台主機B，到主機B就進到內網，可以直連測試主機A。  
如果要打指令，大概會長得像下面這樣，等於是透過machineB ，開一個 pseudo-tty，再執行 ssh進到machineA：  
```bash
ssh -t userB@machineB.ip -p 9453 ssh userA@machineA.ip
```
要簡單一點找到[這個 stackoverflow](https://askubuntu.com/questions/311447/how-do-i-ssh-to-machine-a-via-b-in-one-command)，
關鍵字是ssh proxy，在 .ssh/config 裡面加上這些設定  
```txt
Host machineB
  Hostname machineB.ip
  User userB

Host machineA
  User userA
  ProxyCommand ssh -q machineB nc -q0 machineA.ip 22
```
ProxyCommand 指定要連到這台 Host 時要下的指令為何，這裡會用 ssh quiet mode ，再執行 netcat 接入machineA，這樣只要用 ssh machineA 就能完全上述工作啦  
當然這樣每次連線都要打兩次密碼，不想打密碼，照上面在機器上放入自己的公鑰即可。