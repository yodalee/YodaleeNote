---
title: "在Archlinux 安裝arduino 開發環境"
date: 2016-09-20
categories:
- Setup Guide
tags:
- archlinux
- arduino
series: null
---

最近開始接觸arduino開發板，在archlinux 上開發arduino 也相當簡單，照著 [wiki](https://wiki.archlinux.org/index.php/arduino)做便是：  
<!--more-->

先用yaourt 裝arduino，然後把一般使用者加到uucp 跟lock 群組裡面，讓使用者可以取用serial 的權限：  
```bash
gpasswd -a $USER uucp
gpasswd -a $USER lock
```

再來登出登入就設定完了，打開arduino 就有介面可以使用了。  
![arduino](/images/posts/arduino.png)

另外有遇到一個問題，因為手上拿到的arduino 使用的是Intel Edison的板子，因此打開arduino 之後，要用它的board manager （中譯板子管理員）安裝Intel Edison 的板子。  

而安裝時會出問題，大致的錯誤訊息會類似這樣：  
```txt
Setting it up...find: invalid mode '+111'
/tmp/tmp.ioGoYaYhZu/relocate_sdk.sh /home/yodalee/.arduino15/packages/Intel/tools/core2-32-poky-linux/1.6.2+1.0/i686/relocate_sdk.sh
SDK could not be set up. Relocate script failed. Abort!
```
然後如果不理它直接去arduino 裡面編譯看看的話，會出現類似這樣的錯誤：  
```txt
$HOME/.arduino15/packages/Intel/tools/core2-32-poky-linux/1.6.2+1.0/i686/sysroots/x86_64-pokysdk-linux/usr/bin/i586-poky-linux/i586-poky-linux-g++: No such file or directory
```

總之在家目錄的超深的地方，某個g++ 檔案找不到，但如果你去它所寫的路徑看一下，它確確實實的就在那裡，直接在shell 下執行會得到一樣的結果。  
第一次遇到這個問題是在管工作站的時候，某個EDA 公司給的執行檔，也是怎麼跑都跑不起來，當下完全就是見鬼了，檔案就在那裡linux 你是跟我開玩笑嗎？
後來那個EDA 好像是給錯版本，忘了是32 bits 的工作站給了64 bits 執行檔，還是64 bits 工作站給了32 bits 執行檔，總之後來強者我同事解掉了。  

## 解法一（不完整，請用解法二）  
如果用file 去看那個執行檔就會看出一點端倪，裡面有這句：  
```txt
interpreter /opt/poky-edison/1.6.1/sysroots/core2-32-poky-linux/lib/ld-linux.so.2
```
意即這個執行檔需要這個dynamic linker來執行，而安裝時，這個路徑並沒弄好，因為在這個安裝包
（$HOME/.arduino/packages/Intel/tools/core2-32-poky-linux/1.6.2+1.0/i686）
下面沒有找到這個檔案sysroots/core2-32-poky-linux/lib/ld-linux.so.2  
因此解法就是在opt下面，用softlink連結1.6.1到i686 下面，編譯就能跑得起來了。  
上述工作站的問題也是類似，大概是忘了裝32/64 bits 的libc，在ubuntu的話應該要補裝libc6-i386 lib32stdc++6 等。  

## 解法二：  
這個才是正常的解法，在i686 資料夾下，會找到安裝時執行的script：install\_script.sh  
實際執行的話也會報錯，它在呼叫relocate\_sdk.sh裡面執行relocate\_sdk.py後會出錯，原因是給relocate\_sdk.py 參數太少了。  
後來查到[真正的原因跟解法](http://askubuntu.com/questions/764715/unable-to-install-intel-i586-library-intel-galileo-gen-2-in-arduino-ide-on-ubu)  

把install\_script.sh 裡面的  
```bash
executable_files=$($SUDO_EXEC find "$native_sysroot" -type f -perm +111 -exec printf "\"%s\" " {} \; )
```
的+111 改成 /111就行了，就是find 出錯導致executable\_files 沒找到檔案，
relocate\_sdk.sh 就沒把該修改interpreter 的執行檔傳給relocate\_sdk.py，最後就變成interpreter 還指向/opt 的狀況。  

確實去找manpage find，會找到這行  
```txt
-perm +mode
This is no longer supported (and has been deprecated since 2005). Use -perm /mode instead.
```
所以大概是這個script 太久沒維護了吧。  

## 後話：  
現在筆電的archlinux 自從我 2013/4/24 10:26:04 灌好之後，經歷了無數程式開發，無論系統程式、機器學習、Android、Arduino，從來沒讓我失望過，archlinux果然是不敗開發神機。  
至於我怎麼知道這個時間，是參考[這個](http://unix.stackexchange.com/questions/9971/how-do-i-find-how-long-ago-a-linux-system-was-installed)，
用tune2fs 去偵測例如root 或boot 分割區的創立時間，大致就是系統灌好的時間了。