# -*- coding: utf-8 -*-


class ZigguratException(Exception):
    def __init__(self, msg, value=None):
        self.msg = msg
        self.value = value

    def __str__(self):
        return self.msg.format(self.value)


class ZigguratSessionException(ZigguratException):
    pass


class ZugguratTreeException(ZigguratException):
    pass


class ZigguratResourceTreeMissingException(ZugguratTreeException):
    pass


class ZigguratResourceTreePathException(ZugguratTreeException):
    pass


class ZigguratResourceOutOfBoundaryException(ZugguratTreeException):
    pass
