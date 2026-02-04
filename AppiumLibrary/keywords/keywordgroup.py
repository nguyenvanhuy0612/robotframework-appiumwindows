# -*- coding: utf-8 -*-
import inspect
import functools

# Internal/private marker attribute name
_RUN_ON_FAILURE_MARKER = "__rof_processed__"


def _run_on_failure_decorator(method):
    """Decorator to wrap keyword methods with _run_on_failure support."""
    if getattr(method, _RUN_ON_FAILURE_MARKER, False):
        # Already decorated or ignored → skip re-wrapping
        return method

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as err:
            self = args[0] if args else None
            if self and hasattr(self, "_run_on_failure"):
                if not getattr(err, "_run_on_failure_executed", False):
                    self._run_on_failure()
                    err._run_on_failure_executed = True
            raise

    setattr(wrapper, _RUN_ON_FAILURE_MARKER, True)      # mark as decorated
    return wrapper


def ignore_on_fail(method):
    """Decorator to mark methods that should never be wrapped by run_on_failure."""
    setattr(method, _RUN_ON_FAILURE_MARKER, True)
    return method


class KeywordGroupMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        for name, method in list(attrs.items()):
            if (
                not name.startswith('_')
                and inspect.isfunction(method)
                and not getattr(method, _RUN_ON_FAILURE_MARKER, False)
            ):
                attrs[name] = _run_on_failure_decorator(method)
        return super().__new__(cls, clsname, bases, attrs)


class KeywordGroup(metaclass=KeywordGroupMetaClass):
    def _invoke_original(self, method, *args, **kwargs):
        """
        Call the original (undecorated) implementation of a method.

        Accepts either:
          - method name (str), e.g. self._invoke_original("click", el)
          - bound method itself, e.g. self._invoke_original(self.click, el)

        Falls back to the current method if undecorated.
        Returns None if method not found at all.
        """
        if isinstance(method, str):
            method = getattr(self, method, None)
        if method is None:
            return None

        if hasattr(method, "__wrapped__"):
            # It's a decorated method (function), so we must pass self
            return method.__wrapped__(self, *args, **kwargs)

        # It's an undecorated bound method, so self is already bound
        return method(*args, **kwargs)
