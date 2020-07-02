#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: handler.py
@time: 2020/04/29
@author: huameicc
"""

import logging
import time
import re
import hashlib
import json
import functools
from aiohttp import web

from aioweb import get, post, template
from model import User, Blog, generate_id
from api import ApiValueError, ApiError, ApiResourceNotFoundError, ApiPermissionError, Page
from config import configs as cfgs

COOKIE_NAME = 'aweSession'
_COOKIE_KEY = cfgs.session.secret
_COOKIE_MAX_AGE = 86400

_RE_EMAIL = re.compile(r'^[a-z0-9\-._]+@[a-z0-9\-_]+(?:\.[a-z0-9\-_]+){1,4}$')
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
    blogs = [Blog(id="tsb1", name="Blog Test 1", summary=summary, createtime=time.time() - 10),
             Blog(id="tsb2", name="Blog Test 2", summary=summary, createtime=time.time() - 100),
             Blog(id="tsb3", name="Blog Test 3", summary=summary, createtime=time.time() - 3900),
             Blog(id="tsb4", name="Blog Test 4", summary=summary, createtime=time.time() - 86400),
             Blog(id="tsb5", name="Blog Test 5", summary=summary, createtime=time.time() - 86400 * 10)]
    return dict(blogs=blogs)


@get('/api/users')
async def api_get_users():
    users = await User.find_by()
    for u in users:
        u.passwd = '******'
    return dict(users=users)


def user2cookie(user, max_age):
    expires = str(int(time.time()) + max_age)
    pss = '%s:%s:%s:%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    shss = hashlib.sha1(pss.encode('utf-8')).hexdigest()
    return '-'.join([user.id, expires, shss])


def _user_response(user):
    """ set_cookie, return user json"""
    user_cookie = user2cookie(user, max_age=_COOKIE_MAX_AGE)
    user.passwd = '******'
    resp = web.json_response(data=user, dumps=functools.partial(json.dumps, default=lambda x: x.__dict__))
    resp.set_cookie(COOKIE_NAME, user_cookie, max_age=_COOKIE_MAX_AGE, httponly=True)
    logging.info('%s[%s] signed in.' % (user.name, user.email))
    return resp


async def cookie2user(val):
    if not val or not isinstance(val, str):
        return None
    li = val.split('-')
    if not len(li) == 3:
        return None
    uid, expires, shss = li
    # 过期
    try:
        if int(expires) < time.time():
            return None
    except BaseException as e:
        logging.exception(e)
        return None
    # 验证密码
    user = await User.find(uid)
    if not user:
        return None
    _s = '%s:%s:%s:%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    sh1 = hashlib.sha1()
    sh1.update(_s.encode('utf-8'))
    if shss != sh1.hexdigest():
        logging.info('invalid cookie.')
        return None
    user.passwd = '******'
    return user


def check_permission(request):
    """manage operations permission check: admin=1 needed."""
    _user = request.__user__
    if not _user or not _user.admin:
        raise ApiPermissionError()
    return _user


@get('/signup')
@template('register.html')
def signup():
    return {}


@get('/signin')
@template('signin.html')
def signin():
    return {}


@get('/signout')
def signout():
    resp = web.HTTPFound('/')
    resp.set_cookie(COOKIE_NAME, '--', max_age=0, httponly=True)
    raise resp


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
    sh_pass = hashlib.sha1(('%s:%s' % (uid, passwd)).encode('utf-8')).hexdigest()
    img = 'http://www.gravatar.com/avatar/%s?d=mm&s=120' % (hashlib.md5(email.encode('utf-8')).hexdigest())
    user = User(id=uid, name=name.strip(), email=email, passwd=sh_pass, image=img)
    rs = await user.insert()
    if rs != 1:
        raise ApiError('register:failed', '', 'insert user failed.')
    return _user_response(user)


@post('/api/authenticate')
async def api_authenticate(email, passwd):
    if not email:
        raise ApiValueError('email', 'Invalid email.')
    if not passwd:
        raise ApiValueError('passwd', 'Invalid passwd.')
    users = await User.find_by(email=email)
    if len(users) < 1:
        raise ApiValueError('email', 'This email is not registered.')
    user = users[0]
    sh_pass = hashlib.sha1(('%s:%s' % (user.id, passwd)).encode('utf-8')).hexdigest()
    if sh_pass != user.passwd:
        raise ApiValueError('passwd', 'Password is wrong.')
    return _user_response(user)


def check_blog_empty(name, summary, content):
    """blog fields cannot be empty."""
    name, summary, content = name.strip(), summary.strip(), content.strip()
    if not name:
        raise ApiValueError('name', 'Blog need a title.')
    if not summary:
        raise ApiValueError('summary', 'Summary cannot be empty.')
    if not content:
        raise ApiValueError('content', 'Content cannot be empty.')
    return name, summary, content


def parse_pageindex(pageindex):
    pindex = 1
    try:
        pindex = int(pageindex)
    except (TypeError, ValueError):
        pass
    return max(1, pindex)


@get('/manage/blogs')
@template('manage_blogs.html')
def manage_blogs(pageindex="1"):
    return dict(pageindex=parse_pageindex(pageindex))


@get('/manage/blog/create')
@template('edit_blog.html')
def create_blog():
    return dict(blogid='', action='/api/blog/create')


@get('/manage/blog/edit')
@template('edit_blog.html')
def edit_blog(blogid):
    return dict(blogid=blogid, action='/api/blog/update')


@get('/api/blogs')
async def api_get_blogs(pageindex='1'):
    pindex = parse_pageindex(pageindex)
    count = await Blog.find_count()
    page = Page(count, pindex)
    blogs = await Blog.find_by(orders=[('createtime', 0),], limit=(page.offset, page.limit))
    return dict(page=page, blogs=blogs)


@get('/api/blog/{blogid}')
async def api_get_blog(blogid):
    blogs = await Blog.find_by(id=blogid)
    if not blogs:
        raise ApiResourceNotFoundError('blog', 'blog not exists.')
    return dict(blog=blogs[0])


@post('/api/blog/create')
async def api_create_blog(request, name, summary, content):
    _user = check_permission(request)
    name, summary, content = check_blog_empty(name, summary, content)
    # insert new blog
    blog = Blog(user_id=_user.id, user_name=_user.name, user_image=_user.image, name=name, summary=summary,
                content=content)
    rs = await blog.insert()
    if rs != 1:
        logging.error('insert blog error: %s rows affected.' % rs)
        raise ApiError('create-blog:failed', msg='insert blog failed.')
    return dict(blog=blog)


@post('/api/blog/update')
async def api_update_blog(request, name, summary, content, id, **kwargs):
    check_permission(request)
    name, summary, content = check_blog_empty(name, summary, content)
    # update
    rs = await Blog.update_by(set_dict=dict(name=name, summary=summary, content=content), where_dict=dict(id=id))
    if rs != 1:
        logging.error('update blog error: %s rows affected.' % rs)
        raise ApiError('update-blog:failed', msg='blog not exists.')
    # return same blog
    blog = Blog(id=id, name=name, summary=summary, content=content, **kwargs)
    return dict(blog=blog)


@post('/api/blog/delete')
async def api_delete_blog(request, blogid):
    check_permission(request)
    rs = await Blog.remove_by(id=blogid)
    if rs != 1:
        logging.error('delete blog error: %s rows affected.' % rs)
        raise ApiError('delete-blog:failed', msg='blog not exists.')
    return dict(blogid=blogid)