---
title: "開始使用 Google Test：基本設定"
date: 2018-07-21
categories:
- simple setup
tags:
- cpp
- google test
series: null
---

故事是這樣子，最近突發奇想用一些零碎時間寫了一個 C++ 的 regex project，因為已經好久沒有寫 C++ 都在寫 Rust，
回鍋發現 C++ 怎麼可以廢話這麼多，長得又醜，以後哪個人再跟我說 Rust 的的生命週期很醜的，我就叫你去看 C++ 的 template code，看你還敢不敢再說 Rust 醜。  
扯遠了，總之這次寫的 C++ 專案，其實只是當個練習，看能不能藉由實作專案熟悉 C++ 11、14的功能，
也決定引入 CMake 和 Google test 等等我之前一直都沒有學會的東西，從做中學這樣。  
<!--more-->

這篇先來介紹一下 [Google test](https://github.com/google/googletest) 超基礎設定，詳細請參考官網。  

當我們把程式準備好，通常會自己偷懶寫一個 main，然後在裡面呼叫所有測試用的函式，測試就是手動執行編譯出來的執行檔，但是這樣做的問題不少，諸如：
* 缺乏足夠的 assert 跟框架支援
* 測試很難擴張
* 沒有量化多少測試通過等等

雖說有時也會重新發明這些輪子來測試就是XDD。  

這當然是個問題，所以很多公司或單位都推出測試框架，讓寫測試變成一件愉悅~~大家都願意做~~的事，Google Test 就是其中一個，
看一看覺得不難寫就決定用了，同樣在使用 Google Test 的包括像 Google 自己的 chromium，LLVM 編譯器等等；其他的測試框架像是強者我同學 JJL 推的 catch2。  

要使用 Google test 的第一步是先安裝，Linux 只要用套件管理員安裝即可，Windows 的話我救不了你，請到 Google test Github 網頁看編譯教學。  
接著我們要設定專案，首先寫一個測試，如果是自幹一個主程式的話，通常會像這樣：  
```cpp
void test_something();

int main(int argc, char *argv[])
{
  test_something();
  return 0;
}

void test_something() {
  assert(true);
}
```
執行下去沒噴掉就是測試通過了，我知道可能有些人在暗自竊笑：怎麼可能有人這樣子寫測試程式，不過真的很對不起我以前真的就這樣子寫測試，
為了要測不同的東西還分成許多執行檔，導致 Makefile 裡面一堆項目，各種雷，請大家叫我雷神王。  
不過如果你已經這樣子寫測試了，把它改成 Google test 也是相當簡單的事情；每一個測試的函式會對應到Google test裡面的 TEST，
用 TEST(test\_suite\_name, test\_case\_name) 代替；主程式會由 Google test 生成不用寫，整個測試會修改成這樣：  
```cpp
// include google test
#include "gtest/gtest.h"

TEST(testSuite1, test_something) {
  EXPECT_TRUE(true) << "This should not fail";
}
```
變得簡短很多，不需要再維護我們有多少個測試，把測試寫到主程式也省掉，只需要維護好每一個單一測試即可。  

Google 測試提供一系列的 assert 跟 expect 兩種測試用的函式，
兩者的差別在於 assert 會直接將中止程式，expect 只會顯示錯誤之後繼續執行測試；基本上可以的話用 expect 就對了，在一次測試中回報盡可能多的結果。   
只要是能夠透過 ostream 輸出的內容，都可以用接續在 assert 跟 expect 後面，作為失敗時的輸出。  
Assert 跟 Expect 完整的列表可以在 Github 上 Google test 的[文件](https://github.com/google/googletest/blob/master/googletest/docs/primer.md#assertions)找到。  

再來我們就可以來編譯了，如果你是用 Makefile 的話，在編譯的時候加上 [Google test 安裝路徑](https://gist.github.com/mawenbao/9223908)，在連結的時候 -l gtest 即可。  

如果是用 CMake 的話我，請參考[這個連結](https://stackoverflow.com/questions/8507723/how-to-start-working-with-gtest-and-cmake)：  

```cmake
# Google Test
add_executable(unittest unittest.cpp)
enable_testing()
target_link_libraries(unittest gtest gtest_main)
add_test(unittestSuite unittest)
```

我們要產生一個新的執行檔 unittest，在 link library 加上 gtest 跟 gtest\_main，
CMake enable\_testing 我也不確定是什麼意思，老實說我覺得 CMake 對我來說有一點複雜到不透明了，
我很難理解每一個 command 是在做什麼，要做到什麼功能需要加上什麼 command，如果不 Google 的話也很難知道怎麼寫，有一種在寫 javascript 的感覺（誒  

編譯完成之後就會出現 unittest 這個執行檔，此時再執行即可：  
```txt
[==========] Running 3 tests from 1 test cases.
[----------] Global test environment set-up.
[----------] 3 tests from testDFA
[ RUN ] testDFA.test_dfa_rulebook
[ OK ] testDFA.test_dfa_rulebook (0 ms)
[ RUN ] testDFA.test_dfa
[ OK ] testDFA.test_dfa (0 ms)
[ RUN ] testDFA.test_dfa_design
[ OK ] testDFA.test_dfa_design (0 ms)
[----------] 3 tests from testDFA (0 ms total)

[----------] Global test environment tear-down
[==========] 3 tests from 1 test cases ran. (1 ms total)
[ PASSED ] 3 tests.
```

祝大家 google test 愉快，我相信隨著我 project 變大，很快的我會遇到更多 CMake 跟 Google Test 的用法，到時候再整理出來發文了。