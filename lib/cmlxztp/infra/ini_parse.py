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
@date:   Sep 27, 2017
"""
from __future__ import absolute_import, division, print_function

import os

from cmlxztp.infra import conf_dir
from cmlxztp.infra.logger import logger
from six.moves import configparser


class IniError(Exception):
    pass


class IniParser(object):

    def __init__(self):
        self._parser = configparser.SafeConfigParser()
        self._ini_file = os.path.join(conf_dir, "cmlxztp.ini")
        read_ok = self._parser.read(self._ini_file)
        if not read_ok:
            logger.error("Failed to open ini file: %s", self._ini_file)

    @staticmethod
    def _safe_get_opt(method, section, option):
        try:
            return method(section, option)
        except configparser.Error as exc:
            logger.error("Failed to get ini option %s.%s: %s",
                         section, option, str(exc))
        except ValueError as exc:
            logger.error("Failed to convert ini option %s.%s: %s",
                         section, option, str(exc))
        raise IniError("Section: %s, Option: %s" % (section, option))

    def get_opt(self, section, option):
        """Return an option string value."""
        return self._safe_get_opt(self._parser.get, section, option)

    def get_int_opt(self, section, option):
        """Return an option int value."""
        return self._safe_get_opt(self._parser.getint, section, option)

    def get_bool_opt(self, section, option):
        """Return an option bool value."""
        return self._safe_get_opt(self._parser.getboolean, section, option)


# pylint: disable=invalid-name
iniparser = IniParser()
