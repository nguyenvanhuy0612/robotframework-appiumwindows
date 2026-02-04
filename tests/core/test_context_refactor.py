
import unittest
from unittest.mock import MagicMock, patch
import sys
import types

# MOCK DEPENDENCIES BEFORE IMPORTING TARGET MODULE
# Robot
mock_robot = types.ModuleType("robot")
mock_robot_libraries = types.ModuleType("robot.libraries")
mock_builtin = types.ModuleType("robot.libraries.BuiltIn")
mock_robot_utils = types.ModuleType("robot.utils")

sys.modules["robot"] = mock_robot

sys.modules["robot.libraries"] = mock_robot_libraries
sys.modules["robot.libraries.BuiltIn"] = mock_builtin
sys.modules["robot.utils"] = mock_robot_utils

mock_robot_api = types.ModuleType("robot.api")
sys.modules["robot.api"] = mock_robot_api
mock_robot_api.logger = MagicMock()

# Create BuiltIn class mock
class MockBuiltIn:
    def get_variable_value(self, name, default=None):
        return default
    def log(self, *args):
        pass




mock_builtin.BuiltIn = MagicMock(return_value=MockBuiltIn())
mock_builtin.RobotNotRunningError = Exception
mock_robot_utils.timestr_to_secs = MagicMock(return_value=1.0)
mock_robot_utils.abspath = MagicMock(return_value="/mock/path")
mock_robot_utils.ConnectionCache = MagicMock()

# Selenium
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
mock_selenium_webdriver.Keys = MagicMock()
class MockWebElement:
    def __init__(self, name="mock_element"):
        self.name = name
    def __repr__(self):
        return f"<MockWebElement {self.name}>"
mock_selenium_webelement.WebElement = MockWebElement





# Appium
mock_appium = types.ModuleType("appium")
sys.modules["appium"] = mock_appium

mock_appium_webdriver = types.ModuleType("appium.webdriver")
sys.modules["appium.webdriver"] = mock_appium_webdriver
mock_appium.webdriver = mock_appium_webdriver

mock_appium_options = types.ModuleType("appium.options")
sys.modules["appium.options"] = mock_appium_options
mock_appium.options = mock_appium_options

mock_appium_options_common = types.ModuleType("appium.options.common")
sys.modules["appium.options.common"] = mock_appium_options_common
mock_appium_options.common = mock_appium_options_common

mock_appium_options_common.AppiumOptions = MagicMock()

mock_appium_webdriver_common = types.ModuleType("appium.webdriver.common")
sys.modules["appium.webdriver.common"] = mock_appium_webdriver_common
mock_appium_webdriver.common = mock_appium_webdriver_common

mock_appium_webdriver_common_appiumby = types.ModuleType("appium.webdriver.common.appiumby")
sys.modules["appium.webdriver.common.appiumby"] = mock_appium_webdriver_common_appiumby
mock_appium_webdriver_common.appiumby = mock_appium_webdriver_common_appiumby


mock_appium_webdriver_common_appiumby.AppiumBy = MagicMock()

mock_appium_webdriver_mobilecommand = types.ModuleType("appium.webdriver.mobilecommand")
sys.modules["appium.webdriver.mobilecommand"] = mock_appium_webdriver_mobilecommand
mock_appium_webdriver.mobilecommand = mock_appium_webdriver_mobilecommand
mock_appium_webdriver_mobilecommand.MobileCommand = MagicMock()

# AppiumLibrary
# We do NOT mock "AppiumLibrary" itself because we want to load the real "AppiumLibrary.keywords._element" module
# However, we DO want to mock "AppiumLibrary.locators" to avoid dependency issues.
mock_appiumlibrary_locators = types.ModuleType("AppiumLibrary.locators")
sys.modules["AppiumLibrary.locators"] = mock_appiumlibrary_locators

class MockElementFinder:
    def find(self, application, locator, tag):
        return []

mock_appiumlibrary_locators.ElementFinder = MagicMock(return_value=MockElementFinder())

# Import the module under test
# We need to ensure we can import from the relative path if this script is run from project root
import os
sys.path.append(os.getcwd())

# We also need to mock .keywordgroup.KeywordGroup because relative import might fail or we want to control it
# But since the file exists, we can try to import it naturally or mock it.
# Let's rely on the real file if possible, or mock it if it has heavy dependencies.
# The real file uses some decorators, which should be fine.

from AppiumLibrary.keywords._element import _ElementKeywords

class TestElementContext(unittest.TestCase):
    def setUp(self):
        self.ek = _ElementKeywords()
        # Mock internal helpers to isolate context logic
        self.ek._element_finder = MagicMock()
        self.ek._current_application = MagicMock(return_value="mock_app")
        # Mock _invoke_original to bypass retry decorators or other complexities if needed
        # But _ElementKeywords inherits from KeywordGroup which has _invoke_original.
        # We'll mock it for 'appium_get_elements' calls used in finding context.

        self.ek._invoke_original = MagicMock()
        self.ek._info = MagicMock()
        self.ek._debug = MagicMock()
        self.ek._warn = MagicMock()

    def test_initial_context(self):
        """Test initial context state."""
        # BEFORE REFACTOR: self._context is None
        # AFTER REFACTOR: self._context should be {}
        # We will adjust this test assertion as we refactor.
        # For now, let's just print it to see current state.
        print(f"Initial Context: {self.ek._context}")

    def test_set_search_context_basic(self):
        """Test setting search context with a simple locator."""
        locator = "id=container"
        mock_element = MockWebElement("container_element")
        
        # Setup mock return for finding the context element
        # Logic in refactor: uses _invoke_original("appium_get_elements", ...) -> _element_find -> _element_finder.find
        self.ek._element_finder.find.return_value = [mock_element]
        
        # Unmock _invoke_original to use the real implementation (inherited from KeywordGroup)
        del self.ek._invoke_original

        # Call set_search_context
        # New signature: set_search_context(self, context, reference=None, timeout=20)
        self.ek.set_search_context(locator, timeout=5)

        # Check state matches expected structure
        # After refactor, we expect: {'element': mock_element, 'locator': locator}
        print(f"Context after set: {self.ek._context}")
        
        self.assertIsInstance(self.ek._context, dict)
        self.assertEqual(self.ek._context['element'], mock_element)
        self.assertEqual(self.ek._context['locator'], locator)

if __name__ == "__main__":
    unittest.main()
