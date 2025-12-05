import time
from typing import Callable, Tuple, Any, Optional, Union

from appium.webdriver import WebElement as AppiumElement
from robot.libraries.BuiltIn import BuiltIn
from robot.utils import timestr_to_secs
from selenium.common import WebDriverException

from AppiumLibrary.locators import ElementFinder
from AppiumLibrary.utils import find_extra, until
from .keywordgroup import KeywordGroup


class _ElementAppiumKeywords(KeywordGroup):
    """Keywords for finding and interacting with elements in Appium tests.

    This class provides methods for element location, waiting, and context management
    specifically designed for Appium-based mobile and desktop testing.
    """

    def __init__(self):
        self._element_finder = ElementFinder()
        self._bi = BuiltIn()
        self._context = {}

    def appium_get_context(self, element_only=False, locator_only=False):
        """Get the current search context.

        Args:
            element_only: If True, return only the element part of context
            locator_only: If True, return only the locator part of context

        Returns:
            The current context dict, or specific part if flags are set
        """
        if element_only:
            return self._context.get('element')
        if locator_only:
            return self._context.get('locator')
        return self._context

    def appium_set_context(self, context, reference, timeout, clear=True) -> dict:
        """Set the search context for subsequent element operations.

        Args:
            context: Locator string, AppiumElement, or context dict
            reference: Reference for finding context element
            timeout: Timeout for finding context element
            clear: Whether to clear existing context first

        Returns:
            The previous context dict
        """
        old_context = self._context
        if clear:
            self._context = {}

        if isinstance(context, str):
            self._context['element'] = self._find_context(context, reference, timeout)
            self._context['locator'] = context
        if isinstance(context, AppiumElement):
            self._context['element'] = context
            self._info(f"Setting context element directly, using reference '{reference}' as locator")
            self._context['locator'] = reference
        elif isinstance(context, dict) and context.get('locator'):
            self._info(f"Setting context from dictionary: {context}")
            self._context['element'] = self._find_context(context['locator'], reference, timeout)
            self._context['locator'] = context['locator']

        if not self._context.get('element'):
            self._warn("Failed to set context element - no valid element found")
            self._context = {}

        return old_context

    def _find_context(self, locator, reference=None, timeout=20, ref_timeout=5):
        """Find context element based on locator and reference.

        Args:
            locator: Primary locator string
            reference: Reference for finding specific element
            timeout: Timeout for finding elements
            ref_timeout: Timeout for reference-based finding

        Returns:
            The found context element

        Raises:
            Exception: If no elements found or reference is invalid
        """
        elements = self._invoke_original("appium_get_elements", locator, timeout)
        if not elements:
            raise Exception(f"No elements found for locator '{locator}' within {timeout}s")

        element = None

        # Numeric reference (int or str)
        if isinstance(reference, int) or (isinstance(reference, str) and reference.isnumeric()):
            idx = int(reference)
            if not (0 <= idx < len(elements)):
                raise Exception(f"Reference index {idx} is out of range (0-{len(elements)-1}) for locator '{locator}'")
            element = elements[idx]

        # String sub-locator
        elif isinstance(reference, str):
            for el in elements:
                if self._invoke_original("appium_get_elements_in_element", el, reference, ref_timeout):
                    element = el
                    break

        # Default - first element
        else:
            element = elements[0]

        if not element:
            raise Exception(f"Could not find context element for locator '{locator}' with reference '{reference}'")

        return element

    def appium_clear_context(self):
        """Clear the current search context.

        Returns:
            The previous context dict
        """
        old_context = self._context
        self._context = {}
        return old_context

    def appium_element_exist(self, locator, timeout=10) -> bool:
        """Check if element exists within timeout period.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            True if element exists, False otherwise
        """
        def func():
            elements = self._appium_get(locator)
            if elements:
                return True
            raise Exception(f"Element '{locator}' not found yet")

        result, _ = until(timeout, func)
        return result is not None

    def _appium_get(self, locator):
        """Get elements using locator within current context.

        Args:
            locator: Element locator string

        Returns:
            List of found elements
        """
        application = self._context.get('element') or self._current_application()
        elements = find_extra(application, self._element_finder, locator)
        return elements

    def appium_elements_exist(self, locator, timeout=10) -> list | bool:
        """Check if elements exist and return them.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            List of elements if found, False otherwise
        """
        def func():
            elements = self._appium_get(locator)
            if elements:
                return elements
            raise Exception(f"Elements '{locator}' not found yet")

        result, _ = until(timeout, func)
        return result if result is not None else False

    def appium_wait_element_visible(self, locator, timeout=10) -> AppiumElement | bool:
        """Wait until element becomes visible.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            The visible element if found, False otherwise
        """
        def func():
            elements = self._appium_get(locator)
            if elements and elements[0].is_displayed():
                return elements[0]
            raise Exception(f"Element '{locator}' not visible yet")

        result, _ = until(timeout, func)
        return result if result is not None else False

    def appium_wait_element_not_visible(self, locator, timeout=10) -> bool:
        """Wait until element is not visible.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            True if element becomes not visible, False otherwise
        """
        not_visible_count = 0

        def func():
            nonlocal not_visible_count
            elements = self._appium_get(locator)
            if not elements or (elements and not elements[0].is_displayed()):
                not_visible_count += 1
                if not_visible_count >= 2:
                    return True
            else:
                not_visible_count = 0
            raise Exception(f"Element '{locator}' is still visible")

        result, _ = until(timeout, func)
        return result is not None

    def appium_element_should_be_visible(self, locator, timeout=10) -> bool:
        """Assert that element is visible.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            True if element is visible

        Raises:
            Exception: If element is not visible within timeout
        """
        def func():
            elements = self._appium_get(locator)
            if elements and elements[0].is_displayed():
                return True
            raise Exception(f"Element '{locator}' is not visible")

        result, exception = until(timeout, func, allow_none=False)
        if result is None:
            raise Exception(f"Element '{locator}' should be visible but is not within {timeout}s")
        return True

    def appium_element_should_be_not_visible(self, locator, timeout=10) -> bool:
        """Assert that element is not visible.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            True if element is not visible

        Raises:
            Exception: If element is visible within timeout
        """
        def func():
            elements = self._appium_get(locator)
            if not elements or (elements and not elements[0].is_displayed()):
                return True
            raise Exception(f"Element '{locator}' is visible")

        result, exception = until(timeout, func, allow_none=False)
        if result is None:
            raise Exception(f"Element '{locator}' should not be visible but is within {timeout}s")
        return True

    def appium_first_found_element(self, *locators, timeout=10, include_element=False) -> int | AppiumElement:
        """Find the first element from multiple locators.

        Args:
            *locators: Variable number of element locator strings
            timeout: Maximum time to wait in seconds
            include_element: If True, return (index, element) tuple, otherwise return index

        Returns:
            Index of first found element, or -1 if none found.
            If include_element=True, returns (index, element) or (-1, None)
        """
        def func():
            for index, locator in enumerate(locators):
                elements = self._appium_get(locator)
                if elements:
                    return (index, elements[0]) if include_element else index
            raise Exception(f"None of the elements {list(locators)} found yet")

        result, _ = until(timeout, func)
        if result is not None:
            return result
        return (-1, None) if include_element else -1

    def appium_get_element(self, locator, timeout=10, required=True) -> AppiumElement:
        """Get a single element.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds
            required: If True, raises exception if element not found

        Returns:
            The found element

        Raises:
            Exception: If element not found and required=True
        """
        def func():
            elements = self._appium_get(locator)
            if elements:
                return elements[0]
            raise Exception(f"Element '{locator}' not found yet")

        result, _ = until(timeout, func)
        if result is None and required:
            raise Exception(f"Element '{locator}' not found within {timeout}s")
        return result

    def appium_get_elements(self, locator, timeout=10) -> list:
        """Get multiple elements.

        Args:
            locator: Element locator string
            timeout: Maximum time to wait in seconds

        Returns:
            List of found elements, empty list if none found
        """
        def func():
            elements = self._appium_get(locator)
            if elements:
                return elements
            raise Exception(f"Elements '{locator}' not found yet")

        result, _ = until(timeout, func)
        return result if result is not None else []

    def _appium(self, locator, condition='exist', **kwargs):
        """Internal helper method for element operations.

        Args:
            locator: Element locator string
            condition: Type of condition to check ('exist', etc.)
            **kwargs: Additional keyword arguments

        Returns:
            Result of the operation
        """
        def _func():
            if condition == 'exist':
                return self._appium_get(locator)
            # Add other conditions as needed
            return None

        r, e = self._until(10, _func)
        return r

    def _element_find_extra(self, locator, first_only, required, tag=None):
        """Find elements with extra filtering options.

        Args:
            locator: Element locator (string or WebElement)
            first_only: If True, return only first element
            required: If True, raise error if no elements found
            tag: Optional tag filter

        Returns:
            Single element if first_only=True, list otherwise
        """
        application = self._context.get('element') or self._current_application()
        elements = None
        if isinstance(locator, str):
            _locator = locator
            elements = self._element_finder.find_extra(application, _locator, tag)
            if required and len(elements) == 0:
                raise ValueError(f"Element locator '{locator}' did not match any elements.")
            if first_only:
                if len(elements) == 0:
                    return None
                return elements[0]
        elif isinstance(locator, AppiumElement):
            if first_only:
                return locator
            else:
                elements = [locator]
        return elements

    def _until(
            self,
            timeout: Union[str, int, float],
            func: Callable[[], Any],
            allow_none: bool = False,
            excepts=WebDriverException,
            delay: float = 0.5,
    ) -> Tuple[Any, Optional[Exception]]:
        """
        Repeatedly executes `func` until:
          - it returns a non-None value, OR
          - allow_none=True, OR
          - timeout occurs.

        Returns:
            (result, last_exception)
        """

        end_time = time.time() + timestr_to_secs(timeout)
        last_exception = None

        while time.time() < end_time:
            try:
                result = func()

                last_exception = None

                if result is not None:
                    return result, last_exception

                if result is None and allow_none:
                    return result, last_exception

            except excepts as e:
                last_exception = e

            time.sleep(delay)

        # If no exception recorded, produce a timeout exception
        if last_exception is None:
            last_exception = f"Timed out after {timeout}"

        return None, last_exception
