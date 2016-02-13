"""
A module containing useful utility functions for swk.

swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see swk/main.py for more information on License and contacts
"""

import sys


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class SWKHelperFunctions(object):
    def __init__(self):
        pass

    @staticmethod
    def print_line_with_host_prefix(line, host, is_err=False, colorful=True, print_prefix=True):
        parallel_line_prefix = '[%s]: '
        if print_prefix:
            data = parallel_line_prefix % host + line.replace('\n', '\n' + parallel_line_prefix % host, line.count('\n') - 1)
        else:
            data = line

        if not data.endswith('\n'):
            data += '\n'

        if is_err:
            if colorful:
                data = Bcolors.FAIL + data + Bcolors.ENDC
            outstream = sys.stderr
        else:
            outstream = sys.stdout

        outstream.write(data)
        outstream.flush()
