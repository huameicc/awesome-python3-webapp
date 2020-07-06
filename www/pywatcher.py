#!usr/bin/python3
# -*- coding: utf-8 -*-

"""
@file: pywatcher.py
@time: 2020/07/03
@author: huameicc
"""

import os, sys, subprocess
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer


class PyFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent):
        if event.src_path.endswith('.py'):
            print('py file changed: %s' % event.src_path)
            self.callback()


class MyProcessMgr:
    def __init__(self, command=('echo', 'ok')):
        self.command = list(command)
        self.process = None  # type: subprocess.Popen

    def kill_process(self):
        if self.process:
            print('process %s terminating...' % self.process.pid)
            self.process.terminate()
            self.process.wait()
            print('process terminated: %s' % self.process.returncode)
        self.process = None

    def start_process(self):
        self.process = subprocess.Popen(self.command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        print('start process %s: ' % self.process.pid + ' '.join(self.command))

    def restart_process(self):
        self.kill_process()
        self.start_process()

    def __call__(self, *args, **kwargs):
        return self.restart_process()


def run_watch(handler, path):
    obsrv = Observer()
    obsrv.schedule(handler, path, recursive=True)
    obsrv.start()
    print('start watching: %s' % path)
    try:
        while obsrv.is_alive():
            obsrv.join(1)
    except KeyboardInterrupt:
        obsrv.stop()
        print('pywatcher KeyboardInterrupt')
    print('pywatcher stop.')
    obsrv.join()


if __name__ == '__main__':
    argv = sys.argv[1:]
    print(argv)
    if not argv:
        argv = ['python', './app.py']
        # argv = ['python', '--version', '&', 'pip', '--version']
        # argv = ['cmd', '/k', 'date /t']
    if len(argv) == 1 and not argv[0].startswith('python'):
        argv.insert(0, 'python')
    mgr = MyProcessMgr(command=argv)
    mgr.start_process()
    run_watch(handler=PyFileSystemEventHandler(callback=mgr), path=os.path.abspath('.'))
