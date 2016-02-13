"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see swk/main.py for more information on License and contacts
"""

from swk import classes


class DryRunPlugin(classes.SWKCommandPlugin):
    _commands = {'dr': {'requires_hostlist': True, 'help': 'Expand the host expression and print the results. Arguments: <host exression>\n'}}
    _commands_help_message = "Dry run Plugin:\ndr - do nothing, just print hostlist\n\n"

    def __init__(self, *args, **kwargs):
        super(DryRunPlugin, self).__init__(*args, **kwargs)

    def _run(self):
        for host in self._hostlist:
            print(host)

    def run_command(self):
        self._run()
