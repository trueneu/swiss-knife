"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../../sk for more information on License and contacts
"""

import sk_classes


class DryRunPlugin(sk_classes.SKCommandPlugin):
    _commands = {'dr': {'requires_hostlist': True}}
    _commands_help_message = "dr - do nothing, just print hostlist\n"

    def __init__(self, *args, **kwargs):
        super(DryRunPlugin, self).__init__(*args, **kwargs)

    def _run(self):
        for host in self._hostlist:
            print(host)

    def run_command(self):
        self._run()
