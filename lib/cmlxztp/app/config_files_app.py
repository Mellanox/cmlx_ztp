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

import os

from cmlxztp.app.base_config_app import BaseConfigApp, BaseConfigMgr
from cmlxztp.infra import conf_dir
from cmlxztp.dbmgr.config_files_repository import ConfigFilesRepository


class ConfigFilesApp(BaseConfigApp):
    COMMANDS = """\
config_file=/tmp/{0}
target_path={1}
service_name={2}
mv ${{config_file}} ${{target_path}}
sudo systemctl restart ${{service_name}}
"""
    _confile_files = ConfigFilesRepository()

    @classmethod
    def get_config_name(cls):
        return 'ZTP_STAGE_FILES'

    def _get_commands(self):
        commands = []
        for conf_file in self._confile_files:
            file_commands = self.COMMANDS.format(
                conf_file.uuid, conf_file.file_dst, conf_file.service_name)
            commands.extend(file_commands.split('\n'))
        return commands

    def _get_transfered_files(self):
        files_list = []
        for conf_file in self._confile_files:
            src_file = os.path.join(conf_dir, conf_file.file_name)
            dst_file = '/tmp/%s' % conf_file.uuid
            files_list.append((src_file, dst_file))
        return files_list


class ConfigFilesMgr(BaseConfigMgr):
    JOB_DESCRIPTION = "Cumulus Config Files Upload"
    _app_cls = ConfigFilesApp
    _task_type = "Config Files"
    SECTION = 'ConfigFiles'
