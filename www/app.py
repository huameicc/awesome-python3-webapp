import asyncio, os, json, time
import logging
import functools
from aiohttp import web
from www.aioweb import scan_add_routes


logging.basicConfig(level='INFO')


@web.middleware
async def log_middleware(request, handler):
    logging.info('%s %s' % (request.method, request.path))
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
        return web.Response(body=resp.encode('utf-8'), content_type='text/html; charset=utf-8')
    if isinstance(resp, dict):
        template = resp.get('__template__')
        if template is None:
            return web.json_response(resp, dumps=functools.partial(json.dumps, default=lambda x: x.__dict__),
                                     content_type='application/json; charset=utf-8')
        return web.Response(body=app['__templates__'].get_template(template).render(resp).encode('utf-8'),
                            content_type='text/html; charset=utf-8')
    return web.Response(text=repr(resp), charset='utf-8', content_type='text/plain; charset=utf-8')


def init_jinja2_template():
    pass


async def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html')


async def init():
    app = web.Application(middlewares=[log_middleware, resp_middleware])
    app.router.add_routes([web.get('/', index)])
    scan_add_routes(app, 'www.handler')
    init_jinja2_template()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 9000)
    await site.start()
    logging.info('server started at http://127.0.0.1:9000...')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    loop.run_forever()
