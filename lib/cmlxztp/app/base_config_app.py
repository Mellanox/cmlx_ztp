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

import uuid

from cmlxztp.app.ssh_app import SshApp, SshMgr
from cmlxztp.infra.logger import report_logger


class BaseConfigApp(SshApp):

    POST_COMMANDS = """\
ZTP_FILE=~/.cmlxztp
grep -q "^{0}=" ${{ZTP_FILE}} && \
sed "s/^{0}=.*/{0}=TRUE/" -i ${{ZTP_FILE}} || \
echo {0}=TRUE >> ${{ZTP_FILE}}
"""

    def __init__(self, dev_info, results_queue, task_type, task_params):
        super(BaseConfigApp, self).__init__(dev_info, results_queue, task_type,
                                            task_params)
        self._uuid = uuid.uuid4()
        self._post_init()

    def _post_init(self):
        pass

    @classmethod
    def get_config_name(cls):
        pass

    def _get_post_commands(self):
        config_name = self.get_config_name()
        if config_name:
            post_commands = self.POST_COMMANDS.format(config_name)
            return post_commands.split('\n')


class BaseConfigMgr(SshMgr):
    JOB_DESCRIPTION = "Cumulus Configuration"
    _app_cls = BaseConfigApp
    _task_type = "Configuration"

    def _get_ip_addr_list(self):
        stage = self._app_cls.get_config_name()
        ip_list = []
        for ipaddr, dev_doc in self._db.iterdevices():
            if dev_doc.configurable:
                if stage:
                    stages = dev_doc.stages
                    if stages:
                        stage_status = stages.get(stage)
                        if stage_status:
                            continue
                ip_list.append(ipaddr)
        return ip_list

    def _handle_results(self):
        changed = False
        stage = self._app_cls.get_config_name()
        for ipaddr, result in self._aggregator.iterresults():
            stages = None

            if result.exitcode == 0:
                dev_doc = self._db.get_device_document(ipaddr)
                stages = dev_doc.stages
                stages[stage] = True
                changed = True
                state_str = "Success"
            else:
                state_str = "Failed"
            report_logger.info("%s: Device: %s, %s",
                               self.JOB_DESCRIPTION, ipaddr, state_str)
        if changed:
            self._db.save()
