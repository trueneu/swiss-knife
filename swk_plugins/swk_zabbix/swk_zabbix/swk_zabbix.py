"""
swk_zabbix - an swk plugin enabling Zabbix API

Copyright (C) 2016  Pavel "trueneu" Gurkov

see https://github.com/trueneu/swiss-knife for more information on License and contacts
"""

from swk import classes
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
                                                                  '<host expression> <name> <until date>\n'},
                 'rmmntnce': {'requires_hostlist': False, 'help': 'Removes zabbix maintenance. Arguments: '
                                                                  '<maintenance name>\n'}}
    _commands_help_message = "Zabbix plugin:\n" \
                             "lszbx - list zabbix hostgroups\n" \
                             "lsmntnce - list zabbix maintenances\n" \
                             "addmntnce - add zabbix maintenance\n" \
                             "rmmntnce - removes zabbix maintenance\n\n"
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
                since=active_since, till=active_till, name=maintenance['name'].encode('utf-8'),
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
        res = zapi.maintenance.exists(name=mntnce_name)
        if res:
            mntnce_id = zapi.maintenance.get(filter={'name': mntnce_name})[0]['maintenanceid']
            zapi.maintenance.delete(mntnce_id)
        else:
            raise ZabbixError("Maintenance doesn't exist")

    def run_command(self):
        if self._command == 'lszbx':
            self._lszbx()
        elif self._command == 'lsmntnce':
            self._lsmntnce()
        elif self._command == 'addmntnce':
            self._addmntnce()
        elif self._command == 'rmmntnce':
            self._rmmntnce()

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
