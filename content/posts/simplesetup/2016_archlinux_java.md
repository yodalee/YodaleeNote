---
title: "archlinux 上使用archlinux-java 切換不同java 版本"
date: 2016-07-05
categories:
- Setup Guide
tags:
- archlinux
- java
series: null
---

Java 2014 年就推出java 8 了，從java 6 到java 8 共有三個版本的 java，各版本間無法相容，例如要開發Android 的話就要使用java 6，
而目前電腦上安裝的Eclipse Mars 2.0，看到java 6 就會作嘔回報：  
```txt
Version 1.6.0_45 of the JVM is not suitable for this product. Version: 1.7 or greater is required.
```
在Ubuntu 上開發時，可以使用[alternatives](http://lj4newbies.blogspot.tw/2007/04/2-jvm-on-one-linux-box.html)來切換不同的java 版本  
<!--more-->

這個問題至少一年前在archlinux 還沒有解決，記得那時候為了修android 的課程裝了AUR的java 6，後來要寫minecraft plugin java 6 就被我刪了  

幸好最近發現已經有解決方案了：[archlinux-java](https://wiki.archlinux.org/index.php/java#Switching_between_JVM)  

使用上很直覺，透過status 檢視目前安裝哪些java 版本：  
```bash
$ archlinux status
Available Java environments:
java-6-jdk
java-6-jre/jre
java-7-openjdk (default)
```

透過set 選擇要改用哪個版本：  
```bash
archlinux-java set java-6-jre/jre
```

因為這些動作都會改動 /usr 的內容，所以都需要super user 權限。  

當然 [wiki](https://wiki.archlinux.org/index.php/java#Package_pre-requisites_to_support_archlinux-java)
 上也有教你如何把java 打包成archlinux-java 接受的格式，不過一般人應該用不到這個：  