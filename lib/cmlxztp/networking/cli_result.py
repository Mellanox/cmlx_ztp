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
@date:   Aug 27, 2015
"""

RESULT_FORMAT = """\
exitcode: %s
stdout: %s
stderr: %s
"""


class ProcessResult(object):

    def __init__(self):
        self._stdout = ""
        self._stderr = ""
        self._exitcode = 0

    @property
    def stdout(self):
        return self._stdout

    @stdout.setter
    def stdout(self, value):
        self._stdout = value

    @property
    def stderr(self):
        return self._stderr

    @stderr.setter
    def stderr(self, value):
        self._stderr = value

    @property
    def exitcode(self):
        return self._exitcode

    @exitcode.setter
    def exitcode(self, value):
        self._exitcode = value

    def __repr__(self):
        return RESULT_FORMAT % (self.exitcode, self.stdout, self.stderr)


class CliResult(ProcessResult):

    def __init__(self):
        super(CliResult, self).__init__()
        self._epilogue = None

    @property
    def epilogue(self):
        return self._epilogue

    @epilogue.setter
    def epilogue(self, value):
        self._epilogue = value
