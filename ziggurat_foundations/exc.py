class ZigguratException(Exception):
    def __init__(self, msg, value=None):
        self.msg = msg
        self.value = value

    def __str__(self):
        return self.msg.format(self.value)


class ZigguratSessionException(ZigguratException):
    pass


class ZigguratResourceTreeMissingException(ZigguratException):
    pass


class ZigguratResourceTreePathException(ZigguratException):
    pass


class ZigguratResourceOutOfBoundaryException(ZigguratException):
    pass
