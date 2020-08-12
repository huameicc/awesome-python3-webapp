#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file:gravatar_upgrade.py
@time:2020/07/08
@author:huameicc

d=[Value]
404: do not load any image if none is associated with the email hash, instead return an HTTP 404 (File Not Found) response
mp: (mystery-person) a simple, cartoon-style silhouetted outline of a person (does not vary by email hash)
identicon: a geometric pattern based on an email hash
monsterid: a generated 'monster' with different colors, faces, etc
wavatar: generated faces with differing features and backgrounds
retro: awesome generated, 8-bit arcade-style pixelated faces
robohash: a generated robot with different colors, faces, etc
blank: a transparent PNG image (border added to HTML below for demonstration purposes)
"""

import logging
import asyncio
import re
try:
    import orm
    from model import User, Blog, Comment
except ImportError:
    import sys
    import os
    print(os.getcwd())
    sys.path.append(os.getcwd())
    import orm
    from model import User, Blog, Comment


_REPP = r'(?<=[?&])d=[a-zA-Z]+(?=&|$)'   # &d=mm ?d=mp ?d=mp&  ...
_REPL = 'd=wavatar'

# modify http to https
# _REPP = r'^http://'
# _REPL = 'https://'


def _replace_image(string):
    """ return new image str."""
    return re.sub(_REPP, _REPL, string)


async def upgrade_setdefault_wavatar():
    await orm.create_pool('wwwdata', 'wwwdata', 'awesome')
    user_change_count, user_total_count = 0, 0
    blog_change_count, blog_total_count = 0, 0
    comt_change_count, comt_total_count = 0, 0

    def _log_final(success=True):
        logging.warning('-------- Upgrade %s! -------- ' % (success and 'Succeed' or 'Failed'))
        logging.warning('users: total(%s), updated(%s)' % (user_total_count, user_change_count))
        logging.warning('blogs: total(%s), updated(%s)' % (blog_total_count, blog_change_count))
        logging.warning('comments: total(%s), updated(%s)' % (comt_total_count, comt_change_count))
        logging.warning('#####################################')

    try:
        logging.warning('#####################################')
        logging.warning('-------- Upgrade starting: Set image default to %s.. -------- ' %_REPL)
        #
        users = await User.find_by()
        user_total_count = len(users)
        logging.warning('-- Upgrading users [%s]...' % user_total_count)
        for u in users:
            _img = _replace_image(u.image)
            if _img == u.image:
                continue
            logging.warning('-- %s ===> %s' % (u.image, _img))
            logging.debug(await User.update_by(set_dict=dict(image=_img), where_dict=dict(id=u.id)))
            user_change_count += 1

        logging.warning('-- upgrade table users finished [%s].' % user_change_count)

        #
        blogs = await Blog.find_by()
        blog_total_count = len(blogs)
        logging.warning('-- Upgrading blogs [%s]...' % blog_total_count)
        for u in blogs:
            _img = _replace_image(u.user_image)
            if _img == u.user_image:
                continue
            logging.warning('-- %s ===> %s' % (u.user_image, _img))
            logging.debug(await Blog.update_by(set_dict=dict(user_image=_img), where_dict=dict(id=u.id)))
            blog_change_count += 1
        logging.warning('-- upgrade table blogs finished [%s].' % blog_change_count)

        #
        comments = await Comment.find_by()
        comt_total_count = len(comments)
        logging.warning('-- Upgrading comments [%s]...' % comt_total_count)
        for u in comments:
            _img = _replace_image(u.user_image)
            if _img == u.user_image:
                continue
            logging.warning('-- %s ===> %s' % (u.user_image, _img))
            logging.debug(await Comment.update_by(set_dict=dict(user_image=_img), where_dict=dict(id=u.id)))
            comt_change_count += 1
        logging.warning('-- upgrade table comments finished [%s].' % comt_change_count)
        # Success
        _log_final(True)
    except:
        # Failed
        logging.exception('******* upgrade encounter an exception. *********')
        _log_final(False)
    finally:
        await orm.close_pool()


if __name__ == '__main__':
    LOG_FORMAT = "%(asctime)s - %(levelname)s : %(message)s "
    logging.basicConfig(level='WARN', format=LOG_FORMAT)
    asyncio.run(upgrade_setdefault_wavatar())
