# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license. 
# See the NOTICE for more information.

import os

import gevent
from gevent import core
from gevent import monkey
monkey.noisy = False
from gevent.pool import Pool
from gevent import wsgi

import gunicorn
from gunicorn.workers.base import Worker

class GEvent2Worker(Worker):
    
    base_env = {
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'SERVER_SOFTWARE': 'gevent/%s gunicotn/%s' % (gevent.__version__,
                                                    gunicorn.__version__),
        'SCRIPT_NAME': '',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    
    @classmethod
    def setup(cls):
        from gevent import monkey
        monkey.patch_all()
   
    def handle_request(self, req):
        gevent.getcurrent()
        gevent.spawn(self.handle, req)
       
    def handle(self, req):
        handle = wsgi.WSGIHandler(req)
        handle.handle(self)
        
    def run(self):
        self.socket.setblocking(0)
        env = self.base_env.copy()
        
        env.update({
            'SERVER_NAME': self.address[0],
            'SERVER_PORT': str(self.address[1]) 
        })
        self.base_env = env
        
        
        http = core.http()
        http.set_gencb(self.handle_request)
        self.application = self.wsgi
        acceptor = gevent.spawn(http.accept, self.socket.fileno())
        
        try:
            while self.alive:
                self.notify()
            
                if self.ppid != os.getppid():
                    self.log.info("Parent changed, shutting down: %s" % self)
                    gevent.kill(acceptor)
                    break
                gevent.sleep(0.1)            

        except KeyboardInterrupt:
            pass


        
        
        