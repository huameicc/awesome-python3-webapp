#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: api.py
@time: 2020/04/29
@author: huameicc
"""


class ApiError(Exception):
    def __init__(self, error: str, data='', msg=''):
        super().__init__(msg)
        self.error = error
        self.data = data
        self.msg = msg