---
title: "Javascript Worker"
date: 2015-05-10
categories:
- web
tags:
- javascript
series: null
---

最近在寫一些前端的東西，深覺前．端．超．難．(yay) ，接觸了HTM5 javascript 的[worker](http://www.html5rocks.com/en/tutorials/workers/basics/) ，
在這裡筆記一下：  
<!--more-->

簡單來說，一般javascript的指令，都是存在一個執行緒裡執行，而worker 則可以開另一個執行緒在背景執行， 就不會block住前端的UI的script。  

使用方法也很簡單，宣告一個worker並傳入一個檔案路徑，這個worker 就會負責執行檔案內的javascript。  
要和worker 溝通，一律要經過postmessage跟onmessage 介面：

* postmessage 代入一個參數，可以用json寫得超級複雜，包括File, Blob, ArrayBuffer都可以傳遞
* 在對方的onmessage就會被呼叫，並包含這個物件的複製版本。  

我看到的設計是這樣，在主要文件內 main.js 中，宣告worker  
```js
var worker = new Worker("workerFile");
```

在workerFile 內要定義onmessage 函式，並且用參數的command判斷執行哪個對應的函式：  
```js
this.onmessage = function(e) {
    switch(e.data.command) {
        case 'act1':
            fun_act1(e.data.payload);
        break;
    }
}
```
這時候main.js就可以利用postmessage 叫worker 作事：  
```js
worker.postMessage({
    command: 'act1',
    payload: blahblahblah
})
worker.onmessage = function(e) {
    data = e.data;
}
```
同樣我們在worker 裡面也可以呼叫postmessage，對方接口就是main.js 裡的onmessage，這樣就能做到雙方互相傳遞資料。  

如果不想要以複製的方式傳遞資料，可以改用transferable object 的方式，減少複製成本，
另外因為是多執行緒的關係，在worker 裡面，不應該去動到DOM，window, document, parent，這些都不是thread-safe。  

參考 [worker 的spec](https://html.spec.whatwg.org/multipage/workers.html)