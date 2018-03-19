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
@date:   Mar 17, 2017
"""
from __future__ import absolute_import, division, print_function

import os
import threading

from six import iteritems

from cmlxztp.infra.ini_parse import iniparser
from cmlxztp.infra.job_mgr import JobStatus
from cmlxztp.infra.logger import logger, report_logger
from cmlxztp.multiproc.multiproc_mgr import MultiProcMgr
from cmlxztp.multiproc.progress_notifier import ProgressMsg, ProgressNotifier
from cmlxztp.multiproc.worker_proc import AbstractWorkerTask


class DevInfo(object):
    SYS_TYPE_CUMULUS = "cumulus"

    def __init__(self, ipaddr, sys_type, job_id, dev_params=None):
        self._ipaddr = ipaddr
        self._sys_type = sys_type
        self._job_id = job_id
        self._dev_params = dev_params

    @property
    def ipaddr(self):
        return self._ipaddr

    @property
    def sys_type(self):
        return self._sys_type

    @property
    def job_id(self):
        return self._job_id

    @property
    def dev_params(self):
        return self._dev_params

    @ipaddr.setter
    def ipaddr(self, val):
        self._ipaddr = val

    @sys_type.setter
    def sys_type(self, val):
        self._sys_type = val

    @job_id.setter
    def job_id(self, val):
        self._job_id = val

    @dev_params.setter
    def dev_params(self, val):
        self._dev_params = val


class TaskError(Exception):

    def __init__(self, msg, err_code=1):
        self.err_code = err_code
        super(TaskError, self).__init__(msg)


class BaseApp(AbstractWorkerTask):

    def __init__(self, dev_info, results_queue, task_type, task_params):
        super(BaseApp, self).__init__(results_queue)
        self._dev_info = dev_info
        self._task_type = task_type
        self._task_params = task_params
        self._progress_notifier = ProgressNotifier(results_queue)

    def get_task_id(self):
        return self._dev_info.ipaddr

    def _get_task_runtime_env(self):
        return "pid: %s, thread_id: %s" % (os.getpid(),
                                           threading.current_thread().ident)

    def execute(self):
        task_env = self._get_task_runtime_env()
        logger.info("Creating %s task: %s",
                    self._task_type, task_env)
        logger.info("%s, handling device: %s",
                    task_env, self._dev_info.ipaddr)
        self._perform_task()
        logger.info("%s, device: %s done",
                    task_env, self._dev_info.ipaddr)

    def _perform_task(self):
        # pylint: disable=broad-except
        progress_msg = ProgressMsg(self._dev_info.job_id, JobStatus.RUNNING)
        self._notify(progress_msg)
        try:
            result = self._task_main()
            self._update_progress(100, result)
        except TaskError as exc:
            self._update_failure(exc)
        except Exception as exc:
            self._update_failure(TaskError(str(exc), 1))
            logger.exception(str(exc))

    def _update_progress(self, progress, result):
        if progress == 100:
            progress_msg = ProgressMsg(
                self._dev_info.job_id, JobStatus.COMPLETED,
                result=result)
        else:
            progress_msg = ProgressMsg(self._dev_info.job_id,
                                       job_progress=progress)
        self._notify(progress_msg)

    def _notify(self, progress_msg):
        self._progress_notifier.notify(self._dev_info, progress_msg)

    def _update_failure(self, fail):
        progress_msg = ProgressMsg(
            self._dev_info.job_id, JobStatus.FAILED, err_code=fail.err_code,
            err_description=str(fail))
        self._notify(progress_msg)

    def _task_main(self):
        raise NotImplementedError(
            "%s.%s", self.__class__.__name__, self._task_main.__name__)


class BaseAggregator(object):

    def __init__(self, task_type):
        self._results = {}
        self._task_type = task_type

    def iterresults(self):
        return iteritems(self._results)

    def _handle_result(self, result, fail):
        if result is not None:
            return result
        return fail

    def aggregate(self, dev_if, result, fail):
        if result is not None and not fail:
            logger.info(
                "aggregating %s result for job(%s-%s)",
                self._task_type, dev_if.job_id, dev_if.ipaddr)
            self._results[dev_if.ipaddr] = result


class BaseProcMgr(object):
    JOB_DESCRIPTION = "Main Job"
    _app_cls = None
    _task_type = None
    SECTION = None

    def __init__(self, devices_db, job_mgr):
        self._job_mgr = job_mgr
        self._job_id = None
        self._aggregator = None
        self._db = devices_db
        self._proc_mgr = None

    def _handle_results(self):
        pass

    def _get_ip_addr_list(self):
        pass

    def _gen_dev_info(self, ipaddr, job_id):
        sys_type = DevInfo.SYS_TYPE_CUMULUS
        return DevInfo(ipaddr, sys_type, job_id, None)

    def _gen_dev_info_list(self):
        dev_list = []
        ip_list = self._get_ip_addr_list()
        for ipaddr in ip_list:
            job_id = self._job_mgr.add_job(
                "%s %s" % (self.JOB_DESCRIPTION, ipaddr), self._job_id)
            dev_info = self._gen_dev_info(ipaddr, job_id)
            dev_list.append(dev_info)
        return dev_list

    def _prepare_run(self):
        pass

    def run(self):
        report_logger.info('%s: starting', self.JOB_DESCRIPTION)
        if self.SECTION:
            enable = iniparser.get_bool_opt(self.SECTION, "enable")
            if not enable:
                logger.info("%s: not enabled, skipping..",
                            self.__class__.__name__)
                report_logger.info('%s: skip', self.JOB_DESCRIPTION)
                return
        self._prepare_run()
        self._job_id = self._job_mgr.add_job(self.JOB_DESCRIPTION)
        logger.info("%s: retrieving list of devices", self.__class__.__name__)
        dev_list = self._gen_dev_info_list()
        if not dev_list:
            logger.info("%s: no devices found", self.__class__.__name__)
            report_logger.info('%s: no devices found', self.JOB_DESCRIPTION)
            return
        logger.info("%s: handling %s devices", self.__class__.__name__,
                    len(dev_list))
        self._run_procs(dev_list)
        self._handle_results()
        report_logger.info('%s: done', self.JOB_DESCRIPTION)

    def _create_aggregator(self):
        pass

    def _run_procs(self, dev_list):
        """
        run procs
        """
        self._aggregator = self._create_aggregator()
        self._proc_mgr = MultiProcMgr(self._app_cls, self._aggregator)
        self._proc_mgr.create_procs(
            dev_list, self._task_type, None, self._job_mgr)
        self._proc_mgr.wait()
        return True

    def terminate(self):
        if self._proc_mgr:
            logger.info("%s: terminate!", self.__class__.__name__)
            self._proc_mgr.terminate()
