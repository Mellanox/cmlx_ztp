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
@date:   Mar 16, 2017
"""
from __future__ import absolute_import, division, print_function

import threading

from cmlxztp.infra.job_mgr import JobStatus
from cmlxztp.infra.logger import logger


class ProgressMsg(object):

    def __init__(self, job_id, job_status=None, job_progress=None,
                 result=None, err_code=None, err_description=None):
        self._job_id = job_id
        self._job_status = job_status
        self._job_progress = job_progress
        self._result = result
        self._err_code = err_code
        self._err_description = err_description

    @property
    def job_id(self):
        return self._job_id

    @property
    def job_status(self):
        return self._job_status

    @property
    def job_progress(self):
        return self._job_progress

    @property
    def result(self):
        return self._result

    @property
    def err_code(self):
        return self._err_code

    @property
    def err_description(self):
        return self._err_description


class ProgressNotifier(object):

    def __init__(self, queue):
        self._queue = queue

    def notify(self, dev_if, progress_msg):
        self._queue.put((dev_if, progress_msg))


class ProgressListener(object):

    def __init__(self, result_aggregator, queue, name, job_mgr):
        self._stopped = False
        self.job_mgr = job_mgr
        self._result_aggregator = result_aggregator
        self._queue = queue
        self._name = name
        self._event = threading.Event()

    def listen(self):
        th = threading.Thread(target=self._listen_in_thread)
        th.start()

    def stop(self):
        self._stopped = True
        self.send_stop_message()

    @classmethod
    def _send_stop_msg_in_thread(cls, queue, name):
        try:
            if queue:
                logger.info("Listener %s - sending stop message!", name)
                queue.put(None, False)
        except (IOError, EOFError):
            pass
        logger.info("Listener %s - stop message sent!", name)

    def send_stop_message(self):
        th = threading.Thread(target=self._send_stop_msg_in_thread,
                              args=(self._queue, self._name))
        th.start()

    def _listen_in_thread(self):
        logger.info("Progress Listener %s - start listening thread",
                    self._name)
        while not self._stopped:
            try:
                msg = self._queue.get()
            except (IOError, EOFError):
                break
            if msg:
                dev_if, progress_msg = msg
                self._progress_updated(dev_if, progress_msg)
            else:
                break
        self._event.set()
        logger.info("Progress Listener %s - stop listening", self._name)

    def _progress_updated(self, dev_if, progress_msg):
        if not progress_msg:
            return
        logger.info(
            "Progress Listener %s : updating progress for job(%s - %s)",
            self._name, dev_if.job_id, dev_if.ipaddr)
        job_id = progress_msg.job_id
        jod_data = self.job_mgr.get_job(job_id)
        if not jod_data:
            return
        job_status = jod_data.status

        if not self.job_mgr.is_done(job_status):
            self.job_mgr.update_job_status(
                job_id, progress_msg.job_status,
                progress=progress_msg.job_progress,
                err_code=progress_msg.err_code,
                err_description=progress_msg.err_description)
        fail = (progress_msg.job_status == JobStatus.FAILED)
        if self._result_aggregator:
            self._result_aggregator.aggregate(
                dev_if, progress_msg.result, fail)

    def join(self):
        while True:
            if self._event.wait(1):
                break
