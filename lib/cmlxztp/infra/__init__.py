"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2017. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.
"""
from __future__ import absolute_import, division, print_function

import os


def _get_base_dir():
    curr_file = __file__
    curr_dir = os.path.dirname(curr_file)
    _base_dir = os.path.join(curr_dir, os.pardir, os.pardir, os.pardir)
    _base_dir = os.path.normpath(_base_dir)
    return _base_dir


# pylint: disable=invalid-name
base_dir = _get_base_dir()


def _get_conf_dir(_base_dir):
    conf_path = os.path.join(_base_dir, 'conf')
    if not os.path.isdir(conf_path):
        conf_path = '/etc/cmlxztp'
    return conf_path


def _get_data_dir(_base_dir):
    data_path = os.path.join(_base_dir, 'data')
    if not os.path.isdir(data_path):
        data_path = '/var/lib/cmlxztp/data'
    return data_path


conf_dir = _get_conf_dir(base_dir)
data_dir = _get_data_dir(base_dir)
