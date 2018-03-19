"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2017. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Samer Deeb
@date:   Aug 24, 2015
"""
from __future__ import absolute_import, division, print_function

import re
import socket
import time

import paramiko
from paramiko.ssh_exception import AuthenticationException
from six import iteritems

from cmlxztp.infra.logger import logger
from cmlxztp.networking.base_client import BaseClient
from cmlxztp.networking.cli_result import CliResult
from cmlxztp.networking.host_model import HostModel


class HostClientError(Exception):
    pass


class HostClient(BaseClient):
    AUTH_BASIC = 0
    AUTH_KERBEROS = 1
    _builtin_initial_commands = []
    _builtin_finalization_commands = []

    def __init__(self, host_data):
        """
        Constructor
        """
        self._timeout = None
        self._operation_timeout = 3600
        self._auth = None
        self._result = CliResult()
        self._connetction_timeout = None
        super(HostClient, self).__init__(host_data)

    def _extract_host_data(self, host_data):
        super(HostClient, self)._extract_host_data(host_data)
        self._timeout = host_data.get(HostModel.TIMEOUT)
        self._auth = host_data.get(HostModel.AUTHENTICATION)

    def connect(self):
        raise NotImplementedError("%s.%s is not implemented!",
                                  self.__class__.__name__,
                                  "connect")

    def execute(self, commands, initial_commands=None,
                final_commands=None, separator=None, interactive=False,
                interactive_params=None):
        raise NotImplementedError("%s.%s is not implemented!",
                                  self.__class__.__name__,
                                  "execute")

    def set_operation_timeout(self, tout):
        self._operation_timeout = tout

    def set_connection_timeout(self, tout):
        self._connetction_timeout = tout

    def get_hostname(self):
        return self._hostname

    def get_result(self):
        return self._result

    def _get_all_commands(self, commands, initial_commands=None,
                          final_commands=None):
        all_commands = []
        all_commands.extend(self._builtin_initial_commands)
        if initial_commands:
            all_commands.extend(initial_commands)
        all_commands.extend(commands)
        if final_commands:
            all_commands.extend(final_commands)
        all_commands.extend(self._builtin_finalization_commands)
        return all_commands


class SshHostClient(HostClient):
    RECV_READY_INTERVAL = 0.5
    RECV_BUFFER_INTERVAL = 0.05
    RECV_BUFFER_SIZE = 10000
    _RECONNECT_WAIT_AFTER_RELOAD = 30
    _DISCONNECT_WAIT_AFTER_RELOAD = 2
    _WAIT_BEFORE_RELOAD = 1
    _RELOAD_WAIT_INTERVAL = 10

    _prompt_suffixes = []
    _error_regex = None
    _exec_mode = False
    _reload_commands = []

    def __init__(self, host_data):
        """
        Constructor
        """
        super(SshHostClient, self).__init__(host_data)
        self._ssh_client = None
        self._ssh_channel = None
        self._interactive_params = None

    def connect(self):
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._ssh_client.connect(self._hostname, port=self._port,
                                     username=self._username,
                                     password=self._password,
                                     timeout=self._timeout,
                                     look_for_keys=False)
        except AuthenticationException:
            # override auth failure message
            raise AuthenticationException(
                "SSH Authentication failure: please check device credentials")

    def _open_shell(self):
        self._ssh_channel = self._ssh_client.invoke_shell()
        self._ssh_channel.settimeout(self._operation_timeout)
        self._recv_initial_prompt()

    def _invoke_shell_commands(self, commands, initial_commands,
                               final_commands, separator):
        if not self._ssh_client:
            raise HostClientError(
                "No connection was established with host'%s'" % self._hostname)
        if not commands:
            return
        self._open_shell()
        all_commands = self._get_all_commands(
            commands, initial_commands, final_commands)
        start_concat_output_pos = len(self._builtin_initial_commands)
        end_concat_output_pos = len(
            all_commands) - len(self._builtin_finalization_commands)
        separator_pos_list = []
        if initial_commands:
            separator_pos_list.append(
                start_concat_output_pos + len(initial_commands))
        if final_commands:
            separator_pos_list.append(
                end_concat_output_pos - len(final_commands))
        for index, command in enumerate(all_commands):
            sts, output = self._exec_single_command(command)
            if index in separator_pos_list and separator is not None:
                self._result.stdout += separator
            if not sts:
                self._result.exitcode = 1
                self._result.stderr = output
                break
            if index >= start_concat_output_pos and \
                    index < end_concat_output_pos:
                self._result.stdout += output
        self._ssh_channel.close()

    def _hide_passwords(self, _, output):
        return output

    def _exec_single_command(self, command):
        if command in self._reload_commands:
            return self._send_reload(command)
        self._ssh_channel.send("%s\n" % command)
        output = self._recv()
        errors = self._check_errors(output)
        output = self._hide_passwords(command, output)
        return not errors, output

    def _sleep(self, interval, timeout):
        time.sleep(interval)
        return timeout - interval

    def _send_reload(self, command):
        # pylint: disable=broad-except
        logger.info("reload command '%s' initiated on '%s'",
                    command, self._hostname)
        timeout = self._operation_timeout
        timeout = self._sleep(self._WAIT_BEFORE_RELOAD, timeout)
        logger.info("sending reload command '%s' '%s'",
                    command, self._hostname)
        self._ssh_channel.send("%s\n" % command)
        output = "%s\n" % command
        timeout = self._sleep(self._DISCONNECT_WAIT_AFTER_RELOAD, timeout)
        self._ssh_channel.close()
        logger.info("'%s': closing connection to '%s' and try to reconnect",
                    command, self._hostname)
        timeout = self._sleep(self._RECONNECT_WAIT_AFTER_RELOAD, timeout)
        connected = False
        while timeout > 0:
            try:
                self.connect()
                connected = True
                break
            except Exception:
                timeout = self._sleep(self._RELOAD_WAIT_INTERVAL, timeout)
        if connected:
            logger.info("'%s': connection restored to '%s'",
                        command, self._hostname)
            self._open_shell()
            for cmd in self._builtin_initial_commands:
                self._exec_single_command(cmd)
            output += "reload done successfully\n"
        else:
            logger.info("'%s': restoring connection to '%s'- timeout",
                        command, self._hostname)
            output += "Error: timeout while waiting for reload end!\n"
        logger.info("reload command on '%s' ended, status: %s",
                    self._hostname, connected)
        return connected, output

    def _get_separator_commands(self, _):
        return []

    def _exec_commands(self, commands, initial_commands, final_commands,
                       separator):
        if not commands:
            return
        all_commands = []
        all_commands.extend(self._builtin_initial_commands)
        if initial_commands:
            all_commands.extend(initial_commands)
            if separator:
                all_commands.extend(self._get_separator_commands(separator))
        all_commands.extend(commands)
        if final_commands:
            if separator:
                all_commands.extend(self._get_separator_commands(separator))
            all_commands.extend(final_commands)
        all_commands.extend(self._builtin_finalization_commands)
        self._ssh_channel = self._ssh_client.get_transport().open_session()
        self._ssh_channel.settimeout(self._operation_timeout)
        command_str = "\n".join(all_commands)
        self._ssh_channel.exec_command(command_str)
        stdout = self._ssh_channel.makefile('r', -1)
        self._result.stdout += stdout.read()
        stderr = self._ssh_channel.makefile_stderr('r', -1)
        self._result.stderr += stderr.read()
        self._result.exitcode = self._ssh_channel.recv_exit_status()
        self._verify_connection()
        self._ssh_channel.close()

    def execute(self, commands, initial_commands=None, final_commands=None,
                separator=None, interactive=False, interactive_params=None):
        self._interactive_params = interactive_params or {}
        try:
            if self._exec_mode and not interactive:
                return self._exec_commands(commands, initial_commands,
                                           final_commands, separator)
            return self._invoke_shell_commands(
                commands, initial_commands, final_commands, separator)
        except socket.timeout:
            raise HostClientError("Timeout while receiving data from :%s" %
                                  self._hostname)

    def _recv_initial_prompt(self):
        return self._recv()

    def _verify_connection(self):
        transport = self._ssh_client.get_transport()
        if not transport or not transport.is_active() or \
                not transport.is_alive():
            raise HostClientError(
                "device '%s' has disconnected unexpectedly!" %
                self._hostname)

    def _recv(self, check_prompt=True, should_wait=True):

        if not self._ssh_channel:
            raise HostClientError(
                "No channel was opened with host'%s'" % self._hostname)
        self._check_recv_ready(should_wait)
        output = self._recv_output(check_prompt, should_wait)
        # remove last line - of prompt
        # handle case with "\r" appears without "\n"
        if not check_prompt:
            return output
        sep = "\n"
        rpos = output.rfind("\r")
        npos = output.rfind("\n")
        if rpos > npos:
            sep = "\r"
        output_lines = output.rsplit(sep, 1)
        return output_lines[0]

    def _check_recv_ready(self, should_wait):
        sleep_time = 0
        while not self._ssh_channel.recv_ready():
            self._verify_connection()
            if not should_wait:
                raise HostClientError(
                    "No data to receive for host'%s'" % self._hostname)
            time.sleep(self.RECV_READY_INTERVAL)
            self._verify_connection()
            sleep_time += self.RECV_READY_INTERVAL
            if sleep_time > self._operation_timeout:
                raise socket.timeout()
        return sleep_time

    def _recv_output(self, check_prompt, should_wait):
        output = u""
        is_prompt = False
        while not is_prompt:
            self._verify_connection()
            recv_out = self._ssh_channel.recv(self.RECV_BUFFER_SIZE)
            recv_out = ''.join([c if ord(c) < 128 else '?' for c in recv_out])
            output = output + recv_out
            if not check_prompt:
                break
            for suffix, resp in iteritems(self._interactive_params):
                if output.endswith(suffix):
                    logger.info("got interactive prompt: %s, response: %s",
                                suffix, resp)
                    if resp == "@DEVICE_PWD@":
                        resp = self._password
                    elif resp == "@DEVICE_USR@":
                        resp = self._username
                    self._ssh_channel.send("%s\n" % resp)
                    output = output + self._recv(check_prompt, should_wait)
                    return output
            for suffix in self._prompt_suffixes:
                if output.endswith(suffix):
                    is_prompt = True
            if not is_prompt:
                time.sleep(self.RECV_BUFFER_INTERVAL)
        return output

    def _check_errors(self, output):
        if self._error_regex and output:
            match = self._error_regex.search(output)
            return match is not None
        return False


class MlnxSwitch(SshHostClient):
    _prompt_suffixes = ["# ", "> ", "# \b ", "> \b ", "#  \b", ">  \b"]
    _error_regex = re.compile(r"\A%|\r\n%|\n%")
    _builtin_initial_commands = ["no cli session paging enable", "enable",
                                 "configure terminal"]
    RELOAD_COMMAND = "reload noconfirm"
    RELOAD_FORCE_COMMAND = "reload force"
    _reload_commands = set([RELOAD_COMMAND, RELOAD_FORCE_COMMAND])
    _password_commands_regex = re.compile(r"(.*)password ([\w]+)(.*)")

    def _hide_passwords(self, command, output):
        if self._password_commands_regex.search(command):
            return self._password_commands_regex.sub(
                r"\1password ****\3", output)
        return super(MlnxSwitch, self)._hide_passwords(command, output)


class CiscoSwitch(SshHostClient):
    _prompt_suffixes = ["# "]
    _error_regex = re.compile(
        r"\A%|\r\n%|\n%|\AERROR:|\nERROR:|\r\nERROR:"
        "|Auth passphrase specified is not strong enough:"
        "|Unable to perform the action")
    _builtin_initial_commands = ["terminal length 0", "configure terminal"]
    _reload_commands = set(["reload"])


class JuniperSwitch(SshHostClient):
    _prompt_suffixes = ["# ", "> "]
    _error_regex = re.compile(r"(\A\s*\^)|(\r\n\s*\^)|(\n\s*\^)")
    _builtin_initial_commands = ["set cli screen-length 0"]


class AristaSwitch(SshHostClient):

    """
    This class is implements Arista switch
    """
    _prompt_suffixes = ["#", ">"]
    _error_regex = re.compile(r"\A%|\r\n%|\n%")
    _builtin_initial_commands = [
        "terminal length 0", "enable", "configure terminal"]


class HpSwitch(SshHostClient):

    """
    This class is implements Hp switch
    """
    _prompt_suffixes = ["# ", "continue"]
    _error_regex = re.compile(r"Invalid input:")
    _builtin_initial_commands = ["\n", "configure", "no page"]


class BrocadeSwitch(SshHostClient):

    """
    This class is implements Brocade switch
    """
    _prompt_suffixes = ["# ", ]
    _error_regex = re.compile(
        r"Invalid input parameters.|\n*command not found")
    _builtin_initial_commands = ["terminal length 0"]


class H3cSwitch(SshHostClient):

    """
    This class is implements Hp H3c switch
    """
    _prompt_suffixes = ["<HP>"]
    _error_regex = re.compile(r"Invalid input:")
    _builtin_initial_commands = ["screen-length disable", ]


class LinuxHost(SshHostClient):

    """
    This class is implements Linux host
    """
    _exec_mode = True
    _prompt_suffixes = ["# ", "#", "> ", ">", "$", "$ "]
    _reload_commands = ["reboot", "sudo reboot", "sudo reboot -f"]

    def _get_separator_commands(self, separator):
        cmds = []
        if separator:
            cmds.append('echo -n "%s"' % separator)
        return cmds
