import time
from typing import Callable, Tuple, Any, Optional, Union

from appium.webdriver import WebElement
from robot.utils import timestr_to_secs
from selenium.common import WebDriverException, TimeoutException


def find_extra(application, element_finder, locator, first_only=False, required=False, tag=None):
    # Resolve elements from locator
    if isinstance(locator, str):
        elements = element_finder.find_extra(application, locator, tag) or []
    elif isinstance(locator, WebElement):
        elements = [locator]
    else:
        raise TypeError(f"Unsupported locator type: {type(locator)}")

    # If required → must have at least 1 element
    if required and not elements:
        raise ValueError(f"Element locator '{locator}' did not match any elements.")

    # If no elements and not required → early return
    if not elements:
        return None if first_only else []

    # first_only=True → return single element
    if first_only:
        return elements[0]

    # Otherwise return full list
    return elements


def until(
    timeout: Union[str, int, float],
    func: Callable[..., Any],
    *args,
    allow_none: bool = False,
    excepts=WebDriverException,
    delay: float = 0.5,
    **kwargs
) -> Tuple[Any, Optional[Exception]]:
    """
    Repeatedly executes `func` until:
      • it returns a non-None value, OR
      • allow_none=True (returns even if result is None), OR
      • timeout expires.

    Returns:
        (result, last_exception)
    """

    end_time = time.time() + timestr_to_secs(timeout)
    last_exception: Optional[Exception] = None

    while True:
        try:
            result = func(*args, **kwargs)
            last_exception = None  # reset last error on successful call

            # Case 1: success (non-None)
            if result is not None:
                return result, None

            # Case 2: result=None but allow_none=True means return immediately
            if allow_none:
                return None, None

        except excepts as exc:
            last_exception = exc

        # Timeout check *after* performing operation
        if time.time() >= end_time:
            break

        time.sleep(delay)

    # Timeout reached ---------------------------------------------------------
    # If no exception occurred during attempts, create one
    if last_exception is None:
        last_exception = TimeoutException(f"Timed out after {timeout}")

    # Returning None means: timeout OR last call returned None (when !allow_none)
    return None, last_exception
