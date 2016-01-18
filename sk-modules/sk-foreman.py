import sk_classes
import requests
import sys
import logging
import foreman

class ForemanError(sk_classes.SKParsingError, sk_classes.SKCommandError):
    def __init__(self, message):
        super(ForemanError, self).__init__(message)


class ForemanPlugin(sk_classes.SKParserPlugin, sk_classes.SKCommandPlugin):
    _parsers = []
    _parsers_help_message = ""

    _commands = {'getenv': {'requires_hostlist': True}, 'setenv': {'requires_hostlist': True}}
    _commands_help_message = "getenv - get foreman environment\nsetenv - set foreman environment\n"

    def __init__(self, *args, **kwargs):
        super(ForemanPlugin, self).__init__(*args, **kwargs)

        self._verify_ssl_boolean = bool(getattr(self, "_verify_ssl", "yes") in ['yes', 'Yes', 'True', 'true'])

    def _get_host_info(self):
        fapi = foreman.client.Foreman(self._foreman_url, (self._user, self._password), verify=self._verify_ssl_boolean)

        data = fapi.hosts.index()
        print(data)
        return data

    def _getenv(self):
        self._get_host_info()

    def run_command(self):
        if self._command == 'getenv':
            self._getenv()
