---
title: "用 verilator 輔助數位電路設計：Verilator Framework"
date: 2023-08-27
categories:
- verilog
tags:
- verilog
- verilator
series:
- verilator
forkme: rsa256
images:
- /images/verilator/verilator_flow.png
---

準備好 C model 和 SystemC 之後，我們的主角 verilator 終於帥氣登場啦。

verilator 會做什麼呢？它的使用流程是這樣子的，它會先分析你寫的 verilog/system verilog 檔案，
然後把它轉成一個 C++ 的標頭檔與實作，裡面的 class 會模擬你寫的 verilog 的行為。  
接著你寫另一個 C++ 程式，初始化 verilator 產生出來的 class，餵它 clock 和其他你想要測試的信號，
就能模擬 verilog module 在接收這些信號時的行為，詳細的使用方式，一樣請參考[強者我同學 johnjohnlin 的 blog](https://ys-hayashi.me/2020/12/verilator-2/)。
<!--more-->
容我使用我們投影片裡面的圖片來介紹這個流程：

![verilator_flow](/images/verilator/verilator_flow.png)

聽起來很美好，但使用 verilator 來驗證會有一些問題：
首先如果我們設計一個 verilog module，又要為它客製化編寫 C++ 程式來餵測資，效率會非常的差。
當然，這個問題用 iverilog 沒有比較好解，因為 iverlog 還是需要 verilog testbench，寫起來沒有比 C++ 簡單。  
問題是通常來說，寫 verilog 的工程師不會熟 C++，很難做到自己實作自己測，
但實作的人是最了解的人，交給其他人測都會顯著提高溝通成本和降低測試效率。  
因此，我們必須在實作上加上一些規範，透過這層虛擬化簡化 verilog 設計與測試，
讓不熟 C++ 的 verilog 工程師也能輕鬆使用 verilator 才行。

# valid/ready handshake protocol

由於 verilog 是硬體底層的描述語言，一般稱呼是：*硬體界的組合語言*，因此在設計的時候如果不守一些規範，
很容易就寫出無法重用的硬體模組，例如在[我還很菜的時候寫的文章]({{< relref "verilog1">}}) 直接就開始教 state machine，
這在實作完之後擴展性上就很容易炸掉。

valid/ready handshake protocol 是硬體設計上廣為使用的規範。
本體是沒有看到標準，但如 [Berkeley 大學的講義](https://inst.eecs.berkeley.edu/~cs150/Documents/Interfaces.pdf)，
以及講解最完整的 [ARM 的網頁](https://developer.arm.com/documentation/ihi0022/c/Channel-Handshake/Handshake-process)，
都顯示這個 protocol 的廣泛使用。  

大體是這樣子的，在兩個 verilog 模組間要溝通的時候，只需要 valid/ready 兩條線來溝通，
另外還有不限定大小的 data（也可以沒有 data，單純叫下一級起來做事），從前一級 Tx 連結到後一級 Rx。  
valid 由 Tx 對 Rx，表示現在介面上的資料是可傳輸的，ready 由 Rx 對 Tx，表示我現在可以接收資料；
只要在 clock 的 positive edge 時，valid/ready 都是 true，就表示傳輸成立，資料會從 Tx 傳輸到 Rx。

整體運作如下圖所示：

![validready](/images/verilator/validready.png)

1. 第一個 positive edge，valid = 0 即沒有資料要傳輸。
2. 第二個 positive edge，valid = 1 但 ready = 0 下一級還沒準備好，不會傳輸。
3. 第三個 positive edge，valid, ready = 1，傳輸成立。

在 ARM 的 AMBA 中還有兩條規範：

1. Tx 不可以等到 ready 起來了才把 valid 拉起來，這是為了效率考量，要等就會浪費一個 cycle 的時間。
2. Tx 一但把 valid 拉起來了，在傳輸成功之前就不能把 valid 再降下去。

至於 Rx 把 ready 拉起來能不能再降下去？  
這是一個二選一的問題，要不是對前一級 valid 嚴格就是對後一級 ready 嚴格，我認為是可以的。  

有了 valid/ready protocol，我們在 verilog 設計以及 verilator 測試上，
都強制規定模組為一組 valid/ready input 跟一組 valid/ready output；依照過去經驗，這能覆蓋大約 85% 的模組設計。

# DUT_wrapper

如 johnjohnlin 在 blog 所述，verilator 支援兩種模式，[C++](https://ys-hayashi.me/2020/12/verilator-2/)
 和 [SystemC](https://ys-hayashi.me/2021/01/verilator-3/)；也就是把你的 verilog 轉成 C++ 或是 SystemC。  
雖然說用 SystemC 來寫會比較方便，內建的 Clock 還有 Thread 都優於 C++ 版本，但 SystemC 有個重大的缺點：波形會倒出不來，
照著說明實作只會得到一個空的波形檔，原因不明（我心理大概有個底，應該是沒去設定時間造成的）。  

沒辦法倒波形對驗證硬體還有除錯上無疑是致命的，因此我們改用 C++，先實作一層 SystemC DUT_wrapper 把 C++ 介面接到 SystemC，
外面就能用 SystemC 的 clk 來驅動，比較方便。

```cpp
template <typename DUT>
SC_MODULE(DUTWrapper) {
  SC_HAS_PROCESS(DUTWrapper);
  DUTWrapper(const sc_module_name &name)
    : sc_module(name), ctx(new VerilatedContext), dut(new DUT(ctx.get())),
  tfp(new VerilatedFstC) {
    Init();
    SC_THREAD(Executor);
  }

  ~DUTWrapper() { tfp->close(); }
}
```

DUTWrapper 設計為泛型，可以接受 verilator 產生的任意型別的 DUT，初始化時會[準備好倒出 fst 波型檔](https://veripool.org/guide/latest/faq.html#how-do-i-generate-fst-waveforms-traces-in-c-or-systemc)；
接著會將 rst_n 降下來重設 DUT。  
是的，這裡我們假設 DUT 的時脈稱為 clk，重設叫 rst_n 而且是低態動作，是個多數通用的寫法，未來也許該改成可以設定會比較好。

```Cpp
void Init() {
  Verilated::traceEverOn(true);
  ctx->traceEverOn(true);
  dut->trace(tfp.get(), 99); // Trace 99 levels of hierarchy (or see below)
  std::string filename = std::string(dut->modelName()) + "_dump.fst";
  tfp->open(filename.c_str());

  dut->clk = 0;
  dut->rst_n = 1;
  dut->eval();
  tfp->dump(ctx->time());

  ctx->timeInc(1);
  dut->rst_n = 0;
  dut->eval();
  tfp->dump(ctx->time());

  ctx->timeInc(1);
  dut->rst_n = 1;
  dut->eval();
  tfp->dump(ctx->time());
}
```

# Connector

稍後再來看 DUT_wrapper 的 Executor，為了向 DUT 寫入跟讀出資料，我們需要實作 Connector，
分別會實作 before_clk 和 after_clk 兩個函式。  
目前我們有 [InputConnector](https://github.com/yodalee/rsa256/blob/master/vtuber/bridge/verilator/input_connector.h)
和 [OutputConnector](https://github.com/yodalee/rsa256/blob/master/vtuber/bridge/verilator/output_connector.h)
兩種子型別，一個負責把東西寫進去，一個負責把東西讀出來，
在 constructor 都會接下 DUT 的 valid/ready reference；可以繼承這個 class，
並提供 write_port/read_port 函式以便從 verilog 編譯成的 class 讀寫東西。  

input_connector 和 output_connect 的 before_clk 和 after_clk 分別都經過實測跟重構，
才能在波形檔上看到完美的波形，不會有那種 ready 在經過時脈正緣瞬間就掉下去的狀況。  
另外 Connector 也支援 random 模式，以 InputConnector 為例，在不設定 random policy 的狀況下，只要還有資料要寫入，
就一定會把 valid 信號拉起來；或者也可以用 random policy 讓 valid 信號隨機性的拉起，用來模擬實際電路運作時可能出現的狀況。

# DUT_wrapper executor
最後我們看看 DUT_wrapper 的 executor：

```cpp
void Executor() {
while (true) {
  wait(this->clk.posedge_event());

  for (auto &connector : this->connectors) {
    connector->before_clk(dut.get());
  }
  dut->clk = true;
  dut->eval();

  bool update = false;
  for (auto &connector : this->connectors) {
    update |= connector->after_clk(dut.get());
  }
  if (update) {
    dut->eval();
  }
  if (dump_waveform) {
    tfp->dump(ctx->time());
  }
  ctx->timeInc(period_ps);

  // negative edge of clk
  dut->clk = false;
  Step();
  ctx->timeInc(period_ps);
}
}
```

其實說穿了也沒什麼稀奇：
1. 每次 systemc 的 clock 正緣，就先觸發所有 connector 的 before_clk。
2. 設定時脈轉正並呼叫 verilator eval。
3. 呼叫 connector after_clk 檢查過了正緣有沒有需要修正的 valid/ready，由於 after_clk 不一定每次都會觸發，可以用回傳值跳過一次 eval。
4. 倒波形，並步進 verilator 時間。
5. 設定時脈負緣，模擬和倒波形。

# scoreboard

測試會把資料餵進我們的 DUT 裡面，出來的資料跟標準答案比較，這裡我們再實作一個 scoreboard 的 module，
內部分別有兩個 queue 接收來自 DUT 結果和標準答案。  
一但兩個 queue 都不是空的，都會對最新的答案用 memcmp 進行比較。  
據 johnjohnlin 的說法，一般來說看到錯誤的測資就可以切掉了不用讓它跑完，這裡我們是塞一下 RaiseFailure 的 callback 給它，
如果使用者想切掉就切掉，不想切掉送 empty function 進來就好了。

```cpp
void check() {
  while (goldens.size() != 0 && receiveds.size() != 0) {
    const DataType &received = receiveds.front();
    const DataType &golden = goldens.front();

    if (memcmp(&golden, &received, sizeof(DataType)) == 0) {
    } else {
      LOG(ERROR) << "Golden != Verilog Out: " << golden << " vs " << received;
      pass = false;
      RaiseFailure();
    }
    goldens.pop_front();
    receiveds.pop_front();
  }
}
```

# testbench
最後我們有個 SystemC module testbench ，把上述的模組都整在一起。

```cpp
template <typename In, typename Out, typename DUT>
SC_MODULE(TestBench) {
  DUTWrapper<DUT> dut_wrapper;
  unique_ptr<ScoreBoard<Out>> score_board;
  sc_clock clk;

  TestBench(const sc_module_name &name, bool dump_waveform = false)
    : sc_module(name), dut_wrapper("dut_wrapper", dump_waveform),
      score_board(new ScoreBoard<Out>(KillSimulation)),
      clk("clk", 1.0, SC_NS) {
    dut_wrapper.clk(clk);
  }
}
```

testbench 宣告了 systemC clk 來驅動 DUT_wrapper；初始化好 ScoreBoard 準備比較資料。  
testbench 的 run 函式負責開始 systemc 模擬，並在結束後檢查 score_board 跟 dut_wrapper 是否 pass。  

```cpp
int run(int duration, sc_time_unit unit) {
  sc_start(duration, unit);
  bool is_pass = true;
  if (!score_board->is_pass()) {
    LOG(ERROR) << "Score board result mismatch" << endl;
    is_pass = false;
  }
  if (!dut_wrapper.is_pass()) {
    LOG(ERROR) << "DUT Wrapper final check not passed" << endl;
    is_pass = false;
  }
  return !is_pass;
}
```

# 寫 Testbench

對使用者來說，現在寫 verilog 的測試變得簡單許多，大概分為：
1. 繼承 InputConnector 跟 OutputConnector，針對 verilog module 提供 write_port 跟 read_port 函式，由於我們有 pack 跟 unpack 函式，未來有機會連這步也不用做
2. 宣告 Testbench，並對 DUT wrapper 註冊這兩個模組
3. 對 Testbench 依序注入想要測試的 input 與 golden data
4. 呼叫 Testbench 的 run 函式，測試就完成了。

例如我們測試計算 2^256 mod N 是否正確的程式碼：

```cpp
int sc_main(int, char **) {
  unique_ptr<TestBench_TwoPower> testbench(
      new TestBench_TwoPower("TestBench_two_power_mod_sv", /*dump=*/true));

  auto driver =
      make_shared<Driver>(testbench->dut_wrapper.dut->i_valid,
                          testbench->dut_wrapper.dut->i_ready, nullptr);
  auto monitor = make_shared<Monitor>(
      testbench->dut_wrapper.dut->o_valid, testbench->dut_wrapper.dut->o_ready,
      [&](const OUT &out) { return testbench->notify(out); }, KillSimulation,
      nullptr);
  testbench->register_connector(
      static_cast<shared_ptr<Connector<DUT>>>(driver));
  testbench->register_connector(
      static_cast<shared_ptr<Connector<DUT>>>(monitor));

  KeyType modulus(
      "E07122F2A4A9E81141ADE518A2CD7574DCB67060B005E24665EF532E0CCA73E1");
  driver->push_back({.power = TwoPowerIn::IntType(512), .modulus = modulus});
  driver->push_back({.power = TwoPowerIn::IntType(256), .modulus = modulus});

  TestBench_TwoPower::OutType golden
  from_hex(
      golden,
      "0AF39E1F831CB4FCD92B17F61F473735C687593A931C97D2B60AD6C7443F09FDB");
  testbench->push_golden(golden);
  from_hex(
      golden,
      "0x1F8EDD0D5B5617EEBE521AE75D328A8B23498F9F4FFA1DB99A10ACD1F3358C1F");
  testbench->push_golden(golden);

  return testbench->run(1, SC_US);
```

要新增更多資料只要從 driver 跟 testbench 送即可。

當然這個框架還有很多進步的空間，例如：
* 怎麼樣一次灌大筆的資料進去？
* 如果不是一進一出的模組，該怎麼測試？
* 怎麼樣跟 cmake 的 ctest 整合等等？
在 COSCUP 之後我們也有努力在改進，但總之，有了這些工具就能專注在寫 verilog 了，
下一章就來進到實作~~垃圾語言~~ verilog 的部分吧。
