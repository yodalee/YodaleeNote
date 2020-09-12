---
title: "淺談rust option type"
date: 2016-04-21
categories:
- rust
tags:
- rust
series: null
---

強者我同學qcl 做了一系列的簽名檔，大體的概念就是用女友狂炸執行緒，以下是C++ version：  
```c++
int main(int argc, char *argv[]) {
    QCL *qcl = new QCL();
    Girl *gf = qcl->findGirlfriend();
    printf(“%s\n”, gf→name());
    return 0;
}
```
```shell
qcl@QCLS:~$ g++ qcl.cc
qcl@QCLS:~$ ./a.out
Segmentation fault
```
<!--more-->

另外還有許多版本：python, java, objective C(太強啦都會寫objective C)等等  

最近心血來潮寫了一個rust version ，發現正好可以藉此說明option type 的概念，這樣的設計見諸於一些較新的語言，和較舊語言的新標準，如java ver 8和C++ 17，rust 版本如下：  
```rust
fn main() {
    let qcl = QCL{};
    let gf = qcl.findGirlfriend();
    println!(“{}”, gf.unwrap().name());
}
```
```txt
qcl@QCLS:~$ rustc qcl.rs
qcl@QCLS:~$ ./qcl
thread '<main>' panicked
```

上面的code 裡，QCL struct 的 findGirlfriend() 的宣告如下，它回傳的不是如C++中的Girl，而是Option<Girl>：  
```rust
fn findGirlfriend(&self) -> Option<Girl>
```

所謂option type 是用在函式回傳值可能不會回傳東西的時候，包含了兩種可能的變體：Some 或 None，其基本定義：  
```rust
pub enum Option<T> {
    None,
    Some(T),
}
```
例如文中出現的getGirlfriend，亦或在dictionary 查詢的getValue()  
若是some 則可存取其中的內容；None 則類似null 的設計，如上例中用unwrap()強行取用內容會造成執行緒崩潰  

在上例中，遇到option，比較正規的寫法應該是：  
```rust
match gf {
    Some(girl) => println!("{}", girl.name()),
    None => println!("Not found"),
}
```
藉此迴避None 把thread 給炸了，直接unwrap相對在C/C++ version 就是沒去比較return 的pointer == NULL，
或是在python 裡面沒寫 is None，亦或是Golang 裡面沒寫err != nil。  

的確，加上match去辨識回傳值是否為None，就跟用了== NULL或is None看似相差無幾，但這裡有個至關緊要的差異：  

> option type 就是option type ，None 只會出現在這裡

若girlfriend 回傳值不是option ，就一定要回傳一個Girl 的實體，不管存取它的name 之後是**林志玲**還是**qcl的右手**，它就必須是一個Girl，儘管解出來是**qcl的右手**它仍然夠格當一位適當的女友。  

在其他語言中的Null則不然，我們看到C++ 回傳了一個Null pointer，Null 是空的東西，它什麼都不是；
但他被視為Girl pointer，因此我們可以存取它的name，它可以被賦值給任何一種pointer，它又什麼都是，
Null 如同變形蟲一樣通過對Girl 的型別檢查，這樣簡單的例外設計有極高的自由，卻也容易出錯。  

使用option 讓設計師知道girlfriend有可能為None，也無法對option type 使用來自Girl 的函式與資料，編譯器能在編譯時清楚的指出這類錯誤，並強制設計師在編寫時使用match 檢查，
從而避免None 在執行緒中四處散佈，並到了執行時才將執行緒炸掉，如上文中都已經知道可能是None了，又強行unwrap 程式會爆是自己活該。  

如果我們用上面的例子寫個比喻：  
C語言和允許Null 的語言大概就像：

> 你女友的名字呀，拿去；噢qcl你沒女友呀…干我屁事！你還是自盡吧你  

使用Option 的語言會比較貼心一點：

> 女友的名字嗎，嘿qcl 呀，你有可能沒有女友噢，最好處理一下  

## 參考資料：

[rust option 相關文件](https://doc.rust-lang.org/std/option/)  
[Option\_type](https://en.wikipedia.org/wiki/Option_type)  
[NULL：计算机科学中的最严重错误，造成十亿美元损失](https://linux.cn/article-6503-1.html)  
[補救 null 的策略](http://openhome.cc/Gossip/Programmer/Null.html)