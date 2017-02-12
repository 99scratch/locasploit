#!/usr/bin/env python3
from source.modules._generic_module import *

class Module(GenericModule):
    def __init__(self):
        self.authors = [
            Author(name='Vitezslav Grygar', email='vitezslav.grygar@gmail.com', web='https://badsulog.blogspot.com'),
        ]
        
        self.name = 'locasploit.update.vulnerabilities'
        self.short_description = 'Updates vuln database.'
        self.references = [
            '',
        ]
        
        self.date = '2016-10-25'
        self.license = 'GNU GPLv2'
        self.version = '1.0'
        self.tags = [
            'locasploit',
            'update',
            'CVE',
            'CPE',
            'exploit',
        ]
        self.description = """
This module calls other modules to keep local vulnerability database up to date, namely:
    locasploit.update.cve
    locasploit.update.exploit
    locasploit.cleanup

This should be run frequently, as the list of modified CVE entries is being held for up to 8 days.
"""
        
        self.dependencies = {
        }
        self.changelog = """
"""

        self.reset_parameters()

    def reset_parameters(self):
        self.parameters = {
            'SILENT': Parameter(value='no', mandatory=True, description='Suppress the output'),
            'BACKGROUND' : Parameter(value='yes', mandatory=True, description='yes = run in background, no = wait for it...'),
            #'TIMEOUT' : Parameter(value='5', mandatory=True, description='Number of seconds to wait'),
        }

    def check(self, silent=None):
        if silent is None:
            silent = positive(self.parameters['SILENT'].value)
        result = CHECK_PROBABLY
        # check parameters
        silent = positive(self.parameters['SILENT'].value)
        if not positive(self.parameters['BACKGROUND'].value) and not negative(self.parameters['BACKGROUND'].value):
            if not silent:
                log.err('Bad %s value: %s.', 'BACKGROUND', self.parameters['BACKGROUND'].value)
            result = CHECK_FAILURE
        #if not self.parameters['TIMEOUT'].value.isdigit() or int(self.parameters['TIMEOUT'].value) < 0:
        #    if not silent:
        #        log.err('Bad timeout value: %d', int(self.parameters['TIMEOUT'].value))
        #    result = CHECK_FAILURE
        # can import urlib?
        try:
            from urllib.request import urlretrieve
        except:
            if not silent:
                log.err('Cannot import urllib.request library (urllib5).')
            # TODO other ways?
            result = CHECK_FAILURE

        return result
    
    def run(self):
        silent = positive(self.parameters['SILENT'].value)
        background = positive(self.parameters['BACKGROUND'].value)
        # # # # # # # #
        #t = Thread(silent, int(self.parameters['TIMEOUT'].value))
        t = Thread(silent, background)
        if positive(self.parameters['BACKGROUND'].value):
            return t
        t.start()
        t.join()
        # # # # # # # #
        return None
    
        
class Thread(threading.Thread):
    def __init__(self, silent, background): #,timeout):
        threading.Thread.__init__(self)
        self.silent = silent
        #self.timeout = timeout
        self.terminate = False
        self.background = background
            
    # starts the thread
    def run(self):
        from datetime import datetime
        # TODO check self.terminate somewhere!
        if self.terminate:
            return
        from urllib.request import urlretrieve
        last = lib.db['vuln'].get_property('last_update')
        log.info('Last update: %s' % ('never' if last == -1 else last))

        m = lib.modules['locasploit.update.cve']
        m.parameters['BACKGROUND'].value = 'yes' if self.background else 'no' 
        last_update = lib.db['vuln'].get_property('last_update')
        if last_update != DB_ERROR and (datetime.now() - datetime.strptime(last_update, '%Y-%m-%d')).days < 8:
            log.info('Entries have been updated less than 8 days ago, checking Modified feed only...')
            m.parameters['YEARS'].value = 'Modified'
        else:
            log.info('Entries have been updated more than 8 days ago, checking all feeds for change...')
            m.parameters['YEARS'].value = ' '.join(map(str, range(2002, datetime.now().year+1)))
        log.info('Will update following years: '+ m.parameters['YEARS'].value)
        job = m.run()
        # get job id so we can wait for it
        lucid = None if job is None else [lib.scheduler.add(m.name, time.time(), job)]
        m = lib.modules['locasploit.update.exploit']
        m.parameters['BACKGROUND'].value = 'yes' if self.background else 'no' 
        job = m.run()
        lue = None if job is None else [lib.scheduler.add(m.name, time.time(), job, timeout=None, waitfor=lucid)]
        # cleanup
        m = lib.modules['locasploit.cleanup']
        m.parameters['BACKGROUND'].value = 'yes' if self.background else 'no' 
        job = m.run()
        lib.scheduler.add(m.name, time.time(), job, timeout=None, waitfor=lucid+lue)





    # terminates the thread
    def stop(self):
        self.terminate = True
    

lib.module_objects.append(Module())