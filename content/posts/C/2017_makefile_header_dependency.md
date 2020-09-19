---
title: "Makefile 使用 make depend 進行相依性檢查"
date: 2017-04-08
categories:
- c
tags:
- makefile
series: null
---

在寫Makefile 的時候，一般的規則是這樣的：  
```makefile
Target: Dependency
    Command
```
Makefile文件稱 command 為 recipe，不過我這邊就寫command。  
如果是C 程式，通常也會把 header 檔寫在 dependency 內，否則 header 檔改了結果程式沒有重新編譯就奇怪了，如果每次改了header 都要 make -B 也不是辦法。  
<!--more-->
project 長大的時候，手填 header dependency 變得愈來愈不可行，特別是Makefile 大多是寫 wildcard match，例如這樣把object files 都填入變數 OBJS 之後，直接用代換規則將 .c 編譯成 .o：  
```makefile
SRCS = file1.c file2.c
OBJS = $(SRCS: .c=.o)

target: $(OBJS)
  $(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
  $(CC) -c $(CFLAGS) -o $@ $<
```

在這裡翻譯了[這篇文章 Auto-Dependency Generation](http://make.mad-scientist.net/papers/advanced-auto-dependency-generation/)，
裡面給出一個針對大型專案完整的解決方法，重要的是它有把為何這麼寫的理由講出來：  

## makedepend
最簡單的方法，是在Makefile 裡面加上一個depend 的目標，在這個目標利用一些分析工具，例如makedepend建立 dependency。  
但這樣等於是把 make depend 跟真正的編譯分開了，缺點有兩個：
1. 需要使用者下make depend 才會重建 dependency
2. 如果有子資料夾也要依序下 make depend

我們需要更好的方法。  

首先我們可以利用 makefile 的include 功能，直接 include 一個含有 dependency 的makefile ，把所有source file 設為 include file 的dependency，
這樣只要有source 檔更新，make 時就會自動更新dependency到最新，完全不用使用者介入；但這樣也有缺點

* 只要有檔案更新就要更新的dependency

我們可以做得更好。  

## gnu make 推薦的方法  

參考 [Generating Prerequisites Automatically]https://www.gnu.org/software/make/manual/html_node/Automatic-Prerequisites.html)  
對每一個原始碼檔，產生一個.d 的相依性資訊  
```makefile
%.d: %.c
  @set -e; \
  rm -f $@; \
  $(CC) -M $(CPPFLAGS) $< > $@.Td; \
  sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.Td > $@; \
  rm -f $@.Td
```
先開 set -e 設定只要後面的command 出問題就直接結束，然後把已存在的目標檔 .d 檔刪掉；接著使用gcc 的 -M 參數
（或者用 -MM ，如果不想要產生的dependency 包含system library的header），讀入 name.c 之後，產生如下的 dependency，寫到 .Td 檔案中。  
```makefile
name.o: name.c aaa.h
```
之後用sed將上想 gcc -M 產生的內容，加上name.d 這個target：  
```makefile
name.o name.d: name.c aaa.h
```
對每個.c 檔都產生過 .d 檔之後，就能直接include所有.d 檔案了。  
```makefile
include $(sources: .c=.d)    
```
因為 .d 的dependency 包括對應的 .c 檔，這樣只要.c 檔更新了，makefile 也會重build .d 檔，保持相依資訊在最新，同時只更新需要的 .d ，不會浪費build 的時間。  
這個做法有幾個問題，首先是re-invocation 的問題，使用include的問題在於Makefile 本身的設計，因為include 可能帶入新的變數定義、目標等等，
一但include 的目標有更新，它就會強制重跑一次本體的Makefile ，參考[這一篇](http://make.mad-scientist.net/constructed-include-files/)，
這在大型的專案上會帶來可觀的成本；更嚴重的是，如果我們把 .h 檔給刪除或更名，在編譯的時候會出現錯誤：  
```txt
make: *** No rule to make target 'name.h', needed by 'name.d'. Stop.
```

這是因為name.d 相依於 .h ，.h 已經不存在而且又沒有產生 .h 的rule，Makefile 就會回傳錯誤；雖然改 .h 的狀況不常見，一但遇到就只能手動刪掉所有 .d 檔重新產生。  

要解決上述兩個問題，首先是Makefile 每次都會重新make 的問題，問題是這樣：  
如果有個source 更新了要重新編譯，那我們知不知道新的dependency 也沒差--反正它鐵定要重編譯的，
該做的是為下一次的編譯產生新的 dependency 資訊；所以我們可以把產生 .d 檔這步，移到編譯 .c 檔的時候，大略如下：  

```makefile
OBJS = $(SRCS: .c=.o)
%.o : %.c
  # 產生 .d 檔的位置
  $(CC) -o $@ $<
include $(SRCS:.c=.d)
```

第二個問題比較棘手，這次用的招式是：  
Makefile 中如果有目標但沒有command 或dependency，這個目標又不是個已存在的檔案，這在 makefile 裡稱為 [Force Target](http://www.gnu.org/software/make/manual/html_node/Force-Targets.html)，
那Makefile 無論command有沒有執行， 會預設這個目標已經「被更新到最新」，注意它是有更新的，所以相依於這個目標的目標，也會依序更新下去。  

例如下面這個例子，因為FORCE 每次執行都會被更新，所以clean 也一定會更新而執行  
```makefile
FORCE:

clean: FORCE
  rm $(objects)
```

所以這裡用的技巧就是，把那團相依的.h 檔變成無dependency/command 的目標，產生.Td之後，下面我是分成多行的結果，實際上可以寫得緊密一點，所做的工作包括：
* 用 sed 依序移除comment
* 移除 : 前的target
* 移除行尾接下一行的反斜線
* 移除空白行
* 把行尾變成 : 

這樣本來的dependency 通通變成目標了。   
```bash
cp $*.Td $*.d;
sed -e 's/#.*//'
sed -e 's/^[^:]*: *//'
sed -e 's/ *\\$$//'
sed -e '/^$$/ d'
sed -e 's/$$/ :/' < $*.Td >> $*.d;
rm -f $*.Td
```

最後的問題是，如果我們移除 .d 檔， .c .h 檔又沒有更新則Makefile 也不會重新產生 .d 檔，因為 .d 檔並不是編譯時相依的target；
但 .d 檔又不能是個真的target ，否則又有老問題： include 的時候它會產生 .d 檔，然後整個Makefile 會重跑一次。  

這裡的解法是把 .d 加到 .o 的dependency ，然後加一個空的target，這樣一來，.d 檔如果存在，因為commands 是空的所以什麼事都不做；
如果 .d 被刪除，在make 時 .o 會觸發 .d 的更新，在空的target 更新之後， .o 也跟著更新的時候，一併產生全新的 .d 檔。  
```makefile
%.o: %.c %.d
  command
%.d:
```

最後是一些針對 dependency file 的處理，完整的Makefile 會長這個樣子：  
```makefile
DEPDIR = .depend
DEPFLAGS = -MT $@ -MMD -MP -MF $(DEPDIR)/$*.Td
POSTCOMPILE = mv -f $(DEPDIR)/$*.Td $(DEPDIR)/$*.d

%.o : %.c $(DEPDIR)/%.d
  $(CC) $(DEPFLAGS) $(CFLAGS) -c $<
  $(POSTCOMPILE)

$(DEPDIR)/%.d: ;

.PRECIOUS: $(DEPDIR)/%.d
include $(patsubst %,$(DEPDIR)/%.d,$(basename $(SRCS)))
```

第一段定義depend file 的存取地點，然後定義 DEPFLAGS，利用編譯時插入 DEPFLAGS 把編譯跟產生 dependency 一併做完；相關的 [flags 都是 -M 開頭](https://gcc.gnu.org/onlinedocs/gcc-5.2.0/gcc/Preprocessor-Options.html)：  

* -MT 定義產生出來的目標名稱  
預設是 source 檔的suffix 換成 .o 後綴，並去掉前綴的任何路徑，例如 -MT www 則生成的相依資訊就變成 www: name.h，所以這個選項不一定要加。

* -MM or -M 產生 dependency 資訊
* -MP 直接幫忙對 header file 產生空的 dependency target  
 （顯然gcc 開發者有注意到 .h 並非目標產生的問題），上面提到那一大串 sed ，如果是用 gcc 加上這個選項就不需要了

* -MF 設定輸出到的檔案，相當於 redirect >

POSTCOMPILE 則把暫時的dependency file .Td 改名為.d，如果沒有要對 .Td 做什麼，拿掉這行，指定 -MF 直接寫到 .d 檔也是不錯的選擇。  

第二段在.o 的dependency 加上 .d，command 編譯 .o 檔，同時gcc 產生.d 檔。  
第三段寫入空的 .d 檔目標，以便處理 .d 檔被刪掉的狀況，.precious 讓 .d 檔在Makefile 當掉或被砍掉的時候不會被刪掉；最後 include 產生出來的 .d 檔。  

大概的解法就是這樣，其實，如果project 很小的話，根本就不用這麼大費周章，像[下面這個解法](http://stackoverflow.com/questions/2394609/makefile-header-dependencies)，
直接把所有SRC送給gcc 產生dependency ， 寫到 .depend 檔案，然後每次都include .depend，對 99.9%的project 來說應該都足夠了。  