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
@date:   Dec 20, 2017
"""

from __future__ import absolute_import, division, print_function

import copy
import json
import os

from six import iteritems

from cmlxztp.infra import data_dir


class DeviceDocument(object):
    ATTR_IPADDR = 'ipaddr'
    ATTR_MACADDR = 'macaddr'
    ATTR_SERIAL_NUM = 'serial_num'
    ATTR_REACHABLE = 'reachable'
    ATTR_SYS_TYPE = 'sys_type'
    ATTR_CONFIGURABLE = 'configurable'
    ATTR_STAGES = 'stages'
    ATTR_MODEL = 'model'

    def __init__(self, ipaddr):
        self.ipaddr = ipaddr
        self.macaddr = None
        self.serial_num = None
        self.reachable = False
        self.sys_type = None
        self.configurable = False
        self.stages = None
        self.model = None

    @property
    def data(self):
        return copy.copy(self.__dict__)

    def update(self, dev_data):
        changed = False
        for attr, val in dev_data.iteritems():
            if attr not in self.__dict__:
                continue
            if self.__dict__[attr] != val:
                self.__dict__[attr] = val
                changed = True
        return changed


class DbMgr(object):

    def __init__(self):
        self._repo = {}
        self._data_file = os.path.join(data_dir, "db.json")

    def load(self):
        if self._repo:
            self._repo.clear()
        if os.path.isfile(self._data_file):
            data = {}
            with open(self._data_file) as fp:
                data = json.load(fp)
            for ipaddr, dev_data in iteritems(data):
                dev_doc = self.add_device_document(ipaddr)
                dev_doc.update(dev_data)

    def save(self):
        data = {}
        for ipaddr, dev_doc in self.iterdevices():
            data[ipaddr] = dev_doc.data
        with open(self._data_file, 'w') as fp:
            json.dump(data, fp, indent=4, ensure_ascii=True)

    def get_device_document(self, ipaddr):
        return self._repo.get(ipaddr)

    def add_device_document(self, ipaddr):
        dev_doc = DeviceDocument(ipaddr)
        self._repo[ipaddr] = dev_doc
        return dev_doc

    def iterdevices(self):
        return iteritems(self._repo)
