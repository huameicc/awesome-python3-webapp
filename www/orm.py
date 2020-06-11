#! usr/bin/env python3
# -*- coding: utf-8 -*-

import aiomysql
import logging
import asyncio
from datetime import datetime


__pool = None


def sqllog(sql, args=None):
    if logging.getLogger().level == logging.DEBUG:
        logging.debug('SQL:%s' % sql + (' ARG:%s' % (str(args)[:255],) if args else ''))
    else:
        logging.info('SQL:%s' % sql)


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


async def close_pool():
    if __pool:
        __pool.close()
        await __pool.wait_closed()


async def select(sql, args=None, size=None):
    sqllog(sql, args)
    async with __pool.acquire() as conn:
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
    sqllog(sql, args)
    async with __pool.acquire() as conn:
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
    def __init__(self, name='', column_type='BIGINT', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)


class BoolField(Field):
    def __init__(self, name='', column_type='BOOLEAN', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)


class FloatField(Field):
    def __init__(self, name='', column_type='DOUBLE', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)


class StringField(Field):
    def __init__(self, name='', column_type='VARCHAR(255)', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)


class TextField(Field):
    def __init__(self, name='', column_type='MEDIUMTEXT', default=None):
        super().__init__(name, column_type, default, primary_key=False)


class DateTimeField(Field):
    def __init__(self, name='', column_type='DATETIME', default=None, primary_key=False):
        super().__init__(name, column_type, default, primary_key)

    @staticmethod
    def format(value):
        if value is None:
            return value
        return datetime.strftime(value, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def parse(value):
        if value is None:
            return value
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
                                                                     , ', '.join(map(escape, map(tbfield, fields)))
                                                                     , ', '.join('?' * len(fields)))
        attrdic['__update__'] = 'update %s set %s' % (escape(tbname),
                                                      ', '.join(map(lambda f: '`%s`=?' % f, map(tbfield, fields))))
        attrdic['__remove__'] = 'delete from %s' % (escape(tbname))
        return super().__new__(mcs, name, bases, attrdic)


