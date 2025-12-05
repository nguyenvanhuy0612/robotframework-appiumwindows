import time
from typing import Callable, Tuple, Any, Optional, Union, Type

from appium.webdriver import WebElement
from robot.utils import timestr_to_secs
from selenium.common import WebDriverException, TimeoutException


def find_extra(
    application,
    element_finder,
    locator: Union[str, WebElement],
    first_only: bool = False,
    required: bool = False,
    tag: Optional[str] = None
) -> Optional[Union[WebElement, list]]:
    """Find elements using enhanced locator with extra filtering options.

    Args:
        application: Application/driver instance
        element_finder: Element finder instance
        locator: Element locator (string or WebElement)
        first_only: Return only first element if True
        required: Raise error if no elements found
        tag: Optional tag filter

    Returns:
        Single element if first_only=True, list otherwise, None if no elements and first_only=True

    Raises:
        TypeError: If locator type is unsupported
        ValueError: If required=True and no elements found
    """
    # Validate required parameters
    if application is None:
        raise ValueError("Application instance cannot be None. Provide a valid WebDriver instance.")
    if element_finder is None:
        raise ValueError("Element finder cannot be None. Provide a valid ElementFinder instance.")
    if locator is None:
        raise ValueError("Locator cannot be None. Provide a valid locator string or WebElement.")

    # Resolve elements based on locator type
    if isinstance(locator, str):
        found_elements = element_finder.find_extra(application, locator, tag) or []
    elif isinstance(locator, WebElement):
        found_elements = [locator]
    else:
        raise TypeError(
            f"Unsupported locator type: {type(locator).__name__}. "
            f"Expected str (locator string) or WebElement instance."
        )

    # Handle required constraint
    if required and not found_elements:
        raise ValueError(
            f"Required element not found. Locator '{locator}' did not match any elements. "
            f"Consider checking the locator syntax or increasing timeout."
        )

    # Handle empty results
    if not found_elements:
        return None if first_only else []

    # Return appropriate result based on first_only flag
    return found_elements[0] if first_only else found_elements


def until(
    timeout: Union[str, int, float],
    func: Callable[..., Any],
    *args,
    allow_none: bool = False,
    excepts: Type[Exception] = WebDriverException,
    delay: float = 0.5,
    **kwargs
) -> Tuple[Any, Optional[Exception]]:
    """Repeatedly execute a function until it succeeds or timeout occurs.

    This function provides robust retry logic with configurable timeout,
    exception handling, and delay between attempts.

    Args:
        timeout: Maximum time to wait (seconds or Robot Framework time string)
        func: Function to execute
        *args: Positional arguments for func
        allow_none: If True, return immediately when func returns None
        excepts: Exception type(s) to catch and retry on
        delay: Seconds to wait between attempts
        **kwargs: Keyword arguments for func

    Returns:
        Tuple of (result, last_exception). If successful, last_exception is None.
        If timeout occurs, result is None and last_exception contains the error.

    Raises:
        No exceptions are raised - all are caught and returned as last_exception
    """
    # Validate inputs
    if delay < 0:
        raise ValueError(f"Delay must be non-negative, got {delay}. Use 0 for no delay between attempts.")

    # Convert timeout to seconds and validate
    timeout_seconds = timestr_to_secs(timeout)
    if timeout_seconds <= 0:
        raise ValueError(f"Timeout must be positive, got {timeout_seconds}. Provide a valid timeout value.")

    end_time = time.time() + timeout_seconds
    last_captured_exception: Optional[Exception] = None

    while time.time() < end_time:
        try:
            result = func(*args, **kwargs)

            # Reset exception on successful call
            last_captured_exception = None

            # Handle successful non-None result
            if result is not None:
                return result, None

            # Handle None result with allow_none=True
            if allow_none:
                return None, None

        except excepts as exc:
            last_captured_exception = exc

        # Calculate remaining time to avoid oversleeping
        remaining_time = end_time - time.time()
        if remaining_time <= 0:
            break

        # Sleep for the minimum of delay and remaining time
        sleep_time = min(delay, remaining_time)
        time.sleep(sleep_time)

    # Timeout reached - create appropriate exception if none occurred
    if last_captured_exception is None:
        last_captured_exception = TimeoutException(
            f"Operation timed out after {timeout_seconds:.1f} seconds. "
            f"Consider increasing timeout or checking locator/application state."
        )

    return None, last_captured_exception
