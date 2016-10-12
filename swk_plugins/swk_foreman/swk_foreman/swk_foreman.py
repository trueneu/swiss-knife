"""
swk_foreman - an swk plugin enabling Foreman API

Copyright (C) 2016  Pavel "trueneu" Gurkov

see https://github.com/trueneu/swiss-knife for more information on License and contacts
"""

from swk import classes
from foreman.client import Foreman, ForemanException
from swk.helper_functions import SWKHelperFunctions
import sys
import os
import datetime
import logging
import inspect

class ForemanError(classes.SWKParsingError, classes.SWKCommandError):
    def __init__(self, message):
        super(ForemanError, self).__init__(message)


class ForemanPlugin(classes.SWKParserPlugin, classes.SWKCommandPlugin):
    _parsers = dict()
    _parsers_help_message = ""
    #_delimiter_help_message = "Use {0} as delimiter for classes list in shell mode.\n"
    _delimiter_help_message = ""

    _short_parameters_dict = {'cls': 'class',
                              'hg': 'hostgroup',
                              'env': 'environment',
                              'os': 'os'}

    _short_parameters_help_string = ', '.join(["{k}={v}".format(k=k, v=v) for (k, v) in _short_parameters_dict.items()])

    _search_help_string = "Possible criterias are: {help_string}\n" \
                          "If you specify more than one, they're linked with 'AND' logic.\n" \
                          "Standard Foreman relational operators are supported: =, !=, ~, !~, ^, !^\n".format(
        help_string=_short_parameters_help_string
    )

    _commands = {'getenv': {'requires_hostlist': True, 'help': 'Prints current environment for hosts. '
                                                               'Arguments: <host expression>\n'},
                 'setenv': {'requires_hostlist': True, 'help': 'Sets environment for hosts. Arguments: '
                                                               '<host expression> <environment name>\n'},
                 'getcls': {'requires_hostlist': True, 'help': 'Prints all puppet classes linked to hosts. '
                                                               'Arguments: <host expression>\n'},
                 'addcls': {'requires_hostlist': True, 'help': 'Links new puppet classes to hosts. '
                                                               'Arguments: <host expression> <puppet class name(s)>\n'},
                 'rmcls': {'requires_hostlist': True, 'help': 'Unlinks puppet classes from hosts. '
                                                              'Arguments: <host expression> <puppet class name(s)>\n'},
                 'getgcls': {'requires_hostlist': True, 'help': 'Prints all puppet classes linked to hostgroups. '
                                                                'Arguments: <foreman hostgroup(s)>\n'},
                 'addgcls': {'requires_hostlist': True, 'help': 'Links new puppet classes to hostgroups. '
                                                                'Arguments: <foreman hostgroup(s)> <puppet class name(s)>\n'},
                 'rmgcls': {'requires_hostlist': True, 'help': 'Unlinks puppet classes from hostgroups. '
                                                               'Arguments: <foreman hostgroup(s)> <puppet class name(s)>\n'},
                 'lscls': {'requires_hostlist': False, 'help': 'Prints available puppet classes. Arguments: None\n'},
                 'srch': {'requires_hostlist': False, 'help': 'Finds hosts matching the specified criteria. '
                                                              'Arguments: search criterias.\n' + _search_help_string},
                 'srchg': {'requires_hostlist': False, 'help': 'Finds hostgroups matching the specified criteria. '
                                                               'Arguments: search criterias\n' + _search_help_string},
                 'desc': {'requires_hostlist': True, 'help': 'Describes given hosts. Arguments: <host expression>\n'}}
    _commands_help_message = "Foreman plugin:\n" \
                             "getenv - get foreman environment\nsetenv - set foreman environment (env name)\n" \
                             "getcls - get host assigned puppet classes\naddcls - adds classes to hosts (cls name[s])\n" \
                             "rmcls - removes classes from hosts (cls name[s])\n" \
                             "getgcls, addgcls and rmgcls - do the same to Foreman hostgroups\n" \
                             "\tuse group names instead of host names for 'g' commands\n" \
                             "srch - find hosts matching the criteria\n" \
                             "srchg - find hostgroups matching the criteria\n" \
                             "desc - describe given hosts\n\n"


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
        self._cache_filename = ".foreman_cache"
        self._cache_file = "{0}/{1}".format(self._cache_directory, self._cache_filename)
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
        try:
            os.remove(self._cache_file)
        except OSError:
            pass

    def _get_all_hosts_info(self):
        data = self._read_cache()
        if data is None:
            fapi_hosts_index = self._fapi.hosts.index(per_page=sys.maxsize)
            data = fapi_hosts_index['results']
            self._write_cache(data)
        return data

    def _get_short_hosts_info(self):
        search_string = ' OR '.join(self._hostlist_def_domain)
        hosts_info = self._fapi.hosts.index(per_page=sys.maxsize, search={search_string})['results']
        return hosts_info

    def _set_hosts_environment(self, environment_id):
        try:
            for host in self._hostlist_def_domain:
                self._fapi.hosts.update(host={'environment_id': environment_id}, id=host)
                SWKHelperFunctions.print_line_with_host_prefix("done", host)
            self._kill_cache()
        except Exception as e:
            raise ForemanError(str(e))

    def _getenv(self):
        hosts_info = self._get_short_hosts_info()
        for host_info in hosts_info:
            SWKHelperFunctions.print_line_with_host_prefix(host_info['environment_name'],
                                                          host_info['name'])

    def _get_environment_id(self, environment):
        try:
            return self._fapi.environments.show(id=environment)['id']
        except Exception as e:
            raise classes.SWKCommandError(str(e))

    def _setenv(self):
        environment = self._command_args[0]
        environment_id = self._get_environment_id(environment)
        self._set_hosts_environment(environment_id)

    def _getcls(self):
        hosts_info = self._get_verbose_hosts_info()
        for host_info in hosts_info:
            try:
                SWKHelperFunctions.print_line_with_host_prefix("", host_info['name'])
                for puppet_class in host_info['all_puppetclasses']:
                    print(puppet_class['name'])
            except KeyError:
                raise ForemanError("Foreman info about host says it has no 'all_puppetclasses' field")
            except TypeError:
                raise ForemanError("Foreman returned nonsense. Most probably one of hosts provided doesn't exist.")

    def _get_classes_short_info(self):
        result = list()
        class_list = self._command_args
        for class_name in class_list:
            class_info_verbose = self._fapi.puppetclasses.index(per_page=sys.maxsize, search={'name='+class_name})['results']

            if len(class_info_verbose) > 0:  # if there is such a class
                class_info_short = class_info_verbose[list(class_info_verbose.keys())[0]][0]  # this looks really ugly
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
            logging.debug("hosts methods: {0}".format(dir(self._fapi.hosts)))
            logging.debug("host_clasess_create args: {0}".format(inspect.getargspec(self._fapi.hosts.host_classes_create)))
            for class_id in class_ids_list:
                self._fapi.hosts.host_classes_create(host_id=host, puppetclass_id=class_id)
            SWKHelperFunctions.print_line_with_host_prefix("done", host)

    def _rm_classes_from_hosts(self, classes_short_info):
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for host in self._hostlist_def_domain:
            for class_id in class_ids_list:
                self._fapi.hosts.host_classes_host_id_puppetclass_destroyids(host_id=host, id=class_id)
            SWKHelperFunctions.print_line_with_host_prefix("done", host)

    def _get_hostgroups_short_info(self):
        result = list()
        for hostgroup in self._grouplist:
            result.append(self._fapi.hostgroups.index(per_page=sys.maxsize, search={'name=' + hostgroup})['results'][0])
        return result

    def _add_classes_to_groups(self, classes_short_info):
        hostgroups_short_info = self._get_hostgroups_short_info()
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for hostgroup_info in hostgroups_short_info:
            logging.debug("hostgroup_clasess_create args: {0}".format(inspect.getargspec(self._fapi.hostgroups.hostgroup_classes_create)))
            for class_id in class_ids_list:
                self._fapi.hostgroups.hostgroup_classes_create(hostgroup_id=hostgroup_info['id'], puppetclass_id=class_id)
            SWKHelperFunctions.print_line_with_host_prefix("done", hostgroup_info['name'])

    def _rm_classes_from_groups(self, classes_short_info):
        hostgroups_short_info = self._get_hostgroups_short_info()
        class_ids_list = self._form_class_ids_list(classes_short_info)
        for hostgroup_info in hostgroups_short_info:
            for class_id in class_ids_list:
                self._fapi.hostgroups.hostgroup_classes_hostgroup_id_puppetclass_destroyids(hostgroup_id=hostgroup_info['id'],
                                                                                  id=class_id)
            SWKHelperFunctions.print_line_with_host_prefix("done", hostgroup_info['name'])

    def _addcls(self):
        classes_short_info = self._get_classes_short_info()
        self._add_classes_to_hosts(classes_short_info)

    def _rmcls(self):
        classes_short_info = self._get_classes_short_info()
        self._rm_classes_from_hosts(classes_short_info)

    def _lscls(self):
        all_classes_short_info = self._get_all_classes_short_info()
        for class_short_info in sorted(all_classes_short_info, key=lambda x: x['name']):
            print(class_short_info['name'])

    def _getgcls(self):
        logging.debug("hostgroups methods: {0}".format(dir(self._fapi.hostgroups)))
        hostgroups_info = self._get_verbose_hostgroups_info()
        for hostgroup_info in hostgroups_info:
            try:
                SWKHelperFunctions.print_line_with_host_prefix("", hostgroup_info['name'])
                for puppet_class in hostgroup_info['puppetclasses']:
                    print(puppet_class['name'])
            except KeyError:
                raise ForemanError("Foreman info about group says it has no 'puppetclasses' field")
            except TypeError:
                raise ForemanError("Foreman returned nonsense. Most probably one of hostgroups provided doesn't exist.")

    def _addgcls(self):
        classes_short_info = self._get_classes_short_info()
        self._add_classes_to_groups(classes_short_info)

    def _rmgcls(self):
        classes_short_info = self._get_classes_short_info()
        self._rm_classes_from_groups(classes_short_info)

    def _parse_key_equals_value(self, args_list):
        result = dict()
        relational_operators = ['!=', '!~', '!^', '=', '~', '^', '>', '<', '>=', '<=']
        for entry in args_list:
            parts = None
            for relational_operator in relational_operators:
                if relational_operator in entry:
                    parts = entry.split(relational_operator)
                    break
            if parts is None:
                raise ForemanError("Error in search criterias: {0}".format(entry))
            try:
                result[parts[0]] = (relational_operator, parts[1])
            except:
                raise ForemanError("Error in search criterias: {0}".format(entry))
        return result

    def _require_arguments(self):
        if not len(self._command_args):
            raise ForemanError("Insufficient arguments")

    def _form_search_string(self, criteria):
        search_criteria_dict = self._parse_key_equals_value(criteria)
        search_string = ""
        for k, (o, v) in search_criteria_dict.items():
            if k in self._short_parameters_dict:
                key = self._short_parameters_dict[k]
            else:
                key = k
            search_string += "{key} {op} {value} AND ".format(key=key, value=v, op=o)
        search_string = search_string[:-5]
        return search_string

    def _search(self, method):
        search_string = self._form_search_string(self._command_args)
        try:
            search_results = method(per_page=sys.maxsize, search={search_string})['results']
        except ForemanException as e:
            raise ForemanError("Most probably your search criteria is not supported.")
        for result in search_results:
            print(result['name'])

    def _srch(self):
        self._search(self._fapi.hosts.index)

    def _srchg(self):
        self._search(self._fapi.hostgroups.index)

    def _desc(self):
        hosts_info = self._get_short_hosts_info()

        for host_info in hosts_info:
            connected_hosts_names = list()
            short_hostname = host_info['name'].replace('.' + host_info['domain_name'], '')
            compute_resource_info = self._fapi.compute_resources.index(per_page=sys.maxsize,
                                                     search={self._form_search_string(["name={short_hostname}".
                                                                                      format(short_hostname=short_hostname)])}
                                                     )['results']
            if compute_resource_info:
                compute_resource_id = compute_resource_info[0]['id']
                connected_hosts_info = self._fapi.hosts.index(per_page=sys.maxsize,
                                                         search={self._form_search_string(["compute_resource_id={id}".
                                                                                          format(id=compute_resource_id)])}
                                                         )['results']
                connected_hosts_names = [x['name'] for x in connected_hosts_info]
            SWKHelperFunctions.print_line_with_host_prefix("", host_info['name'])
            print("Hostgroup:\t{hg}\nOS:\t\t{os}\nIP:\t\t{ip}\nResource:\t{res}\nEnv:\t\t{env}\nComment:\t{cmnt}".format(
                hg=host_info['hostgroup_name'], os=host_info['operatingsystem_name'], ip=host_info['ip'],
                cmnt=host_info['comment'], res=host_info['compute_resource_name'],
                env=host_info['environment_name']
            ))
            if connected_hosts_names:
                print("Cnctd hosts:\t{cnctd_hosts}".format(cnctd_hosts=' '.join(connected_hosts_names)))

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
            elif self._command == 'srch':
                self._srch()
            elif self._command == 'srchg':
                self._srchg()
            elif self._command == 'desc':
                self._desc()
        except ForemanException as e:
            raise ForemanError(str(e))

    def parse(self):
        pass
