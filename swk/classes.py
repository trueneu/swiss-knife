"""
A module containing definitions for base plugin classes for swk.

swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see swk/main.py for more information on License and contacts
"""
import abc
import shlex
import logging

class SWKPlugin(object):
    """
    A base class in SWK plugins hierarchy.

    This class is never used neither directly nor when defining plugins.

    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        """
        Constructor:
        just writes all the kwargs passed to class attributes.
        """
        for k, v in kwargs.items():
            setattr(self, "_{0}".format(k), v)


class SWKCommandPlugin(SWKPlugin):
    """
    A class used to build command plugins.

    You must derive from this class for your plugin to be recognized as a command executer.

    _commands is class attr, a dict of dicts with the following structure:
    {"command_name1" : {"requires_hostlist": True/False, "help": str},
     "command_name2" : {"requires_hostlist": True/False, "help": str}
     ...
     }
    where "requires_hostlist" is whether command works with hosts
    "help" is a help message which is shown in shell mode when user issues 'help <command_name>' command.

    _commands_help_message is a class attr, a str
    which should contain plugin's name and a brief description of all the commands included
    """
    _commands = dict()  #: this
    _commands_help_message = ""

    @staticmethod
    def _shlex_quoting_split(string):
        lex = shlex.shlex(string)
        lex.quotes = "'"
        lex.whitespace_split = True
        lex.commenters = ''

        return list(lex)

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        Additional object attributes will be passed when constructing the object:
          self._command contains the string with command invoked
          self._hostlist contains the expanded hostlist if it's required by the command
          self._command_args contains the remainder of command line

        everything mentioned in config file will also be available as self._key = value
        the config file section MUST be named the same as your plugin class

        special variables that might be useful:
           self._swk_dir, self._swk_path - directory and invokation path to main executable
           self._cwd - current working directory at the time main executable was invoked
           self._cache_directory - a directory where you can store anything related to your module work
        """
        super(SWKCommandPlugin, self).__init__(*args, **kwargs)
        shlex_splitted_command_args = list()
        if hasattr(self, "_command_args") and len(self._command_args) > 0 and (self._command_args[0] is not None):
            logging.debug("self._command_args received: {cmdargs}".format(cmdargs=self._command_args))
            for command_arg in self._command_args:
                shlex_splitted_command_args.extend(self._shlex_quoting_split(command_arg))
            self._command_args = shlex_splitted_command_args

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
        """
        This method is called when SWK has done all the preparations and needs the plugin to
        actually execute the command.

        You should redefine it.
        Here you should determine which command is called and process it.
        """


class SWKParserPlugin(SWKPlugin):
    """
    A class used to build parser plugins.

    You must derive from this class for your plugin to be recognized as a hostlist parser.

    _parsers is class attr, a dict of dicts with the following structure:
    {"hostlist_modifier1" : {"help": str},
     "hostlist_modifier2" : {"help": str},}
     ...
     }
    where "help" is a help message which is shown in shell mode when user issues 'help <hostlist_modifier>' command.

    _parsers_help_message is a class attr, a str
    which should contain a brief description of all the hostlist modifiers available
    """

    _parsers = dict()
    _parsers_help_message = ""

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        Additional object attributes will be passed when constructing the object:

        self._hostgroup contains string with hostgroup to be parsed
        self._hostgroup_modifier contains the parser specifier, a single symbol

        everything mentioned in config file will also be available as self._key = value
        the config file section MUST be named the same as your plugin class
        """
        super(SWKParserPlugin, self).__init__(*args, **kwargs)

    @classmethod
    def get_parsers(cls):
        return cls._parsers.keys()

    @classmethod
    def get_parser_help(cls, parser):
        return cls._parsers.get(parser).get('help', 'no help provided\n')

    @abc.abstractmethod
    def parse(self):
        """
        This method is called when SWK needs the plugin to parse a hostlist expression.

        You should redefine it.
        Here you should determine which modifier is used and act accordingly.

        :return: Must return list() of hostnames.
        """

    @classmethod
    def parsers_help(cls):
        return cls._parsers_help_message


class SWKParsingError(Exception):
    """
    A class to derive your parsing errors from.
    Raise it if there's an unrecoverable error when parsing a host expression to stop the command from executing.
    """
    def __init__(self, message):
        """
        Constructor

        :param message: a message to be displayed
        """
        super(SWKParsingError, self).__init__(message)


class SWKCommandError(Exception):
    """
    A class to derive your command execution errors from.
    Raise it if there's an unrecoverable error when executing a command.
    """
    def __init__(self, message):
        """
        Constructor

        :param message: a message to be displayed
        """
        super(SWKCommandError, self).__init__(message)
