"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../sk for more information on License and contacts
"""

import sk_classes
from foreman.client import Foreman, ForemanException
from sk_helper_functions import SKHelperFunctions
import sys
import os
import datetime


class ForemanError(sk_classes.SKParsingError, sk_classes.SKCommandError):
    def __init__(self, message):
        super(ForemanError, self).__init__(message)


class ForemanPlugin(sk_classes.SKParserPlugin, sk_classes.SKCommandPlugin):
    _parsers = []
    _parsers_help_message = ""

    _commands = {'getenv': {'requires_hostlist': True}, 'setenv': {'requires_hostlist': True},
                 'getcls': {'requires_hostlist': True}}
    _commands_help_message = "getenv - get foreman environment\nsetenv - set foreman environment (env name)\n" \
                             "getcls - get assigned puppet classes\n"

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
        self._cache_filename = "foreman"
        self._cache_file = "{0}/{1}".format(self._cache_folder, self._cache_filename)
        self._cache_expire_time = 1800
        self._all_hosts_info = list()

    def _foreman_api_init(self):
        return Foreman(self._foreman_url, (self._user, self._password), verify=self._verify_ssl_boolean, api_version=2)

    def _get_verbose_hosts_info(self):
        result = list()
        for host in self._hostlist_def_domain:
            result.append(self._fapi.hosts.show(id=host))

        return result

    def _read_cache(self):
        try:
            cache_file_mtime = os.path.getmtime(self._cache_file)
        except OSError:
            return None
        now = datetime.datetime.utcnow()
        now_timestamp = (now - datetime.datetime(1970, 1, 1)).total_seconds()
        if now_timestamp - cache_file_mtime > self._cache_expire_time:
            return None
        else:
            with open(self._cache_file, "r") as f:
                raw_data = f.read()
                data = eval(raw_data)
                return data

    def _write_cache(self, data):
        with open(self._cache_file, "w") as f:
            f.write(str(data))

    def _kill_cache(self):
        os.remove(self._cache_file)

    def _get_all_hosts_info(self):
        data = self._read_cache()
        if data is None:
            fapi_hosts_index = self._fapi.hosts.index(per_page=sys.maxsize)
            data = fapi_hosts_index['results']
            self._write_cache(data)
        return data

    def _set_hosts_environment(self, environment_id):
        try:
            for host in self._hostlist_def_domain:
                self._fapi.hosts.update(host={'environment_id': environment_id}, id=host)
                SKHelperFunctions.print_line_with_host_prefix("done", host)
            self._kill_cache()
        except Exception as e:
            raise sk_classes.SKCommandError(str(e))

    def _getenv(self):
        hosts_info = self._get_all_hosts_info()
        filtered_hosts_info = [x for x in hosts_info if x['name'] in self._hostlist_def_domain]
        try:
            for host_info in filtered_hosts_info:
                SKHelperFunctions.print_line_with_host_prefix(host_info['environment_name'],
                                                              host_info['name'])
        except ForemanException as e:
            raise sk_classes.SKCommandError(str(e))

    def _get_environment_id(self, environment):
        try:
            return self._fapi.environments.show(id=environment)['id']
        except Exception as e:
            raise sk_classes.SKCommandError(str(e))

    def _setenv(self):
        environment = self._command_args[0]
        environment_id = self._get_environment_id(environment)
        self._set_hosts_environment(environment_id)

    def _getcls(self):
        hosts_info = self._get_verbose_hosts_info()
        try:
            for host_info in hosts_info:
                try:
                    for puppet_class in host_info['all_puppetclasses']:
                        SKHelperFunctions.print_line_with_host_prefix(puppet_class['name'],
                                                                      host_info['name'])
                except KeyError:
                    raise ForemanException("Foreman info about host says it has no 'all_puppetclasses' field")
        except ForemanException as e:
            raise sk_classes.SKCommandError(str(e))

    def run_command(self):
        if self._command == 'getenv':
            self._getenv()
        elif self._command == 'setenv':
            self._setenv()
        elif self._command == 'getcls':
            self._getcls()

    def parse(self):
        pass
