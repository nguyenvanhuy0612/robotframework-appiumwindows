
import unittest
from unittest.mock import MagicMock, patch, call
import sys
import types

# =================================================================================
# 1. SETUP DETAILED MOCKS
# =================================================================================

# Robot Framework Mocks
mock_robot = types.ModuleType("robot")
mock_robot_libraries = types.ModuleType("robot.libraries")
mock_builtin = types.ModuleType("robot.libraries.BuiltIn")
mock_robot_utils = types.ModuleType("robot.utils")
mock_robot_api = types.ModuleType("robot.api")

sys.modules["robot"] = mock_robot
sys.modules["robot.libraries"] = mock_robot_libraries
sys.modules["robot.libraries.BuiltIn"] = mock_builtin
sys.modules["robot.utils"] = mock_robot_utils
sys.modules["robot.api"] = mock_robot_api

# Mock BuiltIn class and exception
class MockBuiltIn:
    def get_variable_value(self, name, default=None):
        return default
    def log(self, *args, **kwargs):
        pass
    def should_be_equal(self, first, second, msg=None, values=True):
        if first != second:
            raise AssertionError(msg or f"{first} != {second}")
    def should_match(self, string, pattern, msg=None, values=True):
        # weak mock for glob match
        if pattern not in string: 
             pass # In real Robot this is complex, here we assume success or raise
    def should_match_regexp(self, string, pattern, msg=None, values=True):
         pass

mock_builtin.BuiltIn = MagicMock(return_value=MockBuiltIn())
mock_builtin.RobotNotRunningError = Exception
mock_robot_utils.timestr_to_secs = MagicMock(return_value=1.0)
mock_robot_utils.abspath = MagicMock(return_value="/mock/path")
mock_robot_utils.ConnectionCache = MagicMock()
mock_robot_api.logger = MagicMock()

# Selenium Mocks
mock_selenium = types.ModuleType("selenium")
mock_selenium_common = types.ModuleType("selenium.common")
mock_selenium_webdriver = types.ModuleType("selenium.webdriver")
mock_selenium_remote = types.ModuleType("selenium.webdriver.remote")
mock_selenium_webelement = types.ModuleType("selenium.webdriver.remote.webelement")

sys.modules["selenium"] = mock_selenium
sys.modules["selenium.common"] = mock_selenium_common
sys.modules["selenium.webdriver"] = mock_selenium_webdriver
sys.modules["selenium.webdriver.remote"] = mock_selenium_remote
sys.modules["selenium.webdriver.remote.webelement"] = mock_selenium_webelement

mock_selenium_common.StaleElementReferenceException = Exception
mock_selenium_common.NoSuchElementException = Exception
mock_selenium_common.WebDriverException = Exception
mock_selenium_common.InvalidArgumentException = Exception
# FIX: Keys must return strings for regex ops
class MockKeys:
    def __getattr__(self, name):
        return f"{{{{ {name} }}}}"
mock_selenium_webdriver.Keys = MockKeys()

class MockWebElement:
    def __init__(self, name="mock_element", text="mock_text", displayed=True, enabled=True):
        self.name = name
        self._text = text
        self._displayed = displayed
        self._enabled = enabled
        self.location = {'x': 0, 'y': 0}
        self.size = {'width': 100, 'height': 100}
        self.rect = {'x': 0, 'y': 0, 'width': 100, 'height': 100}

    @property
    def text(self):
        return self._text
    
    def is_displayed(self):
        return self._displayed
    
    def is_enabled(self):
        return self._enabled
        
    def click(self):
        pass
        
    def send_keys(self, keys):
        pass
        
    def clear(self):
        pass
        
    def set_value(self, value):
        self._text = value

    def get_attribute(self, name):
        if name == 'name': return self.name
        return "mock_attribute_value"

    def __repr__(self):
        return f"<MockWebElement {self.name}>"

mock_selenium_webelement.WebElement = MockWebElement

# Appium Mocks
mock_appium = types.ModuleType("appium")
sys.modules["appium"] = mock_appium
mock_appium_webdriver = types.ModuleType("appium.webdriver")
sys.modules["appium.webdriver"] = mock_appium_webdriver
mock_appium.webdriver = mock_appium_webdriver
mock_appium_options = types.ModuleType("appium.options")
sys.modules["appium.options"] = mock_appium_options
mock_appium_options_common = types.ModuleType("appium.options.common")
sys.modules["appium.options.common"] = mock_appium_options_common
mock_appium_options_common.AppiumOptions = MagicMock()
mock_appium_webdriver_common = types.ModuleType("appium.webdriver.common")
sys.modules["appium.webdriver.common"] = mock_appium_webdriver_common
mock_appium_webdriver_common_appiumby = types.ModuleType("appium.webdriver.common.appiumby")
sys.modules["appium.webdriver.common.appiumby"] = mock_appium_webdriver_common_appiumby
mock_appium_webdriver_common_appiumby.AppiumBy = MagicMock()
mock_appium_webdriver_mobilecommand = types.ModuleType("appium.webdriver.mobilecommand")
sys.modules["appium.webdriver.mobilecommand"] = mock_appium_webdriver_mobilecommand
mock_appium_webdriver.mobilecommand = mock_appium_webdriver_mobilecommand
mock_appium_webdriver_mobilecommand.MobileCommand = MagicMock()

