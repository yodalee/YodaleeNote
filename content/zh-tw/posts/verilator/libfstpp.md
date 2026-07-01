---
title: "讓 Verilator 倒波形快還要更快"
date: 2026-02-15
categories:
- verilog
- verilator
tags:
- verilator
- fst
---

Verilator 是目前開源乃至於硬體免費仔（欸）的第一首選，雖然它在使用方式上相對複雜，
但你想它身為開源工具，完整支援 systemverilog ，還能有這麼快的模擬速度，到底還有什麼好嫌的呢？

<!--more-->

# verilator fst 出了什麼事？

最近故事是這個樣子的，三個月前強者我同學 JJL 跑來找我，說它發現 verilator 開啟倒 fst
功能的時候，會跑超級慢，可以慢到 15-20 倍的那種慢。  
進去 profiling 之後，發現原因是 Verilator 在倒波形時使用的是 gtkwave 提供的 [libfst](https://github.com/gtkwave/libfst)
，撇開它是用 C 寫的而混雜一堆 memory management 這點不談，這個 library 在 API 
設計上有點…微妙，在主要接收資料的 EmitValueChange 
方面，它要求接收變數時的格式，用的竟然是**字串**的 `0` 跟 `1`。

所以如果要寫入一個 64 bits 的 integer，它就會先執行下列的迴圈：
```c
char buf[64];
char *s = buf;
uint32_t i;
for (i = 0; i < bits; ++i) {
    *s++ = '0' + ((val >> (bits - i - 1)) & 1);
}
```
你看看這都什麼東西…  
因為它介面如此，verilator 在呼叫這個 API 的時候也會做同樣的事，要先把 primitive type 
轉成 char pointer 再傳，為此還用 [AVX512 指令](https://github.com/verilator/verilator/blob/master/include/verilated_trace_imp.h)
把資料轉換成 0/1 字串；但就算用了 AVX512 這樣把資料用 char 灌進去，libfst 又把 char 轉回 binary 
存進 fst 就很沒效率，難怪 performance 直接變 20 倍慢。  

不過平反一下，他們會這樣做一部分原因是來自於 VCD，因為 VCD 就真的是用 char 去存 0/1
，大概是保留了本來的介面才變成這個樣子。

# 工作記錄

強者我同學 JJL 都這麼說了，當然是義不容辭的 +1，於是開了
[verilator_snapshot](https://github.com/yodalee/verilator_snapshot)
這個 repository。
裡面先把 verilator 編譯時用的環境整個冷凍起來，用之前寫的
[RSA256](https://github.com/yodalee/rsa256)
作為 testbench，為了測試的正確性，也實作了一個 simple 的模擬，用 gtkwave 打開來對答案。

做這個 project 最麻煩的是缺乏參考資料，關於 fst 波形檔的資料少之又少，甚至連維基條目也沒有，
也不知道是哪個喪心病狂~~辣手摧花喪心病狂無恥卑鄙變態殺人魔~~的人創造了這個有病的格式。  
網路上只有這位 timhutt 寫了一個 [fst 規格的完整介紹](https://blog.timhutt.co.uk/fst_spec/)
，算是我們這次改寫中可以拿到最完整的參考了。

為了驗證想法， JJL 先用 python 寫了一個
[fst parser](https://github.com/Timmmm/fst_spec/tree/master/sample_code)
，fst format 不像 VCD，是用 binary 的方式儲存格式，還會配上
 lz4, gzip, fastlz 等等壓縮演算法，沒有 parser 輔助的話真的很難除錯。  

在幫我們的 Writer 除錯的過程，也陸續發現幾個 fst parser 在處理波形上的問題，也發了 PR 給原作者，包括：
* Wave_table 可以不壓縮 [#6](https://github.com/Timmmm/fst_spec/pull/6)
* 文件在 endian 上有不確定的地方，測試過後就幫他 update 了例子 [#7](https://github.com/Timmmm/fst_spec/pull/7) 
* 因為 iverilog 用了 GZip 就順手支援所有的壓縮格式 [#9](https://github.com/Timmmm/fst_spec/pull/9)
* Hierarchy 長度是用 varint 存而不是 u64 [#10](https://github.com/Timmmm/fst_spec/pull/10)

# 實驗

在完成幾個比較簡單的 cases 之後，也陸續加上更多 cases，包括一些真的很大的。  
我們 testcase 主要的來源是 [rtlmeter](https://github.com/verilator/rtlmeter)，最後入選的有：
* [vortex mini sgemm](https://github.com/vortexgpgpu/vortex)
* [OpenTitan SHA](https://github.com/lowRISC/opentitan)
* [NVDLA gnet](https://github.com/nvdla/hw)

當然還有更大的，例如 vortex huge sgemm，verilator 跑完之後會生出 **5.9 GB** 的 cpp 
檔案進來編譯，但編完執行可能要跑個幾小時，就先把它從測試行列中取消掉。  
入選之中 NVDLA 是最大的，大概有 500,000 個變數需要儲存，不過出人意料的，實驗結果如下：

| Benchmark           |  No FST (A) | GtkWave FST (B) | This FST (C) | Speedup(B-A)/(C-A) |
|:--------------------|--------:|------------:|---------:|------------------------:|
| picorv32            |    78.4 |      1287.7 |    825.9 |                   1.62x |
| vortex:mini:sgemm   |  7436.3 |     44722.4 |  35042.3 |                   1.35x |
| OpenTitan:sha       | 96603.1 |    193932.0 | 173746.4 |                   1.26x |
| NVDLA:gnet          | 46930.4 |    259299.0 | 258489.8 |                   1.00x |

發現 design 愈大的時候，能吃到的加速紅利就愈小，甚至在剛完成的時候，我們的實作還會比 gtkwave 
的 C 實作還要慢。  
原因是大型設計的變數多很多，要儲存一個變數的內容，光是把對應的儲存處找出來就會先觸動到 cache miss
，去記憶體拉資料的時間就把整個模擬給卡死。  
也就是說瓶頸落在 CPU 在等記憶體的時間，直接掩蓋了把資料從數字轉成字元的時間，把加速的效果全吃了，
這應該是我第一次遇到 [cache miss](https://vocus.cc/article/690b7860fd89780001083c3c
) 能造成如此大影響的程式，太可怕了。

JJL 的評論：
> 倒波形的本質上就是一大堆波形記憶體，直著寫橫著讀

理論上如果有個很大的 cache，例如在 AMD 的 X3D 
處理器上跑，也許有機會觀察到顯著加速，不過第一我們手邊沒有 X3D
，第二隨著設計更大，L3 Cache 還是會被吃光回去拉記憶體。

# 怎麼辦？

為了讓我們的設計無論在大小設計上都能達到應用的效能~~為了證明C++不會比C還要爛~~，
我們還是努力去改進了，最後還是靠 JJL 的巧手，想辦法縮小一個變數所需要的記憶體尺寸，本來是：
* 存資料 vector 24 bytes 
* 儲存上一個寫入的資料 4 bytes，用來計算差異
* 資料寬度 2 bytes
* 是否為 real data flag 1 bit
總共會佔 32 bytes

新版直接把 std vector 拔了，改成手動控制記憶體：
* byte pointer 8 bytes
* 現有記憶體長度、上一個寫入的資料、寬度、real data flag 就全部塞進另一個 8 bytes 去處理

經過這樣的改良，成功在大設計上把速度拉到比 gtkwave 還要快：

| Benchmark           |  No FST (A) | GtkWave FST (B) | This FST (C) | Speedup(B-A)/(C-A) |
|:--------------------|------------:|----------------:|-------------:|-------------------:|
| picorv32            |        72.3 |          1492.2 |        489.6 |              3.40x |
| vortex:mini:sgemm   |      7436.3 |         44871.8 |      31336.3 |              1.57x |
| OpenTitan:sha       |     96603.1 |        193932.0 |     166178.0 |              1.40x |
| NVDLA:gnet          |     46930.4 |        244540.1 |     226628.9 |              1.10x |

而為了追求性能，這樣的設計也是有妥協，例如資料寬度只用 12 bits 儲存，所以只能支援最多 4096 bits 
寬的資料，但說實話，一般資料寬度也很難到 4096 bits 
以上，這麼寬的暫存器沒法真的拿來做什麼，應該沒有人瘋到會開 4097 bits 的乘法器…吧？  
就連加法器吃掉的面積跟對時序的影響大概就來到無法承受的等級了，
我們討論是覺得，在模擬器上不支援這麼大的資料寬度也是沒關係的。

# 結語

這個專案在寫完這部分之後就交還給 JJL [讓他去跟 verilator 交涉](https://github.com/verilator/verilator/issues/6871)
，看看能不能在下一代的 verilator 中推出，也跟 gtkwave 的官方搭上線，讓他們開了一個 [libfstwriter](https://github.com/gtkwave/libfstwriter)
 的 repository 來管理新版的 fst writer。

最後，我想說一下最近一個很夯的話題，也就是 *AI 時代工程師該如何自處？*

理想上的 AI 應該是一句話：

> 幫我寫一個 FstCpp 可以寫出 fst format 的波形檔，接上 Verilator 的 EmitValueChange API

然後他就會去找資料研究 fst 格式，研究 Verilator API 做了什麼，然後開始規畫 Writer 要長什麼樣子……

但現實自然不會這麼美好，誠然這個專案大量使用 AI 在輔助工作，舉凡建立 Github CI
、建立測試、填入測試等，都是請 AI 直接幫生；JJL 也自述都用 AI 幫忙 refactor，請 AI 
幫忙生成修改文件並整理內容跟 verilator 原作者進行交涉，。

但侷限還是很多，fst 這個格式千瘡百孔，參考資料少之又少的情況下，fst 這個詞對 AI 一點意義也沒有，
即使我們先把 timhutt 寫的文件都倒給 AI，那樣混亂的文件仍然無法導正 AI 的方向，
很多格式的細節要如何處理還是要人類先指定，再請 AI 動手。  
為了加速而對資料格式進行調整，這類細節超出 AI 的理解範疇，是透過手動增加大單元測試才察覺問題。  

AI 可以很快速的新增測試，但若遇到設計上的 API 更動，即使有 AI 還是形成 show stopper 
需要人力介入；又如我們在寫出 fst 檔案所需記憶體時，算錯數字以致 fst2vcd 無法正常解析而 crash，也是花了一個人日的時間去除錯 fst2vcd 的實作到底出了什麼問題。

在一個架構已經完善的領域，Best Practice 已經為人所知或是需求並不要求 Best Practice，
諸如 App、UI、網頁伺服器架構、遊戲設計等地，AI 絕對能大殺四方完爆人類；
而在那些冷門領域的重構，就連有興趣的人都如鳳毛麟角，現有的解決方案光是存在就已經是奇蹟的地方，
AI 大體還沒有能力插進來。  
而識別問題、基礎的剖析與除錯、了解各式設計的優劣之處及其原因，仍然是 AI 難以取代的的關鍵部分，
也是 AI 時代仍然需要的關鍵技能。

不過真要我說的話，我十分歡迎 AI 進場設計一個全新的波形檔格式把 fst 給替換掉，或是用 AI
逆向一下 FSDB VWDB 等大廠格式出來讓大家用，造福一下只能用 fst 這有病格式的開源硬體界。