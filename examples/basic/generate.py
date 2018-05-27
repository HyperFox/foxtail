# -*- coding: utf-8 -*-
"""
basic demo

:copyright: (c) 2018 by Hyperfox
:license: BSD
"""
from foxtail.renderer import WebRenderEngine

if __name__ == '__main__':
    class Adj(object):
        def __init__(self):
            super(Adj, self).__init__()
            self.total = 10
            self.avail = 9
            self.percent = '20'

    class Obj(object):
        def __init__(self, status=0, ip='192.168.0.1'):
            super(Obj, self).__init__()
            self.status = status
            self.cpu_percent = [99, 21, 45, 78]
            self.hostname = 'test'
            self.platform = 'win'
            self.mem_total = 'mem_total'
            self.mem_avail = 'mem_avail'
            self.counter = 'counter'
            self.mem = Adj()
            self.ip = ip
            self.disk_usage = {'C': Adj(), 'D': Adj(), 'E': Adj()}
            self.revcounter0 = 'revcounter0'
            self.processes = [['pid', 'proc1', 'proc1.exe info=1']]
            self.monitor_procs = ['monitor1.py', 'monitor2.py']

    data = {'username': 'user1',
            'data': {'192.168.2.1': Obj(1),
                     '192.168.2.2': Obj(2),
                     '192.168.2.3': Obj(3),
                     '192.168.2.4': Obj(4),
                     '192.168.2.5': Obj(5)},
            'forloop': Obj(0),
            'load': '',
            'empty': '',
            }
    engine = WebRenderEngine()
    src_path = 'index.html'
    engine.render(src_path, data, 'output.html')