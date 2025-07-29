---
title: "Test Format"
date: 2000-01-01
categories:
- test
tags:
- tag1
- tag2
series:
- test
latex: true
draft: true
weight: 1
AITranslated: true
---

# Entry Table Test

|Module|Description|
|:-|:-|
| Pipeline | 是的這個 module 就叫 pipeline，它控制有 data 要敲一級 Pipeline 這件事，通常會用在一個 module 的最前端，上一級給資料我就先存下來 |
<!--more-->

# Block Test

> Normal quote.

> This is a warning.
{.warning}

> This is dangerous.
{.error}

# Title Test H1
## Title Test H2
### Title Test H3
#### Title Test H4
##### Title Test H5
###### Title Test H6

Content

# Code Test

```python
a = b = 1
while b < 1000000000000:
  print(b)
  a, b = a+b, a
```

# Del Test

2^n 這個上界有點~~可恥~~粗糙但有用，

# Math Test

$$ fib(n) = \frac{1}{\sqrt{5}}(\frac{1+\sqrt{5}}{2})^n-\frac{1}{\sqrt{5}}(\frac{1-\sqrt{5}}{2})^n $$  

# Quote Test

中文問題描述如下：

> 今有物不知其數，三三數之剩二，五五數之剩三，七七數之剩二，問物幾何？

白話翻譯就是有一個數除三餘二、除五餘三、除七餘二，求這個數？  

# Image Test

Text before image

![test image](/android-chrome-512x512.png)

Text after image

# Table Test

Text before Table

|Module|Description|
|:-|:-|
| Pipeline | 是的這個 module 就叫 pipeline，它控制有 data 要敲一級 Pipeline 這件事，通常會用在一個 module 的最前端，上一級給資料我就先存下來 |
| PipelineFilter | 過濾資料，透過外接的 i_pass 訊號，控制輸入資料要不要送去輸出 |
| PipelineDistribute | 一對多驅動多個模組，一次驅動後要等待每個模組都收下才會再送下一組，分散的數量透過 parameter 來控制 |
| PipelineCombine | 收集來自多個模組的輸入整合為一個輸出，收集的數量透過 parameter 來控制 |
| PipelineLoop | 在收到 input 之後，先送出 init signal，接著持續驅動 output module 直到 o_done 訊號為止 |

Text after Table