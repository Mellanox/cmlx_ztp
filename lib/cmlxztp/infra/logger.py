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

import logging


class MainLogger(object):
    LOGGER_NAME = "cmlxztp"
    REPORT_LOGGER_NAME = "cmlxztp_report"

    _FORMAT = '%(asctime)s.%(msecs)03d %(name)-5s %(levelname)-7s %(message)s'
    _DATE_FMT = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FMT)

    def __init__(self):
        logging.basicConfig(format=self._FORMAT, datefmt=self._DATE_FMT)
        self._level = logging.INFO

    def load_logging_conf(self):
        pass

    def add_file_handler(self, logger_name):
        """
        Added a file handler to the given logger.
        @param logger:
            a logger object to add the file handler to.
        @param file_path:
            path to the logging file.
        @param formatter:
            a Format object to add to the handler
        """
        file_path = "/var/log/%s.log" % logger_name
        handler = logging.FileHandler(file_path)
        handler.setFormatter(self.formatter)
        handler.setLevel(self._level)
        _logger = logging.getLogger(logger_name)
        _logger.addHandler(handler)
        _logger.setLevel(self._level)

    @classmethod
    def init_logger(cls):
        logger_obj = cls()
        logger_obj.load_logging_conf()
        logger_obj.add_file_handler(cls.LOGGER_NAME)
        logger_obj.add_file_handler(cls.REPORT_LOGGER_NAME)


# pylint: disable=invalid-name
logger = logging.getLogger(MainLogger.LOGGER_NAME)
report_logger = logging.getLogger(MainLogger.REPORT_LOGGER_NAME)
