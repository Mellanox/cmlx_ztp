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

#
#


class ECNConfigApp(BaseConfigApp):
    COMMANDS = """\
traffic_file=/tmp/{0}.traffic
data_file=/tmp/{0}.data
mv ${{traffic_file}} /etc/cumulus/datapath/traffic.conf
dst=/usr/lib/python2.7/dist-packages/cumulus/__chip_config/mlx/datapath.conf
mv ${{data_file}} ${{dst}}
sudo systemctl restart switchd.service
"""

    @classmethod
    def get_config_name(cls):
        return 'ZTP_STAGE_TRAFFIC'

    def _get_commands(self):
        commands = self.COMMANDS.format(self._uuid)
        return commands.split('\n')

    def _get_transfered_files(self):
        model = self._dev_info.dev_params.model
        file_list = []
        file_name = 'datapath.conf'
        src_file = os.path.join(conf_dir, file_name)
        dst_file = '/tmp/%s.data' % self._uuid
        file_list.append((src_file, dst_file))
        file_name = 'traffic-%s.conf' % model
        src_file = os.path.join(conf_dir, file_name)
        dst_file = '/tmp/%s.traffic' % self._uuid
        file_list.append((src_file, dst_file))
        return file_list


class ECNConfigMgr(BaseConfigMgr):
    SECTION = 'ECN'
    JOB_DESCRIPTION = "Cumulus ECN Configuration"
    _app_cls = ECNConfigApp
    _task_type = "ECN"
