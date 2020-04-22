#! usr/bin/env python3
# -*- coding: utf-8 -*-

import aiomysql
import logging


def sqllog(sql, args=None):
    logging.info('SQL:%s' % sql + (' ,Args:%s' % (args,) if args else ''))


async def create_pool(user, password, db, **kw):
    logging.info('create db connection pool...')
    kw.setdefault('host', '127.0.0.1')
    kw.setdefault('port', 3306)
    kw.setdefault('charset', 'utf8mb4')
    kw.setdefault('autocommit', True)
    kw.setdefault('maxsize', 10)
    kw.setdefault('minsize', 1)
    global __pool
    __pool = await aiomysql.create_pool(user=user, password=password, db=db, **kw)


async def select(sql, args=None, size=None):
    sqllog(sql, args)
    with await __pool.acquire() as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        try:
            await cur.execute(sql, args)
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        except:
            raise
        else:
            logging.info('rows returned: %s' % len(rs))
            return rs
        finally:
            await cur.close()


async def execute(sql, args=None):
    sqllog(sql)
    with await __pool.acquire() as conn:
        cur = await conn.cursor()
        try:
            await cur.execute(sql, args)
            affected = cur.rowcount
        except:
            raise
        else:
            return affected
        finally:
            await cur.close()
