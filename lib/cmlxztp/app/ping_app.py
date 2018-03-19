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

import netaddr

from cmlxztp.app.base_app import BaseApp, BaseAggregator, BaseProcMgr
from cmlxztp.dbmgr.db_mgr import DeviceDocument
from cmlxztp.infra.ini_parse import iniparser
from cmlxztp.infra.logger import report_logger


class PingApp(BaseApp):

    def _task_main(self):
        result = os.system('ping -c 1 %s > /dev/null 2>&1' %
                           str(self._dev_info.ipaddr))
        return result


class PingAggregator(BaseAggregator):
    pass


class PingMgr(BaseProcMgr):
    _app_cls = PingApp
    _task_type = "Ping"
    JOB_DESCRIPTION = "Ping"
    SECTION = "Discovery"

    def __init__(self, devices_db, job_mgr):
        subnets = iniparser.get_opt(self.SECTION, "subnets")
        self._subnets = subnets.split()
        super(PingMgr, self).__init__(devices_db, job_mgr)

    def _handle_results(self):
        changed = False
        for ipaddr, result in self._aggregator.iterresults():
            dev_doc = self._db.get_device_document(ipaddr)
            if not dev_doc:
                dev_doc = self._db.add_device_document(ipaddr)
                changed = True
            if result == 0:
                reachable = True
                state_desc = "Reachable"
            else:
                reachable = False
                state_desc = "Unreachable"
            data = {
                DeviceDocument.ATTR_REACHABLE: reachable
            }
            report_logger.info("%s: Device: %s, %s",
                               self.JOB_DESCRIPTION, ipaddr, state_desc)
            if dev_doc.update(data):
                changed = True
        if changed:
            self._db.save()

    def _create_aggregator(self):
        return PingAggregator(self._task_type)

    def _get_ip_addr_list(self):
        ip_list = []
        for subnet in self._subnets:
            ip_net = netaddr.IPNetwork(subnet)
            ip_list.extend([str(ipaddr) for ipaddr in ip_net])
        return ip_list
