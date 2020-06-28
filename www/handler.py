#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: handler.py
@time: 2020/04/29
@author: huameicc
"""

import time
import re
import hashlib
import json
import functools
from aiohttp import web

from aioweb import get, post, template
from model import User, Blog, generate_id
from api import ApiValueError, ApiError
from config import configs as cfgs


_SESSION_NAME = 'aweSession'
_SESSION_KEY = cfgs.session.secret

_RE_EMAIL = re.compile(r'^[a-z0-9\-._]+@[a-z0-9\-_]+(?:\.[a-z0-9\-_]+){1, 4}$')
_RE_SHA1 = re.compile(r'^[a-f0-9]{40}$')

@get('/test')
@template('test.html')
async def test():
    users = await User.find_by()
    return dict(users=users)

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
    return dict(blogs=blogs)

@get('/api/users')
async def api_get_users():
    users = await User.find_by()
    for u in users:
        u.passwd = '******'
    return dict(users=users)


def user2cookie(user, max_age):
    expires = str(time.time() + max_age)
    pss = '%s:%s:%s:%s' % (user.id, user.passwd, expires, _SESSION_KEY)
    shss = hashlib.sha1().update(pss.encode('utf-8')).hexdigest()
    return '-'.join([user.id, expires, shss])


@post('/api/register')
async def api_register(name, email, passwd):
    if not name or not name.strip():
        raise ApiValueError('username')
    if not _RE_EMAIL.match(email):
        raise ApiValueError('email')
    if not _RE_SHA1.match(passwd):
        raise ApiValueError('passwd')
    users = await User.find_by(email=email)
    if len(users) >= 1:
        raise ApiError('register:failed', 'email', 'email already used.')
    uid = generate_id()
    # salt: uid
    sh_pass = hashlib.sha1().update(('%s:%s' % (uid, passwd)).encode('utf-8')).hexdigest()
    img = 'http://www.gravatar.com/avatar/%s?d=mm&s=120' % (hashlib.md5().update(email.encode('utf-8')).hexdigest())
    user = User(id=uid, name=name.strip(), email=email, passwd=sh_pass, image=img)
    rs = await user.insert()
    if rs != 1:
        raise ApiError('register:failed', '', 'save user failed.')
    user.passwd = '******'
    resp = web.json_response(data=user, dumps=functools.partial(json.dumps, default=lambda x: x.__dict__))
    resp.set_cookie(_SESSION_NAME, user2cookie(user, max_age=86400), max_age=86400, httponly=True)
    return resp