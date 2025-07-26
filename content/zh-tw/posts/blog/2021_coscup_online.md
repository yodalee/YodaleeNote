---
title: "第一次參加線上 COSCUP 就上手"
date: 2021-08-17
categories:
- LifeRecord
- hareware
tags:
- rust
- hardware
series: null
---

人生第二次參加 COSCUP ，上一次已經是在 2019 年的時候，當年的實體活動[心得在此]({{< relref "2019_coscup" >}})，
因為 2019-2020 太懶沒弄出什麼可以看的點子，2020 好像又因為什麼因素（八成是疫情）連實體活動都沒去，
今年也是因為疫情，整個活動直接變成線上的了。
<!--more-->

雖然是線上不過毫不含糊，照樣在兩天開出 14 軌多元的[議程](https://coscup.org/2021/zh-TW/session)，上知天文下至地理~~從外太空聊到行天宮~~，
議程長也使用 [StreamYard](https://streamyard.com/) 進行專業的直播，講者在會前都會進到測試直播間進行測試；
當天必須在指定時間登入直播間等議程長拉你進直播；為了因應當天網路不穩的狀況也要求講者可以的話先預錄演講的影片，no show 還可以有 backup 。

因為預錄的關係，我在 7/12-7/16 那周，工作下班就開始趕工投影片和預錄，這次感謝強者我同學 JJL 同樣幫我看投影片跟預錄影片，
依照大大的建議從 v1 修改到 v3 才定稿，雖然我把 v1 跟 v2 的影片都刪掉了，但我自己的評價的確是 v3 > v2 > v1，有看有 review 還是有差的。

這次投稿的題目是從去年十月左右執行到十二月的 Rust Gameboy emulator，下面是這次的投影片和影片的連結，想說都費力錄影片了，
演講當天也選擇直接播放影片而不是直播講解，這樣時間上比較好控制，我也樂得輕鬆（欸。  
其實如果看 2019 年我上場的[兩支影片](https://www.youtube.com/watch?v=NVIUcNt-R8s)，其實現場拍攝的畫面跟音質都比預錄的直播影片差上不少，
也許未來的 COSCUP，可以走向上傳影片都以講者預錄的內容為主，能提供線下觀眾更好的演講品質。

### 投影片
{{< rawhtml >}}
<iframe src="//www.slideshare.net/slideshow/embed_code/key/tHZ4qm2TjJgmeU" width="595" height="485" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" allowfullscreen> </iframe> <div style="margin-bottom:5px"> <strong> <a href="//www.slideshare.net/youtang5/gameboy-emulator-in-rust-and-web-assembly" title="Gameboy emulator in rust and web assembly" target="_blank">Gameboy emulator in rust and web assembly</a> </strong> from <strong><a href="https://www.slideshare.net/youtang5" target="_blank">Yodalee</a></strong> </div>
{{< /rawhtml >}}

### YouTube 影片連結
{{< youtube "LqcEg3IVziQ" >}}

### Blog 文章
* [Rust Gameboy Emulator]({{< relref "2020_rust_gameboy" >}})
* [Rust Gameboy Emulator Sprite/Joypad]({{< relref "2021_rust_gameboy2">}})
* [使用 Rust 開發 WebAssembly 程式]({{< relref "/series/使用-rust-開發-webassembly-程式">}})

----

這次因為是第一次線上舉辦，整體來說跟現場很不一樣，我那兩天的行程差不多都是：  
起床吃完早餐 -> 開始參加活動 -> 中午就近吃池上便當（兩天都是）-> 參加活動 -> 活動一結束就躺床上補眠小睡 -> 出去吃晚餐 -> 看奧運。  
雖然變成線上，無法午休又要一直專注在演講內容，其實跟在實體會場跑大地差不多累人，也因此活動一結束就斷電小睡，醒來吃完晚餐再接著看奧運。  

在線上的一個好處是可以瞬間參加多個議程軌，只要你螢幕夠大，~~拿出平常追 VTuber 的精神~~要開幾個視窗就開幾個視窗，但我個人是沒這麼做：  
1. 因為我的螢幕只有 17 吋，基本上看一個 youtube 就接近極限了。
2. 人腦天生就只能做一件事，不太可能開兩個視窗還能同時聽兩個演講，那只會什麼都聽不到。

這次 COSCUP 我專注的議程軌，第一天是自己有上的 System Software；第二天是 Hardware 議程軌；
中間偶爾會用休息時間跳去聽主議程軌（無法分門別類的最終歸宿）；或是去 COSCUP 建的 Gather Town 裡面隨便逛。  
這次在線上遇到的人就比較少了，不過有跟傳說中的呂行大大與 MrOrz 大大在 Gather Town 裡面開了同學會；
另外也有其他的演講者認出我是 Gameboy 的講者小聊一陣，但我相信 Gather Town 再怎麼樣還是很難取代實體的交流，特別是徵才活動的部分，不知道這次成效如何？

----

本次活動，我印象深刻的部分，應該是第二天的[硬體議程軌](https://www.ptt.cc/bbs/Tech_Job/M.1627103659.A.B1D.html)，
從開放原始碼的 FPGA、130 nm PDK、efabless 下線服務、人見人恨的魔改 Scala HDL（欸，等等。  
由於個人是電機出身又弄過微波，從 FPGA、下線流程到軟體都弄過一輪，這次的議程軌的內容都非常親切（Scala 除外），
有一輪議程在介紹整個下線流程的，從合成、佈線、佈 H tree、DRC/LVS 驗證，根本就像是在聽大學部的積體電路設計。

整場聽下來，我是覺得硬體目前仍然不脫由商業公司進行主導的局面，其實不光是硬體，就算是軟體也是如此，
多數的開源專案如 vscode 也是 Microsoft 在背後進行主導，才能這樣確定整體開發方向，快速回應社群需求，由專職設計師負責切割問題吸引社群進來參與。  
簡而言之還是執行的問題，不少開源軟體專案走一走就進到死胡同，缺乏主導讓社群無法參與，或是參與之後由社群做成一鍋大炒麵，愈改愈改不動。  
在成本更大的硬體，缺執行力的社群競爭力又會更低，軟體開源畢竟零成本專案跑不動就算了，硬體真的走下線那套誰敢試？  
這次公開的 openPDK 揭示了開源專案的驅動力，就是只夠拿到 130 nm 的阿公級製程，連台灣各大學電機系走 CIC 的都比它高級；
而這樣子的驅動力還是 Google 在背後整合的結果。

硬體因為初期投入成本的關係，會限制能投入的題目，一定要大到一個一定的程度，幾乎可以保證能獲得足夠收益才有投資硬體的必要，不然就是浪費沙子，
而題目大到這種程度就會有商業公司跳下來玩了；如果用開源硬體能解的問題太小、小到商業公司還不願意投入，又很難從成品回收成本。  
在某場演講裡講者宣稱他們的開源方案，硬體開發幾個月人時的工作，在幾天內達到做完，我聽完只覺得畫唬爛，
這麼有效的話檯面上的各大企業還不捧著錢搶購你們的解決方案，各豬屎屋養一堆專職設計、佈線、驗證的，哪可能驚天一筆把他們的工作都變不見？  

**正如軟體沒有銀彈，硬體也沒有**。

我個人預測，可見的未來所謂的開源硬體仍然會是由營利公司在背後主導，就如上面的連結就有毒舌網友對 quicklogic/lattice 的評論：
> 大概是lattice自己的軟體太弱打不過 Intel (altera) Xilinx，乾脆開源讓大家一起改演算法。發現社群比內部 RD 還好用，所以改口歡迎了。

我是覺得這個評論其實反映了部分的現實，開源社群的力量其實有點像一萬頭綿羊，數量很多、幾無成本但散成一團，需要好好引導才能有效發揮戰力；
公司的 RD 則比較像獅子，養起來很貴，但能深入專案中的困難問題進行探究。  
這次的研討會也看到，開源硬體工具鏈大量使用了來自軟體開發的概念，諸如版本控制、CI/CD 的整合，都是目前閉源工具鏈上比較少見的設計。  
如何才能結合兩者的優勢達到最強大的生產力，讓只有公司能碰觸到的最新議題能即時反應給社群，讓社群匯集的生產力能超越閉源公司 RD，
也許是未來硬體產業鏈與開源硬體社群需要一同面對的願景與挑戰。  
