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

import csv
import os
import uuid

from cmlxztp.infra import conf_dir


class ConfigFile(object):

    def __init__(self, config_data):
        self.file_name = config_data['file_name']
        self.file_dst = config_data['file_dst']
        self.service_name = config_data['service_name']
        self.uuid = str(uuid.uuid4())

        if self.file_name:
            self.file_name = self.file_name.strip()
        if self.file_dst:
            self.file_dst = self.file_dst.strip()
        if self.service_name:
            self.service_name = self.service_name.strip()

    def __repr__(self, *args, **kwargs):
        return self.file_name


class ConfigFilesRepository(object):

    FIELD_NAMES = ('file_name', 'file_dst', 'service_name')

    def __init__(self):
        self._repo = list()
        self._read_csv()

    def _read_csv(self):
        csv_file_name = os.path.join(conf_dir, "config_files.csv")
        with open(csv_file_name) as csvfile:
            reader = csv.DictReader(csvfile, self.FIELD_NAMES)
            next(reader, None)
            for row in reader:
                config_file = ConfigFile(row)
                if config_file.file_name:
                    self._repo.append(config_file)

    def __iter__(self):
        return  self._repo.__iter__()
