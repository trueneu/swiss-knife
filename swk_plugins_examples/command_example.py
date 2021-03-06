"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see https://github.com/trueneu/swiss-knife for more information on License and contacts
"""

from swk import classes


class CommandPluginExample(classes.SWKCommandPlugin):
    _commands = {'cmdexample2': {'requires_hostlist': True, 'help': 'Example command. Requires hostlist to run\n'}}
    _commands_help_message = "Example Command Plugin\ncmdexample2 - do nothing\n\n"

    def __init__(self, *args, **kwargs):
        super(CommandPluginExample, self).__init__(*args, **kwargs)

    def run_command(self):
        print("I'm running a command which requires hostlist!")
        print("See what I got: cmd is {0}, hostlist is {1}, arguments are {2}".format(self._command, self._hostlist,
                                                                                      self._command_args))

    def run_command(self):
        self._run()
