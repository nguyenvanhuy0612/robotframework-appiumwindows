# -*- coding: utf-8 -*-
import ast
import re
import time

from robot.libraries.BuiltIn import BuiltIn
from robot.utils import timestr_to_secs
from selenium.webdriver import Keys
from selenium.webdriver.remote.webelement import WebElement
from unicodedata import normalize

from AppiumLibrary.locators import ElementFinder
from .keywordgroup import KeywordGroup


OLD_KEYWORDS = [
    'clear_text', 'click_element', 'click_text', 'input_text_into_current_element',
    'input_text', 'input_password', 'input_value', 'hide_keyboard', 'is_keyboard_shown',
    'page_should_contain_text', 'page_should_not_contain_text', 'page_should_contain_element',
    'page_should_not_contain_element', 'element_should_be_disabled', 'element_should_be_enabled',
    'element_should_be_visible', 'element_name_should_be', 'element_value_should_be',
    'element_attribute_should_match', 'element_should_contain_text', 'element_should_not_contain_text',
    'element_text_should_be', 'get_webelement', 'scroll_element_into_view',
    'get_webelement_in_webelement', 'get_webelements', 'get_element_attribute',
    'get_element_location', 'get_element_size', 'get_element_rect', 'get_text',
    'get_matching_xpath_count', 'text_should_be_visible', 'xpath_should_match_x_times'
]


