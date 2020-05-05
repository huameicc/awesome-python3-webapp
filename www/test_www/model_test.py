#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: model_test.py
@time: 2020/04/27
@author: huameicc
"""

import logging
import asyncio
import orm
from model import User, Blog, Comment


async def test():
    await orm.create_pool('wwwdata', 'wwwdata', 'awesome')
    try:
        u = User(name='Test', email='test@hello.com', passwd='666666', image='about:blank')
        logging.debug(await u.insert())
    except BaseException as e:
        logging.error(e)
    # find all users
    try:
        logging.debug('user number: %s', await User.find_count())
        users = await User.find_by(name='test')
        logging.debug(', '.join(map(str, users)))
        if users:
            user = users[0]
            user.passwd = '654321' if user.passwd == '123456' else '123456'
            logging.debug(await user.update())
    except BaseException as e:
        logging.error(e)
    finally:
        await orm.close_pool()


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    asyncio.run(test())
