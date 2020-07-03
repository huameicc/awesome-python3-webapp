#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: api.py
@time: 2020/04/29
@author: huameicc
"""


class Page:
    """分页信息"""
    def __init__(self, itemcount, pageindex=1, pagesize=2):
        self.itemcount = itemcount
        self.pagesize = max(pagesize, 1)
        self.pagecount = itemcount // self.pagesize + (itemcount % self.pagesize and 1)
        if pageindex > self.pagecount:
            self.pageindex = 1
            self.offset = 0
            self.limit = 0
        else:
            self.pageindex = max(pageindex, 1)
            self.offset = self.pagesize * (self.pageindex-1)
            self.limit = self.pagesize
        # pagination
        self.hasnext = self.pagecount > self.pageindex
        self.hasprev = self.pageindex > 1

    def __str__(self):
        return str(type(self))[8:-2] + \
               '(%s)' % ', '.join(map(lambda _k: '%s=%s' % (_k, repr(self.__dict__[_k])), sorted(self.__dict__)))

    __repr__ = __str__


class ApiError(Exception):
    def __init__(self, error: str, data='', msg=''):
        super().__init__(msg)
        self.error = error
        self.data = data
        self.msg = msg


class ApiValueError(ApiError):
    def __init__(self, field, msg=''):
        super().__init__('value:invalid', field, msg)


class ApiResourceNotFoundError(ApiError):
    def __init__(self, name, msg=''):
        super().__init__('resource:notFound', data=name, msg=msg)


class ApiPermissionError(ApiError):
    def __init__(self, operation='permission', msg=''):
        super().__init__('permission:forbidden', operation, msg)
