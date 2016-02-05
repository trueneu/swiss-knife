"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../../sk for more information on License and contacts
"""

from sk import sk_classes


class CommandAndParserPluginExample(sk_classes.SKCommandPlugin, sk_classes.SKParserPlugin):
    _commands = {'cmdexample1': {'requires_hostlist': False}}
    _commands_help_message = "cmdexample1 - do nothing\n"
    _parsers = ['%']
    _parsers_help_message = "%testparser1\n"

    def __init__(self, *args, **kwargs):
        super(CommandAndParserPluginExample, self).__init__(*args, **kwargs)

    def _run(self):
        print("I'm running a command which doesn't require hostlist!")
        print("See what I got: cmd is {0}, arguments are {1}".format(self._command, self._command_args))

    def run_command(self):
        self._run()

    def parse(self):
        return ["Host1"]
