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

import signal
import sys

from cmlxztp.app.classifier_app import ClassifierMgr
from cmlxztp.app.config_app import ConfigMgr
from cmlxztp.app.config_files_app import ConfigFilesMgr
from cmlxztp.app.ecn_traffic_app import ECNConfigMgr
from cmlxztp.app.image_upgrade_app import ImageUpgradeMgr
from cmlxztp.app.license_app import LicenseMgr
from cmlxztp.app.ping_app import PingMgr
from cmlxztp.app.pre_config_app import PreConfigMgr
from cmlxztp.dbmgr.db_mgr import DbMgr
from cmlxztp.infra.job_mgr import JobMgr
from cmlxztp.infra.logger import logger, MainLogger, report_logger


class MainApp(object):
    MANAGER_CLASSES = (
        PingMgr, ClassifierMgr, PreConfigMgr, ImageUpgradeMgr,
        LicenseMgr, ConfigMgr, ConfigFilesMgr, ECNConfigMgr)

    def __init__(self):
        self._curr_mgr = None
        self._devices_db = DbMgr()
        self._devices_db.load()
        self._job_mgr = JobMgr()

    def _sig_handler(self, signum, _):
        logger.info("Got signal %s, terminating...", signum)
        if self._curr_mgr:
            self._curr_mgr.terminate()
        sys.exit(0)

    def run(self):
        signal.signal(signal.SIGINT, self._sig_handler)
        signal.signal(signal.SIGTERM, self._sig_handler)

        logger.info("Starting new session")
        report_logger.info("*****Start*****")
        for mgr_cls in self.MANAGER_CLASSES:
            logger.info("Starting Manager: %s", mgr_cls.__name__)
            self._curr_mgr = mgr_cls(self._devices_db, self._job_mgr)
            self._curr_mgr.run()
        report_logger.info("******End******")
        logger.info("Session finished")


if __name__ == '__main__':
    MainLogger.init_logger()
    MainApp().run()
