import sk_classes
from foreman.client import Foreman, ForemanException
from sk_helper_functions import SKHelperFunctions


class ForemanError(sk_classes.SKParsingError, sk_classes.SKCommandError):
    def __init__(self, message):
        super(ForemanError, self).__init__(message)


class ForemanPlugin(sk_classes.SKParserPlugin, sk_classes.SKCommandPlugin):
    _parsers = []
    _parsers_help_message = ""

    _commands = {'getenv': {'requires_hostlist': True}, 'setenv': {'requires_hostlist': True}}
    _commands_help_message = "getenv - get foreman environment\nsetenv - set foreman environment\n"

    def _append_default_domain(self):
        result = list()
        for host in self._hostlist:
            if not host.endswith(self._default_domain):
                host += '.' + self._default_domain
            result.append(host)

        return result

    def __init__(self, *args, **kwargs):
        super(ForemanPlugin, self).__init__(*args, **kwargs)
        self._verify_ssl_boolean = bool(getattr(self, "_verify_ssl", "yes") in ['yes', 'Yes', 'True', 'true'])
        self._hostlist_def_domain = self._append_default_domain()
        self._fapi = self._foreman_api_init()

    def _foreman_api_init(self):
        return Foreman(self._foreman_url, (self._user, self._password), verify=self._verify_ssl_boolean)

    def _get_hosts_info(self):
        result = list()

        for host in self._hostlist_def_domain:
            result.append(self._fapi.hosts.show(id=host))

        return result

    def _set_hosts_environment(self, environment_id):
        try:
            for host in self._hostlist_def_domain:
                self._fapi.hosts.update(host={'environment_id': environment_id}, id=host)
                SKHelperFunctions.print_line_with_host_prefix("done", host)
        except ForemanException as e:
            raise sk_classes.SKCommandError(str(e))

    def _getenv(self):
        hosts_info = self._get_hosts_info()
        try:
            for host_info in hosts_info:
                SKHelperFunctions.print_line_with_host_prefix(host_info['host']['environment']['environment']['name'],
                                                              host_info['host']['name'])
        except ForemanException as e:
            raise sk_classes.SKCommandError(str(e))

    def _get_environment_id(self, environment):
        try:
            return self._fapi.environments.show(id=environment)['environment']['id']
        except Exception as e:
            raise sk_classes.SKCommandError(str(e))

    def _setenv(self):
        environment = self._command_args[0]
        environment_id = self._get_environment_id(environment)
        self._set_hosts_environment(environment_id)

    def run_command(self):

        if self._command == 'getenv':
            self._getenv()
        elif self._command == 'setenv':
            self._setenv()

    def parse(self):
        pass
