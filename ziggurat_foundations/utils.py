# -*- coding: utf-8 -*-
"""
Utility functions.
"""
import random
import string


class PlaceholderPasswordChecker(object):
    """Match and return false on check() for '*' (a password hash
    consisting of a single asterisk.) DelegatingPasswordManager would
    otherwise throw an exception 'unrecognized password hash'.
    """

    def match(self, encoded):
        return encoded == "*"

    def check(self, encoded, password):
        return False


class ModelProxy(dict):
    """
    Holds model references used in services
    """

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        return self[key]


class NOOP(object):
    """
    For tree manager
    """

    def __nonzero__(self):
        return False

        # py3 compat

    __bool__ = __nonzero__


noop = NOOP()


def generate_random_string(chars=7):
    """

    :param chars:
    :return:
    """
    return u"".join(random.sample(string.ascii_letters * 2 + string.digits, chars))
