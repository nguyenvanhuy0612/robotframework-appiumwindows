# -*- coding: utf-8 -*-
import inspect
import functools

# Internal/private marker attribute
_ROF_STATE_ATTR = "__rof_processed__"


def _run_on_failure_decorator(method):
    """Decorator to wrap keyword methods with _run_on_failure support."""
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception:
            self = args[0] if args else None
            if self and hasattr(self, "_run_on_failure"):
                self._run_on_failure()
            raise

    return wrapper


def ignore_on_fail(method):
    """Decorator to mark methods that should never be wrapped by run_on_failure."""
    setattr(method, _ROF_STATE_ATTR, True)
    return method


class KeywordGroupMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        for name, method in list(attrs.items()):
            if (
                not name.startswith('_')
                and inspect.isfunction(method)
                and not getattr(method, _ROF_STATE_ATTR, False)
            ):
                attrs[name] = _run_on_failure_decorator(method)
        return super().__new__(cls, clsname, bases, attrs)


class KeywordGroup(metaclass=KeywordGroupMetaClass):

    def _get_original(self, method_or_name):
        """
        Get the original (undecorated) method object.

        :param method_or_name: function object or method name (str)
        :return: original method (callable)
        :raises AttributeError: if method name not found
        :raises TypeError: if input is neither str nor callable
        """
        if isinstance(method_or_name, str):
            method = getattr(self.__class__, method_or_name, None)
            if method is None:
                raise AttributeError(f"Method '{method_or_name}' not found on {self.__class__.__name__}")
        elif callable(method_or_name):
            method = method_or_name
        else:
            raise TypeError(
                f"Expected method name (str) or callable, got {type(method_or_name).__name__}"
            )

        return getattr(method, '__wrapped__', method)

    def _invoke_original(self, method_or_name, *args, **kwargs):
        """
        Invoke the original (undecorated) implementation of a method.

        :param method_or_name: function object or method name (str)
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: result of calling the original method
        :raises AttributeError, TypeError: if method lookup fails
        """
        original = self._get_original(method_or_name)
        return original(self, *args, **kwargs)
