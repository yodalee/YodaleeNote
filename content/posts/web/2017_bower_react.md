---
title: "使用bower安裝react 前端環境"
date: 2017-01-14
categories:
- web
- simple setup
tags:
- javascript
- python
- react
- bower
series: null
---

最近寫message-viewer ，想在bottle.py 執行的server 上面跑React.js，於是就小找了一下，
基本上排除了使用 bottle-react 這種懶人套件，我想要的就是能直接寫，同時react jsx 也能在我的管控之下的設定。  
後來找到[這篇文章](https://realpython.com/blog/python/the-ultimate-flask-front-end/)，照著它的步驟、跟留言的回覆做就成功了，在這邊整理一下：  
<!--more-->

這裡就不介紹React.js 的運作原理了，筆者到目前也還在學，總之我們就跟裡面的一樣，先寫個 view.html，裡面沒什麼，
就是用React 寫一個Hello World，直接使用 [cdnjs](https://cdnjs.com/libraries/react/) 提供的 react library：  
```html
<!DOCTYPE html>
<html>
  <head lang="en">
    <meta charset="UTF-8">
    <title>View Test</title>
  </head>
  <body>
    <div id="content"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.1.0/react.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.1.0/react-dom.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/babel-core/5.8.38/browser.min.js"></script>

    <script type="text/babel">
var hello = React.createClass({
  render: function() {
    return (<h2>Hello World!</h2>);
  }
});

ReactDOM.render(
  React.createElement(hello, null),
  document.getElementById('content')
);
    </script>
  </body>
</html>
```

接著我們使用任何一種server 的template engine ，我這裡用的是Jinja2就能把網頁跑起來，因為script 來自CDN，
所以不必特別設定就能直接使用，打開來應該會出現h1 的Hello World。  
```python
app.route('/view', 'GET', MessageViewHandler)
@route('/view')
def MessageViewHandler():
    template = JINJA_ENVIRONMENT.get_template('view.html')
    return template.render()
```
下一步我們要在自己的電腦上面裝上React，我們使用的是前端的管理程式bower，像是bootstrap, React 什麼的都可以裝，  

因為我是用archlinux ，本身就提供了bower 套件，所以可以用 pacman 裝bower；非archlinux 的發行版就要用npm 裝bower：  
```bash
$ npm install -g bower
$ npm init  
$ npm install --save-dev bower   
```
有了bower之後，在project 中初始一個bower：  
```bash
$ bower init   
```

設定直接接受預設設定即可，它會產生一個 bower.json 檔案，我們另外要指定bower 安裝檔案的路徑為static，這要編輯 .bowerrc 並加入下列內容：  
```json
{  
    "directory": "./static/bower\_components"  
}
```
並使用bower 安裝套件，可以用
```bash
bower install <package\_name> --save
```
或是在bower.json 中加入套件名之後，再呼叫 bower install

我們這裡用第二種方法，在bower.json 的dependency 下面加上：  
```json
"dependencies": {
  "bootstrap": "^3.3.6",
  "react": "^15.1.0",
  "babel": "^5.8.38"
}
```
並執行 bower install，就能安裝好所需的套件，這時project 中的檔案應該差不多是這樣：  

```txt
.bowerrc  
.gitignore  
bower.json  
package.json  
static/bower\_components  
template/   
```
現在可以把上面的cdnjs 換成本地資料夾的static link:  
```html
<script src="/static/bower\_components/react/react.min.js"></script>  
<script src="/static/bower\_components/react/react-dom.min.js"></script>  
<script src="/static/bower\_components/babel/browser.min.js"></script>
```

同時在server 要加上static handler來處理所有對static 的連結：  
```python
@route('/static/<path:path>')
def callback(path):
    return static_file(path, root='static')
```

這樣應該就能在python server 上面寫react.js 的網頁前端了，把剛剛的view.html 打開來跑跑看吧。