"""pypi.

Desc: Library for getting information about Python packages by querying
      The CheeseShop (PYPI a.k.a. Python Package Index).


Author: Rob Cakebread <cakebread at gmail>

License  : BSD (See COPYING)

added by Pavel Gurkov (true.neu@gmail.com)
Please refer to original License text at https://github.com/cakebread/yolk
"""

from __future__ import print_function

import re
import platform
import os
import pkg_resources
if platform.python_version().startswith('2'):
    import xmlrpclib
    import urllib2
else:
    import xmlrpc.client as xmlrpclib
    import urllib.request as urllib2

XML_RPC_SERVER = 'https://pypi.python.org/pypi'


class ProxyTransport(xmlrpclib.Transport):

    """Provides an XMl-RPC transport routing via a http proxy.

    This is done by using urllib2, which in turn uses the environment
    varable http_proxy and whatever else it is built to use (e.g. the
    windows    registry).

    NOTE: the environment variable http_proxy should be set correctly.
    See check_proxy_setting() below.

    Written from scratch but inspired by xmlrpc_urllib_transport.py
    file from http://starship.python.net/crew/jjkunce/ by jjk.

    A. Ellerton 2006-07-06

    """

    def request(self, host, handler, request_body, verbose):
        """Send xml-rpc request using proxy."""
        # We get a traceback if we don't have this attribute:
        self.verbose = verbose
        url = 'http://' + host + handler
        request = urllib2.Request(url)
        try:
            request.add_data(request_body)
        except AttributeError:
            request.data = request_body
        # Note: 'Host' and 'Content-Length' are added automatically
        request.add_header('User-Agent', self.user_agent)
        request.add_header('Content-Type', 'text/xml')
        proxy_handler = urllib2.ProxyHandler()
        opener = urllib2.build_opener(proxy_handler)
        fhandle = opener.open(request)
        return self.parse_response(fhandle)


def check_proxy_setting():
    """If the environmental variable 'HTTP_PROXY' is set, it will most likely
    be in one of these forms:

    proxyhost:8080 http://proxyhost:8080 urlllib2
    requires the proxy URL to start with 'http://' This routine does that, and
    returns the transport for xmlrpc.

    """
    try:
        http_proxy = os.environ['HTTP_PROXY']
    except KeyError:
        return

    if not http_proxy.startswith('http://'):
        match = re.match(r'(http://)?([-_\.A-Za-z]+):(\d+)', http_proxy)
        os.environ['HTTP_PROXY'] = 'http://%s:%s' % (match.group(2),
                                                     match.group(3))
    return


class CheeseShop(object):

    """Interface to Python Package Index."""

    def __init__(self):
        self.xmlrpc = self.get_xmlrpc_server()

    def get_xmlrpc_server(self):
        """Return PyPI's XML-RPC server instance."""
        check_proxy_setting()
        if 'XMLRPC_DEBUG' in os.environ:
            debug = 1
        else:
            debug = 0
        return xmlrpclib.Server(XML_RPC_SERVER, transport=ProxyTransport(),
                                verbose=debug)

    def package_releases(self, package_name):
        """Query PYPI via XMLRPC interface for a pkg's available versions."""
        return self.xmlrpc.package_releases(package_name)


def get_highest_version(versions):
    """Return highest available version for a package in a list of versions.

    Uses pkg_resources to parse the versions.

    @param versions: List of PyPI package versions
    @type versions: List of strings

    @returns: string of a PyPI package version

    """
    sorted_versions = []
    for ver in versions:
        sorted_versions.append((pkg_resources.parse_version(ver), ver))

    sorted_versions = list(reversed(sorted(sorted_versions)))
    return sorted_versions[0][1]

