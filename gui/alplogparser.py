#!/usr/bin/env python
#
# Copyright (c) Patrick Hanckmann
# All rights reserved.
#
# License information is provided in LICENSE.md
#
# Author: Patrick Hanckmann <hanckmann@gmail.com>
# Project: Alpine System Info Log Viewer

import dateutil
from abc import ABCMeta
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Tuple


__author__ = "Patrick Hanckmann"
__copyright__ = "Copyright 2020, Patrick Hanckmann"
__version__ = "0.0.1"
__email__ = "hanckmann@gmail.com"
__status__ = "Testing"  # "Production"


# ############## #
# Module Parsers
# ############## #

def split_first_colon(line: str) -> Tuple[str, str]:
    line = line.strip()
    parts = line.split(':')
    key = parts[0].strip()
    data = line.replace('{}:'.format(key, '')).strip()
    return key, data


class AlpLogModule(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        self.timestamp = None
        self.items = dict()

    def set_timestamp(self, timestamp: datetime):
        self.timestamp = timestamp

    def to_table(self):
        return [list()]

    def to_table_header_vertical(self):
        return []

    def to_table_header_horizontal(self):
        return []


class Unknown(AlpLogModule):

    def __init__(self):
        super().__init__()
        self.items['lines'] = list()

    def add_line(self, line) -> None:
        if not line.strip():
            return
        self.items['lines'].append(line)


class Header(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        # Parsing
        line = line.strip()
        value = None
        key, data = split_first_colon(line)
        if key == 'date':
            value = dateutil.parser.parse(data)
        elif key == 'time':
            value = dateutil.parser.parse(data)
        elif key == 'Kernel version':
            value = data.replace('#', '')
        elif key == 'send e-mail':
            if data == 'yes':
                value = True
            else:
                value = False
        else:
            # Simple items and future proofing
            value = data
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
            # Special case, we need to check for extra instance
            if 'processor' in self.items:
                # Create new instance and return as such
                new_instance = CPU()
                new_instance.add_line(line)
                return new_instance
            value = int(data)
        elif key in ('processor', 'cpu family', 'model', 'stepping', 'physical id', 'siblings', 'core id', 'cpu cores', 'apicid', 'initial apicid', 'cpuid level', 'clflush size', 'cache_alignment'):
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
        self.items[key] = value


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
            raise ValueError('Unexpected value ({})'.format(line))


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
        if line.strip().startswith('inet'):
            parts = line.strip().split()
            self.items['inet'] = parts(1)
        elif line.strip().startswith('inet6'):
            parts = line.strip().split()
            self.items['inet6'] = parts(1)


class IPAddress(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return
        self.items['ip'] = str(line.strip())


class Disks(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class Mount(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class ZFSPools(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class SmartStatus(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class RCStatus(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class USB(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class Process(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class Users(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


class Groups(AlpLogModule):

    def add_line(self, line) -> None:
        if not line.strip():
            return


# ############## #
# Logfile Parser
# ############## #

class AlpLogParser():

    module_headers = {
        "UNKNOWN": Unknown(),
        "CPU": CPU(),
        "MEMORY": Memory(),
        "NETWORK": Network(),
        "EXTERNAL IP ADDRESS": IPAddress(),
        "DISKS": Disks(),
        "MOUNT": Mount(),
        "ZFS POOLS": ZFSPools(),
        "SMART STATUS": SmartStatus(),
        "RC STATUS": RCStatus(),
        "USB": USB(),
        "PROCESSES": Process(),
        "USERS": Users(),
        "GROUPS": Groups(),
    }

    def __init__(self, filepath: Path):
        # Open file and iterate over lines
        # Evaluate two lines to detect modules (headers)
        self.modules = list()
        with open(filepath) as fp:
            current_module = None
            for line in fp:
                new_module = self.detect_module(line)
                if new_module:
                    self.modules.append(current_module)
                    current_module = new_module
                    current_module.set_timestamp(self.modules[0].timestamp)
                else:
                    current_module.add_line(line)
            self.modules.append(current_module)

    def detect_module(self, line: str) -> Optional[AlpLogModule]:
        if line == 'STATUS INFORMATION':
            # File header detected
            return Header()
        if line.startswith('# '):
            # Module header detected
            line = line.replace('# ', '')
            line = line.replace(':', '')
            if line not in self.module_headers:
                print('ERROR: Module not supported: {}'.format(line.replace('#', '')))
                line = 'UNKNOWN'
            return self.module_headers[line]
        return None
