"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see swk for more information on License and contacts
"""
import abc


class SWKPlugin():
    __metaclass__  = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, "_{0}".format(k), v)
        """fill in everything"""


class SWKCommandPlugin(SWKPlugin):
    _commands = dict()
    _commands_help_message = ""

    def __init__(self, *args, **kwargs):
        super(SWKCommandPlugin, self).__init__(*args, **kwargs)

    @classmethod
    def get_commands(cls):
        return cls._commands.keys()

    @classmethod
    def get_command_help(cls, command):
        return cls._commands.get(command).get('help', 'no help provided\n')

    @classmethod
    def requires_hostlist(cls, command):
        return cls._commands.get(command).get('requires_hostlist', True)

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
          self._swk_dir, self._swk_path - directory and invokation path to main executable
          self._cwd - current working directory at the time main executable was invoked
          self._cache_folder - a directory where you can store anything related to your module work"""


class SWKParserPlugin(SWKPlugin):
    _parsers_help_message = ""
    _parsers = dict()

    def __init__(self, *args, **kwargs):
        super(SWKParserPlugin, self).__init__(*args, **kwargs)

    @classmethod
    def get_parsers(cls):
        return cls._parsers.keys()

    @classmethod
    def get_parser_help(cls, parser):
        return cls._parsers.get(parser).get('help', 'no help provided\n')

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


class SWKParsingError(Exception):
    def __init__(self, message):
        super(SWKParsingError, self).__init__(message)
    """raise this if there's error in parsing"""


class SWKCommandError(Exception):
    def __init__(self, message):
        super(SWKCommandError, self).__init__(message)
    """raise this if there's unrecoverable error in command execution"""
