"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see ../sk for more information on License and contacts
"""


import sk_classes
import paramiko
import os
import multiprocessing
import sys
import socket
import scp
import logging
import signal

class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def print_ssh_line(line, host, is_err=False, colorful=True, print_prefix=True):
    parallel_line_prefix = '[%s]: '
    if print_prefix:
        data = parallel_line_prefix % host + line.replace('\n', '\n' + parallel_line_prefix % host, line.count('\n') - 1)
    else:
        data = line

    if not data.endswith('\n'):
        data += '\n'

    if is_err:
        if colorful:
            data = Bcolors.FAIL + data + Bcolors.ENDC
        outstream = sys.stderr
    else:
        outstream = sys.stdout

    outstream.write(data)
    outstream.flush()


def paramiko_thread_init():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def paramiko_scp_thread_run(paramiko_thread_config, source, dest):
    connect_error_exit_code = 254
    unknown_error_exit_code = 255
    scp_error_exit_code = 253
    host = paramiko_thread_config['hostname']

    paramiko_ssh_client = paramiko.SSHClient()
    paramiko_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        paramiko_ssh_client.connect(**paramiko_thread_config)
    except socket.gaierror as e:
        print_ssh_line(e.strerror, host, is_err=True, print_prefix=True)
        return host, connect_error_exit_code
    paramiko_ssh_transport = paramiko_ssh_client.get_transport()

    scpclient = scp.SCPClient(paramiko_ssh_transport)

    try:
        scpclient.put(source, dest, recursive=True)
    except OSError as e:
        print_ssh_line(str(e), host, is_err=True)
        return host, e.errno
    except scp.SCPException as e:
        print_ssh_line(str(e), host, is_err=True)
        return host, scp_error_exit_code
    except Exception as e:
        print_ssh_line(str(e), host, is_err=True)
        return host, unknown_error_exit_code

    paramiko_ssh_client.close()
    scpclient.close()
    print_ssh_line("done", host)
    return host, 0


def paramiko_scp_gather_thread_run(paramiko_thread_config, source, dest):
    connect_error_exit_code = 254
    unknown_error_exit_code = 255
    scp_error_exit_code = 253
    host = paramiko_thread_config['hostname']

    paramiko_ssh_client = paramiko.SSHClient()
    paramiko_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        paramiko_ssh_client.connect(**paramiko_thread_config)
    except socket.gaierror as e:
        print_ssh_line(e.strerror, host, is_err=True, print_prefix=True)
        return host, connect_error_exit_code
    paramiko_ssh_transport = paramiko_ssh_client.get_transport()

    scpclient = scp.SCPClient(paramiko_ssh_transport)

    source_basename = os.path.basename(source)

    try:
        scpclient.get(source, local_path="{0}_{1}".format(source_basename, host), recursive=True)
    except OSError as e:
        print_ssh_line(str(e), host, is_err=True)
        return host, e.errno
    except scp.SCPException as e:
        print_ssh_line(str(e), host, is_err=True)
        return host, scp_error_exit_code
    except Exception as e:
        print_ssh_line(str(e), host, is_err=True)
        return host, unknown_error_exit_code

    paramiko_ssh_client.close()
    scpclient.close()
    print_ssh_line("done", host)
    return host, 0


def paramiko_exec_thread_run_keyboard_interrupt_wrapper(paramiko_thread_config, cmd, timeout):
    try:
        result = paramiko_exec_thread_run(paramiko_thread_config, cmd, timeout)
    except KeyboardInterrupt:
        pass
    return result


def paramiko_exec_thread_run(paramiko_thread_config, cmd, timeout):
    ##DEBUG PRINT
    #print(cmd)

    connect_error_exit_code = 254
    host = paramiko_thread_config['hostname']

    paramiko_ssh_client = paramiko.SSHClient()
    paramiko_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        paramiko_ssh_client.connect(**paramiko_thread_config)
    except (socket.gaierror, socket.error) as e:
        print_ssh_line(str(e), host, is_err=True, print_prefix=True)
        return host, connect_error_exit_code
    paramiko_ssh_transport = paramiko_ssh_client.get_transport()
    paramiko_channel = paramiko_ssh_transport.open_session()
    paramiko_channel.exec_command(cmd)

    recv_buffer = str()
    recv_stderr_buffer = str()
    break_next_time = False

    paramiko_channel.settimeout(timeout)
    while True:
        if paramiko_channel.exit_status_ready():  # we should know if we're finished to read all the output below
            break_next_time = True

        if paramiko_channel.recv_ready():
            recv_buffer += str(paramiko_channel.recv(4096))
        if paramiko_channel.recv_stderr_ready():
            recv_stderr_buffer += str(paramiko_channel.recv_stderr(4096))

        if break_next_time:  # we should read until it's all in the buffer as we'll have no further opportunity
            while True:
                recv = str(paramiko_channel.recv(4096))
                recv_buffer += recv
                if len(recv) == 0:
                    break

            while True:
                recv_stderr = str(paramiko_channel.recv_stderr(4096))
                recv_stderr_buffer += recv_stderr
                if len(recv_stderr) == 0:
                    break

        if len(recv_buffer) > 0:
            last_newline_pos = recv_buffer.rfind('\n')
            if last_newline_pos != -1:
                if last_newline_pos != len(recv_buffer) - 1:
                    recv_buffer_tail = recv_buffer[last_newline_pos:]
                    recv_buffer_head = recv_buffer[:last_newline_pos]
                    print_ssh_line(recv_buffer_head, host, is_err=False)
                    recv_buffer = recv_buffer_tail
                else:
                    print_ssh_line(recv_buffer, host, is_err=False)
                    recv_buffer = ""

        if len(recv_stderr_buffer) > 0:
            last_newline_pos = recv_stderr_buffer.rfind('\n')
            if last_newline_pos != -1:
                if last_newline_pos != len(recv_stderr_buffer) - 1:
                    recv_stderr_buffer_tail = recv_stderr_buffer[last_newline_pos:]
                    recv_stderr_buffer_head = recv_stderr_buffer[:last_newline_pos]
                    print_ssh_line(recv_stderr_buffer_head, host, is_err=True)
                    recv_stderr_buffer = recv_stderr_buffer_tail
                else:
                    print_ssh_line(recv_stderr_buffer, host, is_err=True)
                    recv_stderr_buffer = ""

        if break_next_time:
            break

    paramiko_ssh_client.close()
    return host, paramiko_channel.recv_exit_status()


class SSHPluginError(sk_classes.SKCommandError):
    def __init__(self, message):
        super(SSHPluginError, self).__init__(message)


class SSHPlugin(sk_classes.SKCommandPlugin):
    _commands = {'ssh': {'requires_hostlist': True},
                 'pssh': {'requires_hostlist': True},
                 'dist': {'requires_hostlist': True},
                 'gather': {'requires_hostlist': True}}
    _commands_help_message = "SSH plugin:\nssh - execute a command over ssh host by host (cmd)\n" \
                             "pssh - parallel exec (cmd)\n" \
                             "dist - distribute " \
                             "a file over ssh to hosts (source [destination, default is cwd])\ngather - gather " \
                             "remote files from hosts to local machine (source [destination, default is cwd]). " \
                             "gather adds a suffix (_hostname) to local filenames\n\n"

    def __init__(self, *args, **kwargs):
        super(SSHPlugin, self).__init__(*args, **kwargs)
        os.chdir(self._cwd)
        self._ssh_command = ""

        if len(self._command_args) == 0:
            raise sk_classes.SKCommandError("Insufficient arguments.")

        for command_arg in self._command_args:
            self._ssh_command += command_arg + ' '
        self._ssh_command = self._ssh_command[:-1]

        if self._command == 'dist':
            if len(self._command_args) > 1:
                self._source = self._command_args[:-1]
                self._dest = self._command_args[-1]
            else:
                self._source = self._command_args[0]
                self._dest = '.'

        if self._command == 'gather':
            self._source = self._command_args[0]
            if len(self._command_args) == 2:
                self._dest = self._command_args[1]
                if os.path.exists(self._dest):
                    if not os.path.isdir(self._dest):
                        raise SSHPluginError("gather command destination can be a directory only.")
                else:
                    try:
                        os.mkdir(self._dest)
                    except OSError as e:
                        raise SSHPluginError("couldn't mkdir {0}: {1}".format(self._dest, str(e)))
            elif len(self._command_args) == 1:
                self._dest = '.'
            else:
                raise SSHPluginError("gather command supports only two args.")

        self._hosts = self._hostlist
        self._timeout = int(getattr(self, "_timeout", 5))
        self._threads_count = int(getattr(self, "_threads_count", 10))

    def _update_paramiko_configs_from_ssh_config(self):
        #  paramiko_configs is a dict: { 'hostname1': {'hostname': hostname1, 'username': username1, etc}, ... }
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        paramiko_ssh_config = paramiko.SSHConfig()

        if os.path.exists(ssh_config_path):
            with open(ssh_config_path) as f:
                paramiko_ssh_config.parse(f)

        for host_config in self._paramiko_configs:
            user_config_for_host = paramiko_ssh_config.lookup(host_config['hostname'])
            for k2 in ('hostname', 'user', 'port'):
                if k2 in user_config_for_host:
                    if k2 == 'user':
                        host_config['username'] = user_config_for_host[k2]
                    else:
                        host_config[k2] = user_config_for_host[k2]

    def _paramiko_configs_set(self):
        # the way the ssh configuration for making the connections is defined is here

        self._paramiko_configs = list()

        # first, just fill in the hostnames
        for host in self._hosts:
            host_properties = dict()
            host_properties['hostname'] = host
            host_properties['timeout'] = self._timeout
            self._paramiko_configs.append(host_properties)

        # then use what user has in ssh config
        self._update_paramiko_configs_from_ssh_config()

        # then override everything with what's passed to us in constructor
        for host_config in self._paramiko_configs:
            #  k is a host, v is a dict of settings for the host
            host_config['username'] = self._username

    def _print_results_summary(self):
        failed_hosts = ""
        failed_hosts_present = False

        for result in self._results:
            host, exit_status = result
            if exit_status not in self._exit_statuses.keys():
                self._exit_statuses[exit_status] = host
            else:
                self._exit_statuses[exit_status] += ", " + host
            if exit_status != 0:
                failed_hosts += host + ", "
                failed_hosts_present = True

        failed_hosts = failed_hosts[:-2]

        if failed_hosts_present:
            sys.stdout.write("\n===\nFailed hosts (exit_status: hosts):\n")
            for k, v in self._exit_statuses.items():
                if k != 0:
                    sys.stdout.write("%s: %s;\n" % (str(k), str(v)))
            fix_command = "\nFix: {0} {1} {2} {3}\n".format(self._sk_path, self._command, failed_hosts, self._ssh_command)
            sys.stdout.write(fix_command)

    def _run(self):
        self._paramiko_configs_set()
        self._exit_statuses = dict()

        if self._command == "pssh":
            self._pool = multiprocessing.Pool(processes=min(self._threads_count, len(self._paramiko_configs)))
            self._pool_results = [self._pool.apply_async(paramiko_exec_thread_run_keyboard_interrupt_wrapper,
                                                         (paramiko_thread_config, self._ssh_command, self._timeout))
                                  for paramiko_thread_config in self._paramiko_configs]


#            self._pool.close()
            try:
#                self._pool.join()
                self._results = [result.get(0xFFFF) for result in self._pool_results]
            except KeyboardInterrupt:
                print("Ctrl-C caught!")
                sys.exit(2)

        elif self._command == "ssh":  # sequential
            counter = 1
            count = len(self._hosts)
            self._results = list()
            try:
                for paramiko_config in self._paramiko_configs:
                    sys.stdout.write("%s [%d/%d]\n" % (paramiko_config["hostname"], counter, count))
                    sys.stdout.flush()
                    self._results.append(paramiko_exec_thread_run(paramiko_config, self._ssh_command, self._timeout))

                    counter += 1
            except KeyboardInterrupt:
                print("Ctrl-C caught!")
                sys.exit(2)

        elif self._command == "dist":
            self._pool = multiprocessing.Pool(processes=self._threads_count)
            self._pool_results = [self._pool.apply_async(paramiko_scp_thread_run, (paramiko_thread_config, self._source,
                                                                                   self._dest))
                                  for paramiko_thread_config in self._paramiko_configs]

            self._pool.close()
            self._pool.join()

            self._results = [result.get() for result in self._pool_results]
        elif self._command == "gather":
            os.chdir(self._dest)

            self._pool = multiprocessing.Pool(processes=self._threads_count)
            self._pool_results = [self._pool.apply_async(paramiko_scp_gather_thread_run, (paramiko_thread_config,
                                                                                          self._source,
                                                                                          self._dest))
                                  for paramiko_thread_config in self._paramiko_configs]

            self._pool.close()
            self._pool.join()

            self._results = [result.get() for result in self._pool_results]

        self._print_results_summary()

    def run_command(self):
        self._run()
