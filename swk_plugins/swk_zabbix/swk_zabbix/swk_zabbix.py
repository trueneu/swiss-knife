"""
swk_zabbix - an swk plugin enabling Zabbix API

Copyright (C) 2016  Pavel "trueneu" Gurkov

see https://github.com/trueneu/swiss-knife for more information on License and contacts
"""

from __future__ import unicode_literals
from swk import classes
from swk.helper_functions import SWKHelperFunctions
import pyzabbix
import sys
import logging
import datetime
import re
from itertools import chain
import time


class ZabbixError(classes.SWKCommandError, classes.SWKParsingError):
    def __init__(self, message):
        super(ZabbixError, self).__init__(message)


class ZabbixPlugin(classes.SWKCommandPlugin, classes.SWKParserPlugin):
    _commands = {'lszbx': {'requires_hostlist': False, 'help': 'Lists zabbix hostgroups. Arguments: None\n'},
                 'lsmntnce': {'requires_hostlist': False, 'help': 'Lists zabbix maintenances. Arguments: None\n'},
                 'addmntnce': {'requires_hostlist': True, 'help': 'Adds zabbix maintenance. Arguments: '
                                                                  '<host expression> <name> <time period>\n'},
                 'rmmntnce': {'requires_hostlist': False, 'help': 'Removes zabbix maintenance. Arguments: '
                                                                  '<maintenance name>\n'},
                 'upmntnce': {'requires_hostlist': False, 'help': 'Updates zabbix maintenance. Arguments: '
                                                                  '<maintenance name> <time period>\n'},
                 'lstmplt': {'requires_hostlist': False, 'help': 'Lists zabbix templates. Arguments: None\n'},
                 'lszbxhosthg': {'requires_hostlist': True, 'help': 'Lists zabbix hostgroups host belongs to. '
                                                                 'Arguments: <host expression>\n'},
                 'upzbxhosthg': {'requires_hostlist': True, 'help': 'Replace host(s) hostgroups with new ones. '
                                                                    'Arguments: <host expression> <hostgroups comma separated>\n'},
                 'lshosttmplt': {'requires_hostlist': True, 'help': 'Lists zabbix templates linked to host(s). '
                                                                    'Arguments: <host expression>\n'},
                 'uphosttmplt': {'requires_hostlist': True, 'help': 'Replace host(s) templates with new ones. '
                                                                    'Arguments: <host expression> <templates comma separated>\n'},

                 }
    _commands_help_message = "Zabbix plugin:\n" \
                             "lszbx - list zabbix hostgroups\n" \
                             "lsmntnce - list zabbix maintenances\n" \
                             "addmntnce - add zabbix maintenance\n" \
                             "rmmntnce - remove zabbix maintenance\n" \
                             "upmntnce - update zabbix maintenance\n" \
                             "lszbxhosthg - list zabbix hostgroups host belongs to\n" \
                             "upzbxhosthg - replace host(s) hostgroups with new ones\n" \
                             "lstmplt - list zabbix templates\n" \
                             "lshosttmplt - list zabbix templates linked to host(s)\n" \
                             "uphosttmplt - replace host(s) zabbix templates with new ones\n\n"

    _parsers = {'^': {'help': 'expands zabbix hostgroups. Has a special keyword ALL for all hosts can be found.\n'}}
    _parsers_help_message = "^zabbix_hostgroup, ^ALL for all hosts\n"

    def __init__(self,  *args, **kwargs):
        super(ZabbixPlugin, self).__init__(*args, **kwargs)
        self._verify_ssl_boolean = bool(getattr(self, "_verify_ssl", "yes") in ['yes', 'Yes', 'True', 'true'])

    def _zbx_connect(self):
        try:
            zapi = pyzabbix.ZabbixAPI(self._zabbix_url)
            zapi.login(self._user, self._password)
            zapi.session.verify = self._verify_ssl_boolean
        except pyzabbix.ZabbixAPIException as e:
            msg, code = e.args
            raise ZabbixError(msg)
        return zapi

    def _lszbx(self):
        result = list()
        zapi = self._zbx_connect()
        hostgroups = zapi.hostgroup.get(output=["name"])
        for hostgroup in hostgroups:
            result.append(hostgroup["name"])
        for part in sorted(result):
            sys.stdout.write(part + "\n")
        return

    def _lsmntnce(self):
        zapi = self._zbx_connect()
        now_ts = int(time.mktime(datetime.datetime.now().timetuple()))
        maintenances = zapi.maintenance.get(output=["name", "active_since", "active_till"],
                                            selectHosts=["name"],
                                            selectGroups=["name"])
        for maintenance in sorted(maintenances, key=lambda x: x['active_since']):
            hosts_groups = ', '.join(chain(['\033[1m{}\033[0m'.format(x['name']) for x in maintenance['groups']],
                                            [x['name'] for x in maintenance['hosts']]))
            active_since_ts = int(maintenance['active_since'])
            active_till_ts = int(maintenance['active_till'])

            active_since = datetime.datetime.fromtimestamp(active_since_ts)
            active_till = datetime.datetime.fromtimestamp(active_till_ts)
            sys.stdout.write('{modifier_s}{since} - {till}\t {name!s:<40}\t{hosts_groups}{modifier_k}\n'.format(
                since=active_since, till=active_till, name=maintenance['name'],
                hosts_groups=hosts_groups,
                modifier_s='' if active_till_ts > now_ts else '\033[1;31m',
                modifier_k='' if active_till_ts > now_ts else '\033[0m',
            ))

    @staticmethod
    def _convert_suffixed_time_to_seconds(s):
        r = re.compile(r'^(\d+)(m|h|d|M|Y)?$')
        match = r.match(s)
        if not match:
            raise ZabbixError('Invalid duration supplied')
        seconds = int(match.group(1))
        multiplier_dict = {'m': 60, 'h': 60 * 60, 'd': 60 * 60 * 24, 'M': 60 * 60 * 24 * 30, 'Y': 60 * 60 * 24 * 365}
        multiplier = multiplier_dict[match.group(2)] if match.group(2) else 1
        return seconds * multiplier

    def _addmntnce(self):
        now_ts = int(time.mktime(datetime.datetime.now().timetuple()))
        try:
            mntnce_name = "{}:: {}".format(self._user, ' '.join(self._command_args[0:-1]))
        except IndexError:
            raise ZabbixError('Insufficient arguments')

        try:
            duration = ZabbixPlugin._convert_suffixed_time_to_seconds(self._command_args[-1])
        except IndexError:
            raise ZabbixError('Insufficient arguments')

        hosts_found = set()
        host_ids = []
        zapi = self._zbx_connect()
        for host in self._hostlist:
            res = zapi.host.get(filter={"name": host}, output="refer")
            if res:
                hosts_found.add(host)
                host_ids.append(res[0]['hostid'])
        possible_groups = set(self._hostlist) - hosts_found
        if possible_groups:
            res = zapi.hostgroup.get(filter={"name": list(possible_groups)}, output="refer")
            group_ids = [x['groupid'] for x in res] if res else None
        else:
            group_ids = None
        parameters = {'hostids': host_ids, 'timeperiods': [{'period': duration}],
                      'name': mntnce_name, 'active_since': now_ts,
                      'active_till': (now_ts + duration), 'groupids': group_ids}
        zapi.maintenance.create(**parameters)

    def _rmmntnce(self):
        zapi = self._zbx_connect()
        try:
            mntnce_name = ' '.join(self._command_args)
        except IndexError:
            raise ZabbixError('Insufficient arguments')
        res = zapi.maintenance.get(filter={'name': mntnce_name})
        if res:
            mntnce_id = zapi.maintenance.get(filter={'name': mntnce_name})[0]['maintenanceid']
            zapi.maintenance.delete(mntnce_id)
        else:
            raise ZabbixError("Maintenance doesn't exist")

    def _upmntnce(self):
        zapi = self._zbx_connect()
        now_ts = int(time.mktime(datetime.datetime.now().timetuple())) + 10
        try:
            mntnce_name = "{}".format(' '.join(self._command_args[:-1]))
        except IndexError:
            raise ZabbixError('Insufficient arguments')
        try:
            duration = ZabbixPlugin._convert_suffixed_time_to_seconds(self._command_args[-1])
        except IndexError:
            raise ZabbixError('Insufficient arguments')

        res = zapi.maintenance.get(filter={'name': mntnce_name})
        if res:
            mntnce_info = zapi.maintenance.get(filter={'name': mntnce_name}, selectHosts='hostid',
                                               selectGroups='groupid')[0]
            mntnce_id = int(mntnce_info['maintenanceid'])
            host_ids = [int(x['hostid']) for x in mntnce_info['hosts']]
            group_ids = [int(x['groupid']) for x in mntnce_info['groups']]

            parameters = {'hostids': host_ids, 'timeperiods': [{'period': duration}],
                          'name': mntnce_name, 'active_since': now_ts,
                          'active_till': (now_ts + duration), 'groupids': group_ids,
                          'maintenanceid': mntnce_id}
            zapi.maintenance.delete(mntnce_id)
            zapi.maintenance.create(**parameters)
        else:
            raise ZabbixError("Maintenance doesn't exist")

    def _lstmplt(self):
        zapi = self._zbx_connect()
        for template in sorted(zapi.template.get(output=['name']), key=lambda x: x['name']):
            sys.stdout.write(template['name'] + '\n')

    def _upzbxhosthg(self):
        hostgroup_names = [x.strip() for x in ' '.join(self._command_args).split(',')]
        zapi = self._zbx_connect()
        hostgroup_ids = [int(x['groupid']) for x in zapi.hostgroup.get(filter={'name': hostgroup_names}, output='extend')]
        if len(hostgroup_ids) != len(hostgroup_names):
            raise ZabbixError("Some hostgroups cannot be found, aborting")
        host_ids = [int(x['hostid']) for x in zapi.host.get(filter={'name': self._hostlist})]
        zapi.host.massupdate(hosts=[{'hostid': x} for x in host_ids],
                             groups=[{'groupid': x} for x in hostgroup_ids])

        for host in self._hostlist:
            SWKHelperFunctions.print_line_with_host_prefix('Done', host)

    def _lszbxhosthg(self):
        zapi = self._zbx_connect()
        r = zapi.host.get(filter={'name': self._hostlist}, output=['name'], selectGroups='extend')
        for host in r:
            try:
                for group in host['groups']:
                    SWKHelperFunctions.print_line_with_host_prefix(group['name'], host['name'])
            except KeyError:
                pass

    def _lshosttmplt(self):
        zapi = self._zbx_connect()
        res = zapi.host.get(filter={'name': self._hostlist}, output=['name'],
                            selectParentTemplates=['name', 'templateid'])
        for host in res:
            try:
                for template in host['parentTemplates']:
                    SWKHelperFunctions.print_line_with_host_prefix(template['name'], host['name'])
            except KeyError:
                pass

    def _uphosttmplt(self):
        zapi = self._zbx_connect()
        template_names = [x.strip() for x in ' '.join(self._command_args).split(',')]
        template_ids = [int(x['templateid']) for template_name in template_names
                        for x in zapi.template.get(filter={'name': template_name}, output='extend')]
        if len(template_ids) != len(template_names):
            raise ZabbixError("Some templates cannot be found, aborting")
        current_hosts_templates = zapi.host.get(filter={'name': self._hostlist}, output=['name'],
                                                selectParentTemplates=['name', 'templateid'])
        host_ids = [int(x['hostid']) for x in current_hosts_templates]
        for host in current_hosts_templates:
            current_template_ids = [{"templateid": x['templateid']} for x in host['parentTemplates']]
            zapi.host.update(hostid=host['hostid'], templates_clear=current_template_ids)

        zapi.host.massupdate(hosts=[{'hostid': x} for x in host_ids],
                             templates=[{'templateid': x} for x in template_ids])

        for host in self._hostlist:
            SWKHelperFunctions.print_line_with_host_prefix('Done', host)

    def run_command(self):
        if self._command == 'lszbx':
            self._lszbx()
        elif self._command == 'lsmntnce':
            self._lsmntnce()
        elif self._command == 'addmntnce':
            self._addmntnce()
        elif self._command == 'rmmntnce':
            self._rmmntnce()
        elif self._command == 'lstmplt':
            self._lstmplt()
        elif self._command == 'upmntnce':
            self._upmntnce()
        elif self._command == 'lszbxhosthg':
            self._lszbxhosthg()
        elif self._command == 'upzbxhosthg':
            self._upzbxhosthg()
        elif self._command == 'lshosttmplt':
            self._lshosttmplt()
        elif self._command == 'uphosttmplt':
            self._uphosttmplt()

    def _zabbix_expand_hostgroup(self):
        result = list()
        zapi = self._zbx_connect()
        hostgroup = zapi.hostgroup.get(filter={"name": self._hostgroup})
        if len(hostgroup) > 0:
            hostgroup_id = hostgroup[0]["groupid"]
            hosts = zapi.host.get(output=["host"], groupids=[hostgroup_id])
            for host in hosts:
                result.append(host["host"])
        logging.debug("Expanded zabbix hostgroup {0} into {1}".format(self._hostgroup, result))
        return result

    def _zabbix_list_all_hosts(self):
        result = list()
        zapi = self._zbx_connect()
        hosts = zapi.host.get(output=["host"])
        for host in hosts:
            result.append(host["host"])
        logging.debug("Expanded zabbix hostgroup {0} into {1}".format(self._hostgroup, result))
        return result

    def parse(self):
        if not self._hostgroup == 'ALL':
            return self._zabbix_expand_hostgroup()
        else:
            return self._zabbix_list_all_hosts()