class _ElementKeywords(KeywordGroup):
    def __init__(self):
        self._element_finder = ElementFinder()
        self._bi = BuiltIn()
        self._context = {}

    # Context
    def get_search_context(self):
        """Returns the currently stored search context.
        
        The search context is the element implicitly used as the parent for all subsequent relative element lookups.
        
        Returns:
        A dictionary containing the stored 'element' and 'locator'.
        

        Examples:
        | Get Search Context |
        """
        return self._context

    def set_search_context(self, context, reference=None, timeout=None):
        """Find and store the parent element.

        Examples:
        | Set Search Context | $context_value | $reference_value | 10s |
        """
        old_context = self._context
        self._context = {}
        # default timeout if None
        timeout = timeout or 20

        if isinstance(context, str):
            self._context['element'] = self._find_context(context, reference, timeout, timeout)
            self._context['locator'] = context
        elif isinstance(context, WebElement):
            self._context['element'] = context
            self._info(f"WARNING!!! Reference use as locator: {reference}")
            self._context['locator'] = reference
        elif isinstance(context, dict) and context.get('locator'):
            self._info(f"Context: {context}")
            self._context['element'] = self._find_context(context['locator'], reference, timeout, timeout)
            self._context['locator'] = context['locator']

        if not self._context.get('element'):
            self._info("WARNING!!! Search Context Empty")
            self._context = {}

        return old_context

    def _find_context(self, locator, reference=None, timeout=20, ref_timeout=5):
        elements = self.appium_get_elements(locator, timeout)
        if not elements:
            raise Exception(f"No elements found for locator '{locator}'")

        element = None

        # Numeric reference (int or str)
        if isinstance(reference, int) or (isinstance(reference, str) and reference.isnumeric()):
            idx = int(reference)
            if not (0 <= idx < len(elements)):
                raise Exception(f"Reference index {idx} out of range for locator '{locator}'")
            element = elements[idx]

        # String sub-locator
        elif isinstance(reference, str):
            for el in elements:
                # Use appium_get_elements_in_element logic, but we need to be careful with timeout
                if self.appium_get_elements_in_element(el, reference, ref_timeout):
                    element = el
                    break

        # Default - first element
        else:
            element = elements[0]

        if not element:
            raise Exception(f"Not found context '{locator}' with reference '{reference}'")

        return element

    def clear_search_context(self):
        """Clear stored context.

        Examples:
        | Clear Search Context |
        """
        old_context = self._context
        self._context = {}
        return old_context

    # Public, element lookups

    # TODO CHECK ELEMENT
    def appium_element_exist(self, locator, timeout=None):
        """Checks if an element exists on the screen.
        
        Unlike `Wait Until Element Is Visible`, this simply checks for presence in the layout tree, regardless of visibility.

        Arguments:
        - ``locator``: The element to check for.
        - ``timeout``: Maximum time to wait for it to appear.
        
        Returns:
        True if the element exists, raises an Exception otherwise.
        
        Examples:
        | ${exists}= | Appium Element Exist | id=MyButton |
        """
        self._info(f"Appium Element Exist '{locator}', timeout {timeout}")

        def func():
            elements = self._element_find(locator, False, False)
            if elements:
                self._info(f"Element '{locator}' exist")
                return True
            raise Exception(f"Element '{locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Check existence of '{locator}'",
            required=False,
            poll_interval=None
        )

    def appium_wait_until_element_is_visible(self, locator, timeout=None):
        """Waits until the specified element is visibly displayed on the screen.
        
        This keyword fails if the timeout expires before the element becomes visible.

        Arguments:
        - ``locator``: The element to wait for.
        - ``timeout``: Maximum time to wait (defaults to the global library timeout).
        
        Examples:
        | Appium Wait Until Element Is Visible | name=Submit | timeout=10s |
        """
        self._info(f"Appium Wait Until Element Is Visible '{locator}', timeout {timeout}")

        def func():
            element = self._element_find(locator, True, True)
            if element and element.is_displayed():
                self._info(f"Element '{locator}' visible")
                return True
            raise Exception(f"Element '{locator}' not visible yet")

        return self._retry(
            timeout,
            func,
            action=f"Wait until element '{locator}' is visible",
            required=False,
            poll_interval=None
        )

    def appium_wait_until_element_is_not_visible(self, locator, timeout=None):
        """Waits until the specified element is no longer visible or no longer exists.
        
        This keyword fails if the element is still visible after the timeout expires.

        Arguments:
        - ``locator``: The element that should disappear.
        - ``timeout``: Maximum time to wait.
        
        Examples:
        | Appium Wait Until Element Is Not Visible | id=LoadingSpinner |
        """
        self._info(f"Appium Wait Until Element Is Not Visible '{locator}', timeout {timeout}")

        def func():
            elements = self._element_find(locator, False, False)
            # require 2 consecutive checks where element is not found
            if not elements:
                if not hasattr(func, "_not_found_count"):
                    func._not_found_count = 1
                else:
                    func._not_found_count += 1
                if func._not_found_count >= 2:
                    self._info(f"Element '{locator}' not exist")
                    return True
            else:
                func._not_found_count = 0
            raise Exception(f"Element '{locator}' still visible")

        return self._retry(
            timeout,
            func,
            action=f"Wait until element '{locator}' is not visible",
            required=False,
            poll_interval=None
        )

    def appium_element_should_be_visible(self, locator, timeout=None):
        """Asserts that the given element is currently visible on the screen.
        
        This is an alias for `Appium Wait Until Element Is Visible` but explicitly implies an assertion intended for test validation.

        Arguments:
        - ``locator``: The element that must be visible.
        - ``timeout``: Maximum time to wait for the element.
        

        Examples:
        | Appium Element Should Be Visible | id=MyElement | 10s |
        """
        self._info(f"Appium Element Should Be Visible '{locator}', timeout {timeout}")

        def func():
            element = self._element_find(locator, True, True)
            if element and element.is_displayed():
                self._info(f"Element '{locator}' visible")
                return True
            raise Exception(f"Element '{locator}' not visible yet")

        self._retry(
            timeout,
            func,
            action=f"Assert element '{locator}' is visible",
            required=True,
            poll_interval=None
        )

    def appium_first_found_elements(self, *locators, timeout=None, index_only=True):
        """Find the first existing element from a list of locators.

        Iterates through ``locators`` and returns the index (and optionally the
        element) of the first one that is present on the page.

        Arguments:
        - ``*locators``:   One or more locator strings to try in order.
        - ``timeout``:     Maximum time to keep retrying (default: library timeout).
        - ``index_only``:  If True, return only the index. If False, return a
                           tuple ``(index, element)``.

        Returns:
        - ``index_only=True``:  the 0-based index, or ``-1`` if nothing found.
        - ``index_only=False``: a tuple ``(index, element)``, or ``(-1, None)``
          if nothing found.
        

        Examples:
        | Appium First Found Elements | id=ButtonA | id=ButtonB | timeout=10s | index_only=True |
        """
        self._info(f"Appium First Found Elements '{locators}', timeout {timeout}")

        def func():
            for index, locator in enumerate(locators):
                elements = self._element_find(locator, False, False)
                if elements:
                    self._info(f"Element '{locator}' exist, return {index}")
                    return index if index_only else (index, elements[0])
            raise Exception(f"None of the elements {locators} found yet")

        result = self._retry(
            timeout,
            func,
            action=f"Find first existing element from {locators}",
            required=False,
            return_value=True,
            poll_interval=None
        )
        if result is None:
            return -1 if index_only else (-1, None)
        return result

    # TODO FIND ELEMENT
    def appium_get_element(self, locator, timeout=None, required=True):
        """Finds and returns the first element matching the given locator.
        
        Arguments:
        - ``locator``: The element locator.
        - ``timeout``: Maximum time to wait to find the element.
        - ``required``: If True, raises an Exception if the element is not found.
        
        Returns:
        A WebElement instance.
        
        Examples:
        | ${btn}= | Appium Get Element | id=SubmitButton |
        """
        self._info(f"Appium Get Element '{locator}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._element_find(locator, True, False)
            if element:
                self._info(f"Element exist: '{element}'")
                return element
            raise Exception(f"Element '{locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get element '{locator}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_get_elements(self, locator, timeout=None):
        """Finds and returns a list of all elements matching the given locator.
        
        Arguments:
        - ``locator``: The element locator.
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A list of WebElement instances, or an empty list if none are found.
        
        Examples:
        | ${buttons}= | Appium Get Elements | class=Button |
        """
        self._info(f"Appium Get Elements '{locator}', timeout {timeout}")

        def func():
            elements = self._element_find(locator, False, False)
            if elements:
                self._info(f"Elements exist: '{elements}'")
                return elements
            raise Exception(f"Elements '{locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get elements '{locator}'",
            required=False,
            return_value=True,
            poll_interval=None
        ) or []

    def appium_get_button_element(self, index_or_name, timeout=None, required=True):
        """Locates an element of type 'Button' by its name or index.
        
        Arguments:
        - ``index_or_name``: The specific name text of the button, or its numeric index.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, raises an exception if not found.
        
        Returns:
        A WebElement pointing to the button.
        

        Examples:
        | Appium Get Button Element | Submit | timeout=10s | required=True |
        """
        self._info(f"Appium Get Button Element '{index_or_name}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._find_element_by_class_name('Button', index_or_name)
            if element:
                self._info(f"Element exist: '{element}'")
                return element
            raise Exception(f"Button '{index_or_name}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get button element '{index_or_name}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_get_element_text(self, text, exact_match=False, timeout=None, required=True):
        """Locates an element purely by matching its visible text (Name attribute).
        
        Arguments:
        - ``text``: The text string to search for.
        - ``exact_match``: If True, the element's text must match exactly. If False, it checks if it contains the text.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, raises an exception if not found.
        
        Returns:
        The matched WebElement.
        

        Examples:
        | Appium Get Element Text | Welcome | exact_match=True | timeout=10s |
        """
        self._info(f"Appium Get Element Text '{text}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._element_find_by('Name', text, exact_match)
            if element:
                self._info(f"Element text found: '{text}'")
                return element
            raise Exception(f"Element Text '{text}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get element text '{text}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_get_element_by(self, key='*', value='', exact_match=False, timeout=None, required=True):
        """A generic advanced locator that searches elements by a specific dynamic attribute key and value.
        
        Arguments:
        - ``key``: The attribute/property name to search by. Default is '*' (any attribute).
        - ``value``: The value of the attribute to match.
        - ``exact_match``: If True, the value must match exactly.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, raises an exception on failure.
        

        Examples:
        | Appium Get Element By | AutomationId | SubmitButton | exact_match=True |
        """
        self._info(f"Appium Get Element By '{key}={value}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._element_find_by(key, value, exact_match)
            if element:
                self._info(f"Element exist: '{element}'")
                return element
            raise Exception(f"Element '{key}={value}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get element by '{key}={value}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_get_element_in_element(self, parent_locator, child_locator, timeout=None):
        """Finds a child element located inside a specific parent element.
        
        Arguments:
        - ``parent_locator``: The locator of the parent container element.
        - ``child_locator``: The locator of the child element to find inside the parent.
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A WebElement referencing the child.
        

        Examples:
        | Appium Get Element In Element | id=ParentElement | id=ChildElement | timeout=10s |
        """
        self._info(f"Appium Get Element In Element, child '{child_locator}', parent '{parent_locator}', timeout {timeout}")

        def func():
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._current_application()

            elements = self._element_finder.find(parent_element, child_locator, None)
            if elements:
                self._info(f"Element exist: '{elements[0]}'")
                return elements[0]
            raise Exception(f"Element '{child_locator}' in '{parent_locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get element '{child_locator}' in '{parent_locator}'",
            required=True,
            return_value=True,
            poll_interval=None
        )

    def appium_get_elements_in_element(self, parent_locator, child_locator, timeout=None):
        """Finds all child elements matching a locator inside a specific parent element.
        
        Arguments:
        - ``parent_locator``: The locator of the parent container element.
        - ``child_locator``: The locator of the children elements to find inside the parent.
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A list of child WebElements.
        

        Examples:
        | Appium Get Elements In Element | id=ListContainer | class=ListItem | timeout=10s |
        """
        self._info(f"Appium Get Elements In Element, child '{child_locator}', parent '{parent_locator}', timeout {timeout}")

        def func():
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._current_application()

            elements = self._element_finder.find(parent_element, child_locator, None)
            if elements:
                self._info(f"Elements exist: '{elements}'")
                return elements
            raise Exception(f"Elements '{child_locator}' in '{parent_locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get elements '{child_locator}' in '{parent_locator}'",
            required=False,
            return_value=True,
            poll_interval=None
        ) or []

    def appium_find_element(self, locator, timeout=None, first_only=False):
        """Finds elements targeting a specific locator.
        
        This is a flexible alias keyword that can return either a single element or a list of elements depending on the `first_only` flag.

        Arguments:
        - ``locator``: The element locator.
        - ``timeout``: Maximum time to wait for the element.
        - ``first_only``: If True, returns only the first matched element (or None if not found). If False, returns a list of all matches.
        
        Returns:
        A single WebElement or a list of WebElements.
        

        Examples:
        | Appium Find Element | id=SubmitButton | timeout=10s | first_only=True |
        """
        elements = self.appium_get_elements(locator=locator, timeout=timeout)
        if first_only:
            if elements:
                return elements[0]
            self._info("Element not found, return None")
            return None
        return elements

    # TODO GET ELEMENT ATTRIBUTE
    def appium_get_element_attribute(self, locator, attribute, timeout=None):
        """Retrieves a specific attribute value from an element.

        Arguments:
        - ``locator``: The element whose attribute you want to read.
        - ``attribute``: The name of the attribute (e.g., 'Name', 'ClassName', 'HelpText').
        - ``timeout``: Maximum time to wait.
        
        Returns:
        The string value of the attribute.
        
        Examples:
        | ${name}= | Appium Get Element Attribute | id=MyButton | Name |
        """
        self._info(f"Appium Get Element Attribute '{attribute}' Of '{locator}', timeout '{timeout}'")

        def func():
            element = self._element_find(locator, True, True)
            att_value = element.get_attribute(attribute)
            if att_value is not None:
                self._info(f"Attribute value: '{att_value}'")
                return att_value
            raise Exception(f"Attribute '{attribute}' of '{locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get attribute '{attribute}' of '{locator}'",
            required=False,
            return_value=True,
            poll_interval=None
        )

    def appium_get_element_attributes(self, locator, attribute, timeout=None):
        """Retrieves a specific attribute value from all elements that match the locator.

        Arguments:
        - ``locator``: The element locator.
        - ``attribute``: The name of the attribute to extract from all matched elements.
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A list of string attribute values.
        

        Examples:
        | Appium Get Element Attributes | class=ListItem | Name | timeout=10s |
        """
        self._info(f"Appium Get Element Attributes '{attribute}' Of '{locator}', timeout '{timeout}'")

        def func():
            elements = self._element_find(locator, False, True)
            att_values = [element.get_attribute(attribute) for element in elements]
            if any(att_values):
                self._info(f"Attributes value: '{att_values}'")
                return att_values
            raise Exception(f"Attributes '{attribute}' of '{locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get attributes '{attribute}' of '{locator}'",
            required=False,
            return_value=True,
            poll_interval=None
        ) or []

    def appium_get_element_attributes_in_element(self, parent_locator, child_locator, attribute, timeout=None):
        """Retrieves a specific attribute value from all child elements matching `child_locator` within the `parent_locator`.

        Arguments:
        - ``parent_locator``: The parent context element.
        - ``child_locator``: The child elements to find.
        - ``attribute``: The attribute to extract from the children.
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A list of string attribute values from the matched children.
        

        Examples:
        | Appium Get Element Attributes In Element | id=ListContainer | class=ListItem | Name | timeout=10s |
        """
        self._info(f"Appium Get Element Attributes In Element '{attribute}' Of '{child_locator}' In '{parent_locator}', timeout '{timeout}'")

        def func():
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._current_application()

            elements = self._element_finder.find(parent_element, child_locator, None)
            att_values = [element.get_attribute(attribute) for element in elements]
            if any(att_values):
                self._info(f"Attributes value: '{att_values}'")
                return att_values
            raise Exception(f"Attributes '{attribute}' of '{child_locator}' in '{parent_locator}' not found yet")

        return self._retry(
            timeout,
            func,
            action=f"Get attributes '{attribute}' in element '{child_locator}' of '{parent_locator}'",
            required=False,
            return_value=True,
            poll_interval=None
        ) or []

    def appium_get_text(self, locator, first_only=True, timeout=None):
        """Gets the visible text of an element (or a list of texts if `first_only` is False).

        Arguments:
        - ``locator``: The target element(s).
        - ``first_only``: If True, returns the text of only the first matched element. If False, returns a list of texts from all matched elements.
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A string (if `first_only=True`) or a list of strings.
        
        Examples:
        | ${text}= | Appium Get Text | id=TitleLabel |
        | ${texts}= | Appium Get Text | class=ListItems | first_only=False |
        """
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

        return self._retry(
            timeout,
            func,
            action=f"Get text from '{locator}'",
            required=False,
            return_value=True,
            poll_interval=None
        )
    
    def appium_get_rect(self, locator=None, timeout=None):
        """Gets the bounding rectangle of an element, returning its coordinates and dimensions.
        
        If `locator` is completely omitted, this attempts to return the bounding rectangle of the current active search context.

        Arguments:
        - ``locator``: The target element (optional).
        - ``timeout``: Maximum time to wait.
        
        Returns:
        A dictionary containing `x`, `y`, `width`, and `height`.
        
        Examples:
        | ${rect}= | Appium Get Rect | id=MyPanel |
        """
        self._info(f"Appium Get Rect '{locator}', timeout '{timeout}'")

        def func():
            if locator:
                return self._element_find(locator, True, True).rect
            return self._current_application().get_window_rect()

        return self._retry(
            timeout,
            func,
            action=f"Get rect of '{locator}' or window rect",
            required=True,
            return_value=True,
            poll_interval=None
        )

    # TODO CLICK ELEMENT
    def appium_click(self, locator, timeout=None, required=True):
        """Clicks the element identified by the given locator.

        Arguments:
        - ``locator``: The element to click.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, fails the test if not found.
        

        Examples:
        | Appium Click | id=SubmitButton | timeout=10s | required=True |
        """
        self._info(f"Appium Click '{locator}', timeout '{timeout}'")

        def func():
            element = self._element_find(locator, True, True)
            element.click()
            time.sleep(0.5)
            return True

        return self._retry(
            timeout,
            func,
            action=f"Click element '{locator}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_click_text(self, text, exact_match=False, timeout=None, required=True):
        """Clicks an element that exactly or partially matches the given text.

        Arguments:
        - ``text``: The visible text to click.
        - ``exact_match``: If True, requires the element's text to match exactly.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, fails the test if not found.
        

        Examples:
        | Appium Click Text | Confirm | exact_match=True | timeout=10s | required=True |
        """
        self._info(f"Appium Click Text '{text}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._element_find_by('Name', text, exact_match)
            element.click()
            time.sleep(0.5)
            return True

        return self._retry(
            timeout,
            func,
            action=f"Click text '{text}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_click_button(self, index_or_name, timeout=None, required=True):
        """Clicks a button element identified by its name or numeric index.

        Arguments:
        - ``index_or_name``: The specific name text of the button, or its numeric index.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, fails the test if not found.
        

        Examples:
        | Appium Click Button | Cancel | timeout=10s | required=True |
        """
        self._info(f"Appium Click Button '{index_or_name}', timeout '{timeout}', required '{required}'")

        def func():
            element = self._find_element_by_class_name('Button', index_or_name)
            element.click()
            time.sleep(0.5)
            return True

        return self._retry(
            timeout,
            func,
            action=f"Click button '{index_or_name}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_click_multiple_time(self, locator, repeat=1, timeout=None):
        """Clicks the specified element (identified by locator) multiple times sequentially.

        Arguments:
        - ``locator``: The element to click.
        - ``repeat``: The number of times to click the element.
        - ``timeout``: Maximum time to wait for the element.
        

        Examples:
        | Appium Click Multiple Time | id=IncrementCounter | repeat=3 | timeout=10s |
        """
        self._info(f"Appium Click '{locator}' {repeat} times, timeout '{timeout}'")

        for i in range(repeat):
            self._info(f"Click attempt {i + 1}/{repeat}")
            self.appium_click(locator, timeout=timeout, required=True)
    
    # TODO temporary add, will remove in the future
    def appium_click_until(self, locators: list, timeout=None, handle_error=True):
        """
        Click any element in the list of locators until all elements are not found.

        Arguments:
        - ``locators``: List of locators to try in order.
        - ``timeout``: Maximum time to wait for an element to appear (default: None).
        - ``handle_error``: Whether to handle errors (default: True).
        

        Examples:
        | @{buttons} | Create List | id=PopupClose | id=BannerClose |
        | Appium Click Until | ${buttons} | timeout=10s | handle_error=True |
        """
        self._info(f"Appium Click Until: locators='{locators}', timeout='{timeout}', handle_error='{handle_error}'")

        def func():
            found = False
            for locator in locators:
                element = self._element_find(locator, True, False)
                if element:
                    element.click()
                    found = True

            if not found:
                return False
            raise Exception(f"Still found element in {locators}, retrying...")

        return self._retry(
            timeout,
            func,
            action=f"Click until '{locators}'",
            required=not handle_error,
            return_value=False,
            poll_interval=None
        )

    def appium_click_first_match(self, locators: list, timeout=None, handle_error=True):
        """
        Click the first element in the list of locators that appears.

        Arguments:
        - ``locators``: List of locators to try in order.
        - ``timeout``: Maximum time to wait for an element to appear (default: None).
        - ``handle_error``: Whether to handle errors (default: True).
        

        Examples:
        | @{buttons} | Create List | id=Accept | id=Agree | id=OK |
        | Appium Click First Match | ${buttons} | timeout=5s |
        """
        self._info(f"Appium Click First Match: locators='{locators}', timeout='{timeout}', handle_error='{handle_error}'")

        def func():
            found = False
            for locator in locators:
                element = self._element_find(locator, True, False)
                if element:
                    element.click()
                    found = True
                    break

            if not found:
                raise Exception("Elements not found, retrying...")
            return found

        return self._retry(
            timeout,
            func,
            action=f"Click until '{locators}'",
            required=not handle_error,
            return_value=False,
            poll_interval=None
        )

    def appium_click_if_exist(self, locator, timeout=2):
        """Clicks an element if it exists; otherwise does nothing and returns False.

        Arguments:
        - ``locator``: The element to click.
        - ``timeout``: Maximum time to wait. Defaults to 2 seconds.
        
        Returns:
        True if the click was successful, False if the element was not found.
        

        Examples:
        | Appium Click If Exist | id=OptionalAdBanner | timeout=5s |
        """
        self._info(f"Appium Click If Exist '{locator}', timeout '{timeout}'")
        result = self.appium_click(locator, timeout=timeout, required=False)
        if not result:
            self._info(f"Element '{locator}' not found, return False")
        return result

    # TODO SEND KEYS TO ELEMENT
    def appium_input(self, locator, text, timeout=None, required=True):
        """Sends keystrokes to an element.

        Arguments:
        - ``locator``: The element to input text into.
        - ``text``: The string to type out.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, fails the test if the element is not found.
        
        Examples:
        | Appium Input | id=UsernameField | Admin |
        """
        self._info(f"Appium Input '{text}' to '{locator}', timeout '{timeout}', required '{required}'")

        text = self._format_keys(text)
        locator = locator or "xpath=/*"
        self._info(f"Formatted Text: '{text}', Locator: '{locator}'")

        def func():
            element = self._element_find(locator, True, True)
            element.send_keys(text)
            self._info(f"Input successful: '{text}' into '{locator}'")
            return True

        return self._retry(
            timeout,
            func,
            action=f"Input '{text}' into '{locator}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_input_text(self, locator_text, text, exact_match=False, timeout=None, required=True):
        """Finds an element by its visible text and inputs keystrokes into it.

        Arguments:
        - ``locator_text``: The visible text of the element.
        - ``text``: The string to type out into the matched element.
        - ``exact_match``: If True, requires the element's text to match exactly.
        - ``timeout``: Maximum time to wait.
        - ``required``: If True, fails the test if not found.
        
        Examples:
        | Appium Input Text | Enter Password | secret123 |
        """
        self._info(f"Appium Input Text '{text}' to '{locator_text}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'")
        text = self._format_keys(text)
        self._info(f"Formatted Text: '{text}'")

        def func():
            element = self._element_find_by('Name', locator_text, exact_match)
            element.send_keys(text)
            self._info(f"Input successful: '{text}' into element with text '{locator_text}'")
            return True

        return self._retry(
            timeout,
            func,
            action=f"Input '{text}' into element with text '{locator_text}'",
            required=required,
            return_value=True,
            poll_interval=None
        )

    def appium_input_if_exist(self, locator, text, timeout=2):
        """Inputs text into an element only if it exists; otherwise skips without failing.

        Arguments:
        - ``locator``: The element to input text into.
        - ``text``: The string to type out.
        - ``timeout``: Maximum time to wait. Defaults to 2 seconds.
        
        Returns:
        True if the input was successful, False if the element was not found.
        

        Examples:
        | Appium Input If Exist | id=OptionalPromoCode | SAVE20 | 5s |
        """
        result = self.appium_input(locator, text, timeout=timeout, required=False)
        if not result:
            self._info(f"Element '{locator}' not found, skip input and return False")
        return result

    def appium_press_page_up(self, locator=None, press_time=1, timeout=None):
        """Simulates pressing the 'Page Up' keyboard key.

        Arguments:
        - ``locator``: The element to focus before pressing.
        - ``press_time``: Number of times to press the key (default 1).
        - ``timeout``: Maximum time to wait.
        

        Examples:
        | Appium Press Page Up | id=ContentArea | press_time=2 |
        """
        self._info(f"Appium Press Page Up {locator}, press_time {press_time}, timeout {timeout}")
        self.appium_input(locator, "{PAGE_UP}" * press_time, timeout)

    def appium_press_page_down(self, locator=None, press_time=1, timeout=None):
        """Simulates pressing the 'Page Down' keyboard key.

        Arguments:
        - ``locator``: The element to focus before pressing.
        - ``press_time``: Number of times to press the key (default 1).
        - ``timeout``: Maximum time to wait.
        

        Examples:
        | Appium Press Page Down | id=ContentArea | press_time=5 |
        """
        self._info(f"Appium Press Page Down {locator}, press_time {press_time}, timeout {timeout}")
        self.appium_input(locator, "{PAGE_DOWN}" * press_time, timeout)

    def appium_press_home(self, locator=None, press_time=1, timeout=None):
        """Simulates pressing the 'Home' keyboard key.

        Arguments:
        - ``locator``: The element to focus before pressing.
        - ``press_time``: Number of times to press the key (default 1).
        - ``timeout``: Maximum time to wait.
        

        Examples:
        | Appium Press Home | locator=id=TopMenu |
        """
        self._info(f"Appium Press Home {locator}, press_time {press_time}, timeout {timeout}")
        self.appium_input(locator, "{HOME}" * press_time, timeout)

    def appium_press_end(self, locator=None, press_time=1, timeout=None):
        """Simulates pressing the 'End' keyboard key.

        Arguments:
        - ``locator``: The element to focus before pressing.
        - ``press_time``: Number of times to press the key (default 1).
        - ``timeout``: Maximum time to wait.
        

        Examples:
        | Appium Press End | locator=id=Footer |
        """
        self._info(f"Appium Press End {locator}, press_time {press_time}, timeout {timeout}")
        self.appium_input(locator, "{END}" * press_time, timeout)

    def appium_clear_all_text(self, locator, timeout=None):
        """Clears all text in the specified field by sending CTRL+A and DELETE.

        Arguments:
        - ``locator``: The element to clear.
        - ``timeout``: Maximum time to wait for the element.
        

        Examples:
        | Appium Clear All Text | id=SearchInput | timeout=5s |
        """
        self._info(f"Appium Clear All Text {locator}, timeout {timeout}")
        self.appium_input(locator, "{CONTROL}a{DELETE}", timeout)

    def appium_scroll_into_view(self, locator, timeout=None, handle_exception=False):
        """
        Scrolls to the specified element using the Windows extension. This keyword is only available for NovaWindows2

        Arguments:
        - ``locator``: The element to scroll to or locator of the element.
        - ``timeout``: The timeout to wait for the element to be found.
        - ``handle_exception``: If True, return the exception object on failure. If False, raise the exception.

        Returns:
        None or the exception object.
        

        Examples:
        | Appium Scroll Into View | id=FooterBox | timeout=10s | handle_exception=True |
        """
        try:
            element = self.appium_get_element(locator, timeout)
            driver = self._current_application()
            driver.execute_script('windows: scrollIntoView', element)
        except Exception as exc:
            if handle_exception:
                return exc
            raise

    #########################################################################################################
    # TODO old method
    def clear_text(self, locator):
        """Clears the text field identified by `locator`.

        See `introduction` for details about locating elements.
        

        Examples:
        | Clear Text | id=UsernameField |
        """
        self._info("Clear text field '%s'" % locator)
        self._element_find(locator, True, True).clear()

    def click_element(self, locator):
        """Click element identified by `locator`.

        Key attributes for arbitrary elements are `index` and `name`. See
        `introduction` for details about locating elements.
        

        Examples:
        | Click Element | id=SubmitButton |
        """
        self._info("Clicking element '%s'." % locator)
        self._element_find(locator, True, True).click()

    def click_text(self, text, exact_match=False):
        """Click text identified by ``text``.

        By default tries to click first text involves given ``text``, if you would
        like to click exactly matching text, then set ``exact_match`` to `True`.

        If there are multiple use  of ``text`` and you do not want first one,
        use `locator` with `Get Web Elements` instead.

        

        Examples:
        | Click Text | Login | exact_match=True |
        """
        self._element_find_by_text(text, exact_match).click()

    def input_text_into_current_element(self, text):
        """Types the given `text` into currently selected text field.

            Android only.
        

        Examples:
        | Input Text Into Current Element | Hello World |
        """
        self._info("Typing text '%s' into current text field" % text)
        driver = self._current_application()
        driver.set_clipboard_text(text)
        driver.press_keycode(50, 0x1000 | 0x2000)

    def input_text(self, locator, text):
        """Types the given `text` into text field identified by `locator`.

        See `introduction` for details about locating elements.
        

        Examples:
        | Input Text | id=SearchBox | Automation |
        """
        self._info("Typing text '%s' into text field '%s'" % (text, locator))
        self._element_input_text_by_locator(locator, text)

    def input_password(self, locator, text):
        """Types the given password into text field identified by `locator`.

        Difference between this keyword and `Input Text` is that this keyword
        does not log the given password. See `introduction` for details about
        locating elements.
        

        Examples:
        | Input Password | id=PasswordField | secret123 |
        """
        self._info("Typing password into text field '%s'" % locator)
        self._element_input_text_by_locator(locator, text)

    def input_value(self, locator, text):
        """Sets the given value into text field identified by `locator`. This is an IOS only keyword, input value makes use of set_value

        See `introduction` for details about locating elements.
        

        Examples:
        | Input Value | id=QuantityField | 5 |
        """
        self._info("Setting text '%s' into text field '%s'" % (text, locator))
        self._element_input_value_by_locator(locator, text)

    def hide_keyboard(self, key_name=None):
        """Hides the software keyboard on the device. (optional) In iOS, use `key_name` to press
        a particular key, ex. `Done`. In Android, no parameters are used.
        

        Examples:
        | Hide Keyboard | Done |
        """
        driver = self._current_application()
        driver.hide_keyboard(key_name)

    def is_keyboard_shown(self):
        """Return true if Android keyboard is displayed or False if not displayed
        No parameters are used.
        

        Examples:
        | Is Keyboard Shown |
        """
        driver = self._current_application()
        return driver.is_keyboard_shown()

    def page_should_contain_text(self, text, loglevel='DEBUG'):
        """Verifies that current page contains `text`.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        

        Examples:
        | Page Should Contain Text | Welcome to App | DEBUG |
        """
        if not self._is_text_present(text):
            self.log_source(loglevel)
            raise AssertionError("Page should have contained text '%s' "
                                 "but did not" % text)
        self._info("Current page contains text '%s'." % text)

    def page_should_not_contain_text(self, text, loglevel='DEBUG'):
        """Verifies that current page not contains `text`.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        

        Examples:
        | Page Should Not Contain Text | Error | INFO |
        """
        if self._is_text_present(text):
            self.log_source(loglevel)
            raise AssertionError("Page should not have contained text '%s'" % text)
        self._info("Current page does not contains text '%s'." % text)

    def page_should_contain_element(self, locator, loglevel='DEBUG'):
        """Verifies that current page contains `locator` element.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        

        Examples:
        | Page Should Contain Element | id=Dashboard | INFO |
        """
        if not self._is_element_present(locator):
            self.log_source(loglevel)
            raise AssertionError("Page should have contained element '%s' "
                                 "but did not" % locator)
        self._info("Current page contains element '%s'." % locator)

    def page_should_not_contain_element(self, locator, loglevel='DEBUG'):
        """Verifies that current page not contains `locator` element.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        

        Examples:
        | Page Should Not Contain Element | id=LoadingIndicator | NONE |
        """
        if self._is_element_present(locator):
            self.log_source(loglevel)
            raise AssertionError("Page should not have contained element '%s'" % locator)
        self._info("Current page not contains element '%s'." % locator)

    def element_should_be_disabled(self, locator, loglevel='DEBUG'):
        """Verifies that element identified with locator is disabled.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        

        Examples:
        | Element Should Be Disabled | id=SubmitButton |
        """
        if self._element_find(locator, True, True).is_enabled():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be disabled "
                                 "but did not" % locator)
        self._info("Element '%s' is disabled ." % locator)

    def element_should_be_enabled(self, locator, loglevel='DEBUG'):
        """Verifies that element identified with locator is enabled.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        

        Examples:
        | Element Should Be Enabled | id=SubmitButton |
        """
        if not self._element_find(locator, True, True).is_enabled():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be enabled "
                                 "but did not" % locator)
        self._info("Element '%s' is enabled ." % locator)

    def element_should_be_visible(self, locator, loglevel='DEBUG'):
        """Verifies that element identified with locator is visible.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.

        New in AppiumLibrary 1.4.5
        

        Examples:
        | Element Should Be Visible | id=ContentArea |
        """
        if not self._element_find(locator, True, True).is_displayed():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be visible "
                                 "but did not" % locator)

    def element_name_should_be(self, locator, expected):
        """Verifies that the `name` attribute of the element exactly matches the expected text.

        Arguments:
        - ``locator``: The element whose name attribute will be checked.
        - ``expected``: The exact string that the name must equal.
        
        Examples:
        | Element Name Should Be | id=Header | Main Settings |
        """
        element = self._element_find(locator, True, True)
        if str(expected) != str(element.get_attribute('name')):
            raise AssertionError("Element '%s' name should be '%s' "
                                 "but it is '%s'." % (locator, expected, element.get_attribute('name')))
        self._info("Element '%s' name is '%s' " % (locator, expected))

    def element_value_should_be(self, locator, expected):
        """Verifies that the `value` attribute of the element exactly matches the expected text.

        Arguments:
        - ``locator``: The element whose value attribute will be checked.
        - ``expected``: The exact string that the value must equal.
        
        Examples:
        | Element Value Should Be | id=TextInput | admin@example.com |
        """
        element = self._element_find(locator, True, True)
        if str(expected) != str(element.get_attribute('value')):
            raise AssertionError("Element '%s' value should be '%s' "
                                 "but it is '%s'." % (locator, expected, element.get_attribute('value')))
        self._info("Element '%s' value is '%s' " % (locator, expected))

    def element_attribute_should_match(self, locator, attr_name, match_pattern, regexp=False):
        """Verify that an attribute of an element matches the expected criteria.

        The element is identified by _locator_. See `introduction` for details
        about locating elements. If more than one element matches, the first element is selected.

        The _attr_name_ is the name of the attribute within the selected element.

        The _match_pattern_ is used for the matching, if the match_pattern is
        - boolean or 'True'/'true'/'False'/'false' String then a boolean match is applied
        - any other string is cause a string match

        The _regexp_ defines whether the string match is done using regular expressions (i.e. BuiltIn Library's
        [http://robotframework.org/robotframework/latest/libraries/BuiltIn.html#Should%20Match%20Regexp|Should
        Match Regexp] or string pattern match (i.e. BuiltIn Library's
        [http://robotframework.org/robotframework/latest/libraries/BuiltIn.html#Should%20Match|Should
        Match])


        Examples:

        | Element Attribute Should Match | xpath = //*[contains(@text,'foo')] | text | *foobar |
        | Element Attribute Should Match | xpath = //*[contains(@text,'foo')] | text | f.*ar | regexp = True |
        | Element Attribute Should Match | xpath = //*[contains(@text,'foo')] | enabled | True |

        | 1. is a string pattern match i.e. the 'text' attribute should end with the string 'foobar'
        | 2. is a regular expression match i.e. the regexp 'f.*ar' should be within the 'text' attribute
        | 3. is a boolead match i.e. the 'enabled' attribute should be True


        _*NOTE: *_
        On Android the supported attribute names can be found in the uiautomator2 driver readme:
        [https://github.com/appium/appium-uiautomator2-driver?tab=readme-ov-file#element-attributes]


        _*NOTE: *_
        Some attributes can be evaluated in two different ways e.g. these evaluate the same thing:

        | Element Attribute Should Match | xpath = //*[contains(@text,'example text')] | name | txt_field_name |
        | Element Name Should Be         | xpath = //*[contains(@text,'example text')] | txt_field_name |      |

        """
        elements = self._element_find(locator, False, True)
        if len(elements) > 1:
            self._info("CAUTION: '%s' matched %s elements - using the first element only" % (locator, len(elements)))

        attr_value = elements[0].get_attribute(attr_name)

        # ignore regexp argument if matching boolean
        if isinstance(match_pattern, bool) or match_pattern.lower() == 'true' or match_pattern.lower() == 'false':
            if isinstance(match_pattern, bool):
                match_b = match_pattern
            else:
                match_b = ast.literal_eval(match_pattern.title())

            if isinstance(attr_value, bool):
                attr_b = attr_value
            else:
                attr_b = ast.literal_eval(attr_value.title())

            self._bi.should_be_equal(match_b, attr_b)

        elif regexp:
            self._bi.should_match_regexp(attr_value, match_pattern,
                                         msg="Element '%s' attribute '%s' should have been '%s' "
                                             "but it was '%s'." % (locator, attr_name, match_pattern, attr_value),
                                         values=False)
        else:
            self._bi.should_match(attr_value, match_pattern,
                                  msg="Element '%s' attribute '%s' should have been '%s' "
                                      "but it was '%s'." % (locator, attr_name, match_pattern, attr_value),
                                  values=False)
        # if expected != elements[0].get_attribute(attr_name):
        #    raise AssertionError("Element '%s' attribute '%s' should have been '%s' "
        #                         "but it was '%s'." % (locator, attr_name, expected, element.get_attribute(attr_name)))
        self._info("Element '%s' attribute '%s' is '%s' " % (locator, attr_name, match_pattern))

    def element_should_contain_text(self, locator, expected, message=''):
        """Verifies element identified by ``locator`` contains text ``expected``.

        If you wish to assert an exact (not a substring) match on the text
        of the element, use `Element Text Should Be`.

        Key attributes for arbitrary elements are ``id`` and ``xpath``. ``message`` can be used to override the default error message.

        New in AppiumLibrary 1.4.
        

        Examples:
        | Element Should Contain Text | id=MessageBanner | Success |
        """
        self._info("Verifying element '%s' contains text '%s'."
                   % (locator, expected))
        actual = self._get_text(locator)
        if not expected in actual:
            if not message:
                message = "Element '%s' should have contained text '%s' but " \
                          "its text was '%s'." % (locator, expected, actual)
            raise AssertionError(message)

    def element_should_not_contain_text(self, locator, expected, message=''):
        """Verifies element identified by ``locator`` does not contain text ``expected``.

        ``message`` can be used to override the default error message.
        See `Element Should Contain Text` for more details.
        

        Examples:
        | Element Should Not Contain Text | id=MessageBanner | Error |
        """
        self._info("Verifying element '%s' does not contain text '%s'."
                   % (locator, expected))
        actual = self._get_text(locator)
        if expected in actual:
            if not message:
                message = "Element '%s' should not contain text '%s' but " \
                          "it did." % (locator, expected)
            raise AssertionError(message)

    def element_text_should_be(self, locator, expected, message=''):
        """Verifies element identified by ``locator`` exactly contains text ``expected``.

        In contrast to `Element Should Contain Text`, this keyword does not try
        a substring match but an exact match on the element identified by ``locator``.

        ``message`` can be used to override the default error message.

        New in AppiumLibrary 1.4.
        

        Examples:
        | Element Text Should Be | id=Header | Welcome User |
        """
        self._info("Verifying element '%s' contains exactly text '%s'."
                   % (locator, expected))
        element = self._element_find(locator, True, True)
        actual = element.text
        if expected != actual:
            if not message:
                message = "The text of element '%s' should have been '%s' but " \
                          "in fact it was '%s'." % (locator, expected, actual)
            raise AssertionError(message)

    def get_webelement(self, locator):
        """Returns the first [http://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webelement|WebElement] object matching ``locator``.

        Example:
        | ${element}     | Get Webelement | id=my_element |
        | Click Element  | ${element}     |               |

        New in AppiumLibrary 1.4.
        """
        return self._element_find(locator, True, True)

    def scroll_element_into_view(self, locator):
        """Scrolls an element from given ``locator`` into view.
        Arguments:
        - ``locator``: The locator to find requested element. Key attributes for
                       arbitrary elements are ``id`` and ``name``. See `introduction` for
                       details about locating elements.
        Examples:
        | Scroll Element Into View | css=div.class |
        """
        if isinstance(locator, WebElement):
            element = locator
        else:
            self._info("Scrolling element '%s' into view." % locator)
            element = self._element_find(locator, True, True)
        script = 'arguments[0].scrollIntoView()'
        # pylint: disable=no-member
        self._current_application().execute_script(script, element)
        return element

    def get_webelement_in_webelement(self, element, locator):
        """
        Returns a single [http://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webelement|WebElement]
        objects matching ``locator`` that is a child of argument element.

        This is useful when your HTML doesn't properly have id or name elements on all elements.
        So the user can find an element with a tag and then search that elmements children.
        

        Examples:
        | ${child}= | Get Webelement In Webelement | ${parent_element} | id=ChildId |
        """
        elements = None
        if isinstance(locator, str):
            _locator = locator
            elements = self._element_finder.find(element, _locator, None)
            if len(elements) == 0:
                raise ValueError("Element locator '" + locator + "' did not match any elements.")
            if len(elements) == 0:
                return None
            return elements[0]
        elif isinstance(locator, WebElement):
            return locator

    def get_webelements(self, locator):
        """Returns list of [http://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webelement|WebElement] objects matching ``locator``.

        Example:
        | @{elements}    | Get Webelements | id=my_element |
        | Click Element  | @{elements}[2]  |               |

        This keyword was changed in AppiumLibrary 1.4 in following ways:
        - Name is changed from `Get Elements` to current one.
        - Deprecated argument ``fail_on_error``, use `Run Keyword and Ignore Error` if necessary.

        New in AppiumLibrary 1.4.
        """
        return self._element_find(locator, False, True)

    def get_element_attribute(self, locator, attribute):
        """Get element attribute using given attribute: name, value,...

        Examples:

        | Get Element Attribute | locator | name |
        | Get Element Attribute | locator | value |
        """
        elements = self._element_find(locator, False, True)
        ele_len = len(elements)
        if ele_len == 0:
            raise AssertionError("Element '%s' could not be found" % locator)
        elif ele_len > 1:
            self._info("CAUTION: '%s' matched %s elements - using the first element only" % (locator, len(elements)))

        try:
            attr_val = elements[0].get_attribute(attribute)
            self._info("Element '%s' attribute '%s' value '%s' " % (locator, attribute, attr_val))
            return attr_val
        except Exception:
            raise AssertionError("Attribute '%s' is not valid for element '%s'" % (attribute, locator))

    def get_element_location(self, locator):
        """Gets the X and Y coordinates (location) of the element's top-left corner.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        

        Examples:
        | Get Element Location | id=MyElement |
        """
        element = self._element_find(locator, True, True)
        element_location = element.location
        self._info("Element '%s' location: %s " % (locator, element_location))
        return element_location

    def get_element_size(self, locator):
        """Gets the width and height dimensions of the specified element.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        

        Examples:
        | Get Element Size | id=MyElement |
        """
        element = self._element_find(locator, True, True)
        element_size = element.size
        self._info("Element '%s' size: %s " % (locator, element_size))
        return element_size

    def get_element_rect(self, locator):
        """Gets dimensions and coordinates of an element

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        

        Examples:
        | Get Element Rect | id=MyElement |
        """
        element = self._element_find(locator, True, True)
        element_rect = element.rect
        self._info("Element '%s' rect: %s " % (locator, element_rect))
        return element_rect

    def get_text(self, locator, first_only: bool = True):
        """Get element text (for hybrid and mobile browser use `xpath` locator, others might cause problem)

        first_only parameter allow to get the text from the 1st match (Default) or a list of text from all match.

        Example:
        | ${text} | Get Text | //*[contains(@text,'foo')] |          |
        | @{text} | Get Text | //*[contains(@text,'foo')] | ${False} |

        New in AppiumLibrary 1.4.
        """
        text = self._get_text(locator, first_only)
        self._info("Element '%s' text is '%s' " % (locator, text))
        return text

    def get_matching_xpath_count(self, xpath):
        """Returns number of elements matching ``xpath``

        One should not use the `xpath=` prefix for 'xpath'. XPath is assumed.

        | *Correct:* |
        | ${count}  | Get Matching Xpath Count | //android.view.View[@text='Test'] |
        | Incorrect:  |

        If you wish to assert the number of matching elements, use
        `Xpath Should Match X Times`.

        New in AppiumLibrary 1.4.
        

        Examples:
        | Get Matching Xpath Count | $xpath_value |
        """
        count = len(self._element_find("xpath=" + xpath, False, False))
        return str(count)

    def text_should_be_visible(self, text, exact_match=False, loglevel='DEBUG'):
        """Verifies that element identified with text is visible.

        New in AppiumLibrary 1.4.5
        

        Examples:
        | Text Should Be Visible | Welcome | exact_match=True |
        """
        if not self._element_find_by_text(text, exact_match).is_displayed():
            self.log_source(loglevel)
            raise AssertionError("Text '%s' should be visible but did not" % text)

    def xpath_should_match_x_times(self, xpath, count, error=None, loglevel='DEBUG'):
        """Verifies that the page contains the given number of elements located by the given ``xpath``.

        One should not use the `xpath=` prefix for 'xpath'. XPath is assumed.

        | *Correct:* |
        | Xpath Should Match X Times | //android.view.View[@text='Test'] | 1 |
        | Incorrect: |

        ``error`` can be used to override the default error message.

        See `Log Source` for explanation about ``loglevel`` argument.

        New in AppiumLibrary 1.4.
        

        Examples:
        | Xpath Should Match X Times | $xpath_value | $count_value | $error_value | $loglevel_value |
        """
        actual_xpath_count = len(self._element_find("xpath=" + xpath, False, False))
        if int(actual_xpath_count) != int(count):
            if not error:
                error = "Xpath %s should have matched %s times but matched %s times" % (xpath, count, actual_xpath_count)
            self.log_source(loglevel)
            raise AssertionError(error)
        self._info("Current page contains %s elements matching '%s'." % (actual_xpath_count, xpath))

    # Private
    def _retry(
            self,
            timeout,
            func,
            action: str = "",
            required: bool = True,
            return_value: bool = False,
            poll_interval: float = None
    ):
        """
        Retry a function until it succeeds or the timeout is reached.

        Arguments:
        - ``timeout``: Maximum time to retry. Can be a number of seconds or a Robot Framework time string.
        - ``func``: The function to execute.
        - ``action``: Description of the action for error messages.
        - ``required``: If True, raises TimeoutError on failure. If False, returns False or None.
        - ``return_value``: If True, returns the function result (even if None). If False, returns True on success.
        - ``poll_interval``: Seconds to wait between retry attempts (default 0.5s).

        Returns:
        The function result / True / False / None / RetryResult depending on flags.
        """
        start = time.time()
        timeout = timeout or self._timeout_in_secs
        maxtime = start + timestr_to_secs(timeout)
        poll = timestr_to_secs(poll_interval or self._sleep_between_wait)

        result = None
        executed = False
        last_exception = None

        while True:
            try:
                result = func()
                executed = True
                last_exception = None
                break
            except Exception as e:
                last_exception = e

            if time.time() > maxtime:
                # timeout
                break

            time.sleep(poll)

        if self._log_level == 'DEBUG':
            duration = time.time() - start
            self._debug(f"_retry duration for action '{action}': {duration:.2f}s")

        if executed:
            return result if return_value else True

        if required:
            msg = f"{action} failed after {timeout}s"
            if last_exception:
                msg += f". Error: {last_exception}"
            raise TimeoutError(msg) from last_exception

        return None if return_value else False

    def _element_find(self, locator, first_only, required, tag=None):
        application = self._context.get('element') or self._current_application()
        elements = None
        if isinstance(locator, str):
            _locator = locator
            elements = self._element_finder.find(application, _locator, tag)
            if required and len(elements) == 0:
                raise ValueError(f"Element locator '{locator}' did not match any elements.")
            if first_only:
                if len(elements) == 0:
                    return None
                return elements[0]
        elif isinstance(locator, WebElement):
            if first_only:
                return locator
            else:
                elements = [locator]
        # do some other stuff here like deal with list of webelements
        # ... or raise locator/element specific error if required
        return elements

    def _format_keys(self, text):
        # Refer to selenium\webdriver\common\keys.py
        # text = 123qwe{BACKSPACE 3}{TAB}{ENTER}
        pattern = r"\{(\w+)(?: (\d+))?\}"

        def repl(match):
            key_name = match.group(1).upper()
            repeat = int(match.group(2)) if match.group(2) else 1

            if hasattr(Keys, key_name):
                key_value = getattr(Keys, key_name)
                return key_value * repeat
            return match.group(0)

        return re.sub(pattern, repl, text)

    def _element_input_text_by_locator(self, locator, text):
        try:
            element = self._element_find(locator, True, True)
            element.send_keys(text)
        except Exception as e:
            raise e

    def _element_input_text_by_class_name(self, class_name, index_or_name, text):
        try:
            element = self._find_element_by_class_name(class_name, index_or_name)
        except Exception as e:
            raise e

        self._info("input text in element as '%s'." % element.text)
        try:
            element.send_keys(text)
        except Exception as e:
            raise Exception('Cannot input text "%s" for the %s element "%s"' % (text, class_name, index_or_name))

    def _element_input_value_by_locator(self, locator, text):
        try:
            element = self._element_find(locator, True, True)
            element.set_value(text)
        except Exception as e:
            raise e

    def _find_elements_by_class_name(self, class_name):
        elements = self._element_find(f'class={class_name}', False, False, tag=None)
        return elements

    def _find_element_by_class_name(self, class_name, index_or_name):
        elements = self._find_elements_by_class_name(class_name)

        if index_or_name.startswith('index='):
            try:
                index = int(index_or_name.split('=')[-1])
                element = elements[index]
            except (IndexError, TypeError):
                raise Exception('Cannot find the element with index "%s"' % index_or_name)
        else:
            found = False
            for element in elements:
                self._info("'%s'." % element.text)
                if element.text == index_or_name:
                    found = True
                    break
            if not found:
                raise Exception('Cannot find the element with name "%s"' % index_or_name)

        return element

    def _element_find_by(self, key='*', value='', exact_match=False):
        if exact_match:
            _xpath = u'//*[@{}="{}"]'.format(key, value)
        else:
            _xpath = u'//*[contains(@{},"{}")]'.format(key, value)
        return self._element_find(_xpath, True, False)

    def _element_find_by_text(self, text, exact_match=False):
        if self._get_platform() == 'ios':
            element = self._element_find(text, True, False)
            if element:
                return element
            else:
                if exact_match:
                    _xpath = u'//*[@value="{}" or @label="{}"]'.format(text, text)
                else:
                    _xpath = u'//*[contains(@label,"{}") or contains(@value, "{}")]'.format(text, text)
                return self._element_find(_xpath, True, True)
        elif self._get_platform() == 'android':
            if exact_match:
                _xpath = u'//*[@{}="{}"]'.format('text', text)
            else:
                _xpath = u'//*[contains(@{},"{}")]'.format('text', text)
            return self._element_find(_xpath, True, True)
        elif self._get_platform() == 'windows':
            return self._element_find_by("Name", text, exact_match)

    def _get_text(self, locator, first_only: bool = True):
        element = self._element_find(locator, first_only, True)
        if element is not None:
            if first_only:
                return element.text
            return [el.text for el in element]
        return None

    def _is_text_present(self, text):
        text_norm = normalize('NFD', text)
        source_norm = normalize('NFD', self.get_source())
        return text_norm in source_norm

    def _is_element_present(self, locator):
        application = self._current_application()
        elements = self._element_finder.find(application, locator, None)
        return len(elements) > 0

    def _is_visible(self, locator):
        element = self._element_find(locator, True, False)
        if element is not None:
            return element.is_displayed()
        return None

