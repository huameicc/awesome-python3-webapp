#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file:gravatar_upgrade.py
@time:2020/07/08
@author:huameicc
"""

import logging
import asyncio
import orm
import re
from model import User, Blog, Comment


async def upgrade_setdefault_wavatar():
    await orm.create_pool('wwwdata', 'wwwdata', 'awesome')
    try:
        #
        users = await User.find_by()
        logging.debug('user number: %s', len(users))
        for u in users:
            _img = re.sub('(?<=[?&])d=[a-zA-Z]+(?=&|$)', 'd=wavatar', u.image)
            if _img == u.image:
                continue
            logging.info('%s ===> %s' % (u.image, _img))
            u.image = _img
            logging.debug(await u.update())
        logging.info('upgrade set image default to wavatar: table users finished.')

        #
        blogs = await Blog.find_by()
        logging.debug('blog number: %s', len(blogs))
        for u in blogs:
            _img = re.sub('(?<=[?&])d=[a-zA-Z]+(?=&|$)', 'd=wavatar', u.user_image)
            if _img == u.user_image:
                continue
            logging.info('%s ===> %s' % (u.user_image, _img))
            u.user_image = _img
            logging.debug(await u.update())
        logging.info('upgrade set image default to wavatar: table users finished.')

        #
        comments = await Comment.find_by()
        logging.debug('comment number: %s', len(comments))
        for u in comments:
            _img = re.sub('(?<=[?&])d=[a-zA-Z]+(?=&|$)', 'd=wavatar', u.user_image)
            if _img == u.user_image:
                continue
            logging.info('%s ===> %s' % (u.user_image, _img))
            u.user_image = _img
            logging.debug(await u.update())
        logging.info('upgrade set image default to wavatar: table users finished.')
    except BaseException as e:
        logging.error(e)
        raise
    finally:
        await orm.close_pool()


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    asyncio.run(upgrade_setdefault_wavatar())