class Model(metaclass=ModelMetaclass):
    __table__, __primarykey__, __select__, __insert__, __update__, __remove__ = [None] * 6
    __backmappings__, __mappings__, __fields__, __allfields__ = [[]] * 4

    def __init__(self, **kwargs):
        for k in self.__allfields__:
            setattr(self, k, kwargs.get(k))

    def __str__(self):
        return str(type(self))[8:-2] + \
               '(%s)' % ', '.join(map(lambda _k: '%s=%s' % (_k, repr(self.__dict__[_k])), sorted(self.__dict__)))

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
            kw[key] = cls.parse_value(key, v)
        return cls(**kw)

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
    def _sql_condition(cls, **kwargs):
        """
        where conditon
        :param kwargs: where condition
        :return: where_condition_sql, args_for_condition
        """
        _sql = ' where %s' % ' and '.join(map(lambda f: '`%s`=?' % cls.fieldname(f), kwargs.keys())) if kwargs else ''
        _args = tuple(cls.format_value(k, v) for k, v in kwargs.items())
        return _sql, _args

    @classmethod
    def _sql_condition_pk(cls, primary):
        if not cls.__primarykey__:
            raise RuntimeError('%s has no primary key' % cls)
        dic = dict()
        dic[cls.__primarykey__] = primary
        return cls._sql_condition(**dic)

    @classmethod
    def _sql_order(cls, orders):
        """
        order by
        :param orders: tuple list, (field, 1/0), 1: asc, 0 desc
        :return:
        """
        return ' order by %s' % ', '.join(map(lambda t: '`%s` %s' % (cls.fieldname(t[0]), 'asc' if t[1] else 'desc')
                                              , orders)) if orders else ''

    @classmethod
    async def find(cls, primary):
        """根据主键寻找"""
        where_sql, where_args = cls._sql_condition_pk(primary)
        rs = await select(cls.__select__ + where_sql + ';', args=where_args, size=1)
        return rs and cls.__initfromdb__(**rs[0]) or None

    @classmethod
    async def find_by(cls, orders=None, **kwargs):
        """
        where 查询
        :param orders:  tuple list, (field, 1/0), 1: asc, 0 desc
        :param kwargs: where condition
        :return:
        """
        where_sql, where_args = cls._sql_condition(**kwargs)
        order_sql = cls._sql_order(orders)
        rs = await select(cls.__select__ + where_sql + order_sql + ';', args=where_args)
        return [cls.__initfromdb__(**_r) for _r in rs]

    @classmethod
    async def find_count(cls, **kwargs):
        """ count(*) by where-condition"""
        if not cls.__primarykey__:
            raise RuntimeError('%s has no primary key' % cls)
        where_sql, where_args = cls._sql_condition(**kwargs)
        rs = await select('select count(*) c from `%s`%s;' % (cls.__table__, where_sql), args=where_args, size=1)
        return rs[0].get('c') if rs else 0

    async def insert(self):
        """insert new item"""
        args = list(map(self.getvalue_ordefault, self.__fields__))
        affected = await execute(self.__insert__ + ';', args)
        if affected != 1:
            logging.warning('<%s object> insert error: %s rows affected.') % (self.__class__.__name__, affected)
        return affected

    async def update(self):
        """update by pk"""
        if not self.__primarykey__:
            raise RuntimeError('%s has no primary key' % self.__class__)
        where_sql, where_args = self._sql_condition_pk(getattr(self, self.__primarykey__))
        args = list(map(self.getvalue_ordefault, self.__fields__))
        affected = await execute(self.__update__ + where_sql + ';', args=args + list(where_args))
        if affected != 1:
            logging.warning('<%s object> update error: %s rows affected.') % (self.__class__.__name__, affected)
        return affected

    @classmethod
    async def update_by(cls, set_dict, where_dict):
        """
        update by where-condition
        :param set_dict: set key=value, ..
        :param where_dict: where key=value and ..
        :return:
        """
        if not set_dict:
            return 0
        where_sql, where_args = cls._sql_condition(**where_dict)
        update_sql = 'update `%s` set %s' %(cls.__table__,
                                            ', '.join(map(lambda k: '`%s`=?' % cls.fieldname(k), set_dict)))
        set_args = tuple(cls.format_value(k, v) for k, v in set_dict.items())
        affected = await execute(update_sql + where_sql + ';', args=set_args + where_args)
        return affected

    async def remove(self):
        """delete by pk"""
        if not self.__primarykey__:
            raise RuntimeError('%s has no primary key' % self.__class__)
        where_sql, where_args = self._sql_condition_pk(getattr(self, self.__primarykey__))
        affected = await execute(self.__remove__ + where_sql + ';', args=where_args)
        if affected != 1:
            logging.warning('<%s object> remove error: %s rows affected.') % (self.__class__.__name__, affected)
        return affected

    @classmethod
    async def remove_by(cls, **kwargs):
        """delete by where-condition"""
        where_sql, where_args = cls._sql_condition(**kwargs)
        affected = await execute(cls.__remove__ + where_sql + ';', args=where_args)
        return affected

    @classmethod
    def _create_table_sql(cls):
        sql = 'create table `%s` (\n  ' % cls.__table__
        sql += ',\n  '.join(map(lambda f: '`%s` %s not null' % (cls.fieldname(f), cls.__mappings__[f].column_type)
                                  , cls.__allfields__))
        sql += ',\n  primary key(`%s`)' % cls.__primarykey__ if cls.__primarykey__ else ''
        sql += '\n) engine=innodb default charset=utf8mb4;'
        return sql

if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')

    class TM(Model):
        __table__ = 'TMTABLE'
        id = IntegerField('ID', primary_key=True)
        name = StringField('NAME')
        dt = DateTimeField('DateTime')

    async def main():
        tm = TM(id=1, name='Jim', dt=datetime.now())
        print(tm)
        # await tm.insert()
        # await tm.update()
        # await tm.remove()
        # await TM.find(2)

    asyncio.run(main())
