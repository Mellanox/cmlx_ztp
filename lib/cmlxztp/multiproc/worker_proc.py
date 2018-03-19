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
@date:   Dec 12, 2017
"""
from __future__ import absolute_import, division, print_function

import multiprocessing
import os
import signal
import threading

from cmlxztp.infra.logger import logger
from six.moves import queue


def devide_tasks(task_list, proc_count):
    """Yield successive n-sized chunks from list."""
    list_size = len(task_list)
    chunck_size = int(list_size / proc_count)
    if list_size % proc_count != 0:
        chunck_size += 1
    for i in range(0, list_size, chunck_size):
        yield task_list[i:i + chunck_size]


class WorkerTaskError(Exception):
    pass


class AbstractWorkerTask(object):

    def __init__(self, results_queue):
        self._results_queue = results_queue

    def get_task_id(self):
        pass

    def execute(self):
        pass


class WorkerThread(threading.Thread):
    """ Thread executing tasks from a given tasks queue """

    def __init__(self, tasks):
        super(WorkerThread, self).__init__()
        self._tasks = tasks
        self.daemon = True

    def run(self):
        logger.info('starting new thread in process: %s',
                    os.getpid())
        while True:
            task_obj = self._tasks.get()
            try:
                task_obj.execute()
            except WorkerTaskError as e:
                # An exception happened in this thread
                logger.error(
                    "%s: an error ocuured - %s",
                    task_obj.get_task_id(), str(e))
            finally:
                # Mark this task as done, whether an exception happened or not
                self._tasks.task_done()


class WorkerThreadPool(object):
    """ Pool of threads consuming tasks from a queue """

    def __init__(self, pool_size):
        self._tasks = queue.Queue(pool_size)
        for _ in range(pool_size):
            work_thread = WorkerThread(self._tasks)
            work_thread.start()

    def add_task(self, task_obj):
        """ Add a task to the queue """
        self._tasks.put(task_obj)

    def join(self):
        """ Wait for completion of all the tasks in the queue """
        self._tasks.join()


class WorkerProcess(multiprocessing.Process):

    def __init__(self, task_list, pool_size, nice):
        super(WorkerProcess, self).__init__()
        self._task_list = task_list
        self._pool_size = min(pool_size, len(task_list))
        self._thread_pool = None
        self._is_done = False
        self._nice = nice

    def run(self):
        os.nice(self._nice)
        logger.info('starting process: %s, spawning %s threads for %s tasks',
                    os.getpid(), self._pool_size, len(self._task_list))
        self._thread_pool = WorkerThreadPool(
            self._pool_size)
        for task_obj in self._task_list:
            self._thread_pool.add_task(task_obj)
        self._thread_pool.join()
        self._is_done = True

    def kill(self):
        if not self.is_alive():
            return False
        try:
            pid = self.pid
            logger.info('terminating process: %s', pid)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            return False
        return True
