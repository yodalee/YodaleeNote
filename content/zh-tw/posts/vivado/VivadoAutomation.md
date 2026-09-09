---
title: "Vivado 在自動化的最佳實踐"
date: 2026-05-31
categories:
tags:
- Xilinx
- Vivado
---

先說結論，**我不知道**

這本身就是一個困難的題目 vivado 天生就不是為了自動化而實作的（至少看起來不像是），圖形化介面與
vivado project 整合式的儲存環境，當然是提供許多的功能。  
但反過來說，實務上完全不建議把整個 Vivado 
生成的專案檔都塞進版本控制之內，那會讓你絲毫改動都引得版本控制系統大亂，使得
Vivado 專案在自動化與版本管理上一直是個痛點。
<!--more-->

這個問題困擾許多人，搜尋一下可以找到許多討論，像是
 [How do you manage your Vivado projects in git?](https://www.reddit.com/r/FPGA/comments/mw7fsb/how_do_you_manage_your_vivado_projects_in_git/)。  
也有人推出他們的解法，例如 [vivado-git](https://github.com/barbedo/vivado-git) 
這個專案，我還沒嘗試過不知效果如何？

經過嘗試，分享一下自己目前在公司專案上的管理方式，本文會分為兩大部分：  
第一：我們以 [AXI Lite]({{< relref "PynqZ2_AXILite" >}})，出現的 Adder
來做範例，我們要近乎一鍵的打包 IP，並輸出到指定位置。  
第二：用上一步打包產生的 IP，接入 block diagram，並產生準備生成 bitstream 的專案。

下述的 vivado script 多少都跟路徑有關，先說明一下工作路徑：  

`origin_dir` 整個專案的主目錄，會叫這個是因為 Vivado 的 script 就這樣叫  
* `src`：放 hdl code 的資料夾
* `script`：vivado 生成要用的腳本檔與資源
* `ip_repo`：還未 script 化時的 ip 工作目錄
* `proj`：整個 IP 打包到 FPGA 上的 vivado project
* `tmp_pkg`：vivado 暫時性的 project

`ip_repo`, `proj`, `tmp_pkg` 是 vivado project 
的位置，這兩個資料夾可以加到 .gitignore 中。  

# 打包 IP

## 產生 AXI 檔案

一開始手中只有要打包的檔案，還需要 vivado 生成的，處理 AXI 介面的檔案。  
首先打開 vivado，創造一個新的 project，等等就刪掉了，所以叫 tmp_pkg
，不用加 source code

![Create tmp_pkg](/images/xilinx/Auto000_CreateTmpPkg.png)

點選 `Tool` -> `Create and Package New IP` -> `Create a new AXI4 
Peripheral`，模組資訊主要是名字設定一下，會對應到檔名，以及想要的 AXI Lite 如 register 數等等。

![Create AXI](/images/xilinx/Auto001_CreateAXIperipheral.png)

IP 名稱以 Adder 為例，位置設定在 `origin_dir` 內；最後一步不用選 `Edit IP`，選 
`Add IP to the repository`，按 Finish 之後就把這個專案關掉。

去 `origin_dir/ip_repo` 裡面找一下，可以找到 vivado 生成的兩個檔案：
* Adder_v1_0.v：IP最上層
* Adder_v1_0_S00_AXI.v：AXI Lite slave handler

把這兩個檔案一起複製到 src 資料夾內，隨後就可以把 tmp_pkg, ip_repo 兩個資料夾一起刪除。

## 打包 IP

事先把 AXI 檔案修改完成，從頭再來一次，打開 Vivado 創建 tmp_pkg 專案。  
Add Source 把你的專案的 source code 跟方才新增的兩個 AXI 相關的檔案一起加到這個專案內。  

![Add IP Source](/images/xilinx/Auto002_Addfile.png)

點選 `Tool` -> `Create and Package New IP` -> `Package your current project`  
IP location 先選用 `origin_dir/ip_repo`，因為在編輯過程中會產生許多額外的檔案，所以先放在暫時位置。  

![Package Current Project](/images/xilinx/Auto003_PackageCurrent.png)

Vivado 會打開一個工作區，這個工作區有幾個地方跟一般的 Vivado 不一樣，我在下圖把它們標出來：  

左邊多出了 `Edit Packaged IP` 的選項，點下去可以打開右邊的視窗，
在這裡編輯 IP 的資訊、介面、參數等，最後，按下 `package IP` 完成打包。  
按下 `package IP` 後 Vivado 會問你要不要關掉這個臨時的 project，記得選不要，
在下面的 tcl 視窗中找到打包用的 script，如果關掉了也沒差，下面有附上通用的。  

![PackageIP](/images/xilinx/Auto004_PackageIP2.png)

完成之後我們要將以上的流程自動化，選擇 `File` -> `Project` -> `Write TCL`
讓 vivado 把剛剛做的事寫入 package_ip.tcl。  

> 在寫出 package_ip.tcl 的時候，請先寫到 origin_dir 內，再移動到 script 資料夾中  
> 直接存到 script 資料夾，文件內會跑出一堆 ../ 要處理
{.error}

![Write TCL](/images/xilinx/Auto005_WriteTCL.png)

## 修改 package_ip.tcl

vivado 剛寫出的 tcl 腳本可用，但參雜太多不相關的東西，我這三個檔案的 IP 總行數 550
行，需要做個清理把不必要的部分全砍光，這年頭很多清理可以叫 AI 幫忙。

1. 在 ip_repo 中，找到 component.xml，將它移動到 script 資料夾；隨後修改 package_ip.tcl
，把 component.xml 的路徑修改為 script。
2. 找到 create_project 那行，加上 `-force`，這樣跑第二次的時候，即使
tmp_pkg 已存在仍然能強行蓋過去。
3. 找到 `proc checkRequiredFiles` 的定義以及呼叫的地方，整段刪除。
留著也行，但我覺得刪了清爽，原始碼有更動也只需要改動一個地方
（但我覺得如果你原始碼都動了，高機率需要重新打包）。
4. 找到 `proc print_help`，從它的定義開始，到它下面 `if { $::argc > 0 }` 的部分，整段刪除。

另外有一些些例如：
```tcl
if { [info exists ::origin_dir_loc] } {
  set origin_dir $::origin_dir_loc
}
```
讓你用環境變數改掉 origin_dir 的片段，因為很短小，可刪可不刪。

從 tcl 下半部，它依序會
1. 建立 sources_1 並加入原始碼（通常最多的是這裡）
2. 建立 constrs_1 並加入 constraint w檔案
3. 建立 sim_1 保存模擬檔案
4. 建立 synth_1 保存 synthesis 的結果
5. 建立 impl_1 保存 implementation (P&R) 的結果
6. 看你的 script 可能還會出現 impl_2

由於我們是在打包 IP ，所以自 sim_1 以下的內容全部不用保留，全部刪掉即可；constrs_1 如果沒東西也可以考慮刪。

要注意 vivado 在打包 package 的時候，會自動的去判斷你用的是什麼介面，像我們都叫
s00_axi_ 開頭，並且有 awready, wready, bready 等，Vivado 就自行推斷為
AXI Lite 並把 port 與對應的介面對應起來。  
因為我們用的是 Vivado 生成的 AXI Lite .v 檔，這個過程高機率沒有問題；
如果是自己寫的，那在打包的時候，Port and Interface 
那關就要完成相關的設定，讓這個 map 的動作被 Vivado 記錄下來。

有一部分的資訊可能藏在 componenet.xml 中，但我沒把握。

## 修改 ip_repo 的位置

此次研究中，我發現整台電腦上最好有一個共同的 ip_repo 資料夾，把所有的 hardware IP 
生成的 repository 都放到那個資料夾去。

在這裡我選用的是 `${HOME}/ip_repo`，在 package_ip.tcl 中加入以下內容：
```tcl
set home_dir $::env(HOME)
set ip_repo_dir [file normalize [file join $home_dir "ip_repo"]]
```

不是說 Vivado 設定 repository 的時候不能設定多個位置，只是看那個 list 
愈來愈長也是很難管理，還不如集中放。  
至於這個 ip_repo 資料夾能不能連網甚至讓各 hardware IP 在更新的時候自動編譯、CI/CD 
上傳，或是要不要做版本控制，就超過這篇文的內容，要視公司/組織中的規劃而修改。

## package script

最後一步，如果 Vivado 沒有把打包的部分寫出來的話，可加上以下的內容：

```tcl
set core_name "adder"
set core_version "1.0"
set core_vendor "user.org"
set core_library "User"
set display_name "adder_v1_0"
set description "Wrap Adder into AXI Lite"
set ip_root_dir [file normalize \
  [file join $ip_repo_dir "${core_name}_${core_version}"]]
set proj_dir [file normalize "./${_xil_proj_name_}"]

file mkdir $ip_repo_dir
if { [file exists $ip_root_dir] } {
  file delete -force $ip_root_dir
}
file mkdir $ip_root_dir

update_compile_order -fileset sources_1
ipx::package_project -root_dir $ip_root_dir -vendor $core_vendor \
  -library $core_library -taxonomy {/UserIP} -import_files

set core [ipx::current_core]
set_property name $core_name $core
set_property version $core_version $core
set_property display_name $display_name $core
set_property description {$description} $core
ipx::merge_project_changes files $core
ipx::save_core $core
ipx::unload_core $core

set fileset_obj [get_filesets sources_1]
if { $fileset_obj != {} } { 
  set_property "ip_repo_paths" $ip_repo_dir $fileset_obj
  update_ip_catalog -rebuild
}

close_project
file delete -force $proj_dir

puts "INFO: Packaged IP into $ip_root_dir"
puts "INFO: Removed temporary project directory $proj_dir"
```

裡面的 display_name 跟 description 可依現在打包的 IP 修改。  
注意到這個 script 是破壞性的，它會把 `${HOME}/ip_repo` 下的 package
資料夾整個刪掉重做；結束時也會將 tmp_pkg 關掉並刪除。

# 打包 block diagram

第二個 script，一般叫 `script/xxx_proj.tcl`，負責連接 block diagram，以下稱 proj.tcl。

產生方式更簡單一些：
1. 設定 vivado ip 搜尋路徑，指向上述的資料夾，選擇 `Tools` -> `Settings`，在 IP/Repository
做如下圖的設定

![Set IP path](/images/xilinx/Auto005_IPrepo.png)

2. 創造新的 block diagram，連接處理器、IP、AXI Interconnect 等元件的連接
3. Create HDL Wrapper
4. Write TCL 把 proj.tcl 寫出來。

在寫出 TCL 時，選項 `Recreate Block Designs using Tcl`，可以：
1. 勾選 Recreate Block Designs using Tcl
2. 不選 Recreate Block Designs using Tcl，把 xxx_proj 中生成的
.bd 檔加到你的 src 當中，修改 tcl 檔中指向 .bd 檔的路徑。

第一個選擇是 .tcl 很長，包含從頭開始畫出整個 block diagram；但
第二個選擇的 .bd 檔比起 .tcl 長度也沒有比較短，加上更難讀更無法版本管理，我都是選擇第一種讓 
.tcl 重畫 block diagram。

## 修改 proj.tcl

寫出 proj.tcl 後，要做的修改和 package_ip.tcl 差不多（畢竟都是 Vivado 寫出來的）

1. 找到 create_porject 那行，一樣加上 `-force`。
2. 找到 `proc checkRequiredFiles` 的定義以及呼叫的地方，整段刪除。
3. 找到 `proc print_help`，從它的定義開始，到它下面 `if { $::argc > 0 }` 的部分，整段刪除。
4. synth_1 等在第二個 script 不一定會刪，因為含 block diagram 的專案終歸是要跑 
implementation，留著無妨，但如果你覺得檔案太長了那刪了無妨。

與 package_ip.tcl 一樣，加上 ip_repo 位置的設定：
```tcl
set home_dir $::env(HOME)
set ip_repo_dir [file normalize [file join $home_dir "ip_repo"]]
```

並尋找關鍵字 `ip_repo_paths`，把本來的相對路徑修改為 `ip_repo_dir`，讓 vivado 可以找到上一步打包的 IP。
```tcl
if { $obj != {} } {
  set_property "ip_repo_paths" "[file normalize "$ip_repo_dir"]" $obj
}
```

這兩個檔案都準備好之後，我會這樣使用：

```bash
vivado -mode batch -source script/package_ip.tcl
vivado -source script/proj.tcl
```

第一行完成 IP 打包，第二行會打開 vivado 把 block diagram 準備好，等著你按 
synthesis, implementation, generate bitstream。  
如果對自己的設計十分有信心，可以在創造 proj.tcl 的時候，先按過
synthesis, implementation, generate bitstream，然後再寫出 .tcl 
檔，這樣一執行就會一路跑到 bitstream 建完。

# What's Next?

這兩個 script 我目前是滿意的，我自己觀察有幾個可改進之處：  

第一，把 tcl 清得更乾淨易懂，把 src 的部分獨立出來變成一個檔案，讓 tcl 去讀檔，同一份 
tcl script 就可以直接複製給其他的專案使用，不用每個新專案都重複上述所有步驟。  
第二，打包 IP 的 script 顯然應該多做一些事（但又不能太多），至少驗證一下這個 
IP 沒出什麼大問題等。

Vivado 適合的動作我所知有兩個，剩下的都太多太重了：  
1. 跑 Linter，看看有沒有錯誤
2. 跑 Synthesis，看看有沒有錯誤

----

另外是 vivado 版本的問題，不用想了，這部分 vivado [只能用悲劇來形容](https://www.reddit.com/r/FPGA/comments/11jaz0d/different_versions_of_vivado/)

> Vivado on the other hand, not so much. You want to pick ONE version and use it for your project. And everyone working on it will need to use the same version. 

翻譯就是你給我選死一個版本辣。  

我們曾經有個合作的對象，他們裝 2022.2，我們內部不小心升了 2023.2 就爆掉了，
我們的 script 他們跑不起來，解決方式是我們把 2022.2 裝回來，專門生給他們的 script。  

也遇過要 review 的專案，script 是用 2025.1 版寫的，想當然爾我們自然是跑不了。  
用上 script 這招只要 vivado 有更新就沒救了，準備重做吧。

另外一大痛點在於 tcl script 都會和使用的 FPGA、板子、SoC 等等高度綁定，很難用一套 script
，讀入不同設定檔就能生成不同 FPGA 使用的 bitstream 檔，這目前也沒有很好的解法。

# 結論

以上就是目前實作的 Vivado 自動化方案，絕不能說是完美，不過還算堪用吧。  
希望對大家能有所幫助，也希望拋磚引玉，大家一同討論改進，如果各位有什麼秘藏的 Vivado
使用密笈，歡迎在底下留言分享，讓我們找出 Vivado 自動化的最佳實踐究竟是啥。