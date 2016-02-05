"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../../swk for more information on License and contacts
"""

from swk import swk_classes


class ParserPluginExample(swk_classes.SWKParserPlugin):
    _parsers = ['^']
    _parsers_help_message = "^testparser2\n"

    def __init__(self, *args, **kwargs):
        super(ParserPluginExample, self).__init__(*args, **kwargs)

    def parse(self):
        return ["{0}.{1}".format(self._hostgroup, self._hostgroup_modifier)]
