"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see sk for more information on License and contacts
"""
import abc


class SKPlugin():
    __metaclass__  = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, "_{0}".format(k), v)
        """fill in everything"""


class SKCommandPlugin(SKPlugin):
    _commands = dict()
    _commands_help_message = ""

    def __init__(self, *args, **kwargs):
        super(SKCommandPlugin, self).__init__(*args, **kwargs)

    @classmethod
    def get_commands(cls):
        return cls._commands.keys()

    @classmethod
    def requires_hostlist(cls, command):
        return cls._commands.pop(command).pop('requires_hostlist', True)

    @classmethod
    def commands_help(cls):
        return cls._commands_help_message

    @abc.abstractmethod
    def run_command(self):
        """self._command contains the string with command invoked
        self._hostlist contains the parsed hostlist if it's required by the command
        self._command_args contains the remainder of command line

        everything mentioned in config file will also be available as self._key = value
        the config file section MUST be named the same as class

        special variables that might be useful:
          self._sk_dir, self._sk_path - directory and invokation path to main executable
          self._cwd - current working directory at the time main executable was invoked
          self._cache_folder - a directory where you can store anything related to your module work"""


class SKParserPlugin(SKPlugin):
    _parsers_help_message = ""
    _parsers = []

    def __init__(self, *args, **kwargs):
        super(SKParserPlugin, self).__init__(*args, **kwargs)

    @classmethod
    def get_parsers(cls):
        return cls._parsers

    @abc.abstractmethod
    def parse(self):
        """self._hostgroup contains string with hostgroup to be parsed
        self._hostgroup_modifier contains the parser specifier, a single symbol
        method must return a list of hosts

        everything mentioned in config file will also be available as self._key = value
        the config file section MUST be named the same as class"""

    @classmethod
    def parsers_help(cls):
        return cls._parsers_help_message


class SKParsingError(Exception):
    def __init__(self, message):
        super(SKParsingError, self).__init__(message)
    """raise this if there's error in parsing"""


class SKCommandError(Exception):
    def __init__(self, message):
        super(SKCommandError, self).__init__(message)
    """raise this if there's unrecoverable error in command execution"""
