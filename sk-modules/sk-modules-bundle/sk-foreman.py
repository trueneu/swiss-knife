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
                 'getcls': {'requires_hostlist': True}, 'addcls': {'requires_hostlist': True},
                 'rmcls': {'requires_hostlist': True},
                 'getgcls': {'requires_hostlist': True}, 'addgcls': {'requires_hostlist': True},
                 'rmgcls': {'requires_hostlist': True}, 'lscls': {'requires_hostlist': False}}
    _commands_help_message = "Foreman plugin:\n" \
                             "getenv - get foreman environment\nsetenv - set foreman environment (env name)\n" \
                             "getcls - get host assigned puppet classes\naddcls - adds classes to hosts (cls name[s])\n" \
                             "rmcls - removes classes from hosts (cls name[s])\n" \
                             "getgcls, addgcls and rmgcls - do the same to Foreman hostgroups\n" \
                             "\tuse group names instead of host names here\n\n"

    def _append_default_domain(self):
        result = list()
        for host in self._hostlist:
            if not host.endswith(self._default_domain) and not host.endswith('.'):
                host += '.' + self._default_domain
            result.append(host)

        return result

    def __init__(self, *args, **kwargs):
        super(ForemanPlugin, self).__init__(*args, **kwargs)
        self._verify_ssl_boolean = bool(getattr(self, "_verify_ssl", "yes") in ['yes', 'Yes', 'True', 'true'])

        if not (self._command == "getgcls" or self._command == "addgcls" or self._command == "rmgcls"):
            self._hostlist_def_domain = self._append_default_domain()
        else:
            self._grouplist = self._hostlist
        self._fapi = self._foreman_api_init()
        self._cache_filename = "foreman"
        self._cache_file = "{0}/{1}".format(self._cache_folder, self._cache_filename)
        self._cache_expire_time = 1800
        self._all_hosts_info = list()
        self._all_classes_info = list()

    def _foreman_api_init(self):
        return Foreman(self._foreman_url, (self._user, self._password), verify=self._verify_ssl_boolean, api_version=2)

    def _get_verbose_hosts_info(self):
        result = list()
        for host in self._hostlist_def_domain:
            result.append(self._fapi.hosts.show(id=host))

        return result

    def _get_verbose_hostgroups_info(self):
        result = list()
        for group in self._grouplist:
            result.append(self._fapi.hostgroups.show(id=group))

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
            raise ForemanError(str(e))

    def _getenv(self):
        hosts_info = self._get_all_hosts_info()
        filtered_hosts_info = [x for x in hosts_info if x['name'] in self._hostlist_def_domain]
        for host_info in filtered_hosts_info:
            SKHelperFunctions.print_line_with_host_prefix(host_info['environment_name'],
                                                          host_info['name'])

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
        for host_info in hosts_info:
            try:
                for puppet_class in host_info['all_puppetclasses']:
                    SKHelperFunctions.print_line_with_host_prefix(puppet_class['name'],
                                                                  host_info['name'])
            except KeyError:
                raise ForemanError("Foreman info about host says it has no 'all_puppetclasses' field")

    def _get_classes_short_info(self):
        result = list()
        for class_name in self._command_args:
            class_info_verbose = self._fapi.puppetclasses.index(per_page=sys.maxsize, search={'name='+class_name})['results']

            if len(class_info_verbose) > 0:  # if there is such a class
                class_info_short = class_info_verbose[class_info_verbose.keys()[0]][0]  # this looks really ugly
                result.append(class_info_short)
            else:
                raise ForemanError("Class {0} doesn't exist".format(class_name))
        return result

    def _get_all_classes_short_info(self):
        result = list()
        class_info_verbose = self._fapi.puppetclasses.index(per_page=sys.maxsize)['results']
        for parent_class_name, class_info in class_info_verbose.items():
            for subclass_info in class_info:
                class_info_short = subclass_info
                result.append(class_info_short)
        return result

    def _form_class_ids_list(self, classes_short_info):
        class_ids_list = list()
        for class_short_info in classes_short_info:
            class_id = class_short_info['id']
            class_ids_list.append(class_id)
        return class_ids_list

    def _add_classes_to_hosts(self, classes_short_info):
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for host in self._hostlist_def_domain:
            self._fapi.hosts.update(host={'puppetclass_ids': class_ids_list}, id=host)
            SKHelperFunctions.print_line_with_host_prefix("done", host)

    def _rm_classes_from_hosts(self, classes_short_info):
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for host in self._hostlist_def_domain:
            for class_id in class_ids_list:
                self._fapi.hosts.host_classes_host_id_puppetclass_destroyids(host_id=host, id=class_id)
            SKHelperFunctions.print_line_with_host_prefix("done", host)

    def _get_hostgroups_short_info(self):
        result = list()
        for hostgroup in self._grouplist:
            result.append(self._fapi.hostgroups.index(per_page=sys.maxsize, search={'name=' + hostgroup})['results'][0])
        return result

    def _add_classes_to_groups(self, classes_short_info):
        hostgroups_short_info = self._get_hostgroups_short_info()
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for hostgroup_info in hostgroups_short_info:
            self._fapi.hostgroups.update(hostgroup={'puppetclass_ids': class_ids_list}, id=hostgroup_info['id'])
            SKHelperFunctions.print_line_with_host_prefix("done", hostgroup_info['name'])

    def _rm_classes_from_groups(self, classes_short_info):
        hostgroups_short_info = self._get_hostgroups_short_info()
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for hostgroup_info in hostgroups_short_info:
            for class_id in class_ids_list:
                self._fapi.hostgroups.hostgroup_classes_hostgroup_id_puppetclass_destroyids(hostgroup_id=hostgroup_info['id'],
                                                                                  id=class_id)
            SKHelperFunctions.print_line_with_host_prefix("done", hostgroup_info['name'])

    def _addcls(self):
        classes_short_info = self._get_classes_short_info()
        self._add_classes_to_hosts(classes_short_info)

    def _rmcls(self):
        classes_short_info = self._get_classes_short_info()
        self._rm_classes_from_hosts(classes_short_info)

    def _lscls(self):
        all_classes_short_info = self._get_all_classes_short_info()
        for class_short_info in all_classes_short_info:
            print(class_short_info['name'])

    def _getgcls(self):
        hostgroups_info = self._get_verbose_hostgroups_info()
        for hostgroup_info in hostgroups_info:
            try:
                for puppet_class in hostgroup_info['puppetclasses']:
                    SKHelperFunctions.print_line_with_host_prefix(puppet_class['name'],
                                                                  hostgroup_info['name'])
            except KeyError:
                raise ForemanError("Foreman info about group says it has no 'puppetclasses' field")

    def _addgcls(self):
        classes_short_info = self._get_classes_short_info()
        self._add_classes_to_groups(classes_short_info)

    def _rmgcls(self):
        classes_short_info = self._get_classes_short_info()
        self._rm_classes_from_groups(classes_short_info)

    def run_command(self):
        try:
            if self._command == 'getenv':
                self._getenv()
            elif self._command == 'setenv':
                self._setenv()
            elif self._command == 'getcls':
                self._getcls()
            elif self._command == 'addcls':
                self._addcls()
            elif self._command == 'rmcls':
                self._rmcls()
            elif self._command == 'lscls':
                self._lscls()
            elif self._command == 'getgcls':
                self._getgcls()
            elif self._command == 'addgcls':
                self._addgcls()
            elif self._command == 'rmgcls':
                self._rmgcls()
        except ForemanException as e:
            raise ForemanError(str(e))

    def parse(self):
        pass
