#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: handler.py
@time: 2020/04/29
@author: huameicc
"""


from aioweb import get, template
from model import User, Blog

import time

@get('/test')
@template('test.html')
async def test():
    users = await User.find_by()
    return dict(users=users, __template__=index.__template__)

@get('/')
@template('blogs.html')
async def index():
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore' \
              ' et dolore magna aliqua.'
    blogs= [Blog(id="tsb1", name="Blog Test 1", summary=summary, createtime=time.time()-10),
            Blog(id="tsb2", name="Blog Test 2", summary=summary, createtime=time.time()-100),
            Blog(id="tsb3", name="Blog Test 3", summary=summary, createtime=time.time()-3900),
            Blog(id="tsb4", name="Blog Test 4", summary=summary, createtime=time.time()-86400),
            Blog(id="tsb5", name="Blog Test 5", summary=summary, createtime=time.time()-86400*10)]
    return dict(blogs=blogs, __template__=index.__template__)
