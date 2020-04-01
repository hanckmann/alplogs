#!/usr/bin/env python
#
# Copyright (c) Patrick Hanckmann
# All rights reserved.
#
# License information is provided in LICENSE.md
#
# Author: Patrick Hanckmann <hanckmann@gmail.com>
# Project: Alpine System Info Log Viewer

from abc import ABCMeta
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Tuple


__author__ = 'Patrick Hanckmann'
__copyright__ = 'Copyright 2020, Patrick Hanckmann'
__version__ = '0.0.1'
__email__ = 'hanckmann@gmail.com'
__status__ = 'Testing'  # 'Production'


# ############## #
# Module Parsers
# ############## #

def split_first_colon(line: str) -> Tuple[str, str]:
    line = line.strip()
    parts = line.split(':')
    key = parts[0].strip()
    data = line.replace(key, '').strip()
    data = data[1:].strip()
    return key, data


def factory(name):
    module_headers = {
        'IGNORE': Ignore,
        'UNKNOWN': Unknown,
        'CPU': CPU,
        'MEMORY': Memory,
        'NETWORK': Network,
        'EXTERNAL IP ADDRESS': IPAddress,
        'DISKS': Disks,
        'MOUNT': Mount,
        'ZFS POOLS': ZFSPools,
        'SMART STATUS': SmartStatus,
        'RC STATUS': RCStatus,
        'USB': USB,
        'UPGRADABLE PACKAGES': UpgradablePackages,
        'PROCESSES': Process,
        'USERS': Users,
        'GROUPS': Groups,
    }
    if name in module_headers:
        return module_headers[name]()
    else:
        print('ERROR: Module not supported: "{}"'.format(name))
        return module_headers['UNKNOWN']()


