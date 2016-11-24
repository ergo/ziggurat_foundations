# -*- coding: utf-8 -*-
"""
Utility functions.
"""


class PlaceholderPasswordChecker(object):
    """Match and return false on check() for '*' (a password hash
    consisting of a single asterisk.) DelegatingPasswordManager would
    otherwise throw an exception 'unrecognized password hash'.
    """

    def match(self, encoded):
        return encoded == '*'

    def check(self, encoded, password):
        return False
