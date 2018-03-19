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

from cmlxztp.app.ssh_app import SshApp, SshMgr
from cmlxztp.dbmgr.db_mgr import DeviceDocument
from cmlxztp.infra.logger import report_logger


class PreConfigApp(SshApp):
    COMMANDS = """\
ZTP_STAGE_IMAGE=FALSE
ZTP_STAGE_CONF=FALSE
ZTP_STAGE_LICENSE=FALSE
ZTP_STAGE_FILES=FALSE
ZTP_STAGE_TRAFFIC=FALSE
ZTP_FILE=~/.cmlxztp
touch ${ZTP_FILE}
. ${ZTP_FILE}
echo "ZTP_STAGE_IMAGE=${ZTP_STAGE_IMAGE}" > ${ZTP_FILE}
echo "ZTP_STAGE_CONF=${ZTP_STAGE_CONF}" >> ${ZTP_FILE}
echo "ZTP_STAGE_LICENSE=${ZTP_STAGE_LICENSE}" >> ${ZTP_FILE}
echo "ZTP_STAGE_FILES=${ZTP_STAGE_FILES}" >> ${ZTP_FILE}
echo "ZTP_STAGE_TRAFFIC=${ZTP_STAGE_TRAFFIC}" >> ${ZTP_FILE}

cat ${ZTP_FILE}
"""

    PRE_COMMANDS = """\
SUDONEO_FILE="/etc/sudoers.d/sudoneo"
NOPASSWD_SETTING="cumulus ALL=(ALL) NOPASSWD:ALL"

echo "Checking Sudo..."
sudo -S touch ${SUDONEO_FILE}
grep -e "^${NOPASSWD_SETTING}$" ${SUDONEO_FILE}
if [ $? -ne 0 ]; then
    echo "${NOPASSWD_SETTING}" | sudo tee -a ${SUDONEO_FILE} > /dev/null
    echo "configured file."
else
    echo "is already configured."
fi
"""

    def _get_pre_commands(self):
        return self.PRE_COMMANDS.split('\n')

    def _run_pre_commands(self):
        sudo_pwd = self._dev_info.conn_info.password
        commands = self._get_pre_commands()
        interactive = True
        interactive_params = {
            ":": sudo_pwd,
            ": ": sudo_pwd,
        }
        self._exec_commands(commands, interactive, interactive_params)

    def _get_commands(self):
        return self.COMMANDS.split('\n')


class PreConfigMgr(SshMgr):
    JOB_DESCRIPTION = "Cumulus PreConfiguration"
    _app_cls = PreConfigApp
    _task_type = "PreConfiguration"
    SECTION = 'PreConfig'

    def _get_ip_addr_list(self):
        ip_list = []
        for ipaddr, dev_doc in self._db.iterdevices():
            if dev_doc.configurable:
                ip_list.append(ipaddr)
        return ip_list

    def _parse_stages(self, result):
        stages = {}
        lines = result.split('\n')
        for line in lines:
            line = line.strip()
            attrs = line.split('=')
            if len(attrs) == 2:
                attr_name = attrs[0].strip()
                value = attrs[1].strip()
                stages[attr_name] = (value == 'TRUE')
        return stages

    def _handle_results(self):
        changed = False
        for ipaddr, result in self._aggregator.iterresults():
            stages = None
            if result.exitcode == 0:
                stages = self._parse_stages(result.stdout)
                report_logger.info("%s: Device: %s, stages: %s",
                                   self.JOB_DESCRIPTION, ipaddr, stages)
            else:
                report_logger.info("%s: Device: %s, failed",
                                   self.JOB_DESCRIPTION, ipaddr)

            data = {
                DeviceDocument.ATTR_STAGES: stages,
            }
            dev_doc = self._db.get_device_document(ipaddr)
            if dev_doc.update(data):
                changed = True
        if changed:
            self._db.save()
