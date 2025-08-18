# -*- coding: utf-8 -*-
import ast
import re
import time
from dataclasses import dataclass
from typing import Any, Optional

from robot.libraries.BuiltIn import BuiltIn
from robot.utils import timestr_to_secs
from selenium.common import StaleElementReferenceException, NoSuchElementException, WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.remote.webelement import WebElement
from unicodedata import normalize

from AppiumLibrary.locators import ElementFinder
from .keywordgroup import KeywordGroup


@dataclass
class _RetryResult:
    result: Any = None
    executed: bool = False
    last_exception: Optional[Exception] = None
    timeout: bool = False
    duration: float = 0.0


class _ElementKeywords(KeywordGroup):
    def __init__(self):
        self._element_finder = ElementFinder()
        self._bi = BuiltIn()
        self._context = None
        self._context_locator = None

    # Context

    def get_search_context(self, include_locator=False):
        if include_locator:
            return self._context, self._context_locator
        return self._context

    def set_search_context(self, locator, timeout=20):
        """Find and store the parent element."""
        if locator:
            self.clear_search_context()
            self._context = self.appium_get_element(locator, timeout)
            self._context_locator = locator
        return self._context

    def clear_search_context(self):
        """Clear stored context."""
        self._context = None
        self._context_locator = None

    # Public, element lookups

    # TODO CHECK ELEMENT
    def appium_element_exist(self, locator, timeout=20):
        self._info(f"Appium Element Exist '{locator}', timeout {timeout}")

        def func():
            elements = self._element_find(locator, False, False)
            if elements:
                self._info(f"Element '{locator}' exist")
                return True
            raise Exception(f"Element '{locator}' not found yet")

        rr = self._retry(timeout, func)
        return self._handle_retry_result(rr, f"Check existence of '{locator}'", timeout, required=False)

    def appium_wait_until_element_is_visible(self, locator, timeout=20):
        self._info(f"Appium Wait Until Element Is Visible '{locator}', timeout {timeout}")

        def func():
            element = self._element_find(locator, True, True)
            if element and element.is_displayed():
                self._info(f"Element '{locator}' visible")
                return True
            raise Exception(f"Element '{locator}' not visible yet")

        rr = self._retry(timeout, func)
        return self._handle_retry_result(rr, f"Wait until element '{locator}' is visible", timeout, required=False)

    def appium_wait_until_element_is_not_visible(self, locator, timeout=20):
        self._info(f"Appium Wait Until Element Is Not Visible '{locator}', timeout {timeout}")
        maxtime = self._get_maxtime(timeout)
        not_found = 0
        while time.time() < maxtime:
            elements = self._element_find(locator, False, False)
            if not elements:
                not_found += 1
                if not_found >= 2:
                    self._info(f"Element '{locator}' not exist, return False")
                    return False
            else:
                not_found = 0
            time.sleep(0.5)
        self._info(f"Element '{locator}' exist, return True")
        return True

    def appium_element_should_be_visible(self, locator, timeout=20):
        self._info(f"Appium Element Should Be Visible '{locator}', timeout {timeout}")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._element_find(locator, True, True)
                if element and element.is_displayed():
                    self._info(f"Element '{locator}' visible, return True")
                    return
            except Exception:
                pass
            time.sleep(2)
        raise AssertionError("Element '%s' should be visible but did not" % locator)

    def appium_first_found_elements(self, *locators, timeout=20):
        self._info(f"Appium First Found Elements '{locators}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            for index, locator in enumerate(locators):
                elements = self._element_find(locator, False, False)
                if elements:
                    self._info(f"Element '{locator}' exist, return {index}")
                    return index
                time.sleep(0.5)
            time.sleep(0.5)
        self._info(f"Not Found Element From {locators}, timeout '{timeout}'")
        return -1

    # TODO FIND ELEMENT
    def appium_get_element(self, locator, timeout=20, required=True):
        self._info(f"Appium Get Element '{locator}', timeout '{timeout}', required '{required}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            element = self._element_find(locator, True, False)
            if element:
                self._info(f"Element exist: '{element}'")
                return element
            time.sleep(0.5)
        if required:
            raise Exception(f"Element '{locator}' does not exist within timeout of '{timeout}'")
        else:
            return None

    def appium_get_elements(self, locator, timeout=20):
        self._info(f"Appium Get Elements '{locator}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            elements = self._element_find(locator, False, False)
            if elements:
                self._info(f"Elements exist: '{elements}'")
                return elements
            time.sleep(0.5)
        self._info(f"Element '{locator}' does not exist within timeout of '{timeout}'")
        return []

    def appium_get_button_element(self, index_or_name, timeout=20, required=True):
        self._info(f"Appium Get Button Element '{index_or_name}', timeout '{timeout}', required '{required}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._find_element_by_class_name('Button', index_or_name)
                self._info(f"Element exist: '{element}'")
                return element
            except Exception:
                pass
            time.sleep(0.5)
        if required:
            raise Exception(f"Button '{index_or_name}' does not exist within timeout of '{timeout}'")
        else:
            return None

    def appium_get_element_text(self, text, exact_match=False, timeout=20, required=True):
        self._info(
            f"Appium Get Element Text '{text}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            element = self._element_find_by('Name', text, exact_match)
            if element:
                return element
            time.sleep(0.5)
        if required:
            raise Exception(f"Element Text '{text}' does not exist within timeout of '{timeout}'")
        else:
            return None

    def appium_get_element_by(self, key='*', value='', exact_match=False, timeout=20, required=True):
        self._info(
            f"Appium Get Element By '{key}={value}', exact_match '{exact_match}', timeout '{timeout}', required '{required}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._element_find_by(key, value, exact_match)
                self._info(f"Element exist: '{element}'")
                return element
            except Exception:
                pass
            time.sleep(0.5)
        if required:
            raise Exception(f"Element '{key}={value}' does not exist within timeout of '{timeout}'")
        else:
            return None

    def appium_get_element_in_element(self, parent_locator, child_locator, timeout=20):
        self._info(f"Appium Get Element In Element, child '{child_locator}', parent '{parent_locator}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._current_application()
            elements = self._element_finder.find(parent_element, child_locator, None)
            if len(elements) > 0:
                self._info(f"Element exist: '{elements[0]}'")
                return elements[0]
            time.sleep(0.5)
        raise Exception(f"Element '{child_locator}' in '{parent_locator}' does not exist within timeout of '{timeout}'")

    def appium_get_elements_in_element(self, parent_locator, child_locator, timeout=20):
        self._info(f"Appium Get Elements In Element, child '{child_locator}', parent '{parent_locator}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            parent_element = None
            if isinstance(parent_locator, str):
                parent_element = self._element_find(parent_locator, True, False)
            elif isinstance(parent_locator, WebElement):
                parent_element = parent_locator
            if not parent_element:
                parent_element = self._current_application()
            elements = self._element_finder.find(parent_element, child_locator, None)
            if len(elements) > 0:
                self._info(f"Elements exist: '{elements}'")
                return elements
            time.sleep(0.5)
        self._info(f"Element '{child_locator}' in '{parent_locator}' does not exist within timeout of '{timeout}'")
        return []

    def appium_find_element(self, locator, timeout=20, first_only=False):
        elements = self.appium_get_elements(locator=locator, timeout=timeout)
        if not first_only:
            return elements
        if len(elements) == 0:
            self._info("Element not found, return None")
            return None
        return elements[0]

    # TODO GET ELEMENT ATTRIBUTE
    def appium_get_element_attribute(self, locator, attribute, timeout=20):
        self._info(f"Appium Get Element Attribute '{attribute}' Of '{locator}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                att_value = self._element_find(locator, True, True).get_attribute(attribute)
                if att_value:
                    self._info(f"Attribute value: '{att_value}'")
                    return att_value
            except Exception:
                pass
            time.sleep(2)
        self._info(f"Not found attribute '{attribute}' of '{locator}', return None")
        return None

    def appium_get_element_attributes(self, locator, attribute, timeout=20):
        self._info(f"Appium Get Element Attributes '{attribute}' Of '{locator}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                elements = self._element_find(locator, False, True)
                att_values = [element.get_attribute(attribute) for element in elements]
                if any(att_values):
                    self._info(f"Attributes value: '{att_values}'")
                    return att_values
            except Exception:
                pass
            time.sleep(2)
        self._info(f"Not found attributes '{attribute}' of '{locator}', return []")
        return []

    def appium_get_element_attributes_in_element(self, parent_locator, child_locator, attribute, timeout=20):
        self._info(
            f"Appium Get Element Attributes In Element '{attribute}' Of '{child_locator}' In '{parent_locator}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
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
            except Exception:
                pass
            time.sleep(2)
        self._info(f"Not found attribute '{attribute}' of '{child_locator}' in '{parent_locator}', return []")
        return []

    def appium_get_text(self, locator, first_only=True, timeout=20):
        self._info(f"Appium Get Text '{locator}', first_only '{first_only}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                if first_only:
                    element = self._element_find(locator, True, True)
                    text = element.text
                    self._info(f"Text: '{text}'")
                    return text
                else:
                    elements = self._element_find(locator, False, True)
                    text = [element.text for element in elements]
                    if any(text):
                        self._info(f"List Text: '{text}'")
                        return text
            except Exception:
                pass
            time.sleep(2)
        self._info(f"Not found text '{locator}', return None")
        return None

    # TODO CLICK ELEMENT
    def appium_click(self, locator, timeout=20, required=True):
        self._info(f"Appium Click '{locator}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._element_find(locator, True, True)
                element.click()
                time.sleep(0.5)
                return True
            except Exception:
                pass
            time.sleep(0.5)
        if required:
            raise Exception(f"Fail to perform click action on '{locator}'")
        return False

    def appium_click_text(self, text, exact_match=False, timeout=20):
        self._info(f"Appium Click Text '{text}', exact_match '{exact_match}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._element_find_by('Name', text, exact_match)
                element.click()
                time.sleep(0.5)
                return
            except Exception:
                pass
            time.sleep(0.5)
        raise Exception(f"Fail to perform click action on text '{text}'")

    def appium_click_button(self, index_or_name, timeout=20):
        self._info(f"Appium Click Button '{index_or_name}', timeout '{timeout}'")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._find_element_by_class_name('Button', index_or_name)
                element.click()
                time.sleep(0.5)
                return
            except Exception:
                pass
            time.sleep(0.5)
        raise Exception(f"Fail to perform click action on button '{index_or_name}'")

    def appium_click_multiple_time(self, locator, repeat=1, timeout=20):
        for _ in range(repeat):
            self.appium_click(locator, timeout)

    def appium_click_if_exist(self, locator, timeout=2):
        result = self.appium_click(locator, timeout, False)
        if not result:
            self._info(f"Not found '{locator}', return False")
        return result

    def appium_hover(self, locator, start_locator=None, timeout=20, **kwargs):
        self._info(f"Appium Hover '{locator}', timeout '{timeout}'")
        self._appium_hover_api(start_locator=start_locator, end_locator=locator, timeout=timeout, **kwargs)

    def appium_click_offset(self, locator, x_offset=0, y_offset=0, timeout=20, **kwargs):
        self._info(
            f"Appium Click Offset '{locator}', (x_offset,y_offset) '({x_offset},{y_offset})', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, x_offset=x_offset, y_offset=y_offset, **kwargs)

    def appium_right_click(self, locator, timeout=20, **kwargs):
        self._info(f"Appium Right Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, button="right", **kwargs)

    def appium_left_click(self, locator, timeout=20, **kwargs):
        self._info(f"Appium Left Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, button="left", **kwargs)

    def appium_double_click(self, locator, timeout=20, **kwargs):
        self._info(f"Appium Double Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, times=2, **kwargs)

    def appium_drag_and_drop(self, start_locator=None, end_locator=None, timeout=20, **kwargs):
        self._info(f"Appium Drag And Drop '{start_locator} -> {end_locator}', timeout '{timeout}'")
        self._appium_drag_and_drop_api(start_locator=start_locator, end_locator=end_locator, timeout=timeout, **kwargs)

    def appium_drag_and_drop_by_offset(self, x_start, y_start, x_end, y_end):
        x_start, y_start, x_end, y_end = (int(x) for x in [x_start, y_start, x_end, y_end])
        self._info(f"Appium Drag And Drop By Offset ({x_start}, {y_start}) -> ({x_end}, {y_end})")
        rect = self._current_application().get_window_rect()
        x, y = rect['x'], rect['y']
        x_start, y_start, x_end, y_end = x + x_start, y + y_start, x + x_end, y + y_end
        self._info(f"Root rect: {rect}")
        self.execute_script('windows: clickAndDrag', startX=x_start, startY=y_start, endX=x_end, endY=y_end)

    # TODO SEND KEYS TO ELEMENT
    def appium_sendkeys(self, text=None, **kwargs):
        self._info(f"Appium Sendkeys '{text}'")
        self._appium_keys_api(text=text, **kwargs)

    def appium_input(self, locator, text, timeout=20, required=True):
        self._info(f"Appium Input '{text}' to '{locator}', timeout '{timeout}'")
        text = self._format_keys(text)
        locator = locator or "xpath=/*"
        self._info(f"Text: {text}, Locator: {locator}")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._element_find(locator, True, True)
                element.send_keys(text)
                time.sleep(0.5)
                return True
            except Exception:
                pass
            time.sleep(2)
        if required:
            raise Exception(f"Fail to perform input action on '{locator}'")
        return False

    def appium_input_text(self, locator_text, text, exact_match=False, timeout=20):
        self._info(f"Appium Input Text '{text}' to '{locator_text}', exact_match '{exact_match}', timeout '{timeout}'")
        text = self._format_keys(text)
        self._info(f"Text: {text}")
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                element = self._element_find_by('Name', locator_text, exact_match)
                element.send_keys(text)
                time.sleep(0.5)
                return
            except Exception:
                pass
            time.sleep(2)
        raise Exception(f"Fail to perform input action on text '{locator_text}'")

    def appium_input_if_exist(self, locator, text, timeout=2):
        result = self.appium_input(locator, text, timeout, False)
        if not result:
            self._info(f"Not found '{locator}', return False")
        return result

    def appium_press_page_up(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press Page Up {locator}, ")
        self.appium_input(locator, "{PAGE_UP}" * press_time, timeout)

    def appium_press_page_down(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press Page Down {locator}, ")
        self.appium_input(locator, "{PAGE_DOWN}" * press_time, timeout)

    def appium_press_home(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press Home {locator}, ")
        self.appium_input(locator, "{HOME}" * press_time, timeout)

    def appium_press_end(self, locator=None, press_time=1, timeout=5):
        self._info(f"Appium Press End {locator}, ")
        self.appium_input(locator, "{END}" * press_time, timeout)

    def appium_clear_all_text(self, locator, timeout=5):
        self._info(f"Appium Clear All Text {locator}")
        self.appium_input(locator, "{CONTROL}a{DELETE}", timeout)

    # TODO old method
    def clear_text(self, locator):
        """Clears the text field identified by `locator`.

        See `introduction` for details about locating elements.
        """
        self._info("Clear text field '%s'" % locator)
        self._element_find(locator, True, True).clear()

    def click_element(self, locator):
        """Click element identified by `locator`.

        Key attributes for arbitrary elements are `index` and `name`. See
        `introduction` for details about locating elements.
        """
        self._info("Clicking element '%s'." % locator)
        self._element_find(locator, True, True).click()

    def click_text(self, text, exact_match=False):
        """Click text identified by ``text``.

        By default tries to click first text involves given ``text``, if you would
        like to click exactly matching text, then set ``exact_match`` to `True`.

        If there are multiple use  of ``text`` and you do not want first one,
        use `locator` with `Get Web Elements` instead.

        """
        self._element_find_by_text(text, exact_match).click()

    def input_text_into_current_element(self, text):
        """Types the given `text` into currently selected text field.

            Android only.
        """
        self._info("Typing text '%s' into current text field" % text)
        driver = self._current_application()
        driver.set_clipboard_text(text)
        driver.press_keycode(50, 0x1000 | 0x2000)

    def input_text(self, locator, text):
        """Types the given `text` into text field identified by `locator`.

        See `introduction` for details about locating elements.
        """
        self._info("Typing text '%s' into text field '%s'" % (text, locator))
        self._element_input_text_by_locator(locator, text)

    def input_password(self, locator, text):
        """Types the given password into text field identified by `locator`.

        Difference between this keyword and `Input Text` is that this keyword
        does not log the given password. See `introduction` for details about
        locating elements.
        """
        self._info("Typing password into text field '%s'" % locator)
        self._element_input_text_by_locator(locator, text)

    def input_value(self, locator, text):
        """Sets the given value into text field identified by `locator`. This is an IOS only keyword, input value makes use of set_value

        See `introduction` for details about locating elements.
        """
        self._info("Setting text '%s' into text field '%s'" % (text, locator))
        self._element_input_value_by_locator(locator, text)

    def hide_keyboard(self, key_name=None):
        """Hides the software keyboard on the device. (optional) In iOS, use `key_name` to press
        a particular key, ex. `Done`. In Android, no parameters are used.
        """
        driver = self._current_application()
        driver.hide_keyboard(key_name)

    def is_keyboard_shown(self):
        """Return true if Android keyboard is displayed or False if not displayed
        No parameters are used.
        """
        driver = self._current_application()
        return driver.is_keyboard_shown()

    def page_should_contain_text(self, text, loglevel='INFO'):
        """Verifies that current page contains `text`.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        """
        if not self._is_text_present(text):
            self.log_source(loglevel)
            raise AssertionError("Page should have contained text '%s' "
                                 "but did not" % text)
        self._info("Current page contains text '%s'." % text)

    def page_should_not_contain_text(self, text, loglevel='INFO'):
        """Verifies that current page not contains `text`.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        """
        if self._is_text_present(text):
            self.log_source(loglevel)
            raise AssertionError("Page should not have contained text '%s'" % text)
        self._info("Current page does not contains text '%s'." % text)

    def page_should_contain_element(self, locator, loglevel='INFO'):
        """Verifies that current page contains `locator` element.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        """
        if not self._is_element_present(locator):
            self.log_source(loglevel)
            raise AssertionError("Page should have contained element '%s' "
                                 "but did not" % locator)
        self._info("Current page contains element '%s'." % locator)

    def page_should_not_contain_element(self, locator, loglevel='INFO'):
        """Verifies that current page not contains `locator` element.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        """
        if self._is_element_present(locator):
            self.log_source(loglevel)
            raise AssertionError("Page should not have contained element '%s'" % locator)
        self._info("Current page not contains element '%s'." % locator)

    def element_should_be_disabled(self, locator, loglevel='INFO'):
        """Verifies that element identified with locator is disabled.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        """
        if self._element_find(locator, True, True).is_enabled():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be disabled "
                                 "but did not" % locator)
        self._info("Element '%s' is disabled ." % locator)

    def element_should_be_enabled(self, locator, loglevel='INFO'):
        """Verifies that element identified with locator is enabled.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        """
        if not self._element_find(locator, True, True).is_enabled():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be enabled "
                                 "but did not" % locator)
        self._info("Element '%s' is enabled ." % locator)

    def element_should_be_visible(self, locator, loglevel='INFO'):
        """Verifies that element identified with locator is visible.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.

        New in AppiumLibrary 1.4.5
        """
        if not self._element_find(locator, True, True).is_displayed():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be visible "
                                 "but did not" % locator)

    def element_name_should_be(self, locator, expected):
        element = self._element_find(locator, True, True)
        if str(expected) != str(element.get_attribute('name')):
            raise AssertionError("Element '%s' name should be '%s' "
                                 "but it is '%s'." % (locator, expected, element.get_attribute('name')))
        self._info("Element '%s' name is '%s' " % (locator, expected))

    def element_value_should_be(self, locator, expected):
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
        except:
            raise AssertionError("Attribute '%s' is not valid for element '%s'" % (attribute, locator))

    def get_element_location(self, locator):
        """Get element location

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        """
        element = self._element_find(locator, True, True)
        element_location = element.location
        self._info("Element '%s' location: %s " % (locator, element_location))
        return element_location

    def get_element_size(self, locator):
        """Get element size

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        """
        element = self._element_find(locator, True, True)
        element_size = element.size
        self._info("Element '%s' size: %s " % (locator, element_size))
        return element_size

    def get_element_rect(self, locator):
        """Gets dimensions and coordinates of an element

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
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
        | ${count}  | Get Matching Xpath Count | xpath=//android.view.View[@text='Test'] |

        If you wish to assert the number of matching elements, use
        `Xpath Should Match X Times`.

        New in AppiumLibrary 1.4.
        """
        count = len(self._element_find("xpath=" + xpath, False, False))
        return str(count)

    def text_should_be_visible(self, text, exact_match=False, loglevel='INFO'):
        """Verifies that element identified with text is visible.

        New in AppiumLibrary 1.4.5
        """
        if not self._element_find_by_text(text, exact_match).is_displayed():
            self.log_source(loglevel)
            raise AssertionError("Text '%s' should be visible "
                                 "but did not" % text)

    def xpath_should_match_x_times(self, xpath, count, error=None, loglevel='INFO'):
        """Verifies that the page contains the given number of elements located by the given ``xpath``.

        One should not use the `xpath=` prefix for 'xpath'. XPath is assumed.

        | *Correct:* |
        | Xpath Should Match X Times | //android.view.View[@text='Test'] | 1 |
        | Incorrect: |
        | Xpath Should Match X Times | xpath=//android.view.View[@text='Test'] | 1 |

        ``error`` can be used to override the default error message.

        See `Log Source` for explanation about ``loglevel`` argument.

        New in AppiumLibrary 1.4.
        """
        actual_xpath_count = len(self._element_find("xpath=" + xpath, False, False))
        if int(actual_xpath_count) != int(count):
            if not error:
                error = "Xpath %s should have matched %s times but matched %s times" \
                        % (xpath, count, actual_xpath_count)
            self.log_source(loglevel)
            raise AssertionError(error)
        self._info("Current page contains %s elements matching '%s'."
                   % (actual_xpath_count, xpath))

    # Private

    def _get_maxtime(self, timeout) -> float:
        if not timeout:
            timeout = self._bi.get_variable_value("${TIMEOUT}", "20")
        return time.time() + timestr_to_secs(timeout)

    def _retry(self, timeout, func, *args) -> _RetryResult:
        start = time.time()
        timeout = timeout or self._bi.get_variable_value("${TIMEOUT}", "20")
        maxtime = start + timestr_to_secs(timeout)
        rr = _RetryResult()

        while True:
            try:
                rr.result = func(*args)
                rr.executed = True
                rr.last_exception = None
                break
            except Exception as e:
                rr.last_exception = e

            if time.time() > maxtime:
                rr.timeout = True
                break

            time.sleep(0.5)

        rr.duration = time.time() - start
        return rr

    def _handle_retry_result(self, rr, action: str, timeout: int, required: bool, return_value: bool = False):
        """
        Handle the result of a retry operation.
        - return_value=False → treat as action (returns True/False)
        - return_value=True  → treat as getter (returns actual value/None)
        """
        if rr.executed:
            return rr.result if return_value else True

        if required:
            raise TimeoutError(f"{action} failed after {timeout}s") from rr.last_exception

        return None if return_value else False

    def _context_finder(self, locator, tag):
        """Try finding, refresh context on failure, retry once."""
        try:
            return self._element_finder.find(self._context, locator, tag)
        except (StaleElementReferenceException, NoSuchElementException, WebDriverException):
            # Refresh context, then retry
            if self._context_locator is None:
                raise Exception("No context locator stored. Call set_search_context() first.")
            self._context = self.appium_get_element(self._context_locator, 5)
            return self._element_finder.find(self._context, locator, tag)

    def _element_find(self, locator, first_only, required, tag=None):
        application = self._current_application()
        elements = None
        if isinstance(locator, str):
            _locator = locator
            if self._context:
                elements = self._context_finder(_locator, tag)
            else:
                elements = self._element_finder.find(application, _locator, tag)
            if required and len(elements) == 0:
                raise ValueError("Element locator '" + locator + "' did not match any elements.")
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

    def _appium_click_api(self, locator, timeout, **kwargs):
        """
        https://github.com/appium/appium-windows-driver
        https://github.com/appium/appium-windows-driver?tab=readme-ov-file#windows-click

        @param locator:
        @param timeout:
        @param kwargs:

        button: Name of the mouse button to be clicked. An exception is thrown if an unknown button name is provided.
        Supported button names are: left, middle, right, back, forward. The default value is left

        modifier_keys: List of possible keys or a single key name to depress while the click is being performed.
        Supported key names are: Shift, Ctrl, Alt, Win. For example, in order to keep Ctrl+Alt depressed while clicking,
        provide the value of ['ctrl', 'alt']

        """
        x_offset = int(kwargs.get("x_offset", 0))
        y_offset = int(kwargs.get("y_offset", 0))
        is_center = kwargs.get("is_center", False)
        button = kwargs.get("button", "left")
        modifier_keys = kwargs.get("modifierKeys", None)
        duration_ms = int(kwargs.get("durationMs", 100))
        times = int(kwargs.get("times", 1))
        inter_click_delay_ms = int(kwargs.get("interClickDelayMs", 100))
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                elements = self._element_find(locator, False, False)
                if elements:
                    rect = self._current_application().get_window_rect()
                    e_rect = elements[0].rect
                    x = x_offset + rect['x'] + e_rect['x']
                    y = y_offset + rect['y'] + e_rect['y']
                    if is_center:
                        x = x + int(e_rect['width'] // 2)
                        y = y + int(e_rect['height'] // 2)
                    self._info(f"Element location: '({x},{y})'")
                    self.execute_script("windows: click",
                                        x=x,
                                        y=y,
                                        button=button,
                                        modifierKeys=modifier_keys,
                                        durationMs=duration_ms,
                                        times=times,
                                        interClickDelayMs=inter_click_delay_ms)
                    time.sleep(0.5)
                    return
            except Exception:
                pass
            time.sleep(2)
        raise Exception(f"Fail to perform click api action on '{locator}'")

    def _appium_hover_api(self, start_locator, end_locator, timeout, **kwargs):
        """
        https://github.com/appium/appium-windows-driver?tab=readme-ov-file#windows-click
        @param start_locator:
        @param end_locator:
        @param timeout:
        @param kwargs:
        @return:
        """
        start_element_id = str(kwargs.get("startElementId", ""))
        startX = int(kwargs.get("startX", 0))
        startY = int(kwargs.get("startY", 0))
        end_element_id = str(kwargs.get("endElementId", ""))
        endX = int(kwargs.get("endX", 0))
        endY = int(kwargs.get("endY", 0))
        modifier_keys = kwargs.get("modifierKeys", None)
        duration_ms = int(kwargs.get("durationMs", 100))
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                if start_locator:
                    start_element = self._element_find(start_locator, True, False)
                    if start_element:
                        start_element_id = start_element.id
                if end_locator:
                    end_element = self._element_find(end_locator, True, False)
                    if end_element:
                        end_element_id = end_element.id
                self.execute_script("windows: hover",
                                    startElementId=start_element_id,
                                    startX=startX,
                                    startY=startY,
                                    endElementId=end_element_id,
                                    endX=endX,
                                    endY=endY,
                                    modifierKeys=modifier_keys,
                                    durationMs=duration_ms)
                time.sleep(0.5)
                return
            except Exception:
                pass
            time.sleep(2)
        raise Exception(f"Fail to perform hover api action")

    def _appium_drag_and_drop_api(self, start_locator, end_locator, timeout, **kwargs):
        """
        https://github.com/appium/appium-windows-driver?tab=readme-ov-file#windows-clickanddrag
        @param start_locator:
        @param end_locator:
        @param timeout:
        @param kwargs:
        @return:
        """
        start_element_id = str(kwargs.get("startElementId", ""))
        startX = int(kwargs.get("startX", 0))
        startY = int(kwargs.get("startY", 0))
        end_element_id = str(kwargs.get("endElementId", ""))
        endX = int(kwargs.get("endX", 0))
        endY = int(kwargs.get("endY", 0))
        modifier_keys = kwargs.get("modifierKeys", None)
        duration_ms = int(kwargs.get("durationMs", 5000))
        maxtime = self._get_maxtime(timeout)
        while time.time() < maxtime:
            try:
                if start_locator:
                    start_element = self._element_find(start_locator, True, False)
                    if start_element:
                        start_element_id = start_element.id
                if end_locator:
                    end_element = self._element_find(end_locator, True, False)
                    if end_element:
                        end_element_id = end_element.id
                self.execute_script("windows: clickAndDrag",
                                    startElementId=start_element_id,
                                    startX=startX,
                                    startY=startY,
                                    endElementId=end_element_id,
                                    endX=endX,
                                    endY=endY,
                                    modifierKeys=modifier_keys,
                                    durationMs=duration_ms)
                time.sleep(0.5)
                return
            except Exception:
                pass
            time.sleep(2)
        raise Exception(f"Fail to perform drag and drop api action")

    def _appium_keys_api(self, text, **kwargs):
        """
        https://github.com/appium/appium-windows-driver?tab=readme-ov-file#windows-keys
        @param text:
        @param kwargs:
        @return:
        """
        actions = kwargs.get("actions", "")
        # pause = int(kwargs.get("pause", 0))
        # virtual_key_code = int(kwargs.get("virtualKeyCode", 0))
        # down = bool(kwargs.get("down", False))
        if not actions:
            actions = [{"text": text}]
        self.execute_script("windows: keys", actions=actions)

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

