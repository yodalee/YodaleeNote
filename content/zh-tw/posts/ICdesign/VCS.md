---
title: "數位電路使用 VCS 模擬"
date: 2025-03-29
categories:
- verilog
tags:
- ICdesign
- VCS
- Synopsys
---

故事是這樣子的，早年我[寫 verilog 文章]({{< ref "/series/verilog introduction" >}})的時候，
以及直到最近如果我要做簡單的模擬，都是用 iverilog 當例子，但卻有以下兩點致命傷：
1. 效能不佳，近年改成編譯式後聽說有顯著加速，但我相信比起 verilator 和商用軟體還是慢上一截
2. 不支援 systermverilog 與 VHDL，這年頭寫純 verilog 真的是太痛苦了，
用 systemverilog 實作只用 iverilog 則無法模擬
<!--more-->

# 常見的商用模擬工具

而在業界，一擲千金的硬體當然不可能只用 iverilog 來進行模擬驗證，都會使用[商用的 EDA 軟體](https://en.wikipedia.org/wiki/List_of_HDL_simulators)；
目前我所知的工具包括下列幾個：
* Synopsys VCS：今天介紹的工具，可以倒出的 .fsdb 波形，並與 Novas（被 Synopsys 收購）的 Verdi 深度整合，
搭配 kdb 的 debug 方式，之前看同事使用仍然是我看過最快最有效率的。
* Cadence NCSim：Cadence Incisive 工具組的模擬引擎，我在學校的時候還用過它的 ncverilog 模擬器，
但這幾年重新學習下線的時候，已經被下一項的 Xcelium 所取代了。
* Cadence Xcelium：Cadence Incisive 取代 NCSim 的新一代模擬引擎，我自己使用有兩點小結，
  1. 模擬速度不錯，不輸甚至小贏 Synopsys VCS
  2. 第二是 Cadence 標準的 .tcf 格式，使用 Innovus 進行靜態功耗模擬時會需要。
* Mentor Graphics：ModelSim，我沒用過這裡就不提了
* Xilinx Vivado：這也有內建的 verilog 模擬器，但我幾乎不用，畢竟 vivado 的用處是合成 FPGA 不是跑模擬，
Vivado 太肥，開起來建專案只為了跑模擬實在太麻煩了。

如果只比前幾家（維基用了 big 3 這個名詞XD），Synopsys VCS 算得上一個無法忽視的存在，特別 Synopsys 
本身就是 Systemverilog 的主要設計者，VCS 對 Systemverilog 以及 ABV (Assertion-based verification),
VMM (Verification Methodology Manual) 的支援應該都是最佳的。

最近因為一些原因用了一陣 VCS 的功能，下面就來介紹一下怎麼使用這套商用的模擬工具吧。

# VCS 環境設定

首先是 VCS 的環境設定，在工作目錄下新增 synopsys_sim.setup 這個檔案。
1. 這步不是必要的，如果設計簡單不建 library（下面會提到），可以直接跑就好；但如果你想建 library，
這步沒設就會出現很難懂的錯誤。
2. 注意這次**不是隱藏檔**，這真的很謎樣，為什麼 Design Compiler 跟 PrimeTime 都是隱藏檔 VCS 卻不是…。

相關設定可以參考 VCS User Manual，VCS 使用的時候，可以像 C 函式庫一樣，把轉譯的硬體實作分到不同的 library 裡面，模擬的時候再整團連結起來。  
synopsys_sim.setup 就是記錄：現在這裡有哪些 logical library 並且被映射到哪些 physical library 上；只要使用同一個 logical library，修改 synopsys_sim.setup 指向不同的 physical library 即可抽換實作進行模擬。

最小的 synopsys_sim.setup 就是下面兩行：
```txt
WORK > DEFAULT
DEFAULT : ./WORK
```
意思是預設的 library 叫 DEFAULT，而 DEFAULT 生成的檔案會存在 WORK 資料夾內。  
這裡有另一個有趣的設計，logical library 是不分大小寫，但 physical library 因為指向實際的位址，所以要分大小寫~~Synopsys 嘛不意外~~。

如果不知道現下的 library 設定是什麼，可以使用
```csh
show_setup -lib
```
看到。

## 2-step

VCS 有兩種執行的方式，統稱為 2-step 或是 3-step，視模擬對象單純或複雜而定，以下介紹稱二階模擬和三階模擬。  
二階模擬為 Compilation (編譯) 和 Simulation (模擬) 兩階段，編譯將所有的硬體設計全倒進 VCS 裡生成 simv 
執行檔，模擬則執行 simv 進行模擬。  
這在背底應該是自行呼叫 vlogan 編譯 verilog/systemverilog 檔案，並儲存在 default library 內。

```bash
vcs [verilog files]
./simv
```

## 3-step flow

三階模擬則是分為 analyze、elaboration 和 Simulation。  
三階的設計是為了應對硬體設計不同的工具和語言，例如文件中 VCS 表列支援的就包括三套常見的硬體設計語言：
* Verilog (IEEE 1364)
* VHDL (IEEE VHDL 1076-1993)
* SystemVerilog (IEEE 1800 - 2012)
其他包括如 SystemC, DVE 等以進行協同模擬。

Verilog 與 SystemVerilog 可利用 vlogan 這套工具進行分析；VHDL 則使用 vhdlan 進行分析。
```bash
vlogan *.v
vlogan -sverilog *.sv
vhdlan *.vhd
```

這些檔案會被轉為中繼檔並存在指定的 library 內；一般我會給 vlogan 的 option 包括：
* -full64: 使用 64 bits 進行模擬（現在還有人用 32 bits 電腦跑 EDA 嗎）
* -kdb: 生成 Synopsys Verdi debug 用的資訊
* -work [logical lib]: 如果你要指定生成的 library 要放哪裡的話可以下這行
* -f filelist: 用 filelist 來提供要分析的檔案，對大專案很有幫助

如果下了 -work 但後面的名字不在 synopsys_sim.setup 的話，就會得到如下的錯誤
（再次提醒設定檔不是隱藏檔，Synopsys 你到底在搞什麼飛機），這時請記得在 synopsys_sim.setup 
內加上對應的 logical library：

```txt
vlogan -sverilog -full64 -kdb -work MYGO -f filelist.f

Error-[ILWOR] Incorrect Logical Worklib or Reflib
  The incorrect logical lib is "MYGO".  
  Please check your Synopsys setup file.
```

在 elaborate 階段，則是把剛剛已分析好的中繼檔轉成 simv，top module 可以指定 logical library 如 
`MYGO.test_chip_top` 或直接用 test_chip_top ，我在測試時兩者都能成功找到實作並進行模擬。
```bash
vcs -kdb -full64 -top test_chip_top
```

模擬就跟 2-step 一樣，呼叫 simv 執行檔即可。

## 使用 VCS 加密

除了模擬之外，VCS 也包含加密的功能，不過和它的模擬功能是分開的，流程是先把檔案從原始碼轉成加密檔案，再把加密檔案整個送去 VCS 進行模擬。  
注意這裡介紹的加密是 VCS 特有的，並不是 [IEEE1735](https://standards.ieee.org/ieee/1735/7237/) 
所定義的標準加密，加密過後的檔案只能交給其他人，他們只能再拿來跑 VCS 模擬，不能送去合成或其他用途。

VCS 加密的選項總共有四種：
* autoprotect：把整個檔案都加密只留下模組名稱
* auto2protect：不加密 port 的部分
* auto3protect：不加密 port 以及任何在 port 定義之前的 parameter
* protect：只加密檔案中在 `protect` 到 `endprotect` 中間的內容。

一般的操作如下：各檔案使用 autoprotect 全檔加密；top 則使用 auto2protect 保留介面讓使用者知道怎麼打訊號。

選項使用 +putprotect 和 +deleteprotected 讓 vcs 把加密後檔案集中到一個資料夾，並覆蓋已有的檔案。  
要注意的是加密並不會隱藏檔案的階層關係，因此使用者可能還是會從檔名知道你設計的架構，
真的不想被看的話用 cat 把檔案都合成一個也是可行的作法。
```bash
vcs +autoprotect +putprotect+mygo +deleteprotected -f filelist.f
vcs +auto2protect +putprotect+mygo +deleteprotected chip_top.sv
```

加密完一樣可以模擬，只是加密檔案的內容完全不會出現在波形檔上，auto2protect 的檔案只會看到介面。  

# TL;DR

講了這麼多，跟上次一樣，附上我執行加密以及模擬使用的 Makefile，加密之後檔名會從 .sv 變 .svp，所以會需要準備 filelist.f 跟 encrypted.f 兩套檔案表。  
當然，我自己在下線的時候是沒在加密的啦，都是用 2-step 直接跑模擬。

```Makefile

VLOGANOPTS = -sverilog -full64 -kdb -work MYGO

encrypt:
    mkdir -p mygo
    vcs +autoprotect +putprotect+mygo +deleteprotected -f filelist.f
    vcs +auto2protect +putprotect+mygo +deleteprotected chip_top.sv

analyze:
    vlogan ${VLOGANOPTS} -f encrypted.fp

elaborate:
    vcs -full64 test_chip_top -debug_access+all

simv:
    ./simv

```
