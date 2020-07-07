#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: app.py
@time: 2020/7/1
@author: huameicc
"""

import asyncio, os, json, time
import datetime
import logging
import functools
from jinja2 import Environment, FileSystemLoader
from aiohttp import web

import orm
from config import configs as cfgs
from aioweb import scan_add_routes, add_static
from handler import cookie2user, COOKIE_NAME


logging.basicConfig(level='INFO')


@web.middleware
async def log_middleware(request, handler):
    logging.info('%s %s' % (request.method, request.path))
    return await handler(request)


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """
    1. check user_cookie and bind user to request.__user__
    2. check permission for administrative operations.
    :param request:
    :param handler:
    :return:
    """
    user = await cookie2user(request.cookies.get(COOKIE_NAME))
    request.__user__ = user
    if request.path.startswith('/manage/') and not (user and user.admin):
        raise web.HTTPFound('/signin')
    return await handler(request)


@web.middleware
async def resp_middleware(request, handler):
    resp = await handler(request)
    if isinstance(resp, web.StreamResponse):
        return resp
    if isinstance(resp, int) and 100 <= resp < 600:
        return web.Response(status=resp)
    if isinstance(resp, (tuple, list)) and len(resp) == 2 and isinstance(resp[0], int) and 100 <= resp[0] < 600:
        return web.Response(status=resp[0], reason=resp[1])
    if isinstance(resp, bytes):
        return web.Response(body=resp, content_type='application/octet-stream')
    if isinstance(resp, str):
        if resp.startswith('redirect:'):
            raise web.HTTPFound(resp[9:])
        return web.Response(body=resp.encode('utf-8'), content_type='text/html', charset='utf-8')
    if isinstance(resp, dict):
        template = resp.get('__template__')
        if template is None:
            return web.json_response(resp, dumps=functools.partial(json.dumps, default=lambda x: x.__dict__))
        resp.setdefault('user', request.__user__)
        return web.Response(body=request.app['__templates__'].get_template(template).render(resp).encode('utf-8'),
                            content_type='text/html', charset='utf-8')
    return web.Response(text=repr(resp), charset='utf-8', content_type='text/plain')


def init_jinja2_template(app, template='templates', **kwargs):
    logging.info('init jinja2...')
    option = dict(
        autoescape = kwargs.pop('autoescape', True),
        auto_reload = kwargs.pop('autoreload', True)
    )
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), template)
    logging.info('set FileSystemLoader: %s' % path)
    option['loader'] = FileSystemLoader(path)
    _env = Environment(**option)
    app['__templates__'] = _env
    for name, flt in kwargs.pop('filters', dict()).items():
        _env.filters[name] = flt
    if kwargs:
        logging.warning('keys are ignored by init_jinja2: %s' % list(kwargs.keys()))
    logging.info('init jinja2 finished.')


def datetimeflt(val: float):
    t = time.time() - val
    if t < 60:
        return '1分钟前'
    if t < 3600:
        return '%.f分钟前' % (t // 60)
    if t < 86400:
        return '%.f小时前' % (t // 3600)
    if t < 604800:
        return '%.f天前' % (t // 86400)
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')


async def index(request: web.Request):
    name = request.query.get('name', 'Python')
    return web.Response(body=b'<h1>Awesome %s</h1>' % name.encode(), content_type='text/html', charset='utf-8')


async def init():
    await orm.create_pool(user=cfgs.db.user, password=cfgs.db.passwd, db=cfgs.db.database, host=cfgs.db.host,
                          port=cfgs.db.port)
    app = web.Application(middlewares=[log_middleware, auth_middleware, resp_middleware])
    # app.router.add_routes([web.get('/', index)])
    scan_add_routes(app, 'handler')
    add_static(app)
    init_jinja2_template(app, filters=dict(datetime=datetimeflt))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 9000)
    await site.start()
    logging.info('server started at http://127.0.0.1:9000...')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    loop.run_forever()
