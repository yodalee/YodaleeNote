---
title: "Google Test從入門到濫用：參數化測試"
date: 2022-11-05
categories:
- Setup Guide
tags:
- cpp
- google test
series: null
---

發現好久都沒貼文了，因為從八月開始都在忙東忙西都沒時間寫 code，主力在開發的 rrxv6 又（咦我怎麼會說又呢）
在 virtio 嚴重卡關，最近是有突破然後又被 global variable 擋下來，有夠麻煩。  
會寫這篇是這樣的，從十月底小弟接到一個小任務，要用一批網路上的測資，去測試公司內一個專案的正確性，要如何做都是小弟自己決定，考量到：
1. 待測專案用 C 寫的。
2. 測資為自訂的文字格式。

最後決定用 C++ 搭配 [google test](https://github.com/google/googletest) 來開發測試，搭配大量資料進行 Data Driven Testing，
使用的 feature 為 google test 的 [value-parameterized test](https://github.com/google/googletest/blob/main/docs/advanced.md#value-parameterized-tests)。
<!--more-->

事前警告，在 google test 的對應章節中有如下的話語：

> You want to test your code over various inputs (a.k.a. data-driven testing). This feature is easy to abuse, so please exercise your good sense when doing it!

所以，請好好考慮這是不是適合用 google test 的場合，我在結尾回顧一下這段。  

這篇我會用一個，把輸入的 integer 變成 hex string 輸出的小程式來做範例。  

基本設定的部分，可以參考四年前我曾經寫過 google test 的文章[開始使用 Google Test：基本設定](https://yodalee.me/2018/07/2018_google_test/)，
應該涵蓋了本篇從安裝到基本應用，如果不需要 parameterized test，可以看那篇就好了。  

# 測試對象
我們先實作我們的 library，包含 `tohex.h`, `tohex.cpp`, `CMakeLists.txt`，以下是 tohex.cpp 的內容。
```cpp
#include "tohex.h"
#include <string>

std::string to_hex(int32_t val) {
  std::string ret("0x");
  for (size_t i = sizeof(val) * 2; i > 0;) {
    --i;
    int c = 0xf & (val >> (4 * i));
    ret.push_back(c >= 10 ? (c + 'A' - 10) : (c + '0'));
  }
  return ret;
}
```

使用 CMake 來編譯 project。

```cmake
cmake_minimum_required(VERSION 3.0.0)
project(tohex VERSION 0.1.0)
add_library(tohex tohex.cpp)
```

會產出 libtohex.a。

# Google Test

現在我們加上測試檔案 tohex_test.cpp。
```cpp
#include "tohex.h"
#include <gtest/gtest.h>

TEST(ToHexTestSuite, zero) {
  auto s = to_hex(0);
  EXPECT_EQ(s, "0x00000000");
}
```

這個檔案和上面編出來的 libadder.a、gtest 和 gtest_main 一起打包成一個執行檔。
```cmake
add_executable(adder_test adder_test.cpp)
target_link_libraries(adder_test adder gtest gtest_main)
```
執行看看：
```txt
./test_tohex                                                                                                         [0]
Running main() from /build/gtest/src/googletest-release-1.12.1/googletest/src/gtest_main.cc
[==========] Running 1 test from 1 test suite.
[----------] Global test environment set-up.
[----------] 1 test from ToHexTestSuite
[ RUN      ] ToHexTestSuite.zero
[       OK ] ToHexTestSuite.zero (0 ms)
[----------] 1 test from ToHexTestSuite (0 ms total)

[----------] Global test environment tear-down
[==========] 1 test from 1 test suite ran. (0 ms total)
[  PASSED  ] 1 test.
```
google test 會將測試的名字會命名為 Suite Name + '.' + Test Name；可以用參數 `--gtest_filter="*.*"` 來指定要跑什麼測試。

# Fixture Test

上面定義的是最基本的測試，有時候有些測試會需要一些 context，例如先開好一些 class，這時候就能改用 Test Fixture。
先從 google test 的 `::testing::Test` 繼承出 Test Fixture Class，可以在裡面實作需要的 SetUp 跟 TearDown 函式。
```cpp
class ToHexTestSuite : public ::testing::Test {
protected:
  void SetUp() override { std::cout << "Before Test" << std::endl; }
  void TearDown() override { std::cout << "After Test" << std::endl; }
};
```
測試改用 `TEST_F` 來宣告，F 表示 Fixture。

```cpp
TEST_F(ToHexTestSuite, a5) {
  auto s = to_hex(0xa5a55a5a);
  EXPECT_EQ(s, "0xA5A55A5A");
  std::cout << s << std::endl;
}
```

執行的時候會看到：
```txt
./test_tohex                                                                                                         [0]
Running main() from /build/gtest/src/googletest-release-1.12.1/googletest/src/gtest_main.cc
[==========] Running 1 test from 1 test suite.
[----------] Global test environment set-up.
[----------] 1 test from ToHexTestSuite
[ RUN      ] ToHexTestSuite.a5
Before Test
0xA5A55A5A
After Test
[       OK ] ToHexTestSuite.a5 (0 ms)
[----------] 1 test from ToHexTestSuite (0 ms total)
```

對每一個 TEST_F，google test 都會準備好一組 ToHexTestSuite，然後依序呼叫 SetUp, TestBody, TearDown。  
當然也可以把 SetUp 和 TearDown 的功能寫在 Constructor 和 Destructor，對此文件有比較兩種實作的差別，請自行參考
[Should I use the constructor/destructor of the test fixture or SetUp()/TearDown()?](http://google.github.io/googletest/faq.html#CtorVsSetUp)。

# Value-Parameterized Test

進到今天正題，如果我們今天不是測一組，而是幾千組測資呢？  
這時就可以改用 Value-Parameterized Test。首先我們先定義 parameter 的樣式，每一組測試都會帶著輸入資料和答案。
```cpp
struct ToHexTestdata {
  uint32_t in;
  std::string ans;
};
```

google test 定義了 `TestWithParam` 這個 class，在測試時要提供對應的參數，繼承這個 class 並針對我們的 `ToHexTestdata` 特化，生成對應的 TestSuite。
```cpp
class ToHexParameterSuite : public ::testing::TestWithParam<ToHexTestdata> {};
```

測試使用 TEST_P 實作，裡面可以使用 GetParam 拿到測試用的測資。
```cpp
TEST_P(ToHexParameterSuite, ParameterTest) {
  auto param = GetParam();
  auto s = to_hex(param.in);
  EXPECT_EQ(s, param.ans);
}
```

最後呼叫 `INSTANTIATE_TEST_SUITE_P`，這個 macro 有三個參數：

* InstantiationName：用來前綴在測試前的名字，以區分不同來源的測資。
* TestSuiteName：上面實作的 TestWithParam 的 Test Suite class。
* Parameter generator：生出測資的方式，目前我所用的有 Values 和 ValuesIn。

例如我們使用 google test 的 Values，直接把想測的參數寫在後面：
```cpp
INSTANTIATE_TEST_SUITE_P(
  TableInstantiation, ToHexParameterSuite,
  ::testing::Values(
    ToHexTestdata{1, "0x00000001"},
    ToHexTestdata{0xffffffff, "0xFFFFFFFF"}));
```

執行看看：
```txt
[----------] 2 tests from TableInstantiation/ToHexParameterSuite
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/0
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/0 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/1
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/1 (0 ms)
[----------] 2 tests from TableInstantiation/ToHexParameterSuite (0 ms total)
```

## 從檔案讀入測資
如果還要更多測資，不想要單純用寫的？例如我們可以用 python 生出五筆測資，並放到 testdata.txt 裡面。
```python
import random
with open("testdata.txt", "w") as f:
    for _ in range(5):
        rand = random.randrange(0, 1 << 32)
        f.write("{}\n".format(rand))
        f.write("0x{:08X}\n".format(rand))
```

在 C++ 裡面可以實作生成 parameter 的函式，回傳值必須是 std::vector<Parameter Type>（要求的應是 iterable 的容器）
```cpp
std::vector<ToHexTestdata> read_testdata(const std::string &path) {
  std::vector<ToHexTestdata> dataset;
  std::string line;
  std::ifstream fs(path);
  assert(fs.good());
  ToHexTestdata data;
  size_t lineno = 0;
  while (std::getline(fs, line)) {
    lineno++;
    if (lineno % 2 == 0) {
      data.ans = line;
      dataset.push_back(data);
    } else {
      data.in = stoi(line);
    }
  }
  return dataset;
}
```

```cpp
INSTANTIATE_TEST_SUITE_P(
  TableInstantiation, ToHexParameterSuite,
  ::testing::ValuesIn(read_testdata("testdata.txt"));
```

這樣就會執行五組測試了，上面在遇到測資不存在的時候可以不要這麼暴力直接 assert，可以用比較溫柔一點的方式處理。
```txt
[----------] 5 tests from TableInstantiation/ToHexParameterSuite
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/0
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/0 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/1
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/1 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/2
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/2 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/3
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/3 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/4
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/4 (0 ms)
[----------] 5 tests from TableInstantiation/ToHexParameterSuite (0 ms total)
```

## 為測試取名
上面我們可以看到，在 parameter test 的測試命名規則是：

**Instantiation Name + '/' + Test Suite Name + '.' + Test Name + '/' + 流水號**

但這個名字實在很難知道我們測了什麼，不過不用擔心，`INSTANTIATE_TEST_SUITE_P` 有一個選擇性的第四個參數，其型別為：

**func: TestParamInfo<class ParamType> -> std::string**

TEST_P 會用這個函式幫我們產生名字，但要注意名字只能有 alphanum 跟底線，不同測試的名字也不能重複。  
以上面為例子，我們可以在 Parameter 的 class `ToHexTestdata` 裡面加上檔名。

```cpp
struct ToHexTestdata {
  uint32_t in;
  std::string ans;
  std::string filename;
};
```

在 `read_hexdata` 裡面，把檔名跟對應的行數寫到生成的 parameter 裡：
```cpp
std::vector<ToHexTestdata> read_testdata(const std::string &path) {
  std::vector<ToHexTestdata> dataset;
  std::string line;
  std::ifstream fs(path);
  assert(fs.good());
  ToHexTestdata data;
  std::string filename = path;
  filename.erase(std::remove_if(filename.begin(), filename.end(), ::ispunct),
                 filename.end());

  size_t lineno = 0;
  while (std::getline(fs, line)) {
    lineno++;
    if (lineno % 2 == 0) {
      data.ans = line;
      data.filename = filename + "L" + std::to_string(lineno);
      dataset.push_back(data);
    } else {
      data.in = stoi(line);
    }
  }
  return dataset;
}
```

最後在呼叫 `INSTANTIATE_TEST_SUITE_P` 的時候，第四個參數用 lambda，把 TestParamInfo 的 param.filename 給解出來。
```cpp
INSTANTIATE_TEST_SUITE_P(
    TableInstantiation, ToHexParameterSuite,
    ::testing::ValuesIn(read_testdata("testdata.txt")),
    [](::testing::TestParamInfo<ToHexParameterSuite::ParamType> info) {
      return info.param.filename;
    });
```

測試的名字就變得容易辨識了。
```txt
[----------] 5 tests from TableInstantiation/ToHexParameterSuite
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL2
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL2 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL4
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL4 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL6
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL6 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL8
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL8 (0 ms)
[ RUN      ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL10
[       OK ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL10 (0 ms)
[----------] 5 tests from TableInstantiation/ToHexParameterSuite (0 ms total)
```

## 除錯名稱
另外，如果 parameterized test 在失敗的時候，會印出類似這樣的訊息：
```txt
[  FAILED  ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL10,
where GetParam() = 72-byte object <66-84 C1-33 05-00 00-00 48-B3 9C-09 17-56 00-00
0A-00 00-00 00-00 00-00 30-78 33-33 43-31 38-34 36-36 00-09 17-56 00-00 68-B3 9C-09
17-56 00-00 0E-00 00-00 00-00 00-00 74-65 73-74 64-61 74-61 74-78 74-4C 31-30 00-00>
```

這是因為 google test 也不知道要怎麼印出 Parameter，可以對這個 class 實作 `PrintToString` 函式：
```cpp
std::string PrintToString(const ToHexTestdata &data) {
  return std::to_string(data.in) + "->" + data.ans;
}
```

就能看到比較漂亮的除錯訊息了，是說這個機制對我來說有點謎，C++ 怎麼知道我提供了這個函式，並且知道要呼叫我實作的版本的？
```txt
[  FAILED  ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL2, where GetParam() = 2091174464->0x7CA4CA40
[  FAILED  ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL4, where GetParam() = 1416582898->0x546F56F2
[  FAILED  ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL6, where GetParam() = 473667187->0x1C3B9673
[  FAILED  ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL8, where GetParam() = 1508741796->0x59ED92A4
[  FAILED  ] TableInstantiation/ToHexParameterSuite.ParameterTest/testdatatxtL10, where GetParam() = 868320358->0x33C18466
```

# 結語

本篇文章我們~~濫用~~利用了 google test 的 value-parameterized test 功能，讓 google test 可以擴展到外部提供的資料；
我用了這個方法，在一周的時間測了*一萬多筆*測資。  
我個人的感想是，使用 value-parameterized test 的**要點其實不在測試，而是在於 test data**，上面可以觀察到 `TEST_P` 的內容其實非常短小，
因為大量測資的用意是要測試某個介面的正確性，而不是要找邏輯上的 bug，所以測試多半是一個函式呼叫下去，然後驗一下結果對不對。  
進行 parameter test 大部分的精力會是花在 parse data 上。你是否**能確保測資足夠穩定不會亂改格式，以及測資不要包含太多不同格式**？

畢竟 parameter test 只要測資一改就會弄爆大批測試，不斷為了資料而修正你的 parser 時，parser 自身也會出問題，
一不小心會變成要用 google test 去驗證 google test，甚至 test code 的複雜度超越本來要測的程式，這樣就本末倒置了。  

另外說到底，google test 本身是不是為了這種情境而設計的也值得商確，個人覺得在大量測試下，google test 缺乏一個總結的報表，
可以設定 xml output，不過我還沒試驗過，不知道效果如何？  
也許外面有一些更好的 data-driven testing framework 也說不定，如果大家覺得有更適合的 data-driven testing framework，也歡迎分享一下。
