"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../sk for more information on License and contacts
"""

import sk_classes
import pyzabbix
import sys
import logging


class ZabbixError(sk_classes.SKCommandError, sk_classes.SKParsingError):
    def __init__(self, message):
        super(ZabbixError, self).__init__(message)


class ZabbixPlugin(sk_classes.SKCommandPlugin, sk_classes.SKParserPlugin):
    _commands = {'lszbx': {'requires_hostlist': False}}
    _commands_help_message = "lszbx - list zabbix hostgroups\n"
    _parsers = ['^']
    _parsers_help_message = "^zabbix_hostgroup\n"

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

    def parse(self):
        return self._zabbix_expand_hostgroup()
