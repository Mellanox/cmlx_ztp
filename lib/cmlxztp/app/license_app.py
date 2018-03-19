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


class LicenseApp(BaseConfigApp):
    COMMANDS = """\
license_file=/tmp/{0}
sudo cl-license -I ${{license_file}}
systemctl restart switchd
rm -f ${{license_file}}
"""

    @classmethod
    def get_config_name(cls):
        return 'ZTP_STAGE_LICENSE'

    def _get_commands(self):
        commands = self.COMMANDS.format(self._uuid)
        return commands.split('\n')

    def _get_transfered_files(self):
        file_name = 'license.txt'
        src_file = os.path.join(conf_dir, file_name)
        dst_file = '/tmp/%s' % self._uuid
        return[(src_file, dst_file)]


class LicenseMgr(BaseConfigMgr):
    SECTION = 'License'
    JOB_DESCRIPTION = "License Installation"
    _app_cls = LicenseApp
    _task_type = "License"
