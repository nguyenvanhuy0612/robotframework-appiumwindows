
import unittest
import sys
import os
import re
sys.path.append(os.getcwd())
from unittest.mock import MagicMock, patch
from AppiumLibrary.keywords._element import _ElementKeywords
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import appium.webdriver

class TestElementKeywordsCore(unittest.TestCase):
    
    def setUp(self):
        # We need to mock BuiltIn because we are running completely partially isolated from Robot
        self.builtin_patcher = patch('AppiumLibrary.keywords._element.BuiltIn')
        self.mock_builtin_class = self.builtin_patcher.start()
        self.mock_builtin_instance = self.mock_builtin_class.return_value
        # Set timeout to a valid string number
        self.mock_builtin_instance.get_variable_value.return_value = "5"
        
        self.ek = _ElementKeywords()
        self.ek._timeout_in_secs = 5
        self.ek._poll_sleep_between_wait = 0.1 # Use small value for faster tests
        
        # Mock mixin methods not present in _element.py directly
        self.ek._get_platform = MagicMock(return_value='android')
        self.ek.log_source = MagicMock()
        self.ek.get_source = MagicMock(return_value="<html><p>Mock Page Source</p></html>")

        # Mock the application/driver
        self.mock_driver = MagicMock(spec=appium.webdriver.Remote)
        self.mock_driver.get_screenshot_as_base64.return_value = "base64_image"
        self.mock_driver.page_source = "<html><p>Mock Page Source</p></html>"

        # Mock _current_application to return our mock driver
        self.ek._current_application = MagicMock(return_value=self.mock_driver)

        # Mock logging to avoid clutter
        self.ek._info = MagicMock()
        self.ek._debug = MagicMock()
        self.ek._warn = MagicMock()

        # Create a real-ish WebElement to return from finds
        self.mock_element = MagicMock(spec=WebElement)
        # Identify it easily
        self.mock_element.name = "Mock Element" 
        self.mock_element.text = "Mock Text"
        self.mock_element.get_attribute.side_effect = self._mock_get_attribute
        self.mock_element.is_displayed.return_value = True
        self.mock_element.is_enabled.return_value = True
        self.mock_element.location = {'x': 10, 'y': 20}
        self.mock_element.size = {'width': 100, 'height': 50}
        self.mock_element.rect = {'x': 10, 'y': 20, 'width': 100, 'height': 50}

    def _mock_get_attribute(self, name):
        if name == 'name':
            return "Mock Element"
        if name == 'text':
             return "Mock Text"
        if name == 'value':
             return "Mock Value"
        if name == 'content-description':
             return "Mock Desc"
        return "Mock Attribute"

    def tearDown(self):
        self.builtin_patcher.stop()

    def _setup_finding(self, elements=None):
        if elements is None:
            elements = [self.mock_element]
        self.mock_driver.find_elements.return_value = elements

    # ====================================================================
    # CHECK / EXIST / WAIT
    # ====================================================================

    def test_appium_element_exist(self):
        self._setup_finding()
        self.assertTrue(self.ek.appium_element_exist("id=foo"))

    def test_appium_element_exist_false(self):
        self._setup_finding([]) # Empty list
        self.assertFalse(self.ek.appium_element_exist("id=foo"))

    def test_appium_wait_until_element_is_visible(self):
        self._setup_finding()
        self.mock_element.is_displayed.return_value = True
        self.ek.appium_wait_until_element_is_visible("id=foo", timeout="1s")

    def test_appium_wait_until_element_is_not_visible(self):
        # Case 1: Element exists but not visible
        self._setup_finding()
        self.mock_element.is_displayed.return_value = False
        self.ek.appium_wait_until_element_is_not_visible("id=foo", timeout="1s")
        # Case 2: Element does not exist
        self._setup_finding([])
        self.ek.appium_wait_until_element_is_not_visible("id=foo", timeout="1s")

    def test_appium_element_should_be_visible(self):
        self._setup_finding()
        self.mock_element.is_displayed.return_value = True
        self.ek.appium_element_should_be_visible("id=foo")

    def test_text_should_be_visible(self):
         # This uses _element_find_by_text -> internal logic -> calls find_elements usually
         # Or uses XPath.
         # Platform=android -> uses XPath or UIAutomator
         self._setup_finding()
         self.mock_element.is_displayed.return_value = True
         self.ek.text_should_be_visible("Mock Text")

    # ====================================================================
    # GET KEYWORDS
    # ====================================================================

    def test_appium_get_element(self):
        self._setup_finding()
        el = self.ek.appium_get_element("id=foo")
        self.assertEqual(el, self.mock_element)

    def test_appium_get_elements(self):
        self._setup_finding([self.mock_element, self.mock_element])
        els = self.ek.appium_get_elements("id=foo")
        self.assertEqual(len(els), 2)

    def test_appium_get_element_text(self):
        self._setup_finding()
        text = self.ek.appium_get_element_text("Mock Text", exact_match=True)
        self.assertEqual(text.text, "Mock Text")

    def test_appium_get_text(self):
        self._setup_finding()
        text = self.ek.appium_get_text("id=foo")
        self.assertEqual(text, "Mock Text")
        
    def test_get_webelement(self):
        self._setup_finding()
        el = self.ek.get_webelement("id=foo")
        self.assertEqual(el, self.mock_element)
    
    def test_get_webelements(self):
         self._setup_finding()
         els = self.ek.get_webelements("id=foo")
         self.assertEqual(len(els), 1)

    # ====================================================================
    # ATTRIBUTE / LOCATION / SIZE
    # ====================================================================

    def test_appium_get_element_attribute(self):
        self._setup_finding()
        attr = self.ek.appium_get_element_attribute("id=foo", "name")
        self.assertEqual(attr, "Mock Element")

    def test_get_element_location(self):
        self._setup_finding()
        loc = self.ek.get_element_location("id=foo")
        self.assertEqual(loc, {'x': 10, 'y': 20})

    def test_get_element_size(self):
        self._setup_finding()
        size = self.ek.get_element_size("id=foo")
        self.assertEqual(size, {'width': 100, 'height': 50})
        
    def test_get_element_rect(self):
        self._setup_finding()
        rect = self.ek.get_element_rect("id=foo")
        self.assertEqual(rect, {'x': 10, 'y': 20, 'width': 100, 'height': 50})

    # ====================================================================
    # ACTION KEYWORDS
    # ====================================================================

    def test_appium_click(self):
        self._setup_finding()
        self.ek.appium_click("id=foo")
        self.mock_element.click.assert_called()

    def test_click_element(self):
        self._setup_finding()
        self.ek.click_element("id=foo")
        self.mock_element.click.assert_called()

    def test_appium_click_text(self):
        # Uses _element_find_by_text
        self._setup_finding()
        self.ek.appium_click_text("Mock Text")
        self.mock_element.click.assert_called()

    # ====================================================================
    # TESTS FOR REQUIRED CHECK
    # ====================================================================

    def test_appium_click_text_not_required(self):
        # Should not raise if not found
        self._setup_finding([]) # Simulates not found
        result = self.ek.appium_click_text("Mock Text", required=False, timeout="0.1s")
        # _retry returns False if required=False and it fails
        self.assertFalse(result)

    def test_appium_click_button_not_required(self):
        self._setup_finding([])
        result = self.ek.appium_click_button("Mock Button", required=False, timeout="0.1s")
        self.assertFalse(result)
        
    def test_appium_input_text_not_required(self):
        self._setup_finding([])
        # locator_text, text, ...
        result = self.ek.appium_input_text("Mock Field", "Text", required=False, timeout="0.1s")
        self.assertFalse(result)

        
    def test_appium_input(self):
        self._setup_finding()
        self.ek.appium_input("id=foo", "hello")
        self.mock_element.send_keys.assert_called()

    def test_input_text(self):
        self._setup_finding()
        self.ek.input_text("id=foo", "hello")
        self.mock_element.send_keys.assert_called()
        
    def test_input_password(self):
        self._setup_finding()
        self.ek.input_password("id=foo", "secret")
        self.mock_element.send_keys.assert_called()

    def test_clear_text(self):
        self._setup_finding()
        self.ek.clear_text("id=foo")
        self.mock_element.clear.assert_called()

    def test_hide_keyboard(self):
        self.ek.hide_keyboard()
        self.mock_driver.hide_keyboard.assert_called()
        
    def test_is_keyboard_shown(self):
        self.mock_driver.is_keyboard_shown.return_value = True
        self.assertTrue(self.ek.is_keyboard_shown())
        
    def test_scroll_element_into_view(self):
        self._setup_finding()
        self.ek.scroll_element_into_view("id=foo")
        self.mock_driver.execute_script.assert_called()

    # ====================================================================
    # ASSERT KEYWORDS
    # ====================================================================

    def test_page_should_contain_element(self):
        self._setup_finding()
        self.ek.page_should_contain_element("id=foo")

    def test_page_should_not_contain_element(self):
        self._setup_finding([])
        self.ek.page_should_not_contain_element("id=bar")

    def test_page_should_contain_text(self):
        # uses get_source or page_source
        self.ek.page_should_contain_text("Mock Page Source")
        
    def test_page_should_not_contain_text(self):
        self.ek.page_should_not_contain_text("Banana")

    def test_element_should_be_enabled(self):
        self._setup_finding()
        self.mock_element.is_enabled.return_value = True
        self.ek.element_should_be_enabled("id=foo")

    def test_element_should_be_disabled(self):
        self._setup_finding()
        self.mock_element.is_enabled.return_value = False
        self.ek.element_should_be_disabled("id=foo")

    def test_element_attribute_should_match(self):
        self._setup_finding()
        self.ek.element_attribute_should_match("id=foo", "name", "Mock Element")

    def test_element_should_contain_text(self):
        self._setup_finding()
        self.ek.element_should_contain_text("id=foo", "Mock")
        
    def test_element_text_should_be(self):
        self._setup_finding()
        self.ek.element_text_should_be("id=foo", "Mock Text")

    def test_element_name_should_be(self):
        self._setup_finding()
        # _element.py implementation: element.get_attribute('name') == expected
        self.ek.element_name_should_be("id=foo", "Mock Element")

    def test_element_value_should_be(self):
        self._setup_finding()
        # _element.py implementation: element.get_attribute('value')
        self.ek.element_value_should_be("id=foo", "Mock Value")

    # ====================================================================
    # MISC / COMPLEX
    # ====================================================================

    def test_xpath_should_match_x_times(self):
        # find_elements returns list
        self._setup_finding([self.mock_element, self.mock_element])
        self.ek.xpath_should_match_x_times("//foo", 2)
        
    def test_get_matching_xpath_count(self):
        self._setup_finding([self.mock_element, self.mock_element, self.mock_element])
        count = self.ek.get_matching_xpath_count("//foo")
        self.assertEqual(count, "3") # Robot usually returns string count for this kw? or int?
        # AppiumLibrary returns str(len(elements))
        
if __name__ == "__main__":
    unittest.main()
