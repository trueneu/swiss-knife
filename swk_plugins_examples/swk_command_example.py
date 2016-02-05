"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../../swk for more information on License and contacts
"""

from swk import swk_classes


class CommandPluginExample(swk_classes.SWKCommandPlugin):
    _commands = {'cmdexample2': {'requires_hostlist': True}}
    _commands_help_message = "cmdexample2 - do nothing\n"

    def __init__(self, *args, **kwargs):
        super(CommandPluginExample, self).__init__(*args, **kwargs)

    def _run(self):
        print("I'm running a command!")
        print("See what I got: cmd is {0}, hostlist is {1}, arguments are {2}".format(self._command, self._hostlist,
                                                                                      self._command_args))

    def run_command(self):
        self._run()
