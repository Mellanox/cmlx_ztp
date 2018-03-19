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
@date:   Aug 18, 2017
"""
from __future__ import absolute_import, division, print_function

import multiprocessing
import threading
import time

from cmlxztp.infra.logger import logger
from cmlxztp.multiproc.progress_notifier import ProgressListener
from cmlxztp.multiproc.worker_proc import devide_tasks, WorkerProcess


class MultiProcMgr(object):
    multiprocessing.util.log_to_stderr(logger.level)
    _LAST_ID = 1000
    _id_lock = threading.Lock()

    def __init__(self, app_cls, aggregator, thread_pool_size=32, nice=5):
        self._app_cls = app_cls
        self._aggregator = aggregator
        self._thread_pool_size = thread_pool_size
        # keep a proc for listener
        max_proc_count = multiprocessing.cpu_count() / 2 - 1
        if max_proc_count <= 0:
            max_proc_count = 1
        self._max_proc_count = max_proc_count

        self._queue = multiprocessing.Queue()
        self._pool = []
        self._progress_listener = None
        self._terminated = False
        MultiProcMgr._id_lock.acquire()
        _last_id = MultiProcMgr._LAST_ID
        MultiProcMgr._LAST_ID += 1
        MultiProcMgr._id_lock.release()
        self._name = "MultiProcMgr-%06X" % _last_id
        self._nice = nice

    @property
    def aggregator(self):
        return self._aggregator

    @property
    def name(self):
        return self._name

    def create_procs(self, dev_list, task_type, task_params, job_mgr):
        self._distribute_devices(dev_list, task_type, task_params, job_mgr)

    @classmethod
    def _pool_cleanup(cls, pool, name):
        logger.info("%s: cleanup pool processes", name)
        for proc in pool:
            pid = proc.pid
            if proc.kill():
                logger.info("%s: killing process: %s", name, pid)

    @classmethod
    def _terminate_pool(cls, pool, name):
        th = threading.Thread(target=cls._pool_cleanup, args=(pool, name))
        th.start()

    def stop_procs(self):
        self._terminated = True
        if self._progress_listener:
            self._progress_listener.stop()
            self._progress_listener = None
        if self._pool:
            logger.info("%s: terminating pool", self.name)
            self._terminate_pool(list(self._pool), self.name)
            self._pool = []

    def is_running(self):
        return bool(self._pool)

    def _distribute_devices(self, dev_list, task_type, task_params, job_mgr):
        self._progress_listener = ProgressListener(
            self.aggregator, self._queue, self.name, job_mgr)
        self._progress_listener.listen()
        dev_count = len(dev_list)
        logger.info(
            "%s (%s): handling %s devices",
            self.name, task_type, dev_count)
        th = threading.Thread(target=self._create_pool,
                              args=(dev_list, task_type, task_params))
        th.start()

    def _pool_done(self, task_type, start_time, _):
        if not self._pool or self._terminated:
            return
        end_time = time.time()
        logger.info(
            "%s (%s): task done within %s seconds",
            self.name, task_type, end_time - start_time)
        if self._progress_listener:
            self._progress_listener.send_stop_message()
            self._progress_listener = None
        time.sleep(.5)
        self._pool_cleanup(list(self._pool), self.name)
        self._pool = []

    def _maintain_pool(self, pool, task_type, start_time):
        while pool:
            unfinished_procs = []
            for proc in pool:
                if proc.exitcode is not None:
                    # worker exited
                    logger.debug('cleaning up worker %d', proc.pid)
                    proc.join()
                else:
                    unfinished_procs.append(proc)
            pool = unfinished_procs
            if pool:
                time.sleep(.1)
        self._pool_done(task_type, start_time, None)

    def _create_pool(self, dev_list, task_type, task_params):
        proc_count = min(self._max_proc_count, len(dev_list))
        self._pool = []
        task_list = [
            self._app_cls(dev_info, self._queue, task_type, task_params)
            for dev_info in dev_list]
        for sub_task_list in devide_tasks(task_list, proc_count):
            logger.info(
                "%s (%s): task creating process with %s tasks",
                self.name, task_type, len(sub_task_list))
            proc = WorkerProcess(
                sub_task_list, self._thread_pool_size, self._nice)
            self._pool.append(proc)

        for proc in self._pool:
            proc.start()

        start_time = time.time()
        self._maintain_pool(list(self._pool), task_type, start_time)
        logger.info(
            "%s (%s): task finished", self.name, task_type)

    def wait(self):
        self._progress_listener.join()

    def terminate(self):
        if self._pool:
            for proc in self._pool:
                proc.kill()
