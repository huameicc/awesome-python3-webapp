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
            await cur.execute(sql.replace('?', '%s'), args)
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
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
        except:
            raise
        else:
            return affected
        finally:
            await cur.close()


# orm Field
class Field:
    def __init__(self, name, column_type, default_value, primary_key):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default_value = default_value

    def __str__(self):
        return '%s.%s' % (self.__class__.__module__, self.__class__.__name__) \
               + '(%s, %s' % (self.name, self.column_type) \
               + (self.primary_key and ', PK' or '') \
               + (self.default_value is not None and ', %s' % repr(self.default_value) or '') + ')'


class IntegerField(Field):
    def __init__(self, name, column_type='INT', default_value=None, primary_key=False):
        super().__init__(name, column_type, primary_key, default_value)


class FloatField(Field):
    def __init__(self, name, column_type='FLOAT', default_value=None, primary_key=False):
        super().__init__(name, column_type, default_value, primary_key)


class StringField(Field):
    def __init__(self, name, column_type='VARCHAR(255)', default_value=None, primary_key=False):
        super().__init__(name, column_type, primary_key, default_value)


class DateTimeField(Field):
    def __init__(self, name, column_type='DATETIME', default_value=None, primary_key=False):
        super().__init__(name, column_type, default_value, primary_key)


class ModelMetaclass(type):
    """Field 元类"""
    def __new__(msc, name, bases, attrdic):

        return super().__new__(msc, name, bases, attrdic)

class Model(metaclass=ModelMetaclass):
    def 