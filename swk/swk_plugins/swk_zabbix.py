"""
swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../swk for more information on License and contacts
"""

from swk import swk_classes
import pyzabbix
import sys
import logging


class ZabbixError(swk_classes.SWKCommandError, swk_classes.SWKParsingError):
    def __init__(self, message):
        super(ZabbixError, self).__init__(message)


class ZabbixPlugin(swk_classes.SWKCommandPlugin, swk_classes.SWKParserPlugin):
    _commands = {'lszbx': {'requires_hostlist': False, 'help': 'Lists zabbix hostgroups. Arguments: None\n' }}
    _commands_help_message = "Zabbix plugin:\n" \
                             "lszbx - list zabbix hostgroups\n\n"
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

    def run_command(self):
        if self._command == 'lszbx':
            self._lszbx()

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
