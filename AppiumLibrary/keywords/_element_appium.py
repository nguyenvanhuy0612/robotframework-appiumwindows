import time
from typing import Tuple

from appium.webdriver import WebElement as AppiumElement
from robot.libraries.BuiltIn import BuiltIn
from robot.utils import timestr_to_secs
from selenium.common import WebDriverException

from AppiumLibrary.locators import ElementFinder
from .keywordgroup import KeywordGroup


class _ElementKeywordsAppium(KeywordGroup):
    def __init__(self):
        self._element_finder = ElementFinder()
        self._bi = BuiltIn()
        self._context = {}

    def appium_get_context(self, element_only=False, locator_only=False):
        if element_only:
            return self._context.get('element')
        if locator_only:
            return self._context.get('locator')
        return self._context

    def appium_set_context(self, context, reference, timeout, clear=True) -> dict:
        old_context = self._context
        if clear:
            self._context = {}

        if isinstance(context, str):
            self._context['element'] = self._find_context(context, reference, timeout)
            self._context['locator'] = context
        if isinstance(context, AppiumElement):
            self._context['element'] = context
            self._info(f"WARNING!!! Reference use as locator: {reference}")
            self._context['locator'] = reference
        elif isinstance(context, dict) and context.get('locator'):
            self._info(f"Context: {context}")
            self._context['element'] = self._find_context(context['locator'], reference, timeout)
            self._context['locator'] = context['locator']

        if not self._context.get('element'):
            self._info("WARNING!!! Search Context Empty")
            self._context = {}

        return old_context

    def _find_context(self, locator, reference=None, timeout=20, ref_timeout=5):
        elements = self._invoke_original("appium_get_elements", locator, timeout)
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
                if self._invoke_original("appium_get_elements_in_element", el, reference, ref_timeout):
                    element = el
                    break

        # Default - first element
        else:
            element = elements[0]

        if not element:
            raise Exception(f"Not found context '{locator}' with reference '{reference}'")

        return element

    def appium_clear_context(self):
        old_context = self._context
        self._context = {}
        return old_context

    def appium_element_exist(self, locator) -> bool | AppiumElement:
        pass

    def appium_elements_exist(self) -> bool | list:
        pass

    def appium_wait_element_visible(self) -> bool | AppiumElement:
        pass

    def appium_wait_element_not_visible(self) -> bool:
        pass

    def appium_element_should_be_visible(self) -> bool:
        pass

    def appium_element_should_be_not_visible(self) -> bool:
        pass

    def appium_first_found_element(self) -> int | AppiumElement:
        pass

    def appium_get_element(self) -> AppiumElement:
        pass

    def appium_get_elements(self) -> AppiumElement:
        pass

    def _appium(self, locator, condition='exist', **kwargs):

        def _func():
            pass

        r, e = self._until(locator, 10, _func)
        return r

    def _until(self, locator, timeout, func, allow_none=False, excepts=WebDriverException) -> Tuple:
        end_time = time.time() + timestr_to_secs(timeout)

        while True:
            try:
                result = func()

                if result is not None:
                    return result, None

                if allow_none:
                    return None, None
            except excepts as e:
                last_exception = f"'{locator}' Exception: {e}"
            else:
                last_exception = None

            if time.time() > end_time:
                break
            time.sleep(0.5)

        return None, last_exception
