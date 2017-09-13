# encoding: utf8

from __future__ import absolute_import


class RedisMixinException(Exception):
    pass


class NotFound(KeyError, RedisMixinException):
    """Object not found found for a single object query."""
    pass


class MultipleFound(KeyError, RedisMixinException):
    """Multiple objects found for a single object query."""
    pass


class StrictPerformanceException(RedisMixinException):
    """Avoid performance issues on due to programming errors."""
    pass
