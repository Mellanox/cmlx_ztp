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

import paramiko

from cmlxztp.networking.base_client import BaseClient


class SFTPClient(BaseClient):

    def __init__(self, host_data):
        """
        Constructor
        """
        self._transport = None
        self._sftp = None
        super(SFTPClient, self).__init__(host_data)

    def connect(self):
        self._transport = paramiko.Transport((self._hostname, self._port))
        self._transport.connect(username=self._username,
                                password=self._password)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)

    def upload(self, local, remote):
        return self._sftp.put(local, remote)

    def download(self, remote, local):
        return self._sftp.get(remote, local)

    def close(self):
        """
        Close the connection if it's active
        """
        if self._transport and self._sftp and self._transport.is_active():
            self._sftp.close()
            self._transport.close()
        self._transport = None
        self._sftp = None
