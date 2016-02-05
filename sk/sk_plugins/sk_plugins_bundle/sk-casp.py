"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../sk for more information on License and contacts
"""

from sk import sk_classes
import requests
import sys
import logging


class CASPError(sk_classes.SKParsingError, sk_classes.SKCommandError):
    def __init__(self, message):
        super(CASPError, self).__init__(message)


class CaspPlugin(sk_classes.SKParserPlugin, sk_classes.SKCommandPlugin):
    _parsers = ['%']
    _parsers_help_message = "%casp_hostgroup, %ALL for all hosts\n"

    _commands = {'lscasp': {'requires_hostlist': False}}
    _commands_help_message = "Casp plugin:\nlscasp - list casp hostgroups\n\n"

    _casp_api_hostgroups_groupnames_uri = "hostgroups?groupNames=true"
    _casp_api_hostgroup_uri = "hostgroups?group"
    _casp_api_hostgroup_all_hosts_uri = "hostgroups"

    def __init__(self, *args, **kwargs):
        super(CaspPlugin, self).__init__(*args, **kwargs)

        self._verify_ssl_boolean = bool(getattr(self, "_verify_ssl", "yes") in ['yes', 'Yes', 'True', 'true'])

    def _get_data(self, url):
        if not self._verify_ssl_boolean:
            requests.packages.urllib3.disable_warnings()
        try:
            data = requests.get(url, verify=self._verify_ssl_boolean)
        except requests.Timeout:
            raise CASPError("Timeout while getting data from CASP")
        except requests.ConnectionError:
            raise CASPError("Error connecting to CASP")
        except Exception as e:
            raise CASPError("Unknown error in CASP module: %s" % str(e.message))
        return data

    def _casp_list_all_hosts(self):
        result = list()

        url = "{0}/{1}".format(self._casp_api_url, self._casp_api_hostgroup_all_hosts_uri)

        data = self._get_data(url)
        for line in data.content.split('\n'):
            parts = line.split()
            if len(parts) == 3:
                host = parts[2]
                result.append(host)

        logging.debug("Expanded Casp hostgroup {0} into {1}".format(self._hostgroup, result))
        return result

    def _casp_expand_hostgroup(self):
        result = list()

        url = "{0}/{1}={2}".format(self._casp_api_url, self._casp_api_hostgroup_uri,
                                   self._hostgroup)

        data = self._get_data(url)
        for line in data.content.split('\n'):
            parts = line.split()
            if len(parts) == 2:
                host = parts[0]
                result.append(host)

        logging.debug("Expanded Casp hostgroup {0} into {1}".format(self._hostgroup, result))
        return result

    def _lscasp(self):
        result = list()

        url = "{0}/{1}".format(self._casp_api_url, self._casp_api_hostgroups_groupnames_uri)

        data = self._get_data(url)
        for line in data.content.split('\n'):
            parts = line.split()
            if len(parts) == 1:
                group = parts[0]
                result.append(group)

        for part in sorted(result):
            sys.stdout.write(part + "\n")

    def parse(self):
        if not self._hostgroup == 'ALL':
            return self._casp_expand_hostgroup()
        else:
            return self._casp_list_all_hosts()

    def run_command(self):
        if self._command == 'lscasp':
            self._lscasp()
