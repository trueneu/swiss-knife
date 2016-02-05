"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../../sk for more information on License and contacts
"""

import sk_classes


class ParserPluginExample(sk_classes.SKParserPlugin):
    _parsers = ['^']
    _parsers_help_message = "^testparser2\n"

    def __init__(self, *args, **kwargs):
        super(ParserPluginExample, self).__init__(*args, **kwargs)

    def parse(self):
        return ["{0}.{1}".format(self._hostgroup, self._hostgroup_modifier)]
