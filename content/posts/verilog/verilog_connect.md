---
title: "接線接起來 - verilog 接線工具簡介"
date: 2024-12-28
categories:
- verilog
tags:
- verilog
- verilog-mode
- verilogpp
---

故事是這樣子的，在實作硬體的時候，verilog 大多是第一選擇（至少在亞洲區跟美洲區是這樣，VHDL那是另一個故事了），
而 verilog 作為古老的硬體設計語言，從各角度上來看都不足以稱為一款足夠現代的語言，整體的撰寫邏輯上仍然相當不抽象，
即便是細微的修改都可能導致大量的修正工作，即便透過 SystemVerilog 引入些許改進，
受限於開發工具（特別是開源相關的工具）與標準的匱乏，許多有用的功能仍然相當受限。

<!--more-->

在 verilog 開發中，有一部分需要大量時間的工作就是接線，也就是將設計好的子模組，在上層模組
（下層 top module，儘管它們不一定是真的最頂層的模組）中實例化，每個模組的 input, output port 要宣告接到某些線，
這些線會通往 0/1 固定值，連接到其他子模組，或是變成 top module 的 input, output port，以 RSA256.sv 模組，
省略掉模組中的邏輯如下所示：

```systemverilog
module RSA (
  input clk,
  input rst_n,
  input i_valid,
  output i_ready,
  input RSAModIn i_in,
  output o_valid,
  input o_ready,
  output RSAModOut o_out
);

KeyType msg, key, modulus;
logic i_en;
logic s1_i_valid, s1_i_ready;
logic s1_o_valid, s1_o_ready;

Pipeline pipeline_input (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(i_valid),
  .i_ready(i_ready),
  .o_en(i_en),
  .o_valid(s1_i_valid),
  .o_ready(s1_i_ready)
);

IntType power;
assign power = MOD_WIDTH * 2;
KeyType packed_val;
logic dist_valid[2], dist_ready[2];
logic comb_valid[2], comb_ready[2];

logic s1_en;
KeyType s1_msg, s1_key, s1_modulus;

PipelineDistribute #(.N(2)) i_dist (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(s1_i_valid),
  .i_ready(s1_i_ready),
  .o_valid(dist_valid),
  .o_ready(dist_ready)
);

Pipeline pipeline_stg1 (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(dist_valid[0]),
  .i_ready(dist_ready[0]),
  .o_en(s1_en),
  .o_valid(comb_valid[0]),
  .o_ready(comb_ready[0])
);

TwoPower i_twopower (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(dist_valid[1]),
  .i_ready(dist_ready[1]),
  .i_in({power, modulus}),
  .o_valid(comb_valid[1]),
  .o_ready(comb_ready[1]),
  .o_out(packed_val)
);

PipelineCombine #(.N(2)) i_comb (
  .i_valid(comb_valid),
  .i_ready(comb_ready),
  .o_valid(s1_o_valid),
  .o_ready(s1_o_ready)
);

RSAMont i_RSAMont (
  .clk(clk),
  .rst_n(rst_n),
  .i_valid(s1_o_valid),
  .i_ready(s1_o_ready),
  .i_in({packed_val, s1_msg, s1_key, s1_modulus}),
  .o_valid(o_valid),
  .o_ready(o_ready),
  .o_out(o_out)
);
```

這裡我們只實例化五個模組，在稍有規模的 verilog project，top module 實例化 10-20 個模組也不算太少見，
這會需要花費大量的工夫在接線上。

