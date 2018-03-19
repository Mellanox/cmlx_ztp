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
from cmlxztp.dbmgr.dev_params_mgr import dev_params_mgr


class ConfigApp(BaseConfigApp):
    COMMANDS = """\
config_file=/tmp/{0}
bash ${{config_file}}
rm -f ${{config_file}}
"""

    @classmethod
    def get_config_name(cls):
        return "ZTP_STAGE_CONF"

    def _get_commands(self):
        commands = self.COMMANDS.format(self._uuid)
        return commands.split('\n')

    def _get_transfered_files(self):
        dev_config = self._dev_info.dev_config
        dst_file = '/tmp/%s' % self._uuid
        with open(dst_file, 'w') as fp:
            for line in dev_config:
                fp.write('%s\n' % line)
        return[(dst_file, dst_file)]

    def _cleanup(self):
        tmp_file = '/tmp/%s' % self._uuid
        if os.path.isfile(tmp_file):
            os.unlink(tmp_file)


class ConfigMgr(BaseConfigMgr):
    SECTION = 'Config'
    JOB_DESCRIPTION = "Cumulus Configuration"
    _app_cls = ConfigApp
    _task_type = "Configuration"

    def _gen_dev_info(self, ipaddr, job_id):
        dev_info = super(ConfigMgr, self)._gen_dev_info(ipaddr, job_id)
        dev_info.dev_config = dev_params_mgr.get_dev_configuration(
            dev_info.dev_params)
        return dev_info
