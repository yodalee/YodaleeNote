---
title: "數位電路設計系列 - 數位電路設計系列 - Signoff"
date: 2025-11-16
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
images:
- /images/ICdesign/LVSpass.png
---

故事是這樣子的，無論是數位、類比還是微波電路，在晶片的最後一步，都要進行所謂的 signoff 流程，進行最終的檢查看看設計有沒有問題等等。

<!--more-->
一般的 Signoff 流程至少包括兩個：DRC 和 LVS，有些還會加上之前提過的 RC extraction (PEX) + Post-layout simulation，以及跟 LVS 整合的 ERC。

這段稱為 Physical Verification 或 Verification，同樣的三家大廠都會推自己的解決方案：
* Synopsys 的 [IC Validator](https://www.synopsys.com/implementation-and-signoff/physical-verification.html) 
* Cadence 的 [Assura Physical Verification](https://www.cadence.com/zh_TW/home/tools/digital-design-and-signoff/silicon-signoff/assura-physical-verification.html) 
* Mentor 有 [Calibre](https://eda.sw.siemens.com/en-US/ic/calibre-design/)

就我個人所知（至少快十年前的資訊），在這個領域，業界標準是 Mentor 的 Calibre
，在一線的晶圓廠下線，晶圓廠開始生產前的最後一步檢查也是用 Calibre 去跑。  
即便 Synopsys/Cadence 的工具也一直在進步，讓檢查速度更快、消除掉假錯、減少漏過的真錯，但結果還是以 Calibre 做標竿，沒能取代掉 
Calibre 最後一線的地位；箇中理由自然也很好懂，如果有錯誤沒檢查到，一片幾百萬的光罩你要負責嗎？

也因此，到目前為止，個人用過的工具就只有 Calibre ，沒用過 IC Validator 和 Assura，下面的整理就以 Calibre 為主。

# DRC

DRC 為 Design Rule Check 的簡稱，主要是在晶圓製造的時候，有些狀況會做不出來或導致良率下降，
用各金屬層的連線舉例是最常見的，檢查諸如：
* 線寬是不是會太寬、太窄，太寬了一大坨金屬會影響晶片的平坦度、太窄了線可能做不出來直接斷掉
* 線距會不會太近，太近了線會短路
* 金層層和 Via 間有沒有足夠的空間，讓 Via 長不整齊也能連接

當然 DRC 不止這些，還有像：
* 密度規則，例如以 100x100 um2 的區間，金屬密度是否太高或太低，密度太高會長不好，太低沒足夠支撐晶片可能會垮掉
* 天線規則，連接到電晶體的金屬面積會不會太大

諸如此類，都是為了晶片製作過程中，數百道的曝光、蝕刻、金屬沉積的製程誤差導致短路或開路，
造成晶片無法正常工作~~浪費沙子~~。  
當然，這年頭一顆晶片上塞的電晶體數量動輒用十億為單位，可能一層金屬就有幾十億到幾百億個矩形
需要檢查彼此間的關係，要如何又快又正確的檢查就是難中之難了。  

另一方面，先進製程也帶來更多的規則與更多的金屬層，例如古早味的 180nm 製程可能只有五層金屬，DRC 
文件幾百頁左右；40 nm 製程就膨脹到千頁，個位數 nm 的先進製程會多多少規則可想而知。  
也因此 DRC 其實非常浪費算力，就算是幾百核心平行跑，按下 enter 之後可能幾個小時才得到結果也是稀鬆平常。

## DRC 怎麼跑

首先，晶圓廠一定會提供他們的 DRC 規則檔，以下就稱它為 DRC.rule 吧。  
檔案內容可以分為四個部分，注意會改動的只有第一部分的設定，其餘除非你是寫 DRC 
規則的那位不然千萬別亂動，這篇文章也不會深入那些細節，有機會我再寫為說明：
* 設定
* 圖層定義
* 圖層運算
* 規則檢查

## 設定

設定參考如下，需要改的就關於輸入的部分，你的 layout 檔、top cell 名字跟格式（一般都 GDSII 也不用改）：
```tcl
LAYOUT PATH "layout/CHIP.gds"
LAYOUT PRIMARY "top_cell"
LAYOUT SYSTEM GDSII

DRC MAXIMUM RESULTS 1000
DRC RESULTS DATABASE "DRC.db" ASCII
DRC SUMMARY REPORT "DRC.rep" HIER

PRECISION 1000
RESOLUTION 5

FLAG SKEW YES
FLAG OFFGRID YES
FLAG ACUTE YES
FLAG NONSIMPLE YES
```

## 執行

就這樣，有什麼就跑什麼，DRC 通常包含整體規則和密度檢查；ANTENNA 則是單獨的天線規則檢查。  
加上 hier 和 turbo 選項讓它用階層式與多核心模式來加速。
```bash
calibre -drc -hier -turbo DRC.cmd
calibre -drc -hier -turbo ANTENNA.cmd
```

## DRC 報告怎麼看

依照上面的設定會生成兩種輸出：  
1. DRC.db 這類 ASCII 格式，可以在 INNOVUS, Virtuoso 等進行匯入，在 Layout 上檢視有哪些錯誤。
2. DRC.rep 則是文字格式，可以用文字編輯器打開它。

DRC.rep 會有幾個區段：  
**ORIGINAL LAYER STATISTICS**  
統計 calibre 從你的 layout 中，擷取出多少你定義的 LAYERw，這裡可以注意一下數量，例如我的結果：
```txt
LAYER M1 …… TOTAL Original Geometry Count = 881136
```

一般在全數位的 DRC，如果沒有一次過，原因大多只有一個：
> 匯出 gds 檔的時候圖層沒選對。  
{.warning}

M1 應該是 LAYER 100 但你選錯設定，INNOVUS 把它對應到 87，那 Calibre 在擷取 M1 時就會一個 Count 都沒有。

**RULECHECK RESULTS STATISTICS**  
這裡就是重中之重了，會列出每條規則的結果：
```
RULECHECK M1.A  …… TOTAL Result Count = 0
RULECHECK M1.B  …… TOTAL Result Count = 0
RULECHECK M1.C  …… TOTAL Result Count = 0
```

DRC 規則數量眾多，還會有一些錯誤是可允許的假錯，為了避免眼花漏掉不是 0 的數字，可以用 vim 
輸入 `/= [^0]` 直接搜尋檔案中結果不是 0 的規則。

我後來是直接寫 python script，直接幫我 grep 某路徑下所有的 .rep 檔。

```python
import os
import re

def grep_non_zero_lines(directory):
    # Regular expression to match the lines with non-zero values
    pattern = re.compile(r'RULECHECK.*?TOTAL Result Count = (?!0)')

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".rep"):
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        if pattern.search(line):
                            print(f"{file}: {line.strip()}")

if __name__ == "__main__":
    grep_non_zero_lines("result")
```

# LVS

LVS 是指 Layout Versus Schematic，也就是說 APR 軟體寫出的 Layout
，以及另外一套設計本身的示意圖 schematic，兩者進行比對是否相同。

一般來說單純的數位電路，用 ICC2 INNOVUS 這類工具從 verilog 幫你畫出來的，LVS 
應該都是直接 pass 的等級，工具出錯的機會很低的。  
但倘若你是類比、射頻或客製化等等，LVS 就會是個讓你頭大的東西了，網路上也不乏各種教你怎麼看 LVS 
錯誤的文章；如果我哪一年想不開回去手繪 layout 再來寫文教大家。

數位電路的 LVS 背後的流程如下圖所示：
![LVS flowchart](/images/ICdesign/LVSflowchart.png)

1. 從 APR 軟體中匯出的 layout，結合用到的 hard macro 與 Standard cell 成為最終的 layout CHIP.gds
2. Calibre 會讀入 layout，萃取出內部的 device，轉為 LAYOUT.spi 的 spice 連線表
3. 同樣從 APR 軟體中匯出帶 power/ground 的 verilog 檔
4. 利用工具 v2lvs 將 verilog 檔結合 hard macro spice、standard cell spice，輸出 source.spi
5. Calibre 比較 source.spi 與 layout.spi 兩者是否相符

hard macro spice 和 standard cell spice 當然也是晶圓廠提供，一般會叫 .cdl 檔。 

比較時 calibre 其實是在比較兩個 spice 檔是不是同構的，不過執行 LVS 時必須在 Layout 上用 text 
標上 top cell 的 Port，LVS 會用這些作為線索往下進行比較，頂層單元的節點是已知可 match 
的，所以跟實際的 Graph isomorphism problem 還是稍不一樣。  
與 DRC 一樣，現今電路動輒幾億幾十億顆電晶體的時候，光是把幾 GB 的 layout 
讀入、從中萃取所有的元件與走線再進行比較，實務上是不會到 DRC 這麼久，但也是一項耗費算力亟待加速的工程。  

## LVS 設定

與 DRC 相同，修改輸入的部分，這次會有 source 和 layout 兩組輸入，修改檔名、top cell 名跟格式：
```tcl
SOURCE PATH "SORUCE.spi"
SOURCE PRIMARY "top_cell"
SOURCE SYSTEM SPICE

LAYOUT PATH "CHIP.gds"
LAYOUT PRIMARY "top_cell"
LAYOUT SYSTEM GDSII

LVS REPORT "lvs.rep"
```

同樣的，如果是成熟製程與老練的晶圓廠，後續 LVS 高機率是不需要改動的，遇到 LVS error 再詳加研究即可。  

比較可能會動到的有下面這些，就先列一下：
```tcl
LAYOUT CASE         YES
SOURCE CASE         YES
LVS COMPARE CASE    NO  //YES
```
三個 case 確保所有的名字是否保留大小寫，以我的狀況，在 LVS.rule 裡面萃取的 device 名字叫 nmos；但
晶圓廠的 .cdl 中引入的 device 叫 NMOS；`LVS COMPARE CASE YES` 就會出現 LVS 錯誤。

```tcl
LVS POWER NAME "VDD"
LVS GROUND NAME "GND"
```
定義電源與接地的名字，如果你有多組電源就會需要這樣處理，另外接地有些人會用 VSS，也可以在此修改。

```tcl
LAYER M1 100
LAYER M2 100
…
LAYER MTOP 500
TEXT LAYER 550
port layer text 550
ATTACH 550 MTOP
```

這邊要注意的就是圖層了，跟 DRC 一樣，如果匯出的圖層錯了，那整個 LVS 鐵定會出錯。
上面的範例意思如下：
* 500 層是最頂層的 top metal
* 550 層是文字
* 指定 550 層為識別 top cell PORT 用的文字層
* 550 層的文字釘在 500 的 top metal 層上

如果你的 APR 工具沒有寫出 port text 的話，可以在 LVS.rule 內加上 `.include "ports.txt"`
，並填入下列的範例內容，自行標示各 port 的位置。
```tcl
# ports.txt
# LAYOUT TEXT <port name> <x-coord> <y-coord> <layer> <cell name>
LAYOUT TEXT "clk"   55.0  990.9 550 top_cell
LAYOUT TEXT "rst_n" 155.0 990.9 550 top_cell
```

## hardmacro spice 檔

執行 v2lvs 前，先要準備好 hard macro 相關的檔案，這邊只**憑印象**說明記憶體要怎麼處理。  
第一是 verilog 檔，使用[跟 APR 時一樣的]({{< relref "aprmaterial/#hard-macro" >}})
除了 header 之外其他都移除的 .v 檔。  
另一個是 library 檔，使用 spice 的 subckt 語法，要告訴 spice 我們有 hardmacro 這個子電路，
內部因為是黑盒子所以留白就好。

```verilog
module hardmacro (clk, cen, wen, addr, i_data, o_data)
  input clk;
  input cen;
  input wen;
  input [1:0] addr;
  input [7:0] i_data;
  output [7:0] o_data;
endmodule
```

上述的 verilog （容我稍微減少 port 寬度）就會需要一個如下的 subckt 宣告：

```txt
.SUBCKT hardmacro clk cen wen addr[0] addr[1]
i_data[0] i_data[1] i_data[2] i_data[3] i_data[4] i_data[5] i_data[6] i_data[7]
o_data[0] o_data[1] o_data[2] o_data[3] o_data[4] o_data[5] o_data[6] o_data[7]
.ENDS hardmacro
```

因為 array port 都需要展開，所以我也是寫一個 python script 來處理這個問題，要 parse verilog 
來自動生也不是不行，只是有點殺雞用牛刀。

```python
# Usage gen.py addr 2 i_data 8 i_data 8
import sys

def main():
    args = sys.argv[1:]
    if len(args) % 2 != 0:
        print("Arguments must come in pairs: <name> <num>")
        return

    for i in range(0, len(args), 2):
        name = args[i]
        num = int(args[i+1])
        lines = [f"{name}[{j}]" for j in range(num)]
        print("\n".join(lines))

if __name__ == "__main__":
    main()
```

## v2lvs

實際執行，使用 v2lvs 將你 INNOVUS 寫出的 CHIP_pg.v 檔轉成 netlist spice 檔。

```bash
v2lvs -b -s xxx.cdl -v CHIP_pg.v -v hardmacro.v -l hardmacro.l \
-s1 VDD -s0 VSS -o SOURCE.spi
```

有任何的 .cdl 檔就用 -s 匯入，它會變成 SOURCE.spi 的 .INCLUDE 並一起進行 LVS。  
-b 這個選項至關重要，如果你在 [synthesis]({{< relref "designcompiler/#compiletcl" >}}) 
時沒有設定 define_name_rules，design compiler 輸出的 .syn.v 會有反斜線的名字，這些會混淆
 v2lvs 的判斷造成後續的 lvs 的錯誤。  
`-s1 VDD 和 -s0 VSS` 會設定 VDD 與 VSS 為 spice 的全域變數，請填入你的電源接地名稱。

## 執行 lvs
直接執行就好，-spice 只是指定 calibre 把從 layout 中萃取出來的 spice 檔寫出來。  
我的經驗是這幾乎沒什麼用，LVS 的本質就是電腦做圖學的比較，這是人腦不擅長的領域，
數位電路動輒幾十萬幾百萬個元件，既然電腦都解不出來了，怎麼會覺得人腦看一看可以看出問題在哪？  

```bash
calibre -lvs -spice LAYOUT.spi -hier LVS.cmd  
```

## LVS 錯誤了怎麼辦

~~兩手一攤~~  
嚴格來說這是個大哉問，LVS 對的方法只有一種，出錯的方法卻有百百種，我也不是每種都遇過。
在學校做類比遇到的錯誤，現在已經沒印象也無法截圖說明。  
現在我們只談數位電路，一樣的說詞：*從工具出來的高機率不會出錯*，不要急著開始用肉眼對 LAYOUT.spi 跟 SOURCE.spi，或是在 APR 軟體上翻來覆去的，先懷疑是否有設定沒弄對。

以下是我統整(猜測)數位電路最常出錯的原因：

### 1. 圖層沒設對

這點重複很多次不多講了，從 APR 軟體匯出的圖層跟 DRC LVS 設定一定要對起來，對不起來直接 GG。

### 2. Port 沒設對

請檢視 LVS.rep 的 Top cell 的 Port 節，下方的 Port 數量一定要對得上，在 report 找
 `Initial Correspondence Points` 也能找到初始的 port list，請確認你的 port 都有找到。

```txt
******************************************************************
                             INFORMATION AND WARNINGS
******************************************************************
                Matched  Matched  Unmatched  Unmatched  Component
                 Layout   Source     Layout     Source  Type
                -------  -------  ---------  ---------  ---------
   Ports:            20       20          0          0
```

### 3. 大小寫比較設定
上面敘述過了，這個好像意外容易踩到，我建議是 source, layout 都要用 CASE YES，Compare 則看晶圓廠的檔案而定。

### 4. v2lvs -b
上面也敘述過了，我 v2lvs 沒設定 -b 的話會出現 Naming Error：
```txt
******************************************************************
                               INCORRECT OBJECTS
******************************************************************
  LEGEND:
-------
  ne  = Naming Error (same layout name found in source
      circuit, but object was matched otherwise).
```

其他 Error message 包括有 Net 對不起來：
```txt
*******************************************************************
                             INFORMATION AND WARNINGS
*******************************************************************
                Matched  Matched  Unmatched  Unmatched  Component
                 Layout   Source     Layout     Source       Type
                -------  -------  ---------  ---------  ---------
   Ports:            19       19          0          0
   Nets:          57080    57079          0          0
```

實際檢視 layout，會看到有一條線在 source.spi 那邊，名字多一條反斜線而被算成同一條，但在 layout 
上是被兩個 inverter 給切割開的。  
這個問題過去我都是自行合成，會設定 design compiler 的 define_name_rules 避掉這個問題，
這次第一次用別人合成的檔案做 layout 就踩到了，我個人懷疑用 Naming Error 找到所有的文章都是在討論這個錯誤。

## LVS 報告怎麼看

LVS 報告倒是沒什麼好看，如果覺得 lvs.rep 開頭的 warning 太多，可以使用 vim 開檔搜尋，一秒來到結果的位置：
```bash
vim +/OVERALL lvs.rep
```

所以希望大家都能輕鬆過 LVS，只要 LVS.rep 裡面出現這個笑臉就沒問題啦 =b。
![LVS pass](/images/ICdesign/LVSpass.png)

# Makefile

又到文章最後面的 Makefile 時間，以下是我執行 DRC 與 LVS 時使用的 Makefile。  
drc 和 antenna 會有下面的 watch，是因為 DRC 一般花的時間都很久，用 watch 配 ls 
監視結果資料夾有沒有產生輸出檔案，這樣就可以把視窗開著放一邊去做其他事 (X) 看動畫 (O)。

```makefile
drc: FORCE
  calibre -drc -hier -turbo_all DRC.rule
  # watch "ls -lh calibre_result/"

antenna: FORCE
  calibre -drc -hier -turbo_all ANTENNA.rule
  # watch "ls -lh calibre_result/"

v2lvs: CHIP_pg.v
  v2lvs -b -s TECH.cdl -v $< -s1 VDD -s0 GND -o SOURCE.spi

lvs: FORCE
  calibre -lvs -spice LAYOUT.spi -hier LVS.cmd  
```