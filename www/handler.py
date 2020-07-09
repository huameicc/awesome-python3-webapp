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
import markdown2
from aiohttp import web

from aioweb import get, post, template
from model import User, Blog, Comment, generate_id
from api import ApiValueError, ApiError, ApiResourceNotFoundError, ApiPermissionError, Page
from config import configs as cfgs

COOKIE_NAME = 'aweSession'
_COOKIE_KEY = cfgs.session.secret
_COOKIE_MAX_AGE = 86400

_RE_EMAIL = re.compile(r'^[a-z0-9\-._]+@[a-z0-9\-_]+(?:\.[a-z0-9\-_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[a-f0-9]{40}$')


# test use

@get('/test/users')
@template('test.html')
async def test_users():
    """  test_page: show users """
    users = await User.find_by()
    for u in users:
        u.passwd = '******'
    return dict(users=users)


@get('/test/index')
@template('blogs.html')
async def test_index():
    """ test_page: show index(blogs)"""
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore' \
              ' et dolore magna aliqua.'
    blogs = [Blog(id="tsb1", name="Blog Test 1", summary=summary, createtime=time.time() - 10),
             Blog(id="tsb2", name="Blog Test 2", summary=summary, createtime=time.time() - 100),
             Blog(id="tsb3", name="Blog Test 3", summary=summary, createtime=time.time() - 3900),
             Blog(id="tsb4", name="Blog Test 4", summary=summary, createtime=time.time() - 86400),
             Blog(id="tsb5", name="Blog Test 5", summary=summary, createtime=time.time() - 86400 * 10)]
    return dict(blogs=blogs)


# main page
@get('/')
@template('blogs.html')
async def index(pageindex='1'):
    """Main_Page: blogs"""
    data = await api_get_blogs(pageindex)
    return data


# user_functions
def user2cookie(user, max_age):
    expires = str(int(time.time()) + max_age)
    pss = '%s:%s:%s:%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    shss = hashlib.sha1(pss.encode('utf-8')).hexdigest()
    return '-'.join([user.id, expires, shss])


def _user_response(user):
    """construct a request to set_cookie(for logon state), return web.json_response(user)"""
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


# user pages|operations signup/in/out
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


# user sign-up apis: register, authenticate
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
    img = 'http://www.gravatar.com/avatar/%s?d=wavatar&s=120' % (hashlib.md5(email.encode('utf-8')).hexdigest())
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


# user page: users-manage-panel(admin)
@get('/manage/users')
@template('manage_users.html')
def manage_users(pageindex='1'):
    return dict(pageindex=parse_pageindex(pageindex))


# user api: get_by_page, delete
@get('/api/users')
async def api_get_users(pageindex='1'):
    pindex = parse_pageindex(pageindex)
    count = await User.find_count()
    page = Page(itemcount=count, pageindex=pindex)
    users = await User.find_by(orders=[('createtime', 0)], limit=(page.offset, page.limit))
    for u in users:
        u.passwd = '******'
    return dict(users=users, page=page)


@post('/api/user/delete')
async def api_delete_user(request, userid):
    check_permission(request)
    rs = await User.remove_by(id=userid)
    if rs != 1:
        logging.error('delete user error: %s rows affected.' % rs)
        raise ApiError('delete-user:failed', msg='comment does not exist!')
    return dict(userid=userid)


# parse pageindex
def parse_pageindex(pageindex):
    """pageindex str to int."""
    pindex = 1
    try:
        pindex = int(pageindex)
    except (TypeError, ValueError):
        pass
    return max(1, pindex)


# blog content check
def check_blog_content(name, summary, content):
    """blog fields cannot be empty."""
    name, summary, content = name.strip(), summary.strip(), content.strip()
    if not name:
        raise ApiValueError('name', 'Blog need a title.')
    if not summary:
        raise ApiValueError('summary', 'Summary cannot be empty.')
    if not content:
        raise ApiValueError('content', 'Content cannot be empty.')
    if len(summary) > 200:
        raise ApiValueError('summary', 'Summary is too long.')
    return name, summary, content


# blog pages: blog-page, blogs-manage-panel(admin), blog-create/edit-page(admin)

@get('/blog/{blogid}')
@template('blog_detail.html')
async def blog_detail(blogid):
    """
    page for one article & its comments.
    didn't use a rest-api. data is retrieved from db directly and then renderred by jinja2.
    """
    blog = await Blog.find(blogid)
    if not blog:
        raise ApiResourceNotFoundError(msg= 'this blog does not exist anymore!')
    blog.html = markdown2.markdown(blog.content)
    comments = await Comment.find_by(blog_id=blogid)
    for i, cmt in zip(range(len(comments)), comments):
        cmt.html = markdown2.markdown(cmt.content)
        cmt.index = i + 1
    return dict(blog=blog, comments=comments)