class AlpLogModule(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        self.timestamp = None
        self.items = {'lines': []}

    def add_line(self, line) -> None:
        if not line.strip():
            return
        self.items['lines'].append(line)

    def finalise(self) -> None:
        return

    def set_timestamp(self, timestamp: datetime):
        self.timestamp = timestamp

    def to_dict(self):
        return self.items

    def to_table_header(self):
        return tuple([key for key in self.items.keys() if not key == 'lines'])

    def name(self):
        return str(type(self))[21:-2]


class Ignore(AlpLogModule):

    pass  # No extra functionality


class Unknown(AlpLogModule):

    pass  # No extra functionality


class Header(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        # Parsing
        line = line.strip()
        value = None
        key, data = split_first_colon(line)
        if key == 'date':
            value = datetime.strptime(data, '%Y-%M-%d').date()
        elif key == 'time':
            value = datetime.strptime(data, '%H:%M:%S').time()
        elif key == 'Kernel version':
            value = data.replace('#', '')
        elif key == 'send e-mail':
            if data == 'yes':
                value = True
            else:
                value = False
        else:
            # Simple items and future proofing
            if data:
                value = data
        if value is not None:
            self.items[key] = value
        if not self.timestamp:
            if 'date' in self.items and self.items['date'] and 'time' in self.items and self.items['time']:
                self.timestamp = datetime.combine(self.items['date'],
                                                  self.items['time'])


class CPU(AlpLogModule):

    def add_line(self, line) -> Union[None, AlpLogModule]:
        if not line.strip():
            return
        # Parsing
        line = line.strip()
        key, data = split_first_colon(line)
        if key == 'processor':
            # from pudb import set_trace; set_trace()
            # Special case, we need to check for extra instance
            if 'processor' in self.items:
                # Create new instance and return as such
                new_instance = CPU()
                new_instance.add_line(line)
                return new_instance
        if key in ('processor', 'cpu family', 'model', 'stepping', 'physical id', 'siblings', 'core id', 'cpu cores', 'apicid', 'initial apicid', 'cpuid level', 'clflush size', 'cache_alignment'):
            value = int(data)
        elif key in ('cpu MHz', 'bogomips'):
            value = float(data)
        elif key in ('fpu', 'fpu_exception', 'wp'):
            if data.lower() == 'yes':
                value = True
            else:
                value = False
        elif key in ('flags', 'bugs', 'power management'):
            value = data.split()
        else:
            value = str(data)
        if value is not None:
            self.items[key] = value

    def name(self):
        processor = None
        if 'processor' in self.items:
            processor = self.items['processor']
        return '{} - {}'.format(str(type(self))[21:-2], processor)


class Memory(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        data = line.split()
        if line.startswith('Mem'):
            self.items['Mem'] = {
                'total': int(data[1]),
                'used': int(data[2]),
                'free': int(data[3]),
                'shared': int(data[4]),
                'buff/cache': int(data[5]),
                'available': int(data[6]),
            }
        elif line.startswith('Swap'):
            self.items['Swap'] = {
                'total': int(data[1]),
                'used': int(data[2]),
                'free': int(data[3]),
            }
        else:
            pass

    def to_dict(self):
        items = dict()
        for key, value in self.items.items():
            if key == 'lines':
                continue
            for subkey, subvalue in value.items():
                items['{} - {}'.format(key, subkey)] = subvalue
        return items

    def to_table_header(self):
        items = list()
        for key, value in self.items.items():
            if key == 'lines':
                continue
            for subkey in value.keys():
                items.append('{} - {}'.format(key, subkey))
        return tuple(items)


class Network(AlpLogModule):

    def add_line(self, line) -> Union[None, AlpLogModule]:
        if not line.strip():
            return
        # Parsing
        if not line.startswith('    '):
            if 'name' in self.items:
                # Create new instance and return as such
                new_instance = Network()
                new_instance.add_line(line)
                return new_instance
            parts = line.split(':')
            self.items['index'] = int(parts[0])
            self.items['name'] = parts[1].strip()
            self.items['name_other'] = parts[2].strip()
            self.items['lines'] = list()
            return
        self.items['lines'].append(line.strip())
        if line.strip().startswith('inet6'):
            parts = line.strip().split()
            self.items['inet6'] = parts[1]
        elif line.strip().startswith('inet'):
            parts = line.strip().split()
            self.items['inet'] = parts[1]

    def name(self):
        name = None
        if 'name' in self.items:
            name = self.items['name']
        return '{} - {}'.format(str(type(self))[21:-2], name)


class IPAddress(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        self.items['ip'] = str(line.strip())


class Disks(AlpLogModule):

    using = {
        0: 'name',
        # 1: 'maj:min',
        # 2: 'rm   ',
        3: 'size',
        4: 'ro',
        5: 'fstype',
        6: 'mountpoint',
        7: 'uuid',
    }

    def add_line(self, line) -> Union[None, AlpLogModule]:
        if not line.strip():
            return
        # Parsing
        if line.strip().startswith('NAME'):
            return
        if 'name' in self.items:
            # Create new instance and return as such
            new_instance = Disks()
            new_instance.add_line(line)
            return new_instance
        parts = line.split()
        for index, part in enumerate(parts):
            if index in self.using:
                key = self.using[index]
                value = part.strip().replace('├', '').replace('├', '').replace('└', '').replace('─', ' ')
                self.items[key] = value

    def name(self):
        name = None
        if 'name' in self.items:
            name = self.items['name']
        return '{} - {}'.format(str(type(self))[21:-2], name)


class Mount(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        key = line.split()[0]
        self.items[key] = line


class ZFSPools(AlpLogModule):

    using = {
        0: 'name',
        1: 'size',
        2: 'alloc',
        3: 'free',
        4: 'ckpoint',
        5: 'expandsz',
        6: 'frag',
        7: 'cap',
        8: 'dedup',
        9: 'health',
        10: 'altroot',
    }

    def add_line(self, line) -> Union[None, AlpLogModule]:
        if not line.strip():
            return
        # Parsing
        if line.strip().startswith('NAME'):
            return
        # Part 1 or parts 2
        parts = line.split()
        if len(parts) == 11 and 'pool' in parts[0]:
            if 'name' in self.items:
                # Create new instance and return as such
                new_instance = ZFSPools()
                new_instance.add_line(line)
                return new_instance
            for index, part in enumerate(parts):
                if index in self.using:
                    key = self.using[index]
                    value = part.strip()
                    if value == '-':
                        value = ''
                    self.items[key] = value

    def name(self):
        name = None
        if 'name' in self.items:
            name = self.items['name']
        return '{} - {}'.format(str(type(self))[21:-2], name)


class SmartStatus(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class RCStatus(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        parts = line.strip().split()
        if line.startswith('Runlevel'):
            self.items[parts[1].strip().upper()] = ''
        else:
            self.items[parts[0].strip()] = parts[2].strip()


class USB(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class UpgradablePackages(AlpLogModule):

    def __init__(self):
        super().__init__()
        self._packages = list()

    def add_line(self, line) -> None:
        if not line.strip():
            return
        if line.startswith('UPGRADABLE PACKAGES'):
            return
        if line.startswith('-'):
            return
        if line.startswith('Installed'):
            return
        print('added "{}"'.format(line.strip()))
        self._packages.append(line.strip())

    def finalise(self) -> None:
        self.items['count'] = str(len(self._packages)) if len(self._packages) else ''


class Process(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class Users(AlpLogModule):

    def __init__(self):
        super().__init__()
        self._users = list()

    def add_line(self, line) -> None:
        if not line.strip():
            return
        self._users.append(line.strip())

    def finalise(self) -> None:
        for index, user in enumerate(self._users):
            self.items[index] = user


class Groups(AlpLogModule):

    def __init__(self):
        super().__init__()
        self._groups = list()

    def add_line(self, line) -> None:
        if not line.strip():
            return
        self._groups.append(line.strip())

    def finalise(self) -> None:
        for index, group in enumerate(self._groups):
            self.items[index] = group


# ############## #
# Logfile Parser
# ############## #

class AlpLogParser():

    def __init__(self, filepath: Path):
        # Open file and iterate over lines
        # Evaluate two lines to detect modules (headers)
        self.modules = list()
        with open(filepath) as fp:
            current_module = None
            for line in fp:
                new_module = self.detect_module(line)
                if new_module:
                    if current_module:
                        self.finalise_module(module=current_module)
                    current_module = new_module
                    if self.modules and self.modules[0]:
                        current_module.set_timestamp(self.modules[0].timestamp)
                else:
                    if current_module:
                        new_module = current_module.add_line(line)
                        if new_module:
                            self.finalise_module(module=current_module)
                            current_module = new_module
                            current_module.set_timestamp(self.modules[0].timestamp)
            self.finalise_module(module=current_module)

    def finalise_module(self, module):
        if not isinstance(module, Ignore):
            module.finalise()
            self.modules.append(module)

    def detect_module(self, line: str) -> Optional[AlpLogModule]:
        if line.strip() == 'STATUS INFORMATION':
            # File header detected
            return Header()
        if line.strip() == 'UPGRADABLE PACKAGES':
            # File header detected
            return UpgradablePackages()
        if line.strip() == 'ACCESS INFORMATION':
            # File header detected
            return Ignore()
        if line.startswith('# '):
            # Module header detected
            line = line.replace('# ', '')
            line = line.replace(':', '')
            line = line.strip()
            return factory(line)
        return None

    def names(self):
        return [module.name() for module in self.modules]
