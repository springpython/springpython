"""
   Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.       
"""

# stdlib
import logging

# Circuits
from circuits import Component, Manager, Debugger

# ThreadPool
from threadpool import ThreadPool, WorkRequest, NoResultsPending

# Spring Python
from springpython.util import TRACE1
from springpython.context import InitializingObject
from springpython.jms import WebSphereMQJMSException, NoMessageAvailableException

class MessageHandler(object):
    def handle(self, message):
        raise NotImplementedError("Should be overridden by subclasses.")

class WebSphereMQListener(Component):
    """ A JMS listener for receiving the messages off WebSphere MQ queues.
    """
    def __init__(self):
        super(Component, self).__init__()
        self.logger = logging.getLogger("springpython.jms.listener.WebSphereMQListener(%s)" % (hex(id(self))))
        
    def _get_destination_info(self):
        return "destination=[%s], %s" % (self.destination, self.factory.get_connection_info())

    def run(self, *ignored):
        while True:
            try:
                message = self.factory.receive(self.destination, self.wait_interval)
                self.logger.log(TRACE1, "Message received [%s]" % str(message).decode("utf-8"))
                
                work_request = WorkRequest(self.handler.handle, [message])
                self.handlers_pool.putRequest(work_request)
                
                try:
                    self.handlers_pool.poll()
                except NoResultsPending, e:
                    pass

            except NoMessageAvailableException, e:
                self.logger.log(TRACE1, "Consumer did not receive a message. %s" % self._get_destination_info())
                
            except WebSphereMQJMSException, e:
                self.logger.error("%s in run, e.completion_code=[%s], "
                    "e.reason_code=[%s]" % (e.__class__.__name__, e.completion_code, e.reason_code))
                raise

class SimpleMessageListenerContainer(InitializingObject):
    """ A container for individual JMS listeners.
    """
    
    def __init__(self, factory=None, destination=None, handler=None, 
                 concurrent_listeners=1, handlers_per_listener=2, wait_interval=1000):
        """ factory - reference a to JMS connection factory
        destination - name of a queue to get the messages off
        handler - reference to an object which will be passed the incoming messages
        concurrent_listeners - how many concurrent JMS listeners the container
                               will manage
        handlers_per_listener - how many handler threads each listener will receive
        wait_interval - time, in milliseconds, indicating how often each JMS
                        listener will check for new messages
        """

        self.factory = factory
        self.destination = destination
        self.handler = handler
        self.concurrent_listeners = concurrent_listeners
        self.handlers_per_listener = handlers_per_listener
        self.wait_interval = wait_interval
        
        self.logger = logging.getLogger("springpython.jms.listener.SimpleMessageListenerContainer")
    
    def after_properties_set(self):
        """ Run by Spring Python after all the JMS container's properties have
        been set.
        """
        
        for idx in range(self.concurrent_listeners):
            # Create as many Circuits managers as there are JMS listeners.
            manager = Manager()
            manager.start()
            
            # A pool of handler threads for each listener.
            handlers_pool = ThreadPool(self.handlers_per_listener)
            
            # Each manager gets assigned its own listener.
            listener = WebSphereMQListener()
            
            # Assign the listener and a debugger component to the manager.
            manager += listener
            manager += Debugger(logger=self.logger)
            
            listener.factory = self.factory
            listener.destination = self.destination
            listener.handler = self.handler
            listener.handlers_pool = handlers_pool
            listener.wait_interval = self.wait_interval
            listener.start()
