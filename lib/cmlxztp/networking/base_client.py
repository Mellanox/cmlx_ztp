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
@date:   Feb 3, 2016
"""
from __future__ import absolute_import, division, print_function

from cmlxztp.networking.host_model import HostModel


class BaseClient(object):

    def __init__(self, host_data):
        """
        Constructor
        """
        self._hostname = None
        self._username = None
        self._password = None
        self._port = None
        self._extract_host_data(host_data)

    def _extract_host_data(self, host_data):
        self._hostname = host_data.get(HostModel.HOSTNAME)
        self._username = host_data.get(HostModel.USERNAME)
        self._password = host_data.get(HostModel.PASSWORD)
        self._port = host_data.get(HostModel.PORT)
