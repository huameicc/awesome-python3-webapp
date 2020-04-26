#! usr/bin/env python3
# -*- coding: utf-8 -*-

import aiomysql
import logging
from datetime import datetime


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
            logging.debug('[select] rows returned: %s' % len(rs))
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
            logging.debug('[execute] rows affected: %s' % affected)
            return affected
        finally:
            await cur.close()


# orm Field
class Field:
    def __init__(self, name, column_type, default, primary_key):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    @staticmethod
    def format(value):
        return value

    @staticmethod
    def parse(value):
        return value

    def get_default_value(self):
        return self.default() if callable(self.default) else self.default

    def __str__(self):
        return '%s.%s' % (self.__class__.__module__, self.__class__.__name__) \
               + '(%s, %s' % (self.name, self.column_type) \
               + (self.primary_key and ', PK' or '') \
               + (self.default is not None and ', %s' % repr(self.default) or '') + ')'


class IntegerField(Field):
    def __init__(self, name, column_type='INT', default=None, primary_key=False):
        super().__init__(name, column_type, primary_key, default)


class FloatField(Field):
    def __init__(self, name, column_type='FLOAT', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)


class StringField(Field):
    def __init__(self, name, column_type='VARCHAR(255)', default=None, primary_key=False):
        super().__init__(name, column_type, primary_key, default)


class DateTimeField(Field):
    def __init__(self, name, column_type='DATETIME', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)

    @staticmethod
    def format(value):
        return datetime.strftime(value, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def parse(value):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


class ModelMetaclass(type):
    """Model 元类"""
    def __new__(mcs, name, bases, attrdic):
        if name == 'Model':
            return super().__new__(mcs, name, bases, attrdic)
        tbname = attrdic.setdefault('__table__', name)
        primary_key = None
        fields = []
        mappings = dict()
        backmappings = dict()
        for k, v in attrdic.items():
            if not isinstance(v, Field):
                continue
            mappings[k] = v
            backmappings[v.name or k] = k
            if not v.primary_key:
                fields.append(k)
                continue
            if primary_key:
                raise RuntimeError('Duplicate primary key for %s: %s, %s.' % (name, primary_key, k))
            primary_key = k
        if not primary_key:
            logging.warning('No primary key for %s.' % name)
        for _ in mappings:
            attrdic.pop(_)
        all_fields = [primary_key] + fields if primary_key else fields[:]
        attrdic['__backmappings__'] = backmappings
        attrdic['__mappings__'] = mappings
        attrdic['__fields__'] = fields
        attrdic['__primarykey__'] = primary_key
        attrdic['__allfields__'] = all_fields
        tbfield = lambda f: mappings.get(f).name or f
        escape = lambda f: '`%s`' % f
        attrdic['__select__'] = 'select %s from %s' % (', '.join(map(escape, map(tbfield, all_fields))), escape(tbname))
        attrdic['__insert__'] = 'insert into %s (%s) values (%s)' % (escape(tbname)
                                                                     , ', '.join(map(escape, map(tbfield, all_fields)))
                                                                     , ', '.join('?' * len(all_fields)))
        attrdic['__update__'] = 'update %s set %s where' % (escape(tbname)
                                                           ,', '.join(map(lambda f: '`%s`=?' % f, fields)))
        attrdic['__deletesql__'] = 'delete from %s where' % (escape(tbname))
        return super().__new__(mcs, name, bases, attrdic)


class Model(metaclass=ModelMetaclass):
    __table__, __primarykey__, __select__, __insert__, __update__, __deletesql__ = [None] * 6
    __backmappings__, __mappings__, __fields__, __allfields__ = [[]] * 4

    def __init__(self, **kwargs):
        for k, v in self.__allfields__.items():
            setattr(self, k, kwargs.get(k))

    @classmethod
    def parse_value(cls, key, value):
        return cls.__mappings__.get(key).parse(value)

    @classmethod
    def format_value(cls, key, value):
        return cls.__mappings__.get(key).format(value)

    @classmethod
    def __initfromdb__(cls, **kwargs):
        """init from db result"""
        kw = dict()
        for k, v in kwargs.items():
            key = cls.__backmappings__.get(k)
            if not key:
                logging.warning('%s is not a field of %s' %(k, cls.__table__))
            kw[key] = cls.parse_value(v)
        return cls(**kw)

    def __str__(self):
        return str(type(self))[8:-2] + \
               '(%s)' % ', '.join(map(lambda _k: '%s=%s' % (_k, repr(self.__dict__[_k])), sorted(self.__dict__)))

    @classmethod
    def fieldname(cls, key):
        """
        获取属性实际的表的列名
        :param key:
        :return:
        """
        return cls.__mappings__[key].name or key

    def getvalue(self, key, default=None):
        """获取字段value"""
        if key not in self.__mappings__:
            raise AttributeError('%s is not a table-field of %s' % (key, self.__class__.__name__))
        return self.__mappings__[key].format(getattr(self, key, default))

    def getvalue_ordefault(self, key):
        """获取字段value，会去找Field定义的default"""
        val = self.getvalue(key)
        if val is not None:
            return val
        val = self.__mappings__.get(key).get_default_value()
        logging.debug('<%s object> using default value for %s: %s' % (self.__class__.__name__, key, repr(val)))
        setattr(self, key, val)
        return self.__mappings__.get(key).format(val)

    @classmethod
    async def find(cls, primary):
        """根据主键寻找"""
        if not cls.__primarykey__:
            raise RuntimeError('%s has no primary key' % cls)
        rs = await select(cls.__select__ + ' where `%s`=?;' % cls.__primarykey__
                          , (cls.format_value(cls.__primarykey__, primary),)
                          , 1)
        return rs and cls.__initfromdb__(**rs[0]) or None

    @classmethod
    async def findby(cls, orders=None, **kwargs):
        """
        where 查询
        :param orders:  tuple list, (field, 1/0), 1: asc, 0 desc
        :param kwargs: where condition
        :return:
        """
        _sql = cls.__select__
        if kwargs:
            _sql += ' where %s' % ' and '.join(map(lambda f: '`%s`=?' % cls.fieldname(f), kwargs.keys()))
        if orders:
            _sql += ' order by %s' % \
                    ', '.join(map(lambda t: '`%s` %s' % (cls.fieldname(t[0]), 'asc' if t[1] else 'desc'), orders))
        args = tuple(cls.format_value(k, v) for k, v in kwargs.items())
        rs = await select(_sql, args=args)
        return [cls.__initfromdb__(**_r) for _r in rs]


    async def save(self):
        """save new """
        args = list(map(self.getvalue_ordefault, self.__allfields__))
        affected = await execute(self.__insert__, args)
        if affected != 1:
            logging.warning('<%s object> save error: %s rows affected.') % (self.__class__.__name__, affected)
        return affected


# class TM(Model):
#     __table__ = 'TMTABLE'
#     id = IntegerField('ID')
#
# print(TM.id)