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

from cmlxztp.app.base_config_app import BaseConfigApp, BaseConfigMgr
from cmlxztp.infra.ini_parse import iniparser


class ImageUpgradeApp(BaseConfigApp):
    COMMANDS = """\
IMAGE_FILE=/tmp/{0}
sudo onie-install -a -i ${{IMAGE_FILE}}
if [ $? - ne 0 ]; then
    echo "Installation failed!"
    exit 1
else
    sudo reboot
fi
"""

    @classmethod
    def get_config_name(cls):
        return "ZTP_STAGE_IMAGE"

    def _get_commands(self):
        commands = self.COMMANDS.format(self._uuid)
        return commands.split('\n')

    def _get_transfered_files(self):
        image_path = iniparser.get_opt('Image', 'image_path')
        dst_file = '/tmp/%s' % self._uuid
        return[(image_path, dst_file)]


class ImageUpgradeMgr(BaseConfigMgr):
    SECTION = 'Image'
    JOB_DESCRIPTION = "Image Upgrade"
    _app_cls = ImageUpgradeApp
    _task_type = "Image"
