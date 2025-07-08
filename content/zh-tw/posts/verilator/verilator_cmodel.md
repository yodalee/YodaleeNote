---
title: "用 verilator 輔助數位電路設計：C model 與 SystemC"
date: 2023-02-13
categories:
- verilog
tags:
- verilog
- verilator
series:
- verilator
forkme: rsa256
latex: true
---

用 verilator 的目的，就是要驗證 verilog 的實作是正確的，但我們又怎麼知道什麼是正確的呢？  
就要準備好 C model 跟 SystemC 的實作了。
<!--more-->

C model 其實沒有一定要用 C 寫，只要能夠模擬你的實作、得到標準答案的輸入與輸出，要求速度用 python 實作也 OK，
但選用 C/C++ 的一個優勢在於 verilator 是用 C++ 寫的，所以用 C/C++ 寫的 model 比較能和 verilator 的驗證結合在一起。  
SystemC 則是一套 C++ 的函式庫，幫助你實作比較接近底層的硬體行為，把一個大系統拆解成 SystemC 實作的小塊，
在軟體設計時就考慮到硬體實作，減少硬體在未來需要重新設計的風險。

# C model v1

依我自己工作時作為 hardware tester 的經驗，我之前公司的 C model 跟電路設計這邊是分開的，
有獨立的 repository 在管理，使用時要獨立把它簽出來編譯成執行檔，編譯之後輸入輸出是透過檔案來進行。  