這篇文章我們就來介紹兩個開源的接線方案，兩者的功能大同小異，使用者可以在 verilog code 中插入註解，
工具自動剖析模組檔案，透過接線命名判斷哪些模組需要連接在一起，哪些線接到 top module 的 input/output，
哪些又需要額外宣告，以及它們宣告的型別，兩款分別是：
1. [emacs verilog-mode](https://veripool.org/verilog-mode/)
2. [google verilogpp](https://github.com/google/verilogpp)

兩者都是開源工具，誤接或是更大的問題一定有，下面介紹後就會一併列出，我想在商用上一定有更完整的解決方案，
就我所知的話 G 社裡面應該也有比 verilogpp 更完整的工具可以使用。  
這也是沒辦法，畢竟自己實作過 verilog 就會覺得它根本一團爛泥…要什麼沒什麼，
真虧大家可以用這種東西打造出產值幾兆美元的硬體產業。

# verilog-mode

## Install
首先 verilog-mode 是一套 emacs 下的巨集工具，所以必須先裝 emacs。  
直接來到 [verilog-mode github](https://github.com/veripool/verilog-mode)，使用 ELPA 的方式進行安裝。  

## Comment Format

verilog-mode 使用方式，可以參考這篇 [Emacs verilog-mode 的使用](https://www.wenhui.space/docs/02-emacs/verilog_mode_useguide/)
，我的經驗有用到的就下面五個：

* /\*AUTOINPUT*/ 生成 top module 的 input port
* /\*AUTOOUTPUT*/ 生成 top module 的 output port
* /\*AUTOREG*/ 生成 top module 接線需要的 logic
* /\*AUTOWIRE*/ 生成 top module 接線需要的 wire
* /\*AUTOINST*/ 實例化每個子模組

操作也不用記什麼，用 emacs 打開文件：
1. Ctrl+C Ctrl+K 把生成內容全砍掉
2. Ctrl+C Ctrl+A 重新生出內容
3. Ctrl+X Ctrl+S 存檔
4. Ctrl+X Ctrl+C 關掉檔案。

不想記也沒關係，用滑鼠點也可以，準備好要讓 verilog-mode 接線前的檔案會長這樣：

```systemverilog
import RSA_pkg::*;

module RSA (
  // input
  input clk,
  input rst_n,

  input RSAModIn i_in,
  output RSAModOut o_out,

  /*AUTOINPUT*/
  /*AUTOOUTPUT*/
);

IntType power;
assign power = MOD_WIDTH * 2;
KeyType msg, key, modulus;
logic i_en;
logic stg_en;

/*AUTOREG*/
/*AUTOWIRE*/

/* Pipeline AUTO_TEMPLATE (
  .o_valid(s1_valid),
  .o_ready(s1_ready),
  .o_en(i_en),
);
*/
Pipeline pipe1 (/*AUTOINST*/);

/* PipelineDistribute AUTO_TEMPLATE (
  .i_valid(s1_valid),
  .i_ready(s1_ready),
  .o_valid(dist_valid),
  .o_ready(dist_ready),
);
*/
PipelineDistribute #(.N(2)) i_dist (/*AUTOINST*/);

/* Pipeline AUTO_TEMPLATE (
  .i_valid(dist_valid[0]),
  .i_ready(dist_ready[0]),
  .o_en(stg_en),
  .o_valid(comb_valid[0]),
  .o_ready(comb_ready[0]),
);
*/
Pipeline pipe2 (/*AUTOINST*/);

KeyType packed_val;
KeyType s1_msg, s1_key, s1_modulus;

/* TwoPower AUTO_TEMPLATE (
  .i_valid(dist_valid[1]),
  .i_ready(dist_ready[1]),
  .i_in({power, modulus}),
  .o_valid(comb_valid[1]),
  .o_ready(comb_ready[1]),
  .o_out(packed_val),
);
*/
TwoPower i_twopower (/*AUTOINST*/);

/* PipelineCombine AUTO_TEMPLATE (
  .i_valid(comb_valid),
  .i_ready(comb_ready),
  .o_valid(s2_valid),
  .o_ready(s2_ready),
);
*/
PipelineCombine i_comb (/*AUTOINST*/);

RSAMontModIn rsain;
assign rsain = {packed_val, s1_msg, s1_key, s1_modulus};
/* RSAMont AUTO_TEMPLATE (
  .i_valid(s2_valid),
  .i_ready(s2_ready),
  .i_in(rsain),
);
*/
RSAMont i_RSAMont (/*AUTOINST*/);

endmodule
```

概述如下：
用 AUTOINST 生成所有實例，對需要客製化的部分使用 AUTO_TEMPLATE。  
AUTO_TEMPLATE 內有兩種特殊符號可以使用：
* @ 會代換成實例名字的一部分，預設是實例名稱最後的數字，這個設計的用意是取代 verilog 那個難用到爆炸的 generate。
* 承上，AUTO_TEMPLATE 支援一小段的正規表示式規範 @ 被代換的內容，也就是上例中出現的 "_\([a-z]+\)"
* [] 會代換成對應線的寬度，應該是把寬度不一樣的線連接起來的時候，它會自動加入線的寬度，
在 systemverilog 支援 type 的狀況下，這個用處不大；另外現有的 linter 工具多半能找出類似的問題。

## 使用意見

在使用上 verilog-code 會有以下的問題：

1. verilog-mode 只適用在各模組間接線的狀況，也就是說你的模組裡面不能有任何其他邏輯，只能有子模組的宣告，
也因此 RSA256.sv 並不是 verilog-mode 合格的適用對象。
2. verilog-mode 無法處理 systemverilog 的型別，top module input/output 的 RSAModIn i_in 和 
RSAModOut o_out，這兩個訊號雖然沒有接進其他的模組，理應是 top module input/output 的一部分，
但 verilog-mode 受到自訂型別的關係無法成功接線。
3. verilog-mode 無法處理 systemverilog 的 unpack array，例如我內部模組的宣告是 input o_ready [2]，
verilog-mode 外部的接線會宣告為 logic [1:0] ，甚至只宣告為 logic。
4. 理論上我已經宣告了 `i_en` `stg_en` 兩條線，希望這兩條線從 submodule 出來之後可以導入我 top module 的邏輯，
但 verilog-mode 不會處理其他宣告，下面有線沒接就是往 top 的 interface 丟，實在是有點太…沒彈性了。

# Verilogpp

## Install

第二款工具是 Google 出的，用 perl 寫的工具，[載下來](https://github.com/google/verilogpp/blob/master/verilogpp)
放到可執行的地方就可以使用了，比較可惜的是已經七年沒有更新了，雖然考慮到 verilog/systemverilog 更新的頻率，
七年不更新好像也還好(蓋章

使用方式大致就三種：
1. verilogpp <target.sv>：剖析 target.sv 並接線
2. verilogpp -t <target.sv>：刪掉 target.sv 中所有接線
3. verilogpp <target.svpp>：生成 target.sv 並接線，不會動到 target.svpp 的內容，
壞處是 .svpp 的 extension 在編輯器裡沒有 verilog 程式碼格式的設定，要額外設定。

## Comment Format

會用到的註解比 verilog-mode 還要少：
* [/\*\*AUTOINTERFACE**/](https://github.com/google/verilogpp?tab=readme-ov-file#autointerface-macro_autointerface)
等同於 verilog-mode 的  AUTOINPUT + AUTOOUTPUT
* [/\*\*AUTONET --warn**/](https://github.com/google/verilogpp?tab=readme-ov-file#autonet-macro_autonet)
等同於 verilog-mode 的 AUTOREG + AUTOWIRE
* [/\*\*INST instance.sv i_instance**/](https://github.com/google/verilogpp?tab=readme-ov-file#inst-macro_inst)
等同 verilog-mod 的 AUTOINST 跟 AUTO_TEMPLATE

產生的內容會用在 PPSTART PPEND comment 包起來
/\*PPSTART*/
/\*PPEND*/

相比 verilog-mode 的話，它在 INST 不用寫明用哪個模組，而是直接寫出要接的檔案路徑跟實例的名字即可，路徑也支援資料夾路徑。

如果使用 verilogpp 來接線的話，完成體大概會長這樣：

```systemverilog
import RSA_pkg::*;

module RSA (
  /**AUTOINTERFACE**/
);

logic         i_en;
RSAMontModIn  mont_in;
TwoPowerIn    s1_modulus;
logic         s2_en;
TwoPowerOut   twopower_out;

/**AUTONET --warn**/

IntType power;
assign power = MOD_WIDTH * 2;

/**INST Pipeline.sv pipe1
   .o_en(i_en)
   s/^o_/s1_/;
**/

/**INST PipelineDistribute.sv i_dist
  parameter N 2
  s/^i_/s1_/;
  s/^o_/dist_/;
**/

/**INST Pipeline.sv pipe2
  .o_en(s2_en)
  s/^i_(.*)/dist_$1 [1]/;
  s/^o_(.*)/comb_$1 [1]/;
**/

/**INST TwoPower.sv i_twopower
  .i_in(s1_modulus)
  .o_out(twopower_out)
  s/^i_(.*)/dist_$1 [0]/;
  s/^o_(.*)/comb_$1 [0]/;
**/

/**INST PipelineCombine.sv i_comb
  parameter N 2
  s/^i_(valid|ready)/comb_$1/;
  s/^o_(valid|ready)/mont_$1/;
**/

RSAMontModIn  mont_in = {twopower_out, s1_key, s1_msg, s1_modulus},
/**INST RSAMont.sv i_mont
  s/^i_/mont_/;
**/

endmodule
```

## 使用意見

分析來看，verilogpp 跟 verilog-mode 在缺點上幾乎是一致的，畢竟兩者設計的邏輯是一樣的，不過相比之下仍然有較優的地方：

1. verilogpp 可以理解 systemverilog type，在 top module 的輸出入可以正常加入 RSAModIn i_in 和 RSAModOut o_out
2. 跟第一點一樣，verilogpp 可以理解 unpack array 的 port，宣告接線子模組的 unpack array port 在 top module 能正常生成
3. verilogpp 在宣告子模組時可以明確指定路徑檔名，比 verilog-mode 只寫模組名稱卻不知道他去哪裡找模組來得清楚
4. verilogpp 在註解的形式上比 verilog-mode 更直覺些，雖然只要扯到正規表示式都不會太漂亮。

與 verilog-mode 相同，所有缺點都可以直接複製：

1. verilogpp 接線的檔案同樣不能有任何的邏輯，只能有一堆子模組的宣告。
2. verilogpp 一樣無法處理 unpack array 的接線，範例中的 dist_valid, comb_valid 等信號，宣告為 logic [2]，
但分別把 [0] 跟 [1] 接到 pipeline 和 TwoPower 模組，verilogpp 無法判斷 dist_valid, comb_valid 
有接到其他模組，就會把他們接去 top module 的 port。
4. 同理 verilogpp 不會理你已有的宣告，所以處理完在 top module 的 interface 就會出現一堆奇怪的線。

# 結論

本文介紹了兩款 verilog 的接線工具：verilog-mode 和 verilogpp。
就如上所述，這些工具的使用情境都是在一個 **top module 只有一堆子模組宣告**的情況下，自動生成所有模組的實例，
並把對應的線連接在一起；由於工具不會分析內部本來的邏輯，只要你的模組裡有一丁點自己的邏輯，就立刻不適用這些工具。

其次，由於一般命名的一致性，很多模組都會有重複的命名，例如 RSA256 幾乎都是同一套命名邏輯：`i_valid, i_ready, i_in, o_valid, o_ready, o_out`，
兩套工具把 **同名** 線接起來的設計邏輯，無法簡單寫完所有模組宣告就了事，
會像上面兩套範例一樣，必須加入大量註解標示接入這些 port 的線的名字，導致使用這些工具跟用手寫的效率差不多。

各種 systemverilog 的特性，這些工具全都無法處理，症狀是生成完之後 top module 的 interface 會有額外的 port，
生成完後要再手動移去模組內的變數宣告區。

綜上所述，我覺得這些工具的使用情境只有兩種：
1. 設計的時候就把 port 命名弄好，模組不要用 i_valid/ready 這種通用名，完全為*可以使用接線工具*為目標做整體設計。
2. 照常設計，用接線工具幫你產生各子模組實例，代入 port 資訊，後續接線還是切回人工編輯，這樣至少省下打開每個檔案複製定義、刪除 input/output 關鍵字的時間。

在以上幾種使用情境中，我個人認為 verilogpp 較 verilog-mode 優，可以處理 systemverilog 的型別，
另外子模組可以給定路徑，註解指定接線名稱的方式也較 verilog-mode 直覺好懂。  
至於兩者共同的缺點也不怪他們，要處理上述那些問題就必須進到語法分析等階段，不是簡單的 script 工具能做到的了

# 展望未來

本文介紹了兩套不同的 verilog 接線工具，很可惜的兩套都離完美相差甚遠，以下我提出兩個可能的隱藏參賽者。

## verilog/systemverilog language server

打造一套能分析專案中模組的 verilog 檔案的 language server 可能是比較泛用的解決方案，一般接線最煩的，就只有：
1. 找到每個想實例的模組
2. 複製該模組的定義
3. 刪除定義前的 input/output 關鍵字，加上小括號開始接線

如果使用一個 language server 分析過整個專案中的檔案，應該是能輕鬆完成上述的工作；
透過名字接線因為高重複率效率很差，實務上也真的沒必要。

## AI 工具

最近 Github-Copilot 開放大家免費使用了，我在 vscode 上安裝，試著對上述的 RSA256 進行接線。  
成果我覺得有點差強人意，確實 AI 在辨識程式碼 pattern 頗有一套，例如宣告完 `logic modulus`，
下一行打 always_ff 時，自動補齊已經生好全套從 `if (!rst_n)` 到結尾的程式碼，並且變數已經代入 modulus，十分貼心，
這是以往 snippet 工具無法作到的客製化插入程式碼。

但在接線上顯然還力有未逮，理論上 Copilot 應該是能看到整個專案的檔案，
但它顯然還未意識到實例模組與在其他檔案中的模組定義的關係。

使用上出現的都是：
1. 先寫好 Module 1 的實例，定義有 Port A, B。
2. 準備實例 Module 2，定義有 Port A, B, C。
AI 工具會把實例 Module 2 與 Module 1 作連結，以致在 Module 2 下面生成 Part A, B 而忽略 Port C，甚至在 Port D, E 的狀況下，
仍然生出 Port A, B。

如果比較兩個隱藏參賽者的話，我覺得比較踏實的解法是發展一套 verilog 的 language server，現下雖然有
[一些 verilog/systemverilog 的實作](https://microsoft.github.io/language-server-protocol/implementors/servers/)，
但我還沒完整試用過，應該都還沒達到足以擔當接線的大任。

AI 工具的話，我不諱言這也許只是 Copilot 在 Github 看了比較少的 verilog project，如果給 AI 工具足夠的訓練資料，
把每個模組的 input, output port 複製過來這種事，對 AI 工具來說應該是小菜一碟吧？  
AI 工具在發展潛力上比 language server 更多更大，也許會出現超過現有接線工具的 AI 工具也說不定。

為了拯救廣大的 verilog 工程師們，就讓我們拭目以待這兩種隱藏工具的未來發展吧。