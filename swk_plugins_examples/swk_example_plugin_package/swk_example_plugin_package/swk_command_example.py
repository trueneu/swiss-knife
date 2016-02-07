"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../../swk for more information on License and contacts
"""

from swk import swk_classes


class CommandPluginExample(swk_classes.SWKCommandPlugin):
    _commands = {'command_from_plugin': {'requires_hostlist': False}}
    _commands_help_message = "Example Plugin:\ncommand_from_plugin - do nothing\n"

    def __init__(self, *args, **kwargs):
        super(CommandPluginExample, self).__init__(*args, **kwargs)

    def _run(self):
        print("I'm running a command!")
        print("See what I got: cmd is {0}, arguments are {1}".format(self._command, self._command_args))

    def run_command(self):
        self._run()
