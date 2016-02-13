"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see https://github.com/trueneu/swiss-knife for more information on License and contacts
"""

from swk import classes


class ParserPluginExample(classes.SWKParserPlugin):
    _parsers = {'^': {'help': 'Example parser. Does nothing\n'}}
    _parsers_help_message = "^exampleparser2\n"

    def __init__(self, *args, **kwargs):
        super(ParserPluginExample, self).__init__(*args, **kwargs)

    def parse(self):
        return ["{0}.{1}".format(self._hostgroup, self._hostgroup_modifier)]
