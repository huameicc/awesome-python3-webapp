#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: model.py
@time: 2020/04/27
@author: huameicc
"""

def generate_id():
    return '%015d%s000' % (time.time() * 1000, uuid.uuid4().hex)


import time, uuid
from www.orm import Model, StringField, IntegerField, FloatField, BoolField, TextField


class User(Model):
    __table__ = 'users'

    id = StringField(column_type='varchar(50)', default=generate_id, primary_key=True)
    name = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)', default='')
    email = StringField(column_type='varchar(50)', default='')
    admin = BoolField(default=False)
    createtime = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(column_type='varchar(50)', default=generate_id, primary_key=True)
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    user_image = StringField(column_type='varchar(500)')
    name = StringField(column_type='varchar(50)')
    summary = StringField(column_type='varchar(200)', default='')
    content = TextField()
    createtime = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(column_type='varchar(50)', default=generate_id, primary_key=True)
    blog_id = StringField(column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    user_image = StringField(column_type='varchar(500)')
    content = TextField()
    createtime = FloatField(default=time.time)
