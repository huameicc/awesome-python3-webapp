#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file:pywatcher_agent.py
@time:2020/07/18
@author:Jason

fix problem in pycharm: can't get the accurate python virtual environ to run app.py.
"""


from pywatcher import *


if __name__ == '__main__':
    argv = sys.argv[1:]
    print(argv)
    if not argv:
        # argv = ['python', './app.py']
        # argv = ['python', '--version', '&', 'pip', '--version']
        argv = ['D:\\work\\awesome-python3-webapp\\env\\Scripts\\python', 'app.py']
        # argv = ['cmd', '/k', 'date /t']
    if len(argv) == 1 and not argv[0].startswith('python'):
        argv.insert(0, 'python')
    mgr = MyProcessMgr(command=argv)
    mgr.start_process()
    run_watch(handler=PyFileSystemEventHandler(callback=mgr), path=os.path.abspath('.'))
