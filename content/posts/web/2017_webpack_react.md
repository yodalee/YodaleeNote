---
title: "使用webpack打包React.js 專案"
date: 2017-01-19
categories:
- web
- simple setup
tags:
- javascript
- react
- webpack
series: null
---

在[上一篇]({{< relref "2017_bower_react.md">}})我們終於在server 上把React.js 跑起來之後，就能繼續寫下去，
結果很快的我們就遇到另一個問題，那就是怎麼所有code 都擠在一塊了(yay，  

我們上一篇解法的問題，在於我們template render 這個網頁之後，相關的檔案全塞在用 `<script>`引入的javascript 檔案裡，
然後這個文件就引不入其他文件了，而React 提倡的模組化該是能把各元件分別歸檔才是。  
幸好，我們還是有解法的，利用webpack 讓我們把檔案分開，然後用webpack 打包成單一的 javascript 檔案，據說這種寫法就是**入坑**，9
因為一用了webpack 就脫不了身，之後都會綁死在webpack 上面。  
網路上有些[相關的文件](https://rhadow.github.io/2015/04/02/webpack-workflow/  )，就來一步步跟著做：  
<!--more-->

首先先準備我們的front-end/main.jsx，因為使用到react跟react-dom，因此在檔案開頭用require 引入，完成的main.jsx 像這樣：  
```js
'use strict'

var React = require('react')
var ReactDOM = require('react-dom')

var hello = React.createClass({
  render: function() {
    return (<h2>Hello World!</h2>);
  }
});

ReactDOM.render(
  React.createElement(hello, null),
  document.getElementById('content')
);
```

使用npm 安裝webpack ：  
```bash
npm install --save-dev webpack   
```

編輯webpack 的設定檔webpack.config.js：   
```js
var path = require('path');

var config = {
  entry: [path.resolve(__dirname, './front-end/main.jsx')],
  output: {
    path: path.resolve(__dirname, './static'),
    filename: 'bundle.js'
  },
};

module.exports = config;
```

這時候使用webpack 來打包，會出現錯誤訊息：  
```txt
ERROR in ./front-end/main.jsx  
Module parse failed: /home/yodalee/website/message-downloader/front-end/main.jsx Unexpected token (8:12)  
You may need an appropriate loader to handle this file type.   
```
明顯它看不懂react 的jsx 語法，我們需要設定webpack.config.js 遇到 jsx 檔案就使用babel-loader，
還要排除本地的node\_modules 裡面的檔案，與output 同層加上 module 設定：  
```js
var config = {
  entry: [path.resolve(__dirname, './front-end/main.jsx')],
  output: {
    path: path.resolve(__dirname, './static'),
    filename: 'bundle.js'
  },
  module: {
    loaders: [{
        test: /\.jsx?$/,
        loader: 'babel-loader',
        exclude: path.join(__dirname, 'node_modules')
    }]
    },
};
```
並編輯babel的設定檔 .babelrc：  
```json
{ "presets": ["react"], }
```

並且使用npm 安裝babel-loader和preset react：  
```bash
npm install --save-dev babel-loader babel-core babel-preset-react react react-dom   
```
這樣就能用webpack 幫忙打包所有檔案了，有了這個我們就能…嗯…把bower 給刪掉啦(・∀・)。  

現在bundle.js 產生在static 裡面，我們可以把template/view.html 清得乾乾淨淨只剩下這樣就會動了：  
```html
<!DOCTYPE html>
<html>
  <head lang="en">
    <meta charset="UTF-8">
    <title>View Test</title>
  </head>
  <body>
    <div id="content"></div>
    <script src="/static/bundle.js"></script>
  </body>
</html>
```

有沒有覺得超級神奇，我也是這麼覺得的。  
老實說你要說我一知半解我也認了，前端真的是各種古怪離奇，我看網路上那堆stack overflow的答案怎麼每個都不太一樣，然後試著做不能動的居多(yay，這篇要不是強者我同學人生勝利組一哥冠霖大神的指導，根本要試超久才試得出來。  

下面整理一些相關的錯誤訊息：  
```txt
Unexpected token  
```
well 它看不懂 jsx 的檔案，所以需要用babel-loader 來處理 jsx 檔  

```txt
Module not found: Error: Cannot resolve module 'react'  
```
表示它在node\_modules 裡面找不到require 的module，使用npm 安裝即可  

```txt
ERROR in ./front-end/main.jsx  
Module build failed: Error: Couldn't find preset "react" relative to directory "/home/yodalee/website/message-downloader"  
```
這個是指 babel-loader 沒有相關的……套件？像上面裝了babel-preset-react 就解掉了。  

本文感謝強者我同學人生勝利組一哥冠霖大神的指導