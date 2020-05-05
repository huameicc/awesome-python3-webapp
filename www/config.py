#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: config.py
@time: 2020/5/5
@author: huameicc
"""

from config_default import configs


class DotDict(dict):
    """ dict support dot_syntax like dic.a"""
    def __init__(self, seq=None, **kwargs):
        if seq:
            if not isinstance(seq, dict):
                try:
                    seq = dict(seq)
                except:
                    raise
            for k, v in seq.items():
                kwargs.setdefault(k, v)     # kwargs覆盖seq
        for k, v in kwargs.items():
            if isinstance(v, dict):
                kwargs[k] = self.__class__(v)
        super().__init__(**kwargs)

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value


def merge(configs, override_cfgs):
    """ override default_configs by server_configs"""
    for k, v in override_cfgs.items():
        if isinstance(v, dict):
            merge(configs.setdefault(k, dict()), v)
        else:
            configs[k] = v


try:
    from config_server import configs as cfgs
    merge(configs, cfgs)
except ImportError:
    pass


configs = DotDict(configs)


if __name__ == '__main__':
    print(configs)
    print(configs.db.host, configs.session.secret)
    try:
        print(configs.db.err)
    except KeyError:
        import traceback
        print(traceback.format_exc())
