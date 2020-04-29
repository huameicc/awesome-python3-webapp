#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: aioweb.py
@time: 2020/04/29
@author: huameicc

Route Handler:
usage of @get or @post:
    @get('/blog/{id}')
    def handler(id):
        pass

Template using:
    @template(name)
    def handler():
        pass

"""

import logging
import inspect
import asyncio


def template(template_name):
    def decorator(func):
        func.__template__ = template_name
        return func
    return decorator


def get(path):
    def decorator(func):
        func.__method__ = 'GET'
        func.__route__ = path
        return func
    return decorator


def post(path):
    def decorator(func):
        func.__method__ = 'POST'
        func.__route__ = path
        return func
    return decorator


def _resolve_kwargs(func):
    _params, _required, _has_var_kwarg = [], [], False
    for name, param in inspect.signature(func).parameters.items():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            raise RuntimeError('POSITIONAL_ONLY param is not supported in a handler.%s %s' % (func.__name__, name))
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            _has_var_kwarg = True
        if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            _params.append(name)
            if param.default == inspect.Parameter.empty:
                _required.append(name)
    return _params, _required, _has_var_kwarg


def _has_request_arg(func):
    sig = inspect.signature(func)
    for i, (name, para) in enumerate(sig.items()):
        if name == 'request' and para.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            if i != 0:
                raise RuntimeError('request must be the first param for a handler if used. %s%s' % (func.__name__, sig))
            return True
    return False


class RequestHandler:
    """符合aiohttp的handler标准，即只有一个request参数"""
    def __init__(self, func):
        self._func = func
        self._kwargs, self._required_kwargs, self._has_var_kwarg = _resolve_kwargs(func)
        self._has_request_arg = _has_request_arg(func)

    async def __call__(self, request):
        kw = dict()
        if not self._has_var_kwarg:
            kwargs = dict()
            for k in self._kwargs:
                if k in kw:
                    kwargs[k] = kw[k]
            kw = kwargs



def add_route(app, func):
    """add_route_handler for app once per call"""
    if not callable(func):
        raise TypeError('%s is not callable.' % func)
    method = getattr(func, '__method__', None)
    path = getattr(func, '__route__', None)
    if method is None or path is None:
        raise ValueError('@get or @post needed for %s' % func)
    if not asyncio.iscoroutinefunction(func):
        func = asyncio.coroutine(func)
    logging.info('add route %s %s to %s%s' % (method, path, func.__name__, inspect.signature(func)))
    app.router.add_route(method, path, RequestHandler(func))


def scan_add_routes(app, modpath):
    """automatically add handlers to app by scanning <moudle> modpath"""
    r = modpath.rfind('.')
    if r != -1:
        mod = modpath[r+1:]
        pkg = __import__(modpath[:r], globals(), locals(), fromlist=[mod])
        mod = getattr(pkg, mod)
    else:
        mod = __import__(modpath, globals(), locals())
    logging.debug('attr which begins with _ will be ignored in scan_add_routes.')
    for fun in dir(mod):
        if fun.startswith('_'):
            continue
        fun = getattr(mod, fun)
        if not callable(fun):
            continue
        __method__ = getattr(fun, '__method__', None)
        __route__ = getattr(fun, '__route__', None)
        if __method__ is None or __route__ is None:
            if inspect.isfunction(fun):
                logging.warning('function in %s not decorated by @post or @get :%s' % (modpath, fun))
            continue
        add_route(app, fun)


if __name__ == '__main__':
    @template('index.html')
    @get(r'\usr\{id}')
    def f():
        pass
    print(f.__dict__)
