"""
A module containing exceptions for swk.

swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see swk/main.py for more information on License and contacts
"""


class OverriddenCommandError(Exception):
    def __init__(self, message):
        super(OverriddenCommandError, self).__init__(message)


class OverriddenParserError(Exception):
    def __init__(self, message):
        super(OverriddenParserError, self).__init__(message)


class ExpandingHostlistError(Exception):
    def __init__(self, message):
        super(ExpandingHostlistError, self).__init__(message)


class ConfigNotFoundError(Exception):
    def __init__(self, message):
        super(ConfigNotFoundError, self).__init__(message)
