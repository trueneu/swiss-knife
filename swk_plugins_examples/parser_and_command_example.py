"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see https://github.com/trueneu/swiss-knife for more information on License and contacts
"""

from swk import classes


class CommandAndParserPluginExample(classes.SWKCommandPlugin, classes.SWKParserPlugin):
    _commands = {'cmdexample1': {'requires_hostlist': False, 'help': 'cmdexample1 - Example command.\n'}}
    _commands_help_message = "Example Command And Parser Plugin\ncmdexample1 - do nothing\n\n"
    _parsers = {'%': {'help': 'Example parser. Does nothing\n'}}
    _parsers_help_message = "%exampleparser1\n"

    def __init__(self, *args, **kwargs):
        super(CommandAndParserPluginExample, self).__init__(*args, **kwargs)

    def run_command(self):
        print("I'm running a command which doesn't require hostlist!")
        print("See what I got: cmd is {0}, arguments are {1}".format(self._command, self._command_args))

    def run_command(self):
        self._run()

    def parse(self):
        return ["{0}.{1}".format(self._hostgroup, self._hostgroup_modifier)]
