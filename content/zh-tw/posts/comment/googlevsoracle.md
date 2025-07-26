---
title: "google為何輸給Oracle：判決書小整理"
date: 2014-05-16
categories:
- Comment
tags:
- Google
- Oracle
- Android
- Java
series: null
---

眾所矚目的Google vs Oracle在前幾日判決，Oracle逆轉勝了這一局，因為我覺得此案實在太過重要，所以筆者就下載了
[判決書全文](http://cdn1.vox-cdn.com/assets/4431835/13-1021.Opinion.5-7-2014.1.pdf)讀了一遍：  

配上早先其他來源的一些整理：  
<http://yowureport.com/?p=11928>  
<http://www.fosspatents.com/2014/01/api-copyrightability-to-be-confirmed.html>  

並整理重要的論點在此，雖然說有一堆專業用詞不知道怎麼翻，還請路過高手指教；本文歡迎任何人轉載，但請註明出處：
* [YodaLee Note](yodalee.me)

注意此文是判決書論點之整理，不代表yodalee之個人意見，yodalee的個人意見是 "開源碼萬歲 甲骨文去死" (誤)。  
<!--more-->

---

判決書的開頭就先解釋了Java, android, 前次判決的相關狀況，這裡就不再次說明，相信會來到這個垃圾 blog 的人的科技背景應該都不錯~~其實是版主自己懶~~。  

我們就從法律上來看，首先要先確立幾個背景：  

* source code, object code 的確受 copyright literal part 保護  
（不然你覺得copyleft是為何而起？）
* Google 承認Java API 為original and creative，法院也接受這個論述，也就是Java API的確構成copyright存在的要件
* google在android中逐字的複製37個API, 7000行程式碼

> google agrees that it uses the same names and declarations in Android

google複製了例如 `java.lang.math.max(int x, int y)` 這類的宣告，但重新實作了底層的implementation code。  
所以爭議點在於：**Google所複製7000多行的API，究竟是否屬於著作權法保障的範疇？**  
在此判決中認定API屬於保護範圍，並逐一駁回google的理由。  

google用了幾個說法，試圖認定Oracle的著作權為無效或android為合理使用等。  

### 1. API是否落入Merger doctrine?  

> Merger doctrine: idea, expression should be split   

當某個概念(idea)只能用有限的表達方式表達，則概念與表達融合，該表達變為不保護。  

例如：輪子是一個概念，你要做到 "輪子" 的東西必須是圓的(難道能做方的輪子嗎…)，所以你不能將圓形的這個表達方式設為保護範圍，並限制其他人使用類似的表達。  
此決定是決定於製造輪子的時候，而非有人被訴製造輪子的時候；假設今天方的輪子也是可以用的時候，製造輪子的那個人就擁有圓形表達的著作權。  
類似的案例，Nitendo曾展示多種不同加密卡帶的方式，因而取得卡帶加密方式的著作權。  

google主張 java API 的實作方式和 Java 的概念已結合，因此API無法計入著作權保護，而google自行譔寫真正受保護的implementation code，從而避開侵權問題。  
但Oracle在創作Java 時，並非只有有限種譔寫 API 的方式：Math.max 可以寫為 Math.maximum，
Android 可以用不同method分類方式，不同的命名選擇、不同的譔寫方式而達到同樣的效果，無法證明表達和概念是合一，使 merger doctrine 無法成立。  
唯一的例外是三個核心， java packages 的
* java.lang
* java.io
* java.util

不過google對此沒有特別主張。  

### 2. API為短句，無法保護：  

這就如先前整理所說，短句之集合為保護之對象。  

### 3. scene a faire doctrine

原創中必要的要素或習慣之物品不可為copyright:

> If they re standard, stock, or common to a topic, or if they necessarily follow from a common theme or setting.  - Apple Compute, Inc. vs. Microsoft Corp.  

比如要描述警察，你就描述警棍、配槍、制服、鎮暴水車，所以你不能對描述這些內容的文字主張copyright，要求別人描述警察時不能這樣描述。  

Google主張：
> 這37個API已經成為寫Java時不可拋棄的部分，因此37個API的copyright已消失。  

法院說：scene a faire 的概念並無法證明 Oracle copyright 消失，只能作為 Google 侵權之防守；
但google無法提出明確證據指出android使用這37個API是必要，這個論點在地方法院就被駁回。  

### 4. interoperability:  

google主張此舉是為了與Java相容。  

但interoperability並不表示著作權之消失，這裡使用的判決是Sony Computer Entertainment, Inc. vs Connectix, Corp.跟一個類似的案例。  
總之Connectix用反工程的方式，製作出能和Sony卡帶相容的遊戲機，被認定為合理使用，但不影響著作權的創造、原創本身；
而Google也顯然不是使用反工程的方式，了解Java 如何運作，再自行譔寫相關的執行程式；更進一步說，android上的程式和Java也稱不上相容。  

### 5. Fair Use:  
這就是惡名昭彰的"合理使用"，根據是107條：  

> for purposes such as criticism, comment, news reporting, teaching (including multiple copies for classroom use), scholarship, or research, is not an infringement of copyright.

例如我今天想要痛罵祭止兀是笨蛋，我用了他臉書上寫的文章，此時他不能主張著作權；這個部分需要個案討論，事實上fair use被稱為：  
> The most troublesome in the whole law of copyright  

這裡法院駁回google的理由是：  

android並非Java之'transformative'，如上，我要用祭止兀的照片提出評論或新聞使用，就幾不能有任何更動，而必預全部引用，並用於其他用途；顯然android並不合這個標準。  
同時google並非non-commercial的使用引用來的Java API，在實務上只要有營利性的行為，幾乎都會使合理使用的論述效力大幅下降。  

---

大概說到這裡，我知道這樣其實稱不上什麼整理，如果有人提出更多的問題，我會再整理判決書內的回應貼上來。  
看完判決，我覺得Oracle是佔在上風處，不過很有趣的，近十年來科技業最重要的兩個案件：Apple vs Samsung，Google vs Oracle  
贏家 Apple 跟 Oracle 保護了他們最重要的產品，但是卻輸掉了市場  
也許智財權與著作權在軟體的保護已經近乎無效，即使得到保護，卻不一定留得住顧客的心。  

ps. 然後我剛剛看到 TSMC 控告 Samsung 侵權案勝訴，嗯………… 