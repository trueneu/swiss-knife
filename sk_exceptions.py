"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see sk for more information on License and contacts
"""


class OverriddenCommandError(Exception):
    def __init__(self, message):
        super(OverriddenCommandError, self).__init__(message)


class OverriddenParserError(Exception):
    def __init__(self, message):
        super(OverriddenParserError, self).__init__(message)