在這個專案設計之初，我是依照這個經驗在設計的，因此我第一版的 C model 是使用 
[GNU多重精度運算庫 libgmp](https://gmplib.org/) 來開發，這個 v1 後來被 v2 替換掉了，原因下述。  
下面是[保留在 github 上面](https://github.com/yodalee/rsa256/blob/a6dbc6/cmodel/rsa.cpp)的檔案內容：
```cpp
void two_power_mod( mpz_t out, const unsigned power, const mpz_t N) {
  mpz_t base;
  mpz_init_set_ui(base, 1u);

  for (int i = 0; i < power; ++i) {
    mpz_mul_ui(base, base, 2u);
    if (mpz_cmp(base, N) > 0) {
      mpz_sub(base, base, N);
    }
  }
  mpz_set(out, base);
}

void montgomery_base2(mpz_t out, const mpz_t A, const mpz_t B, const mpz_t N) {
  mpz_t round_result; // S in doc
  mpz_init_set_ui(round_result, 0);

  for (int i = 0; i < 256; ++i) {
    bool bit_i = mpz_tstbit(A, i);
    if (bit_i) {
      mpz_add(round_result, round_result, B);
    }
    bool is_odd = mpz_tstbit(round_result, 0);
    if (is_odd) {
      mpz_add(round_result, round_result, N);
    }
    mpz_tdiv_q_ui(round_result, round_result, 2u);
  }
  if (mpz_cmp(round_result, N) > 0) {
    mpz_sub(round_result, round_result, N);
  }
  mpz_set(out, round_result);
}

void lsb_modular_exponentiation(mpz_t out, const mpz_t A,
    const mpz_t B, const mpz_t N) {
  mpz_t square; // T in doc
  mpz_t multiple; // S in doc
  mpz_init_set(square, A);
  mpz_init_set_ui(multiple, 1u);

  for (int i = 0; i < 256; ++i) {
    bool bit_i = mpz_tstbit(B, i);
    if (bit_i) {
      montgomery_base2(multiple, multiple, square, N);
    }
    montgomery_base2(square, square, square, N);
  }

  mpz_set(out, multiple);
}

void rsa(mpz_t out, const mpz_t msg, const mpz_t key, const mpz_t N) {
  mpz_t pack_value;
  mpz_t packed_msg;
  mpz_t crypto_msg;
  mpz_inits(pack_value, packed_msg, crypto_msg, NULL);

  two_power_mod(pack_value, 512, N);
  montgomery_base2(packed_msg, msg, pack_value, N);
  lsb_modular_exponentiation(out, packed_msg, key, N);
}
```

我並沒有打算解釋為什麼 RSA 是這樣做啦…。  
簡單來說最關鍵的是 [montgomery algorithm](https://en.wikipedia.org/wiki/Montgomery_modular_multiplication)，
因為給定 a, b, N，要計算 $ a \cdot b \bmod N $，在取餘數-也就是除法-會很慢
而 montgomery algorithm 可以很快的算完 $ 2^{-256} \cdot a \cdot b \bmod N $。  
因此只要我們先準備好 $ 2^{512} \bmod N $，搭配 montgomery 實作 square and multiply ，
就能很快算出 rsa 需要的 modular exponential 了。  

並不是我們用了 libgmp 就可以直接去算 $ m^e \bmod N $，
不然 libgmp 甚至有附安全版本的 [modular exponential](https://gmplib.org/manual/Integer-Exponentiation)，
rsa 一行指令就寫完了；實作要使用 montgomery C-model 就要盡量用 montgomery 去算，
未來在實作 SystemC 和硬體的時候才有標準答案可以驗證。

# C model v2

在我堪堪作完 C model 開始進到 SystemC 之後，因為自己對 SystemC 不熟，多次諮詢強者我同學 johnjohnlin 大大，
後來他看不下去直接跳下來實作了。  
也多愧了 johnjohnlin 大大的加入，他對 C++ 就熟稔程度跟我不是同一個檔次的，
本來我是使用 SystemC 內建的 [Arbitrary Width Bit Type **sc_bv**](https://www.asic-world.com/systemc/data_types3.html) 來實作，
johnjohnlin 跳進來直接實作一套模擬 verilog register 的 class，也支援 verilog 的各種運算，
例如位移、邏輯運算、加減乘除等等。  
相關的實作可見[專案的 common/include/verilog 資料夾](https://github.com/yodalee/rsa256/tree/master/common/include/verilog)，
至於他因為這個專案又弄出另一套 [namedtuple](https://github.com/johnjohnlin/namedtuple) 的 C++ 工具函式庫，又是另一回事了。

有了這套 verilog 的 class 後，rsa 的 C model 也用 vint 改寫，選個 montgomery 的部分來比較看看：

```cpp
constexpr unsigned kBW_RSA = 256;
typedef verilog::vuint<kBW_RSA> rsa_key_t;

void montgomery_base2(rsa_key_t &out, const rsa_key_t &A, const rsa_key_t &B,
                      const rsa_key_t &N) {
  using extend_key_t = verilog::vuint<kBW_RSA + 2>;
  extend_key_t round{0};
  const extend_key_t extend_B = static_cast<extend_key_t>(B);
  const extend_key_t extend_N = static_cast<extend_key_t>(N);
  for (int i = 0; i < 256; ++i) {
    if (A.Bit(i)) {
      round += extend_B;
    }
    if (round.Bit(0)) {
      round += extend_N;
    }
    round >>= 1;
  }
  if (round > extend_N) {
    round -= extend_N;
  }
  out = static_cast<rsa_key_t>(round);
}
```

比起 version 1，有更明確的指出輸入輸出，以及中間儲存結果的位元數，這是 libgmp 的 model 做不到的。  

在這個階段我跟 johnjohnlin 有爭執過一段時間，兩者分別的主張是：
|我的主張| johnjohnlin 的主張|
|:-|:-|
|C model 沒必要跟實作綁這麼緊，用 libgmp 實作可以跳過細節，專注在演算法上，模擬硬體行為是之後 SystemC 開發者的責任|與硬體行為相近的實作是必要的，愈是貼近未來在驗證上的阻力就愈小|

當然，這兩者的差距在這個 project 上面還看不太出來，畢竟 RSA 稱不上是多複雜的演算法，處理的資料量也很小，
最後就選了 johnjohnlin 的方案，直接在 C model 實作上更貼近最終硬體。  

希望大家能在下面留下各位的意見跟經驗了。

## C model Test

C model 的開發都透過 [google test 進行測試](https://github.com/google/googletest)，
部分子模組的測資是利用 python 去生的，也有一些是數學上的預期結果，例如 $ Montgomery(2^{256}, A) = A $；
另外，當初修課的講義也有留下一些測資。  
以下是 rsa256 的其中一組測試：
```cpp
TEST(RsaTest, test_rsa) {
  // example from tech document or using python hex(m0 ** key % N)
  string str_N("E07122F2A4A9E81141ADE518A2CD7574DCB67060B005E24665EF532E0CCA73E1");
  string str_key("10001");
  string str_m0("412820616369726641206874756F53202C48544542415A494C452054524F50");
  string str_c0("D41B183313D306ADCA09126F3FED6CDEC7DCDCE49DB5C85CB2A37F08C0F2E31");
  rsa_key_t N, key, m0, c0, out;
  from_hex(N, str_N);
  from_hex(key, str_key);
  from_hex(m0, str_m0);
  from_hex(c0, str_c0);

  // check output
  rsa(out, m0, key, N);
  EXPECT_EQ(out, c0);
}
```

# SystemC

就 RSA256 來看，其實 C model 跟 SystemC 的差距真的很小，因為我們在 C model 的部分就把演算法切割得差不多了，
幾個不同的地方像是 SystemC 每個函式還是成包成 class，並且會定義出輸入/輸出的資料型別。  
我個人是推薦直接使用 *模組名稱 + In* 跟 *模組名稱 + Out* 來定義輸入/輸出的資料型別，例如：

```cpp
struct RSAModIn {
  friend ::std::ostream &operator<<(::std::ostream &os, const RSAModIn &v) {
	os << typeid(v).name() << "{" << v.msg << ", " << v.key << ", " << v.modulus
   	<< ::std::endl;
	return os;
  }
  KeyType msg;
  KeyType key;
  KeyType modulus;
};
using RSAModOut = KeyType;
```

定義 operator<< 是 SystemC 的要求，有考慮過要不要設計一個基礎的型別實作 operator<<，輸入輸出都繼承那個基礎型別就好，
但最後沒有這樣設計；另外即便輸出型別就是 `KeyType`，仍然使用 using 造出別名，以示區隔。

下面就是使用 SystemC 實作的 RSA module，在下一章介紹 verilator framework 會看到，設計硬體模組的時候，
大多會使用所謂的 valid/ready handshake protocol，可以很直接地對應到 SystemC 的 FIFO，
因此模組的介面使用 sc_fifo_in/sc_fifo_out 來參考到外部的 fifo。  
相較 C model 可以直接呼叫函式，SystemC 各函式都被包裹在模組之中，位在上層的模組也要規畫好對應使用的 fifo：
```cpp
SC_MODULE(RSA256) {
  sc_in_clk clk;
  sc_fifo_in<RSAModIn> i_data;
  sc_fifo_out<KeyType> o_crypto;

  RSAMontgomery i_montgomery;
  RSATwoPowerMod i_two_power_mod;
  sc_fifo<RSATwoPowerModIn> two_power_mod_in;
  sc_fifo<RSATwoPowerModOut> two_power_mod_out;
  sc_fifo<RSAMontgomeryModIn> montgomery_in;
  sc_fifo<RSAMontgomeryModOut> montgomery_out;

  SC_CTOR(RSA256)
  	: i_montgomery("i_montgomery"), i_two_power_mod("i_two_power_mod") {
    // two_power_mod
    i_two_power_mod.clk(clk);
    i_two_power_mod.data_in(two_power_mod_in);
    i_two_power_mod.data_out(two_power_mod_out);
    // montgomery
    i_montgomery.clk(clk);
    i_montgomery.data_in(montgomery_in);
    i_montgomery.data_out(montgomery_out);
    SC_THREAD(Thread);
  }

  void Thread();
};
```

以下是 Thread 函式的實作，變數在未來會對應到所需的 verilog register，每一對 fifo 的 module_in.write 跟 module_out.read，
就是對一個模組寫入輸入並等待輸出，來模擬 verilog module 的讀寫。

```cpp
void RSA256::Thread() {
  char str[256];
  while (true) {
    const RSAModIn &in = i_data.read();
    const RSATwoPowerModIn::TwoPowerMod_Power_t vuint512{512};
    two_power_mod_in.write({.power = vuint512, .modulus = in.modulus});

    auto pack_value = two_power_mod_out.read();
    montgomery_in.write({.a = in.msg, .b = pack_value, .modulus = in.modulus});
    auto packed_msg = montgomery_out.read();
    const auto &key = in.key;

    KeyType crypto;
    KeyType multiple{1};
    KeyType square{packed_msg};
    for (size_t i = 0; i < kBW; i++) {
      if (key.Bit(i)) {
        montgomery_in.write({.a = multiple, .b = square, .modulus = in.modulus});
        multiple = montgomery_out.read();
      }
      montgomery_in.write({.a = square, .b = square, .modulus = in.modulus});
      square = montgomery_out.read();
    }
    crypto = multiple;
    o_crypto.write(crypto);
  }
}
```

如此一來，一個複雜的演算法，就能透過 SystemC 拆分成很多小小的模組，提供了實作及模組間連結的參考，
每個小模組就能分別交由下面的人來實作。  
例如這版的 RSA 我挑戰一個更激進的目標，我只要用*一個* montgomery module，讓我的 RSA 面積降到最小，
不同於我在作業裡用的*三個*，雖然說作業這樣實作是因為有速度要求，square and multiply 要兩個 montgomery 同時處理才夠快，
montgomery 也不能一次 1 個 bit，要一次實作 2 個 bits 的版本才夠快。

以上大概就是 C model 與 SystemC 的概述，準備好我們的 RSA256 C model 和 SystemC，下一回終於要進到我們的主角 verilator 了。
