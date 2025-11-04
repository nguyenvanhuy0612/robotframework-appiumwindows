# -*- coding: utf-8 -*-
import inspect
import functools

_ROF_STATE_ATTR = "__rof_processed__"


def _run_on_failure_decorator(method):
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

        original = self._get_original(method_or_name)
        return original(self, *args, **kwargs)


class MyKeyword(KeywordGroup):

    @ignore_on_fail
    def keyword1(self):
        print('This is keyword 1')

    def keyword2(self):
        print('This is keyword 2')
        if hasattr(self, 'keyword1'):
            self._invoke_original('keyword1')

if __name__ == '__main__':
    my_keyword = MyKeyword()
    my_keyword.keyword2()