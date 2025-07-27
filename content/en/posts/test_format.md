---
title: Test Format
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
lang: en
---
# Entry Table Test

|Module|Description|
|:-|:-|
| Pipeline | Yes, this module is called pipeline. It controls the act of knocking a tier of Pipeline when there is data. It is usually used at the front end of a module, storing data provided by the previous level. |
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

2^n This upper bound is a bit ~~shameful~~ crude but useful,

# Math Test

$$ fib(n) = \frac{1}{\sqrt{5}}(\frac{1+\sqrt{5}}{2})^n-\frac{1}{\sqrt{5}}(\frac{1-\sqrt{5}}{2})^n $$

# Quote Test

The problem in Chinese is described as follows:

> We have an unknown number, when divided by 3 leaves a remainder of 2, divided by 5 leaves a remainder of 3, and divided by 7 leaves a remainder of 2. What is this number?

In plain language, it is a number which gives a remainder of 2 when divided by 3, a remainder of 3 when divided by 5, and a remainder of 2 when divided by 7. Find this number?

# Image Test

Text before image

![test image](/android-chrome-512x512.png)

Text after image

# Table Test

Text before Table

|Module|Description|
|:-|:-|
| Pipeline | Yes, this module is called pipeline. It controls the act of knocking a tier of Pipeline when there is data. It is usually used at the front end of a module, storing data provided by the previous level. |
| PipelineFilter | Filters data, controlled by the external i_pass signal to determine whether the input data should be sent to output. |
| PipelineDistribute | Drives multiple modules from one source. After a set is driven, it waits for each module to receive before sending the next set. The distributed number is controlled by parameters. |
| PipelineCombine | Collects inputs from multiple modules and integrates them into a single output. The number of collections is controlled by parameters. |
| PipelineLoop | After receiving input, it first sends out an init signal and then continuously drives the output module until the o_done signal is reached. |

Text after Table