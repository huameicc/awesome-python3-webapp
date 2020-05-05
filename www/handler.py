#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: handler.py
@time: 2020/04/29
@author: huameicc
"""


from aioweb import get, template
from model import User

@get('/')
@template('test.html')
async def index():
    users = await User.find_by()
    return dict(users=users, __template__=index.__template__)