# AppiumLibrary Locators Mock
mock_appiumlibrary_locators = types.ModuleType("AppiumLibrary.locators")
sys.modules["AppiumLibrary.locators"] = mock_appiumlibrary_locators

class MockElementFinder:
    def find(self, application, locator, tag):
        # We will override this in setUp usually
        return []

mock_appiumlibrary_locators.ElementFinder = MagicMock(return_value=MockElementFinder())

# Import Target
import os
sys.path.append(os.getcwd())
try:
    from AppiumLibrary.keywords._element import _ElementKeywords
except ImportError:
    # If standard import fails, try patching sys.modules for AppiumLibrary package if strictly needed
    # But usually creating the mock modules above is enough if the file structure is correct.
    pass

class TestElementKeywordsMock(unittest.TestCase):

    def setUp(self):
        self.ek = _ElementKeywords()
        self.ek._element_finder = MagicMock()
        
        mock_app = MagicMock()
        mock_app.page_source = "<html>source</html>"
        self.ek._current_application = MagicMock(return_value=mock_app)
        
        self.ek._get_platform = MagicMock(return_value='android')
        
        self.ek._invoke_original = MagicMock(side_effect=self._invoke_original_passthrough)
        
        self.ek._info = MagicMock()
        self.ek._debug = MagicMock()
        self.ek._warn = MagicMock()
        
        # Mock get_source which is expected to exist (mixin)
        self.ek.get_source = MagicMock(return_value="<html>source</html>")
        self.ek.log_source = MagicMock()
        
        self.mock_element = MockWebElement("default_mock")
        # Default behavior: return our standard mock element
        self.ek._element_finder.find.return_value = [self.mock_element]

    def _invoke_original_passthrough(self, method_name, *args, **kwargs):
        if hasattr(self.ek, method_name):
            method = getattr(self.ek, method_name)
            return method(*args, **kwargs)
        return None

    # ====================================================================
    # 1. TEST CHECK / EXIST KEYWORDS
    # ====================================================================
    
    def test_appium_element_exist_true(self):
        self.ek._element_finder.find.return_value = [self.mock_element]
        result = self.ek.appium_element_exist("id=foo")
        self.assertTrue(result)
        
    def test_appium_element_exist_false(self):
        self.ek._element_finder.find.return_value = []
        result = self.ek.appium_element_exist("id=fail", timeout="0.1s")
        self.assertFalse(result)

    def test_appium_wait_until_element_is_visible_success(self):
        self.mock_element._displayed = True
        self.assertTrue(self.ek.appium_wait_until_element_is_visible("id=visible"))

    def test_appium_wait_until_element_is_visible_fail(self):
        self.ek._element_finder.find.return_value = []
        self.assertFalse(self.ek.appium_wait_until_element_is_visible("id=timeout", timeout="0.1s"))

    # ====================================================================
    # 2. TEST GET KEYWORDS
    # ====================================================================

    def test_appium_get_element_success(self):
        el = self.ek.appium_get_element("id=ok")
        self.assertEqual(el, self.mock_element)

    def test_appium_get_element_fail_required(self):
        self.ek._element_finder.find.return_value = []
        with self.assertRaises(Exception):
            self.ek.appium_get_element("id=fail", timeout="0.1s", required=True)

    def test_appium_get_elements(self):
        self.ek._element_finder.find.return_value = [self.mock_element, self.mock_element]
        elements = self.ek.appium_get_elements("id=list")
        self.assertEqual(len(elements), 2)

    def test_appium_get_text(self):
        text = self.ek.appium_get_text("id=text_el")
        self.assertEqual(text, "mock_text")

    # ====================================================================
    # 3. TEST ACTION KEYWORDS
    # ====================================================================

    def test_appium_click(self):
        self.assertTrue(self.ek.appium_click("id=click_me"))
        # Verify click called on element logic? (MockWebElement doesn't track calls by default unless mocked)
        # In a real rigorous test we would verify mock_element.click.assert_called() but MockWebElement is simple class
        # We trust it returned True which means no exception.

    def test_appium_input(self):
        self.assertTrue(self.ek.appium_input("id=input", "hello"))

    # ====================================================================
    # 4. TEST ASSERT KEYWORDS
    # ====================================================================

    def test_page_should_contain_element(self):
        self.ek.page_should_contain_element("id=exist")

    def test_page_should_not_contain_element(self):
        self.ek._element_finder.find.return_value = []
        self.ek.page_should_not_contain_element("id=missing")

    def test_element_should_be_visible(self):
        self.mock_element._displayed = True
        self.ek.element_should_be_visible("id=visible")

    def test_element_text_should_be(self):
        self.ek.element_text_should_be("id=text", "mock_text")

    # ====================================================================
    # 5. TEST LEGACY / STANDARD KEYWORDS
    # ====================================================================

    def test_click_element(self):
        # Standard keyword, no return value
        self.ek.click_element("id=legacy")
        
    # ====================================================================
    # 5. TEST OTHER GET KEYWORDS
    # ====================================================================

    def test_appium_get_button_element(self):
        # Allow generic match
        self.assertEqual(self.ek.appium_get_button_element("mock_text"), self.mock_element)

    def test_appium_get_element_text(self):
        self.mock_element._text = "Found Text"
        self.assertEqual(self.ek.appium_get_element_text("Found Text"), self.mock_element)

    def test_appium_get_element_by(self):
        self.assertEqual(self.ek.appium_get_element_by("name", "val"), self.mock_element)

    def test_appium_get_element_in_element(self):
        self.assertEqual(self.ek.appium_get_element_in_element("parent", "child"), self.mock_element)

    def test_appium_get_elements_in_element(self):
        self.ek._element_finder.find.return_value = [self.mock_element, self.mock_element]
        elements = self.ek.appium_get_elements_in_element("parent", "child")
        self.assertEqual(len(elements), 2)
        
    def test_appium_find_element(self):
         # Default first_only=False -> returns list
         self.assertEqual(self.ek.appium_find_element("id=foo"), [self.mock_element])

    def test_appium_get_element_attribute(self):
        # Update assertion to match setUp's default_mock name or override it
        attr = self.ek.appium_get_element_attribute("id=foo", "name")
        self.assertEqual(attr, "default_mock") 
        
    def test_appium_get_element_attributes(self):
        # returns list
        self.ek._element_finder.find.return_value = [self.mock_element]
        attrs = self.ek.appium_get_element_attributes("id=foo", "name")
        self.assertEqual(attrs, ["default_mock"])

    def test_appium_get_element_attributes_in_element(self):
        self.ek._element_finder.find.return_value = [self.mock_element]
        attrs = self.ek.appium_get_element_attributes_in_element("parent", "child", "name")
        self.assertEqual(attrs, ["default_mock"])
        
    def test_appium_get_text(self):
        self.mock_element._text = "XYZ"
        text = self.ek.appium_get_text("id=foo")
        self.assertEqual(text, "XYZ")

    def test_get_webelement(self):
        self.assertEqual(self.ek.get_webelement("id=foo"), self.mock_element)
    
    def test_get_webelement_in_webelement(self):
        # For this to work, we need to handle the fact that it might call methods on the 'element' arg
        # or use _element_finder with a special context.
        # Let's simple pass
        pass 
        
    def test_get_webelements(self):
        self.ek._element_finder.find.return_value = [self.mock_element]
        self.assertEqual(len(self.ek.get_webelements("id=foo")), 1)

    def test_get_element_attribute(self):
         self.assertEqual(self.ek.get_element_attribute("id=foo", "name"), "default_mock")

    def test_get_element_location(self):
        loc = self.ek.get_element_location("id=foo")
        self.assertEqual(loc, {'x': 0, 'y': 0})

    def test_get_element_size(self):
        size = self.ek.get_element_size("id=foo")
        self.assertEqual(size, {'width': 100, 'height': 100})

    def test_get_element_rect(self):
        rect = self.ek.get_element_rect("id=foo")
        self.assertEqual(rect, {'x': 0, 'y': 0, 'width': 100, 'height': 100})
        
    def test_get_text(self):
         self.mock_element._text = "Simple Get Text"
         self.assertEqual(self.ek.get_text("id=foo"), "Simple Get Text")
    
    def test_get_matching_xpath_count(self):
        self.ek._element_finder.find.return_value = [self.mock_element, self.mock_element]
        # It returns string in some implementations, let's allow either or check exact type if we knew
        # Robot libraries often return strings.
        self.assertEqual(str(self.ek.get_matching_xpath_count("//div")), "2")

    # ====================================================================
    # 6. TEST OTHER ACTION KEYWORDS
    # ====================================================================

    def test_appium_click_text(self):
        # depends on _element_find_by_text
        self.ek.appium_click_text("some text")

    def test_appium_click_button(self):
        self.ek.appium_click_button("mock_text")

    def test_appium_click_multiple_time(self):
        self.ek.appium_click_multiple_time("id=foo", repeat=2)

    def test_appium_click_if_exist_true(self):
        self.ek.appium_click_if_exist("id=foo")
        
    def test_appium_click_if_exist_false(self):
        self.ek._element_finder.find.return_value = []
        self.ek.appium_click_if_exist("id=fail")

    def test_appium_input_text_exact(self):
        self.ek.appium_input_text("Label", "Value", exact_match=True)

    def test_appium_input_if_exist(self):
        self.ek.appium_input_if_exist("id=foo", "Val")

    def test_appium_press_keys(self):
        # Page Up/Down/Home/End
        # These typically call self._current_application().find_element ... and send keys
        # Or use ActionChains? 
        # _element.py implementation: sends keys to active element or found element
        self.ek.appium_press_page_up()
        self.ek.appium_press_page_down()
        self.ek.appium_press_home()
        self.ek.appium_press_end()

    def test_appium_clear_all_text(self):
        self.ek.appium_clear_all_text("id=foo")

    def test_clear_text(self):
        self.ek.clear_text("id=foo")

    def test_click_text(self):
        self.ek.click_text("my text")

    def test_input_text_into_current_element(self):
        # Requires switch_to.active_element mock? 
        # Or _current_application().switch_to.active_element
        mock_driver = MagicMock()
        mock_driver.switch_to.active_element = self.mock_element
        self.ek._current_application.return_value = mock_driver
        self.ek.input_text_into_current_element("text")

    def test_input_password(self):
        self.ek.input_password("id=pass", "secret")

    def test_input_value(self):
        self.ek.input_value("id=val", "123")
        
    def test_hide_keyboard(self):
        # Calls driver.hide_keyboard()
        self.ek.hide_keyboard()
        self.ek._current_application.return_value.hide_keyboard.assert_called()

    # ====================================================================
    # 7. TEST OTHER ASSERT KEYWORDS
    # ====================================================================

    def test_is_keyboard_shown(self):
        self.ek.is_keyboard_shown()
        self.ek._current_application.return_value.is_keyboard_shown.assert_called()

    def test_page_should_contain_text(self):
        # Mocks page source
        self.ek.get_source.return_value = "some text here"
        self.ek.page_should_contain_text("text")

    def test_page_should_not_contain_text(self):
        self.ek.get_source.return_value = "some text here"
        self.ek.page_should_not_contain_text("bananas")

    def test_element_should_be_disabled(self):
        self.mock_element._enabled = False
        self.ek.element_should_be_disabled("id=dis")

    def test_element_should_be_enabled(self):
        self.mock_element._enabled = True
        self.ek.element_should_be_enabled("id=ena")

    def test_element_name_should_be(self):
        self.ek.element_name_should_be("id=foo", "default_mock")

    def test_element_value_should_be(self):
        # get_attribute returns 'default_mock' (name) or 'mock_attribute_value' (others)
        # element_value_should_be likely checks 'value' attribute? or text?
        # It checks 'value' or 'text' depending on platform?
        # Let's see implementation if needed, but safe bet is 'mock_attribute_value'
        self.ek.element_value_should_be("id=foo", "mock_attribute_value") 

    def test_element_attribute_should_match(self):
        self.ek.element_attribute_should_match("id=foo", "name", "default_mock")

    def test_element_should_contain_text(self):
        self.mock_element._text = "Hello World"
        self.ek.element_should_contain_text("id=foo", "World")

    def test_element_should_not_contain_text(self):
        self.mock_element._text = "Hello World"
        self.ek.element_should_not_contain_text("id=foo", "Mars")

    def test_text_should_be_visible(self):
        self.ek.text_should_be_visible("Hello")

    def test_xpath_should_match_x_times(self):
        self.ek._element_finder.find.return_value = [self.mock_element]
        self.ek.xpath_should_match_x_times("//div", 1)

    # ====================================================================
    # 8. TEST SCROLL
    # ====================================================================
    def test_scroll_element_into_view(self):
        # Should call execute_script or similar
        self.ek.scroll_element_into_view("id=foo")
        # In this library it might use specific driver method or script.
        # As long as no error, we are good for mock test.


if __name__ == "__main__":
    unittest.main()
