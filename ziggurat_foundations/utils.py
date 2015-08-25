"""
Utility functions.
"""
from cryptacular.core import PasswordChecker


class PlaceholderPasswordChecker(PasswordChecker):
    """Match and return false on check() for '*' (a password hash
    consisting of a single asterisk.) DelegatingPasswordManager would
    otherwise throw an exception 'unrecognized password hash'.
    """

    def match(self, encoded):
        return encoded == '*'

    def check(self, encoded, password):
        return False
