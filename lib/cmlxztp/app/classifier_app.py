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
from cmlxztp.dbmgr.dev_params_mgr import dev_params_mgr
from cmlxztp.infra.logger import logger, report_logger


class ClassifierApp(SshApp):
    COMMANDS = """\
MODEL=$(net show system | grep "^Mellanox" | awk '{{print $2}}')
echo "{0}=${{MODEL}}"
MACADDR=$(net show interface eth0 | grep HWaddr | awk -F': ' '{{print $2}}')
echo "{1}=${{MACADDR}}"
SERIAL_NUM=$(/usr/cumulus/bin/decode-syseeprom -e)
echo "{2}=${{SERIAL_NUM}}"
"""

    def _get_commands(self):
        commands = self.COMMANDS.format(DeviceDocument.ATTR_MODEL,
                                        DeviceDocument.ATTR_MACADDR,
                                        DeviceDocument.ATTR_SERIAL_NUM)
        return commands.split('\n')


class ClassifierMgr(SshMgr):
    JOB_DESCRIPTION = "Cumulus Classification"
    _app_cls = ClassifierApp
    _task_type = "Classify"

    def _parse_result(self, result):
        data = {}
        lines = result.split('\n')
        for line in lines:
            line = line.strip()
            attrs = line.split('=')
            if len(attrs) == 2:
                attr_name = attrs[0].strip()
                value = attrs[1].strip()
                data[attr_name] = value
        return data

    def _handle_results(self):
        changed = False
        for ipaddr, result in self._aggregator.iterresults():
            data = {
                DeviceDocument.ATTR_SYS_TYPE: 'Cumulus',
                DeviceDocument.ATTR_SERIAL_NUM: None,
                DeviceDocument.ATTR_MACADDR: None,
                DeviceDocument.ATTR_MODEL: None,
                DeviceDocument.ATTR_CONFIGURABLE: False,
            }
            if result.exitcode == 0:
                data.update(self._parse_result(result.stdout))
                serial_num = data[DeviceDocument.ATTR_SERIAL_NUM]
                serial_num = serial_num.upper()
                if serial_num and dev_params_mgr.dev_exists(serial_num):
                    data[DeviceDocument.ATTR_CONFIGURABLE] = True
                    state_str = "Configurable"
                else:
                    logger.info('Could not find serial number %s in csv file',
                                serial_num)
                    state_str = "Unconfigurable"
                report_logger.info("%s: Device: %s, serial number: %s, %s",
                                   self.JOB_DESCRIPTION, ipaddr, serial_num,
                                   state_str)
            else:
                report_logger.info("%s: Device: %s, Failed",
                                   self.JOB_DESCRIPTION, ipaddr)

            dev_doc = self._db.get_device_document(ipaddr)
            if dev_doc.update(data):
                changed = True
        if changed:
            self._db.save()

    def _get_ip_addr_list(self):
        ip_list = []
        for ipaddr, dev_doc in self._db.iterdevices():
            if dev_doc.reachable:
                ip_list.append(ipaddr)
        return ip_list
