# Python Web App
## 网站效果查看
[boboriji][blogurl]

[blogurl]: https://boboriji.com

## 项目简介
本项目是基于Python协程技术实现的一个异步博客WebApp.主要实现功能:  
1. 博客文章列表页面，及文章详细阅读页面（文章支持markdown）。
2. 用户注册、登录。
3. 普通用户评论文章。
4. 管理员面板可查阅、新建、编辑、删除文章；查看、删除用户；查看、删除评论。

## 主要技术栈
python 3.7  
mysql 5.7  
uikit 2.27.5  
vue 2.6.11  
jquery 3.5.1  
os(开发): windows 10  
os(部署): centos 7

## 项目说明
后端语言使用Python3.7, 基于第三方aiohttp库开发实现完整的后端python web异步框架，并使用jinja2作为其模板语言。利用python元类实现一个异步orm框架，用来支持Mysql数据库的连接与相应操作。

前端使用uikit 2作为网站的主要结构及css样式实现；使用Vue管理前端页面的数据及部分网页内容（如分页模块生成）；使用Jquery控制网页元素，实现Ajax.

后端与前端数据交互使用了大量的restful接口，使结构更为清晰、简洁。

