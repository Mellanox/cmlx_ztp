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

import threading

from cmlxztp.infra.logger import logger


class JobListenerException(Exception):
    pass


class JobStatus(object):
    # pylint: disable=no-init
    INIT = 0
    RUNNING = 1
    COMPLETED = 10
    FAILED = 11


class Job(object):

    def __init__(self, job_id, description='', parent_job_id=None):
        self.job_id = job_id
        self.parent_job_id = parent_job_id
        self.description = description
        self.status = JobStatus.INIT
        self.err_code = 0
        self.err_description = None
        self.progress = 0


class JobMgr(object):

    def __init__(self):
        self.job_repo = {}
        self.child_jobs_mapping = {}
        self._next_job_id = {}
        self._lock = threading.Lock()
        self._listeners = {}

    def _gen_id(self, parent_id):
        self._lock.acquire()
        try:
            next_id = self._next_job_id.get(parent_id, 1)
            self._next_job_id[parent_id] = next_id + 1
            if parent_id:
                return "%s.%s" % (parent_id, next_id)
            return str(next_id)
        finally:
            self._lock.release()

    def add_job(self, description, parent_id=None):
        if parent_id is not None and parent_id not in self.job_repo:
            logger.error("could not find parent job: %s", parent_id)
            return
        job_id = self._gen_id(parent_id)
        job = Job(job_id, description, parent_id)
        self.job_repo[job_id] = job
        if parent_id:
            child_jobs = self.child_jobs_mapping.setdefault(parent_id, [])
            child_jobs.append(job_id)
        return job_id

    def add_listener(self, job_id, listener, *args, **kw):
        listener_data = (listener, args, kw)
        listeners = self._listeners.setdefault(job_id, [])
        listeners.append(listener_data)

    def get_job(self, job_id):
        return self.job_repo.get(job_id)

    def _remove_job(self, job_id):
        child_jobs = self.child_jobs_mapping.get(job_id)
        if child_jobs:
            for child_job in child_jobs:
                self._remove_job(child_job)
            del self.child_jobs_mapping[job_id]
        del self.job_repo[job_id]

    def del_job(self, job_id):
        job = self.get_job(job_id)
        if not job:
            logger.error("could not delete job: %s, not found", job_id)
            return False
        if job.parent_id is not None:
            logger.error("could not delete job: %s, it is a child job", job_id)
            return False
        if not self.is_done(job.status):
            logger.error("could not delete job: %s, job still running", job_id)
            return False
        self._remove_job(job_id)
        return True

    @classmethod
    def is_done(cls, status):
        return status in (JobStatus.COMPLETED, JobStatus.FAILED)

    def _update_parent_job(self, parent_id):

        child_jobs = self.child_jobs_mapping.get(parent_id)
        parent_status = None
        for child_id in child_jobs:
            child_job = self.get_job(child_id)
            if child_job.status == JobStatus.COMPLETED:
                if parent_status != JobStatus.FAILED:
                    parent_status = JobStatus.COMPLETED
            elif child_job.status == JobStatus.FAILED:
                parent_status = JobStatus.FAILED
            else:
                parent_status = None
                break
        if parent_status is not None:
            logger.info('JobMgr: updating parent job %s, status: %s',
                        parent_id, parent_status)
            parent_job = self.get_job(parent_id)
            self._set_job_status(parent_job, parent_status, 100)

    def update_job_status(self, job_id, status, progress=None, err_code=None,
                          err_description=None):
        logger.info('JobMgr: updating job %s, status: %s', job_id, status)
        job = self.get_job(job_id)
        if not job:
            logger.error("trying to update unexisting job: %s", job_id)
        self._set_job_status(job, status, progress, err_code, err_description)
        parent_id = job.parent_job_id
        if parent_id and self.is_done(status):
            self._update_parent_job(parent_id)

    def _notify(self, job_id):
        listeners = self._listeners.get(job_id, [])
        for listener_data in listeners:
            logger.info(
                "notifying listeners for job: %s", job_id)
            try:
                listener, args, kw = listener_data
                listener(job_id, *args, **kw)
            except JobListenerException as e:
                logger.error(
                    "got an error while notiying listener for job: %s (%s)",
                    job_id, str(e))

    def _set_job_status(self, job, status, progress=None, err_code=None,
                        err_description=None):
        prev_status = job.status
        job.status = status
        if progress is not None:
            job.progress = progress
        if err_code is not None:
            job.err_code = err_code
        if err_description is not None:
            job.err_description = err_description
        if prev_status != status:
            self._notify(job.job_id)
