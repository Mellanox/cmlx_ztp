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
@date:   Dec 19, 2017
"""

from __future__ import absolute_import, division, print_function

from cmlxztp.app.base_app import BaseApp, BaseAggregator, BaseProcMgr, \
    TaskError
from cmlxztp.app.base_app import DevInfo
from cmlxztp.infra.ini_parse import iniparser
from cmlxztp.infra.logger import logger
from cmlxztp.networking.host_client import HostModel, LinuxHost
from cmlxztp.networking.sftp_client import SFTPClient
from cmlxztp.dbmgr.dev_params_mgr import dev_params_mgr


class SshConnInfo(object):

    def __init__(self, username, password, port=22, timeout=60):
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout


class SshDevInfo(DevInfo):

    def __init__(self, ipaddr, sys_type, job_id, conn_info):
        super(SshDevInfo, self).__init__(ipaddr, sys_type, job_id)
        self._conn_info = conn_info

    @property
    def conn_info(self):
        return self._conn_info


class SshApp(BaseApp):

    def _get_host_data(self):
        return {
            HostModel.HOSTNAME: self._dev_info.ipaddr,
            HostModel.USERNAME: self._dev_info.conn_info.username,
            HostModel.PASSWORD: self._dev_info.conn_info.password,
            HostModel.PORT: self._dev_info.conn_info.port,
            HostModel.TIMEOUT: self._dev_info.conn_info.timeout,
        }

    def _create_cli_client(self):
        host_data = self._get_host_data()
        return LinuxHost(host_data)

    def _create_sftp_client(self):
        host_data = self._get_host_data()
        return SFTPClient(host_data)

    def _get_pre_commands(self):
        pass

    def _get_transfered_files(self):
        pass

    def _get_commands(self):
        pass

    def _transfer_files(self, files_list):
        sftp_client = self._create_sftp_client()
        sftp_client.connect()
        for local, remote in files_list:
            logger.info(
                "Transfering file %s to %s:%s", local, remote,
                self._dev_info.ipaddr)
            sftp_client.upload(local, remote)
        sftp_client.close()

    def _exec_commands(self, commands, interactive=False,
                       interactive_params=None):
        host_client = self._create_cli_client()
        host_client.connect()
        host_client.execute(commands, interactive=interactive,
                            interactive_params=interactive_params)
        return host_client.get_result()

    def _cleanup(self):
        pass

    def _get_post_commands(self):
        pass

    def _run_pre_commands(self):
        commands = self._get_pre_commands()
        if commands:
            return self._exec_commands(commands)

    def _task_main(self):
        try:
            logger.info("Task main: %s", self._dev_info.ipaddr)
            result = None
            result = self._run_pre_commands()
            if result and result.exit_code != 0:
                return result
            files_list = self._get_transfered_files()
            if files_list:
                self._transfer_files(files_list)
            commands = self._get_commands()
            if commands:
                logger.info("Executing commands on %s", self._dev_info.ipaddr)
                result = self._exec_commands(commands)
            commands = self._get_post_commands()
            if commands:
                result = self._exec_commands(commands)
        except Exception as e:
            logger.error("Got error while handling device %s: %s",
                         self._dev_info.ipaddr, str(e))
            raise TaskError(str(e))
        finally:
            self._cleanup()
        return result


class SshAggregator(BaseAggregator):
    pass


class SshMgr(BaseProcMgr):

    def __init__(self, devices_db, job_mgr):
        self._conn_info = self._load_conn_info()
        super(SshMgr, self).__init__(devices_db, job_mgr)

    def _load_conn_info(self):
        section = "SSH"
        username = iniparser.get_opt(section, "username")
        password = iniparser.get_opt(section, "password")
        port = iniparser.get_int_opt(section, "port")
        timeout = iniparser.get_int_opt(section, "timeout")
        return SshConnInfo(username, password, port, timeout)

    def _create_aggregator(self):
        return SshAggregator(self._task_type)

    def _gen_dev_info(self, ipaddr, job_id):
        dev_doc = self._db.get_device_document(ipaddr)
        serial_num = dev_doc.serial_num
        dev_params = dev_params_mgr.get_dev_params(serial_num)
        sys_type = DevInfo.SYS_TYPE_CUMULUS
        dev_info = SshDevInfo(ipaddr, sys_type, job_id, self._conn_info)
        if dev_params:
            dev_info.dev_params = dev_params
        return dev_info
