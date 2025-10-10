---
title: "數位電路：使用 IP"
date: 2025-08-14
categories:
- ICdesign
tags:
- ICdesign
series:
images:
- /images/ICdesign/HardwareIP.png
---

故事是這樣的，在龐大的硬體產業裡，沒有一家公司能獨立打造一顆晶片，即便是 Nvidia, AMD 這樣 Tier-1 的公司，也有許多的設計是來自授權的 IP（Intellectual Property）。  
現代的晶片就像是堆 IP 積木一樣，每塊積木後面可能都是無數工程師的心血結晶，以及耗費鉅資驗證與最佳化的結果。  
<!--more-->

如果你要授權你的設計給別人，當然不可能把 RTL 白白奉上，不然買方直接看你的 code ，概念看懂再自己實作一份就行了。  
保護硬體智財權是如此重要，IEEE 甚至有一份 [IEEE 1735](https://standards.ieee.org/ieee/1735/7237/) 
在處理這件事，各大 EDA 廠的工具都會有對 IEEE 1735 的支援；現在最新版本是第二版，在 2023 年發佈的。

其背底的運作原理簡要來說是這樣子的：
1. 各 EDA 廠商，如果遵照 IEEE1735 的標準，會保留一份私鑰，並公開發佈對應的公鑰
2. 當我們 IP 廠要提供 IP 的時候，向 EDA 廠商申請公鑰，或是使用發佈出來的公鑰加密一支 AES 金鑰
3. 使用 AES 金鑰加密整個檔案，送給 IP 使用者

IP 使用者把加密檔案用 EDA 軟體開啟時，因為 EDA 軟體帶有各廠商的私鑰，可以解密公鑰加密的 AES 
金鑰，取得 AES 金鑰就能解密檔案。
而對於其他人，沒有私鑰就解不出 AES 的金鑰，從而做到保護實作的作用。

撇開理論不談，目前主流範例看到的，大多使用 RSA 公鑰密碼系統搭配 AES-128-CBC 模式，也曾爆發過[安全漏洞](https://www.ithome.com.tw/news/118076)，
當然這也不怪廠商，私鑰既然寫在軟體內，就一定是寫在某個地方，再不濟從記憶體裡面撈幾乎肯定撈得到，要有效緩解這個問題可能只能在解密時透過網路回原廠拿一把 key，但這樣就不能離線執行。

當然，目前這個漏洞比較沒那麼嚴重，但我認為主要靠的是行規而不是加密，加密或許增加了一些阻力，但不是滴水不漏，
當然，你可以去破私鑰，進而破解你花大錢買到的 IP，問題是接下來呢？  
要無償在網路上公開嗎？那是花我的錢讓大家用是做慈善嗎？  
偷偷私下授權嗎？你買了人家東西，過陣子開始授權同樣東西，賣你 IP 的人肯定直接報警…。  
之後整個產業都知道你會亂破人智財，誰還敢把東西給你用？

# 三種階層的 IP

如這篇參考文件[What is the difference between soft macro and hard macro?](https://asic-soc.blogspot.com/2007/11/what-is-difference-between-soft-macro.html) 所述。  
在硬體產業，根據在整個流程上的位置，大略把 IP 分成 Soft Macro、Firm Macro 與 Hard Macro 三種~~其實我也是寫這篇文才知道~~。  
在這篇攻擊 IEEE 1735 的論文[How Not to Protect Your IP – An Industry-Wide
Break of IEEE 1735 Implementations](https://arxiv.org/abs/2112.04838)中，有一張圖還不錯：

![DifferentIP](/images/ICdesign/HardwareIP.png)

簡而言之，Soft -> Firm -> Hard 就是一路和實際硬體綁得愈來愈緊，
Soft IP 還是 source code；Firm IP 已經轉為 Netlist；Hard IP 則已經是 Layout level 了。

## Soft Macro

在 Soft Macro 提供的即是可合成的 RTL 實作，只要有了可合成的 RTL，不管是 FPGA 還是下線成為 ASIC，Soft Macro 都能勝任。  
但 Soft Macro 也會有對應的缺點，因為 Design Constraint 是在合成時設定，使用者使用的製程不一定是你設計時設想的，
例如設計者可能用來相當厲害的函式庫，時序可以做到 100 MHz；但買家用的製程與函式庫卻不支援某些關鍵的運算，以致最後只能合成到 75 MHz
，這都是 Soft Macro 帶來的不確定性，所以最終的 PPA (performance, power, area) 等等都需要仔細檢查。

給 Soft Macro 時鐵定是需要加密的，我目前聽過的例外是 ARM 的授權，給的錢夠多你就可以拿到 ARM 的原始碼，
他也不怕你抄，反正你沒測試又有專利保護，拿到手你也不能幹嘛，改都改不動。

## Firm Macro

Firm Macro 指的是 RTL 經過合成，轉成 gate-level 的 netlist (連線表/網表)。  

在合成的時候會需要選定好製程，所以 Firm Macro 已經已經和製程綁定了。  
好處是 Firm Macro 已針對 Performance/Power/Area 進行最佳化，不像 Soft Macro 買家負責前端的合成，如果亂動到 Design Constraint，那就可能生出不合預期的電路。  
在 gate-level 時比較不擔心洩漏了，至少不太需要擔心從 gate-level 還原到 RTL。

其實這裡我一直有點疑惑，為什麼不能有一種…有點 generic 的製程，提供一些 common 的元件，總之先不要管 timing，
先把設計換成某種程度的 netlist，已經還原不出本來的 RTL。  
等到確定要使用的製程，再使用從這個 generic 製程轉換到實際的製程上，用實際的元件開始做時序、功耗、面積的最佳化？  
不過這麼多年都沒做到，大概是有什麼限制吧。

## Hard Macro

到了 Hard Macro 層級，提供的就是和和 IC 製造高度綁定的實作。  
一般人會遇到的 Hard Macro，就是 Memory 以及晶片的 pad 等，以記憶體為例，拿到的大概會有幾個：  
* behavior model 的 verilog 檔供你做模擬使用。
* 打包的 .lib 檔或是 .db 檔，讓你在合成的時候加上這個黑盒子，.db 檔會包含時序資料讓 Design Compiler 可以完成時序模擬。
* [LEF](https://en.wikipedia.org/wiki/Library_Exchange_Format) 檔，描述這個 IP 出 pin 的位置，以及電源是怎麼接的？
* GDSII，在 layout 中我們只會拿到 LEF 讓 Layout 軟體看著外型完成 Layout，最後送晶圓廠前，再匯入 GDS 取代 LEF 指定的位置完成 layout。

Hard Macro 已經完成 layout，從外面看就宛如黑盒子，除了 Performance/Power/Area，
也要注意每個 pin 的定義與時序，能夠修改的就只有 layout 時的位置與方向。  
到了 hard macro 這層也不需要特別考慮加密的問題了，除非使用者想要看著 layout 
把電晶體跟邏輯閘還原出來，well 像 6502 CPU 那樣幾千個邏輯閘應該還做得到吧。

# 各軟體的加密方法

各家 EDA 公司加密 IP 的方式，只要是 IEEE1735 是公訂標準大家都會支援，而有些公司如 Synopsys 也會自己搞一套加密。

以下是查到的列表，如果我用過的就在下面加上小節說明使用方式：
* Synopsys VCS Only
* Synopsys Design Compiler Only
* Xilinx Vivado
* Synopsys VCS
* Cadence Incisive (NCsim)
* Mentor Graphics Questa


下面隨我用過慢慢加上去：

## Synopsys VCS Only

可參考之前的 [VCS 文章]({{< relref "vcs#使用-vcs-加密" >}})，使用 autoprotect 選項就能完成加密了，加完密只供用 VCS 進行模擬，不能合成或給其他家廠商使用。

## Synopsys Design Compiler Only 

指令是 synenc，應該隨著買 design compiler 就會一齊附上了，使用起來很單純。
```
synenc *.v *.vp
```
加密之後就只有 design compiler 可以將檔案讀入，讀入後也會立即轉為 design compiler 的中介格式，無法還原出本來的 RTL code，無法送模擬也無法給其他廠商使用

## Xilinx Vivado

Xilinx FPGA 的合成軟體，讓你把 RTL 合成到 FPGA 上，它有實作[IEEE1735 的支援](https://www.amd.com/en/products/adaptive-socs-and-fpgas/intellectual-property/ip-encryption.html)。  
一般的 Vivado license 是沒有 IEEE1735 加密功能的，需要加密功能需向 xilinx_security_app@amd.com 提出申請，只有付費 standard version 能拿到加密功能。

由於這是 IEEE 1735 ，先在 Vivado 安裝資料夾內找到 Vivado 的 public key，路徑在：
```txt
/Vivado/<version>/data/pubkey
```

接著準備 keyfile.txt：

```verilog
`pragma protect version = 2
`pragma protect encrypt_agent = "XILINX"
`pragma protect encrypt_agent_info = "Xilinx Encryption Tool 2022"
`pragma protect begin_commonblock
`pragma protect control error_handling = "delegated"
`pragma protect control runtime_visibility = "delegated"
`pragma protect control child_visibility = "delegated"
`pragma protect control decryption=(activity==simulation) ? "false" : "true"
`pragma protect end_commonblock

`pragma protect begin_toolblock
`pragma protect rights_digest_method="sha256"
`pragma protect key_keyowner = "Xilinx"
`pragma protect key_keyname= "xilinxt_2021_07"
`pragma protect key_method = "rsa"
`pragma protect key_public_key
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvyr1vj1oMct1BYueFRx0
/cf6aPkgzIjCFpPHosRvAsY1i7yjxwdWIdY441tDTTq+UAynD/CU79R/86JXIZct
heAebBBkOyeT5DwZijkvXtkOeY+0d1QFU+DFhlBo6Dv92e3F5XFyDHLms40HdSMK
7cL7z6TaT2YuKTxmr7qnUq87sfTTpbUu6LImP6jML3F3pAe8FDNRvLHxPha5lQAV
usx1MB/T9Iruf4868T2BqMJCWjAFaZK6V3OnKhhFKFXKtK+zpWqVN7XWqORxW7L/
97pZhLiVE5COh22lTbEBEfZGHYzZwlHaIFGCHVxkV+pGRF3ng00bHRko9asLI/qn
lQIDAQAB
`pragma protect control xilinx_configuration_visible = "false"
`pragma protect control xilinx_enable_modification = "false"
`pragma protect control xilinx_enable_probing = "false"
`pragma protect control xilinx_enable_netlist_export = "false"
`pragma protect control xilinx_enable_bitstream = "false"
`pragma protect control xilinx_schematic_visibility="false"
`pragma protect control decryption=(xilinx_activity==simulation) ? "false" : "true"
`pragma protect end_toolblock = ""
```

第一部分是 commonblock，內容是 IEEE 1735 公訂，大體是控制加密檔案在使用時可以有什麼樣的行為，
各個選項的意思就請參考 Xilinx 的網頁[Common Block Definition](https://docs.amd.com/r/en-US/ug1118-vivado-creating-packaging-custom-ip/Common-Rights?tocId=JDVugHeJbZpDPygnA6f8~A) ，
其實我覺得相比 Synopsys, Cadence 跟 Mentor Graphics，AMD 的說明文件根本業界良心了。

第二部分是 toolblock，這就是給加密工具看的，包括設定加密法為 rsa，然後公鑰的內容是什麼，因為標準的關係，似乎不能選其他的加密方式。

最後是工具自有的一些權利，像是能不能寫出 netlist？能不能寫出 bitstream 
等，詳細一請參考 AMD 自己的文件[AMD Tool Rights](https://docs.amd.com/r/en-US/ug1118-vivado-creating-packaging-custom-ip/AMD-Tool-Rights)。

接下來就能使用 vivado 進行加密了：

```tcl
# encrypt.tcl
encrypt [‑key <arg>] ‑lang <arg> [‑batch <arg>] [‑ext <arg>] [‑quiet]
    [‑verbose] [<files>...]
```
* -key 就是給上面寫的 keyfile.txt
* -batch 指定 filelist.f，把所有想加密的檔案寫在裡面
* -ext 是寫出檔案的 extension，如果不指定 vivado 就會把原本的檔案蓋掉，建議加密 .v 改成 .vp，加密 .sv 改成 .svp，Vivado 匯入時才能正確辨識檔案型態。

執行時可以在 shell 執行
```bash
vivado -mode batch -source encrypt.tcl -nolog -nojournal
```

後面兩個選項純粹不想要 vivado 到處生 log 檔和 journal 檔，如果要除錯的話打開也是可以的。
如此一來就能獲得一批加密的檔案了。
