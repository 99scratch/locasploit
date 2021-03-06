#!/usr/bin/env python3
"""
Lists content of dpkg database.
"""
from source.modules._generic_module import *

class Module(GenericModule):
    def __init__(self):
        super().__init__()
        self.authors = [
            Author(name='Vitezslav Grygar', email='vitezslav.grygar@gmail.com', web='https://badsulog.blogspot.com'),
        ]
        
        self.name = 'packages.dpkg.installed'
        self.short_description = 'Finds versions of installed packages.'
        self.references = [
        ]
        self.date = '2016-10-20'
        self.license = 'GNU GPLv2'
        self.version = '1.0'
        self.tags = [
            'linux',
            'package',
            'packages',
            'dpkg',
            'installed',
            'version',
        ]
        
        
        self.description = """This module looks into /var/lib/dpkg/status file to determine version of all installed packages.
"""
        
        self.dependencies = {

        }
        self.changelog = """
"""

        self.reset_parameters()

    def reset_parameters(self):
        self.parameters = {
            'SILENT': Parameter(value='no', mandatory=True, description='Suppress the output'),
            'ACTIVEROOT': Parameter(mandatory=True, description='System to work with'),
            'TAG': Parameter(mandatory=True, description='Tag'),
        }

    def check(self, silent=None):
        if silent is None:
            silent = positive(self.parameters['SILENT'].value)
        activeroot = self.parameters['ACTIVEROOT'].value
        result = CHECK_SUCCESS
        # is the system linux?
        if not get_system_type_from_active_root(activeroot).startswith('lin'):
            if not silent:
                log.warn('Target system does not belong to Linux family.')
            result = CHECK_UNLIKELY
        # can open /var/lib/dpkg/status?
        if not io.can_read(activeroot, '/var/lib/dpkg/status'):
            if not silent:
                log.err('Cannot open /var/lib/dpkg/status file.')
            result = CHECK_FAILURE
        return result

    def run(self):
        silent = positive(self.parameters['SILENT'].value)
        activeroot = self.parameters['ACTIVEROOT'].value
        tag = self.parameters['TAG'].value
        
        results = []
        content = io.read_file(activeroot, '/var/lib/dpkg/status')
        if content == IO_ERROR:
            log.err('Cannot read /var/lib/dpkg/status!')
            return None
        # grep correct lines
        info = list(zip(*[iter([x for x in content.splitlines() if x.startswith(('Package', 'Status', 'Version'))])]*3))
        # add appropriate lines into TB
        for entry in info:
            try:
                pkg = [x.partition(' ')[2] for x in entry if x.startswith('Package')][0]
                version = [x.partition(' ')[2] for x in entry if x.startswith('Version')][0]
                status = [x.partition(' ')[2] for x in entry if x.startswith('Status')][0]
            except: # weird order, skip
                continue
            if 'installed' in status: # that's why dpkg -l | wc differs
                results.append((pkg, None, version))

        tb[tag] = results
        
        if not silent:
            log.ok('%d packages revealed.' % (len(results)))
        return None

lib.module_objects.append(Module())