@get('/manage/blogs')
@template('manage_blogs.html')
def manage_blogs(pageindex="1"):
    """page for blogs manage panel"""
    return dict(pageindex=parse_pageindex(pageindex))


@get('/manage/blog/create')
@template('edit_blog.html')
def create_blog():
    """page for create a new article."""
    return dict(blogid='', action='/api/blog/create')


@get('/manage/blog/edit')
@template('edit_blog.html')
def edit_blog(blogid):
    """page for edit an existed article."""
    return dict(blogid=blogid, action='/api/blog/update')


# blog apis: get-by-page | get-by-id, create, update, delete

@get('/api/blogs')
async def api_get_blogs(pageindex='1'):
    """rest api: 获取一页博客，及分页信息; 可被网站首页及博客管理面板使用"""
    pindex = parse_pageindex(pageindex)
    count = await Blog.find_count()
    page = Page(count, pindex)
    blogs = await Blog.find_by(orders=[('createtime', 0),], limit=(page.offset, page.limit))
    return dict(page=page, blogs=blogs)


@get('/api/blog/{blogid}')
async def api_get_blog(blogid):
    """ get one id-specified article """
    blogs = await Blog.find_by(id=blogid)
    if not blogs:
        raise ApiResourceNotFoundError('blog', 'blog does not exist!')
    return dict(blog=blogs[0])


@post('/api/blog/create')
async def api_create_blog(request, name, summary, content):
    """ create an article"""
    _user = check_permission(request)
    name, summary, content = check_blog_content(name, summary, content)
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
    """ update an article """
    check_permission(request)
    name, summary, content = check_blog_content(name, summary, content)
    # update
    rs = await Blog.update_by(set_dict=dict(name=name, summary=summary, content=content), where_dict=dict(id=id))
    if rs != 1:
        logging.error('update blog error: %s rows affected.' % rs)
        raise ApiError('update-blog:failed', msg='blog does not exist!')
    # return same blog
    blog = Blog(id=id, name=name, summary=summary, content=content, **kwargs)
    return dict(blog=blog)


@post('/api/blog/delete')
async def api_delete_blog(request, blogid):
    """ delete one article """
    check_permission(request)
    rs = await Blog.remove_by(id=blogid)
    if rs != 1:
        logging.error('delete blog error: %s rows affected.' % rs)
        raise ApiError('delete-blog:failed', msg='blog does not exist!')
    return dict(blogid=blogid)


# comment page: comments-manage-panel(admin)
@get('/manage/comments')
@template('manage_comments.html')
def manage_comments(pageindex='1'):
    return dict(pageindex=parse_pageindex(pageindex))


# comment apis: get_by_page, create, delete

@get('/api/comments')
async def api_get_comments(pageindex='1'):
    pindex = parse_pageindex(pageindex)
    count = await Comment.find_count()
    page = Page(itemcount=count, pageindex=pindex)
    comments = await Comment.find_by(orders=[('createtime', 0)], limit=(page.offset, page.limit))
    for comt in comments:
        blog = await Blog.find(comt.blog_id)
        comt.blog_name = blog.name if blog else ''
    return dict(comments=comments, page=page)


@post('/api/comment/create')
async def api_create_comment(request, blogid, content):
    """ create one comment for specified article """
    _user = request.__user__
    if not _user:
        raise ApiPermissionError('用户似乎不在登录状态.')
    content = content.strip()
    if not content:
        raise ApiValueError('content', 'content of comment is empty.')
    comment = Comment(blog_id=blogid, user_id=_user.id, user_name=_user.name, user_image=_user.image, content=content)
    rs = await comment.insert()
    if rs != 1:
        logging.error('insert comment error: %s rows affected.' % rs)
        raise ApiError('insert-comment:failed', msg='insert comment failed.')
    return dict(comment=comment)


@post('/api/comment/delete')
async def api_delete_comment(request, commentid):
    """delete one comment by id"""
    check_permission(request)
    rs = await Comment.remove_by(id=commentid)
    if rs != 1:
        logging.error('delete comment error: %s rows affected.' % rs)
        raise ApiError('delete-comment:failed', msg='comment does not exist!')
    return dict(commentid=commentid)
