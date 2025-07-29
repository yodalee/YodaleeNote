---
title: "筆記整理 FreeRTOS Context Switch"
date: 2021-06-15
categories:
- embedded system
tags:
- embedded system
- c
- arm
- assembly
series: null
---

故事是這樣子的，很早以前大概 2014/2015 的時候，就曾經因為傳說中的 jserv 大大的關係，聽聞傳說中的 FreeRTOS，然後也有不深入地小玩了一下。  
最近又因為到前公司戀戀科技的專案，竟然又接觸到（已經被 Amazon 收購的） FreeRTOS ，花了點時間把 FreeRTOS 移植到某個新的 ARM 平台，
在移植的時候也稍微仔細的 trace 了 FreeRTOS 的程式碼，順便就寫了點筆記，整理一下貼上來。  
<!--more-->

## FreeRTOS 架構

FreeRTOS 整體結構非常簡潔：
* 核心只需要 tasks.c、queue.c、list.c，分別負責管理 Task、Task 間的通訊和管理 Task 用的雙向鏈結資料結構。
* FreeRTOS 將可設定的部分獨立出來，全部塞在 FreeRTOSConfig.h 裡面，讓 FreeRTOS 能針對使用者的應用客製化，像是 heap size, preemption, timer frequency 等等的設定。
* 動態記憶體管理可選擇 portable/MemMang 的 heap_1.c 到 heap_5.c，[五種 heap 的細節如下](https://www.freertos.org/a00111.html)，一般來說用 heap_4 應該是最常見的：
  * heap_1：只有 alloc 沒有 free
  * heap_2：可以 free 但不會合併相鄰的記憶體
  * heap_3：thread safe 的 malloc/free
  * heap_4：會合併相鄰記憶體
  * heap_5：跟 heap_4 類似，不過可以讓 heap 橫跨多個不相鄰的區域：
* 另外為了對應不同的硬體，FreeRTOS 程式碼實作到一個共用的介面，往下的部分則是對應不同硬體的實作，這部分程式碼放在 portable 資料夾裡，對應不用的硬體就有不同的實作。

我看的版本是如下搭配：
* 長期發行版 [FreeRTOS LTS Release 202012.01](https://www.freertos.org/a00104.html)
* 記憶體：heap_4
* portable：GCC/ARM_CM3
* FreeRTOSConfig.h 使用[官方的範例配置](https://www.freertos.org/a00110.html)

## List.c
List 應該是最好看懂的部分啦，它的設計上就是針對 FreeRTOS 的排程而設計的，
可以想像在 List 的實體如 pxReadyTasksLists 管理的就是目前可執行的 TCB（Task Control Block），一個完整的 list 會是這樣的：
List 的資料結構 List_t
```c
typedef struct xLIST
{
  volatile UBaseType_t uxNumberOfItems;
  ListItem_t * configLIST_VOLATILE pxIndex;
  MiniListItem_t xListEnd;
} List_t;
```
* uxNumberOfItems 內含多少 items，方便快速判斷 List 是不是空的。
* xListEnd 標誌這個 List 的結尾，MiniListItem 不會儲存真正 TCB
* pxIndex 指向 List 內一個 item，注意 FreeRTOS 內部是環狀鏈結，從「第一個」item 開始，沿 next 走到 xListEnd 之後，下一個 next 會回到第一個 item，pxIndex 會指向其中一個 item。

ListItem 有兩種 MiniListItem_t 和 ListItem_t，MiniListItem_t 為 ListItem_t 的子集，兩者定義如下。
```c
struct xLIST_ITEM
{
  configLIST_VOLATILE TickType_t xItemValue;
  struct xLIST_ITEM * configLIST_VOLATILE pxNext;
  struct xLIST_ITEM * configLIST_VOLATILE pxPrevious;
  void * pvOwner;
  struct xLIST * configLIST_VOLATILE pxContainer;
};

struct xMINI_LIST_ITEM
{
  configLIST_VOLATILE TickType_t xItemValue;
  struct xLIST_ITEM * configLIST_VOLATILE pxNext;
  struct xLIST_ITEM * configLIST_VOLATILE pxPrevious;
};
```

* xItemValue 用來排序 ListItem；pxNext, pxPrevious 指向前、後兩個 Item。
* pvOwner 用 void，但在 FreeRTOS 通常會指向 TCB。
* pvContainer 指向 Item 所在的 List_t。

可以看到 MiniListItem 就是少了 pvOwner 跟 pxContainer 兩個資料，因為 ListEnd 不儲存實際的 TCB，省掉這兩個 field 可以節省一點記憶體。  
實際上畫 UML 大概是長這個樣子：

![freertoslist](/images/posts/freertoslist.png)

## Trace Code


根據個人的習慣，Trace code 從進入點開始，一個典型的 FreeRTOS 程式，大概會像這樣：
```c
void vTaskCode( void * pvParameters )
{
    for( ;; ) {};
}

int main() {
  TaskHandle_t xHandle = NULL;
  xTaskCreate(vTaskCode, "NAME", 64, (void *) 1, tskIDLE_PRIORITY, &xHandle );
  vTaskStartScheduler()
}
```

定義好 Task 要執行的 code 之後，用 xTaskCreate 生成 Task；呼叫 vTaskStartScheduler 開始，
vTaskStartScheduler 呼叫之後控制權就會轉給 OS，由 OS 負責工作的管理。

## xTaskCreate

整個 xTaskCreate 的步驟大概如下：
1. 分配 stack 記憶體
2. 分配 TCB 記憶體，設定 stack pointer
3. call prvInitializeNewTask，進行 TCB 初始化
  * 計算 stack 界限 pxTopOfStack
  * 複製 NAME 到 TCB
  * 設定 priority
  * 初始化 TCB 的 xStateListItem 和 xEventListItem，這兩個 item 各有用處，xStateListItem 會插入各 State (Ready, Pending..) 的 List 中；xEventListItem 則會插入 Event List 中，讓我們可以從 List 裡的 ListItem 找到這個 TCB
4. call prvAddNewTaskToReadyList：
  * 如果是第一個 Task 的話，會在這裡呼叫 prvInitialiseTaskLists，用以初始化下列 List，pxReadyTasksLists[], xDelayedTaskList1, xDelayedTaskList2 等等
  * 如果 pxReadyTasksLists 已經設定好，那就把新 Task 的 TCB 呼叫 prvAddTaskToReadyList 塞進去。
  * 最後如果新 Task 的 priority 比 pxCurrentTCB（現在正在執行的 TCB）高，會呼叫 taskYIELD_IF_USING_PREEMPTION -> portYIELD_WITHIN_API -> portYIELD，這個在 ARM 內觸發一個 PendSV 中斷進行 context switch，這部分下面會看到怎麼做的。

## vTaskStartScheduler

StartScheduler 會：
1. 呼叫 xTaskCreate 生成一個 IdleTask，priority 為最低的 0。
2. 關掉 Interrupt
3. 設定 xSchedulerRunning 和 xTickCount
4. 呼叫函式 xPortStartScheduler，這個函式理論上就不會回來了。

xPortStartScheduler 在 port.c 裡面，必須依據不同硬體做不同的設定：
1. ARM M3 會先設定 NVIC，設定 PendSV 跟 Systick 兩個 Interrupt 的 priority。
2. 依照配置寫入 portNVIC_SYSTICK_LOAD_REG 設定 Systick 頻率；寫入 portNVIC_SYSTICK_CTRL_REG 開啟 Systick。
3. 呼叫 prvStartFirstTask，開啟 interrupt，用 svc 0 產生 svc interrupt 準備 switch 到第一個 task。

asm 寫 svc 0 並不會告訴你硬體從這裡接手，不知道的話 trace code 到這邊就不知道下一步去哪裡了；答案是 svc interrupt 由指定的 SVC handler 接手：
```c
__asm void vPortSVCHandler( void )
{
  /* Get the location of the current TCB. */
  ldr r3, = pxCurrentTCB
  ldr r1, [ r3 ]
  ldr r0, [ r1 ]
  /* Pop the core registers. */
  ldmia r0 !, {r4-r11,r14}
  msr psp, r0
  isb
  mov r0, # 0
  msr basepri, r0
  bx r14
}
```

r3 = pxCurrentTCB pointer  
r1 = TCB_t 的第一個元素，就是 pxTopOfStack，可以在 tasks.c 的 TCB_t 的元素看到註解：  
```c
volatile StackType_t * pxTopOfStack; /*< Points to the location of the last item placed on the tasks stack.  
 THIS MUST BE THE FIRST MEMBER OF THE TCB STRUCT. */
```
因為你改了 pxTopOfStack 在 TCB 內的位置，就要連著 ASM 的 code 一起改了。  
r0 = stack 的位址  
從 r0 將值從 stack 讀取到 r4-r11, r14。  
msr 設定 stack pointer psp
bx r14 就會跳進 pxCurrentTCB 的程式開始執行，也就是我們的 vTaskCode。

## SysTick 與 PendSV

程式執行一段時間，硬體會發生 SysTick 中斷，這個中斷由 xPortSysTickHandler 承接。
1. 呼叫到 xTaskIncrementTick，記錄 tick 的變數 tickCount +1
2. 檢查和 pxCurrentTCB 相同 priority 的 pxReadyTasksLists，如果有其他的 task，設定 回傳值 xSwitchRequired 為 True。
3. 在 xPortSysTickHandler 內，xTaskIncrementTick 回傳 True 就會設定一個 PendSV 中斷。

曾經我對 PendSV 中斷的存在意義感到疑惑，比如說，為什麼我們不能像 
[mini-arm-os](https://github.com/jserv/mini-arm-os) 一樣在 systick_handler 裡面進行 Context Switch 呢？  

後來查了[一些資料](https://community.arm.com/developer/ip-products/processors/f/cortex-m-forum/4935/question-about-application-of-pendsv)之後，大致整理如下：  
一般作業系統仰賴 Systick 中斷來計時，所以 Systick 中斷的優先權會設定較高，在發生 Systick Interrupt 時，Systick 會搶佔其他中斷的 ISR，
這個時候若 OS 進行 Context Switch，因為 Context Switch 所需的時間可能未知，
表示所有優先權比 Systick 低的中斷處理都會有個長度不定的延遲，有 Real Time 要求的系統都不能接受這種事。  
另外，我們也不能把 Systick 的優先權設低（例如跟 PendSV 一樣低），因為這表示其他中斷可以搶佔 Systick，
也就是作業系統在處理計時上可能會有所延遲，而有些服務的處理可能依賴 Systick 正確地計時。

有了 PendSV 就能完美解決上述的問題，在 Systick Handler 裡面，只做非常簡單的事：
tickCount+1 並檢查 ReadyList 有沒有其他 Task 要切換，有的話就把 PendSV 中斷掛起來， Systick Handler 就結束了。  
這樣如果有其他更重要的中斷需要處理，Systick handler 很快就結束，不會卡死其他中斷；
有其他中斷要處理時，PendSV Handler 也會自動被 MCU 延遲，等到重要的事情處理完，再來處理比較不重要的 Context Switch。

## Context Switch

看了上面那麼多，終於可以講到 Context Switch 了，如上所述由 PendSV Handler xPortPendSVHandler 負責，
下面節錄 handler 最核心的部分，可以看到就是對稱的：
* 存入上一個 Task 的 register
* disable interrupt
* 呼叫 vTaskSwitchContext
* enable interrupt
* 讀取下一個 Task 的 register

```c
__asm void xPortPendSVHandler( void )
{
  extern pxCurrentTCB;
  extern vTaskSwitchContext;

  mrs r0, psp
  isb
  /* Get the location of the current TCB. */
  ldr r3, =pxCurrentTCB
  ldr r2, [ r3 ]

  /* Save the core registers. */
  stmdb r0!, {r4-r11, r14}

  /* Save the new top of stack into the first member of the TCB. */
  str r0, [ r2 ]

  stmdb sp!, {r0, r3}
  mov r0, # configMAX_SYSCALL_INTERRUPT_PRIORITY
  msr basepri, r0
  dsb
  isb
  bl vTaskSwitchContext
  mov r0, # 0
  msr basepri, r0
  ldmia sp!, {r0, r3}

  /* The first item in pxCurrentTCB is the task top of stack. */
  ldr r1, [ r3 ]
  ldr r0, [ r1 ]

  /* Pop the core registers. */
  ldmia r0!, {r4-r11, r14}
  bx r14
}
```

vTaskSwitchContext 內部會呼叫 taskSELECT_HIGHEST_PRIORITY_TASK，裡面會選出目前優先權最高的 Task ，將它設定為 pxCurrentTCB。  
Macro listGET_OWNER_OF_NEXT_ENTRY 會去拿 List 裡面，pxIndex 指向的下一個 ListItem，
如前所述，因為 pxIndex 指向的不是**第一個 Task**，而是其中一個，這個實作可以讓整個 List 裡面的 Task 都輪流執行。  

上面大概就是筆記到 FreeRTOS Context Switch 的流程，整理比我想像得還要花時間，其他筆記有機會再慢慢整理。  
