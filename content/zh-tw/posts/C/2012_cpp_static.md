---
title: "c++ static 修飾詞"
date: 2012-11-13
categories:
- cpp
tags:
- cpp
series: null
---

最近寫基因演算法的project，有需要使用到C++ class的static variable，因為我之前這個東西怎麼寫都會出錯，
這次好不容易在強者陳仕勳(GodGodMouse)的指導下成功寫出可以用的static，在這裡記錄一下怎麼使用C++的static(是說這些文章也多到滿出來了)。  
<!--more-->

靜態物件static的標記包括：
1. global 變數
2. local 變數
3. class 成員

總歸三種使用方式，都是要在程式的各處中使用共有的一份資料，下面針對三種使用方式，分別寫明使用方法及使用的時機：   

## global 變數：

在global 的地方使用static，可以讓該變數由程式的全域變數變成檔案內的全域變數，使用static的全域變數幾乎永遠是好習慣，
畢竟其他程式設計師在用你的程式時只想把你的程式當黑箱子，要是哪個全域變數名字相衝……那大概不是一兩個幹字可以解決的問題，
例如下文中的debug變數，我每個檔案都想要有debug變數，這時就要加上static。  

簡單的例子，我們幾個cpp檔裡面都有一個debug變數(總不能main裡的叫maindebug，gui裡的叫guidebug吧？)，如果不加上static   
```cpp
//main.cpp
int debug  = 0;
//src1.cpp
int debug  = 0;
```
這樣在最後編譯連結的階段，就會回傳錯誤，因為 debug 在這裡被重複定義。  
因此，請為全域變數加上static。  
```cpp
static int debug = 0;
```
或者，與static相對的就是extern，宣告變數是在別的檔案裡有定義，這時候不能再給初始值，因為初始值是從別的檔案來的：   
```cpp
extern char* filename;
```

## local 變數

在函數裡加上static的變數，不同於一般的變數「在函數執行時起始，於函數終結時清除」，static變數在程式一執行時即被宣告。  
我想這個已經芭樂到不能再芭樂的地步了，例子也不勝枚舉，如果我們要輸出某函數被call幾次，請愛用static。   
```cpp
void foo(){
 static int i=0;
 cout << ++i << endl;
}
```

## class member ：

在class裡使用，其功用在於，這個class產生的任何一個 instance，都可看到static的變數或函數。  
比如說我project寫的基因演算法的程式，經由隨機產生了10000個子代，每個子代都要對某一筆測試資料進行處理，看看結果好不好；
這時候當然不可能每一個子代都保留一份測試資料的副本（記憶體不用錢也不是這樣花的吧…），就要用static的方式保存資料，讓每個子代都能看到。  

在class裡面用會複雜一點，假設現在有一個叫 `static_test` 的class，架構如下：   
```cpp
//static_test.h
class static_test {
public:
    static int static_var;
    static void output();
    int i;
};
```
我們宣告了一個static的 integer跟一個 static 的function，在.h宣告中，大部分的東西是一樣的。  
但在定義式裡，就有些不同，由於static物件在是class共有的一部分，宣告class物件時並不會初始化static的物件，因此在.cpp裡面第一件事就是先初始化static物件：   
```cpp
// static_test.cpp
int static_test::static_var;
```
要不要給初始值沒什麼關係，但這行指明：`static_test`中有一個 `static_var`，不寫這行編譯時會出現undefined reference to `static_var`。 

取用static物件時，也要用  ::  指明：我要取用 `static_test` 的物件，例如：   
```cpp
cout << static_test::static_var << endl;
static_test::static_var = 10;
```

static function是類似的事情，每一個class都可以取用這個function，但static function裡面，只能用到static的member，
因為它並非任何一個object的function，自然不能取用其中的內容，就如文中的output()不能取用 i 這個變數。  

據說static member最常用的地方是統計目前程式中生成了幾個object，在 constructor 中對static member+1，destruct的時候-1，
不過作者到目前還是沒遇到相關的場合，所以…就算了吧，能用就好。  

## 致謝：

本篇文章，感謝 GodGodMouse 大大的指導。 