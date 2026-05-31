---
title: "使用 Xilinx 開發板：連接 Interrupt"
date: 2026-05-15
categories:
- FPGA
tags:
- Xilinx
- Vivado
series:
- XilinxBoard
---

故事是這樣子的，一般來說 IP 的工作流程，我們會透過 AXI Lite 寫入 register 
叫 IP 開始工作，那我們要怎麼知道 IP 工作已經完成了？
<!--more-->

最簡單的方法就是把 IP 狀態映射到一個 register 上，驅動就不斷的去~~騷擾~~讀那個 
register，這在實作上叫做 busy polling，簡單粗暴，缺點是驅動就卡死在這裡不能做其他事。  
另一種則是 IP 在完成工作的時候打一個 interrupt 出來，處理器接收到這個 interrupt
就能回頭叫驅動去處理 IP 的收尾工作。

這篇文我們就來看看怎麼做這件事。

# 實驗用的 IP

實驗用的 IP 是這樣的，輸入一個 32 bits 的 threshold，啟動之後計算 
threshold cycles 之後，會發出 done signal。  
一樣使用 AI 幫助實作：

> Implement an Interrupter module.  
> Input start and 32 bits threshold.  
> Output done and 32 bits id.  
> Upon start, run threshold cycles, assert and hold the done signal.  
> Increment id every time a done happens. 

```systemverilog
module interrupter (
  input  logic        clk,
  input  logic        rst_n,

  input  logic        start,
  input  logic [31:0] threshold,

  output logic        done,
  output logic [31:0] id
);

logic [31:0] counter;
logic        running;

always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    counter <= 32'd0;
    running <= 1'b0;
    done    <= 1'b0;
    id      <= 32'd0;
  end else begin
    // Start condition
    if (!running) begin
      running <= 1'b1;
      counter <= 32'd0;
    end
    else begin
      if (counter == threshold - 1) begin
        running <= 1'b0;
        done    <= 1'b1;
        id      <= id + 1;
      end else begin
        counter <= counter + 1;
      end
    end
  end
end
endmodule
```

其實 id 沒什麼必要，刪掉也行。

# 連接 block diagram

打包 IP 基本上就參考之前的 [AXILite]({{<relref "PynqZ2_AXILite" >}})
，接兩個 input register 0, 1 給 start 跟 threshold；
output registers 2, 3 給 done, id。

Interrupt 的設定參考下面這篇 [Interrupt 官方文章](https://pynq.readthedocs.io/en/v3.1/pynq_libraries/interrupt.html)
需要的模組是 AXI Interrupt Control，雙擊點開的設定如下：

![Interrupt Config](/images/xilinx/interrupt_0config.png)

* 我們的 interrupt 模式是 level，我設定是設 manual 並打入 0xFFFFFFFFF
* Processor Interrupt Type 選擇 Level Interrupt
* Processor Interrupt Output connection 選擇 Single

跟上一篇一樣再吐槽一次，Xilinx 你們的 UI 是出了什麼問題？  
這個 auto/manual toggle 是什麼鬼啦，到底 Auto 是 edge interrupt 
還是 level interrupt？

雙擊點開 Zynq 處理器的設定，在 Interrupt 的設定中，啟動 PL-PS Interrupt 
的 F2P shared interrupt。

![Block Diagram](/images/xilinx/Interrupt_1irqport.png)

開始連線，把 IP 的 done 連接到 Interrupt Control 的 Intr[0:0]
Interrupt Control 的 irq 連進 zynq 處理器的 IRQ_F2P 埠
完成的 block diagram 如下圖：
![Block Diagram](/images/xilinx/Interrupt_2block_diagram.png)

# 測試結果

以下是測試用的 python code，ol? 會在 IP 中看到 _interrupts 的物件。

```python
from pynq import Overlay
import timeit
import time

ol = Overlay("interrupt.bit")
ol?
i_int = ol.Interrupter_0
print(i_int._interrupts)
```

_interrupts 的內容
```
{'int_done': {
    'controller': 'axi_intc_0',
    'index': 0,
    'fullpath': 'Interrupter_0/int_done'}
}
```

## 測試一：使用 Polling

```python
ids = []
def by_polling():
    i_int.write(0, 1)
    while(True):
        done = i_int.read(0)
        if done != 0:
            break
    ids.append(i_int.read(4))

for threshold in [1, 10, 100, 1000, 10000, 100000, 1000000]:
    i_int.write(4, threshold)
    exectime = timeit.timeit(by_polling, number=100)
    print(exectime, exectime/100*1e6)
```

測試結果：
| threshold | total time (s) | average time (μs)
|:----|:--------|:--------|
| 1e0 | 0.00663 | 66.3    |
| 1e1 | 0.00655 | 65.5    |
| 1e2 | 0.00701 | 70.1    |
| 1e3 | 0.00813 | 81.3    |
| 1e4 | 0.01690 | 169.0   |
| 1e5 | 0.10566 | 1056.6  |
| 1e5 | 1.00625 | 10062.5 |

## 測試二：使用 Interrupt

由於 Interrupt 會使用 python 的 await 
來實作，一時半刻沒辦法用 timeit 測量，就先改用比較直接的 time 來測試。

```python
for threshold in [1, 10, 100, 1000, 10000, 100000, 1000000]:
    i_int.write(4, threshold)
    ids = []
    start = time.time()
    for _ in range(100):
        i_int.write(0, 1)
        await i_int.int_done.wait()
        ids.append(i_int.read(4))
    end = time.time()
    exectime = end - start
    print(exectime, exectime/100*1e6)
```

| threshold | total time (s) | average time (μs) |
|:----|:--------|:--------|
| 1e0 | 0.09080 | 908.0   |
| 1e1 | 0.07787 | 778.7   |
| 1e2 | 0.07563 | 756.2   |
| 1e3 | 0.08248 | 824.8   |
| 1e4 | 0.07689 | 768.9   |
| 1e5 | 0.16393 | 1639.3  |
| 1e5 | 1.05565 | 10556.5 |

測試結果由 polling 勝出，interrupt 平均會花 700 μs 
的時間，才能讓處理器知道可以接下去運行；如果使用 polling 的話，執行一結束 CPU 
平均 60 μs 就讀到 register 更新了。

不確定打開 Interrupt Control 的 Fast Interrupt 會有多大影響，有機會來試試。

# 結語

這樣就把幾個玩 Xilinx 板子需要的基礎都講完啦。  
只要能組合 AXI Lite, AHB，AXI Stream 跟 Interrupt，相信要連接大部分的 IP
都不成問題才對。  