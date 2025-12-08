import time
from typing import Callable, Tuple, Any, Optional, Union

from appium.webdriver import WebElement as AppiumElement
from robot.libraries.BuiltIn import BuiltIn
from robot.utils import timestr_to_secs
from selenium.common import WebDriverException
from selenium.webdriver.remote.webelement import WebElement

from AppiumLibrary.locators import ElementFinder
from AppiumLibrary.utils import find_extra, until
from .keywordgroup import KeywordGroup

# Default constants for element operations
DEFAULT_TIMEOUT = 10
DEFAULT_POLL_INTERVAL = 0.5


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

    def appium_element_exist(self, locator, timeout=DEFAULT_TIMEOUT) -> bool:
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

        return until(timeout, func, required=False, default=False, excepts=Exception)

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

    def appium_elements_exist(self, locator, timeout=DEFAULT_TIMEOUT) -> list | bool:
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

        return until(timeout, func, required=False, default=False, excepts=Exception)

    def appium_wait_element_visible(self, locator, timeout=DEFAULT_TIMEOUT) -> AppiumElement | bool:
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

        return until(timeout, func, required=False, default=False, excepts=Exception)

    def appium_wait_element_not_visible(self, locator, timeout=DEFAULT_TIMEOUT) -> bool:
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

        return until(timeout, func, required=False, default=False, excepts=Exception)

    def appium_element_should_be_visible(self, locator, timeout=DEFAULT_TIMEOUT) -> bool:
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

        if until(timeout, func, required=False, default=None, excepts=Exception) is None:
            raise Exception(f"Element '{locator}' should be visible but is not within {timeout}s")
        return True

    def appium_element_should_be_not_visible(self, locator, timeout=DEFAULT_TIMEOUT) -> bool:
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

        if until(timeout, func, required=False, default=None, excepts=Exception) is None:
            raise Exception(f"Element '{locator}' should not be visible but is within {timeout}s")
        return True

    def appium_first_found_element(self, *locators, timeout=DEFAULT_TIMEOUT, include_element=False) -> int | AppiumElement:
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

        result = until(timeout, func, required=False, default=None, excepts=Exception)
        if result is not None:
            return result
        return (-1, None) if include_element else -1

    def appium_get_element(self, locator, timeout=DEFAULT_TIMEOUT, required=True) -> AppiumElement:
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

        return until(timeout, func, required=required, default=None, excepts=Exception)

    def appium_get_elements(self, locator, timeout=DEFAULT_TIMEOUT) -> list:
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

        return until(timeout, func, required=False, default=[], excepts=Exception)

    # Moved from _element.py

    def appium_get_button_element(self, index_or_name, timeout=20, required=True):
        self._info(f"Appium Get Button Element '{index_or_name}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._find_element_by_class_name('Button', index_or_name)
            if element:
                self._info(f"Element exist: '{element}'")
                return element
            raise Exception(f"Button '{index_or_name}' not found yet")

        return until(timeout, func, required=required, default=None, excepts=Exception)

    def appium_get_element_text(self, text, exact_match=False, timeout=20, required=True):
        self._info(
            f"Appium Get Element Text '{text}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'"
        )

        def func():
            element = self._element_find_by('Name', text, exact_match)
            if element:
                self._info(f"Element text found: '{text}'")
                return element
            raise Exception(f"Element Text '{text}' not found yet")

        return until(timeout, func, required=required, default=None, excepts=Exception)

    def appium_get_element_by(self, key='*', value='', exact_match=False, timeout=20, required=True):
        self._info(
            f"Appium Get Element By '{key}={value}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'"
        )

        def func():
            element = self._element_find_by(key, value, exact_match)
            if element:
                self._info(f"Element exist: '{element}'")
                return element
            raise Exception(f"Element '{key}={value}' not found yet")

        return until(timeout, func, required=required, default=None, excepts=Exception)

    def appium_get_element_in_element(self, parent_locator, child_locator, timeout=20):
        self._info(
            f"Appium Get Element In Element, child '{child_locator}', parent '{parent_locator}', timeout {timeout}"
        )

        def func():
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._context.get('element') or self._current_application()

            elements = find_extra(parent_element, self._element_finder, child_locator)
            if elements:
                self._info(f"Element exist: '{elements[0]}'")
                return elements[0]
            raise Exception(f"Element '{child_locator}' in '{parent_locator}' not found yet")

        return until(timeout, func, required=True, default=None, excepts=Exception)

    def appium_get_elements_in_element(self, parent_locator, child_locator, timeout=20):
        self._info(
            f"Appium Get Elements In Element, child '{child_locator}', parent '{parent_locator}', timeout {timeout}")

        def func():
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._context.get('element') or self._current_application()

            elements = find_extra(parent_element, self._element_finder, child_locator)
            if elements:
                self._info(f"Elements exist: '{elements}'")
                return elements
            raise Exception(f"Elements '{child_locator}' in '{parent_locator}' not found yet")

        return until(timeout, func, required=False, default=[], excepts=Exception)

    def appium_find_element(self, locator, timeout=20, first_only=False):
        elements = self._invoke_original("appium_get_elements", locator=locator, timeout=timeout)
        if first_only:
            if elements:
                return elements[0]
            self._info("Element not found, return None")
            return None
        return elements

    # TODO GET ELEMENT ATTRIBUTE
    def appium_get_element_attribute(self, locator, attribute, timeout=20):
        self._info(f"Appium Get Element Attribute '{attribute}' Of '{locator}', timeout '{timeout}'")

        def func():
            element = self._element_find(locator, True, True)
            att_value = element.get_attribute(attribute)
            if att_value is not None:
                self._info(f"Attribute value: '{att_value}'")
                return att_value
            raise Exception(f"Attribute '{attribute}' of '{locator}' not found yet")

        return until(timeout, func, required=False, default=None, excepts=Exception)

    def appium_get_element_attributes(self, locator, attribute, timeout=20):
        self._info(f"Appium Get Element Attributes '{attribute}' Of '{locator}', timeout '{timeout}'")

        def func():
            elements = self._element_find(locator, False, True)
            att_values = [element.get_attribute(attribute) for element in elements]
            if any(att_values):
                self._info(f"Attributes value: '{att_values}'")
                return att_values
            raise Exception(f"Attributes '{attribute}' of '{locator}' not found yet")

        return until(timeout, func, required=False, default=[], excepts=Exception)

    def appium_get_element_attributes_in_element(self, parent_locator, child_locator, attribute, timeout=20):
        self._info(
            f"Appium Get Element Attributes In Element '{attribute}' Of '{child_locator}' In '{parent_locator}', timeout '{timeout}'"
        )

        def func():
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._context.get('element') or self._current_application()

            elements = find_extra(parent_element, self._element_finder, child_locator)
            att_values = [element.get_attribute(attribute) for element in elements]
            if any(att_values):
                self._info(f"Attributes value: '{att_values}'")
                return att_values
            raise Exception(f"Attributes '{attribute}' of '{child_locator}' in '{parent_locator}' not found yet")

        return until(timeout, func, required=False, default=[], excepts=Exception)

    def appium_get_text(self, locator, first_only=True, timeout=20):
        self._info(f"Appium Get Text '{locator}', first_only '{first_only}', timeout '{timeout}'")

        def func():
            if first_only:
                element = self._element_find(locator, True, True)
                text = element.text
                if text is not None:
                    self._info(f"Text: '{text}'")
                    return text
            else:
                elements = self._element_find(locator, False, True)
                text_list = [element.text for element in elements if element.text is not None]
                if text_list:
                    self._info(f"List Text: '{text_list}'")
                    return text_list
            raise Exception(f"Text for '{locator}' not found yet")

        return until(timeout, func, required=False, default=None, excepts=Exception)

    # TODO CLICK ELEMENT
    def appium_click(self, locator, timeout=20, required=True):
        self._info(f"Appium Click '{locator}', timeout '{timeout}'")

        def func():
            element = self._element_find(locator, True, True)
            element.click()
            time.sleep(0.5)
            return True

        return until(timeout, func, required=required, default=None, excepts=Exception)

    def appium_click_text(self, text, exact_match=False, timeout=20):
        self._info(f"Appium Click Text '{text}', exact_match '{exact_match}', timeout '{timeout}'")

        def func():
            element = self._element_find_by('Name', text, exact_match)
            element.click()
            time.sleep(0.5)
            return True

        return until(timeout, func, required=True, default=None, excepts=Exception)

    def appium_click_button(self, index_or_name, timeout=20):
        self._info(f"Appium Click Button '{index_or_name}', timeout '{timeout}'")

        def func():
            element = self._find_element_by_class_name('Button', index_or_name)
            element.click()
            time.sleep(0.5)
            return True

        return until(timeout, func, required=True, default=None, excepts=Exception)

    def appium_click_multiple_time(self, locator, repeat=1, timeout=20):
        self._info(f"Appium Click '{locator}' {repeat} times, timeout '{timeout}'")

        for i in range(repeat):
            self._info(f"Click attempt {i + 1}/{repeat}")
            self._invoke_original("appium_click", locator, timeout=timeout, required=True)

    def appium_click_until(self, locators: list, timeout=20, handle_error=True):
        self._info(f"Appium Click Until '{locators}', timeout '{timeout}'")

        def func():
            found_any = False
            for index, locator in enumerate(locators):
                try:
                    elements = self._element_find(locator, False, False)
                    if elements:
                        found_any = True
                        elements[0].click()
                except Exception as exc:
                    if not handle_error:
                        return exc
            if not found_any:
                self._debug(f"Exit click {locators}")
                return

        return until(timeout, func, required=False, default=None, excepts=Exception)

    def appium_click_if_exist(self, locator, timeout=2):
        self._info(f"Appium Click If Exist '{locator}', timeout '{timeout}'")
        result = self._invoke_original("appium_click", locator, timeout=timeout, required=False)
        if not result:
            self._info(f"Element '{locator}' not found, return False")
        return result

    # TODO SEND KEYS TO ELEMENT
    def appium_input(self, locator, text, timeout=20, required=True):
        self._info(f"Appium Input '{text}' to '{locator}', timeout '{timeout}', required '{required}'")

        text = self._format_keys(text)
        locator = locator or "xpath=/*"
        self._info(f"Formatted Text: '{text}', Locator: '{locator}'")

        def func():
            element = self._element_find(locator, True, True)
            element.send_keys(text)
            self._info(f"Input successful: '{text}' into '{locator}'")
            return True

        return until(timeout, func, required=required, default=None, excepts=Exception)

    def appium_input_text(self, locator_text, text, exact_match=False, timeout=20):
        self._info(f"Appium Input Text '{text}' to '{locator_text}', exact_match '{exact_match}', timeout '{timeout}'")
        text = self._format_keys(text)
        self._info(f"Formatted Text: '{text}'")

        def func():
            element = self._element_find_by('Name', locator_text, exact_match)
            element.send_keys(text)
            self._info(f"Input successful: '{text}' into element with text '{locator_text}'")
            return True

        return until(timeout, func, required=True, default=None, excepts=Exception)

    def appium_input_if_exist(self, locator, text, timeout=2):
        result = self._invoke_original("appium_input", locator, text, timeout=timeout, required=False)
        if not result:
            self._info(f"Element '{locator}' not found, skip input and return False")
        return result

    def appium_press_page_up(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press Page Up {locator}, ")
        self._invoke_original("appium_input", locator, "{PAGE_UP}" * press_time, timeout)

    def appium_press_page_down(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press Page Down {locator}, ")
        self._invoke_original("appium_input", locator, "{PAGE_DOWN}" * press_time, timeout)

    def appium_press_home(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press Home {locator}, ")
        self._invoke_original("appium_input", locator, "{HOME}" * press_time, timeout)

    def appium_press_end(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press End {locator}, ")
        self._invoke_original("appium_input", locator, "{END}" * press_time, timeout)

    def appium_clear_all_text(self, locator, timeout=5):
        self._info(f"Appium Clear All Text {locator}")
        self._invoke_original("appium_input", locator, "{CONTROL}a{DELETE}", timeout)
