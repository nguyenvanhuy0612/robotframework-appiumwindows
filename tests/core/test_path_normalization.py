
import unittest
import os
import sys
import pathlib
from unittest.mock import patch, MagicMock

# Mock dependencies that are not installed in this environment
# We need to mock specific submodules so that 'from robot.foo import Bar' works
mocks = [
    'robot',
    'robot.utils',
    'robot.libraries',
    'robot.libraries.BuiltIn',
    'robot.api',
    'robot.api.deco',
    'appium',
    'appium.webdriver',
    'appium.webdriver.common',
    'appium.webdriver.common.appiumby',
    'appium.webdriver.mobilecommand',
    'appium.options.common',
    'selenium',
    'selenium.common',
    'selenium.webdriver',
    'selenium.webdriver.common',
    'selenium.webdriver.common.action_chains',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.remote',
    'selenium.webdriver.remote.webelement',
]

for m in mocks:
    sys.modules[m] = MagicMock()

# Ensure nested access works (e.g. robot.utils)
sys.modules['robot'].utils = sys.modules['robot.utils']
sys.modules['robot'].libraries = sys.modules['robot.libraries']
sys.modules['robot.libraries'].BuiltIn = sys.modules['robot.libraries.BuiltIn']
sys.modules['selenium'].common = sys.modules['selenium.common']
sys.modules['selenium'].webdriver = sys.modules['selenium.webdriver']
sys.modules['selenium.webdriver'].remote = sys.modules['selenium.webdriver.remote']
sys.modules['appium'].webdriver = sys.modules['appium.webdriver']
sys.modules['appium'].webdriver.common = sys.modules['appium.webdriver.common']
sys.modules['appium'].webdriver.mobilecommand = sys.modules['appium.webdriver.mobilecommand']

# Adjust path to allow importing AppiumLibrary
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from AppiumLibrary.keywords._windows import _WindowsKeywords

class TestWindowsPathNormalization(unittest.TestCase):

    def setUp(self):
        self.keywords = _WindowsKeywords()

    def test_01_simple_path_default_sep(self):
        """Should normalize simple path using default separator (backslash)"""
        result = self.keywords.appium_normalize_path("foo/bar")
        self.assertEqual(result, "foo\\bar")

    def test_02_simple_path_explicit_win_sep(self):
        """Should normalize simple path using explicit Windows separator"""
        result = self.keywords.appium_normalize_path("foo/bar", sep="\\")
        self.assertEqual(result, "foo\\bar")

    def test_03_simple_path_posix_sep(self):
        """Should normalize to forward slashes when sep='/'"""
        result = self.keywords.appium_normalize_path("foo\\bar", sep="/")
        self.assertEqual(result, "foo/bar")

    def test_04_mixed_separators_to_win(self):
        """Should handle mixed separators resolving to Windows"""
        result = self.keywords.appium_normalize_path("foo/bar\\baz", sep="\\")
        self.assertEqual(result, "foo\\bar\\baz")

    def test_05_mixed_separators_to_posix(self):
        """Should handle mixed separators resolving to Posix"""
        result = self.keywords.appium_normalize_path("foo/bar\\baz", sep="/")
        self.assertEqual(result, "foo/bar/baz")

    def test_06_redundant_separators(self):
        """Should collapse redundant separators"""
        result = self.keywords.appium_normalize_path("foo//bar\\\\baz", sep="\\")
        self.assertEqual(result, "foo\\bar\\baz")

    def test_07_parent_directory_resolution(self):
        """Should resolve '..' correctly"""
        result = self.keywords.appium_normalize_path("foo/bar/../baz", sep="\\")
        self.assertEqual(result, "foo\\baz")

    def test_08_current_directory_resolution(self):
        """Should resolve '.' correctly"""
        result = self.keywords.appium_normalize_path("./foo", sep="\\")
        self.assertEqual(result, "foo")

    def test_09_trailing_separators(self):
        """Should strip trailing separators"""
        result = self.keywords.appium_normalize_path("foo/bar/", sep="\\")
        self.assertEqual(result, "foo\\bar")

    def test_10_absolute_windows_path(self):
        """Should handle absolute Windows paths preserving drive letter"""
        result = self.keywords.appium_normalize_path("C:\\Users\\Robot", sep="\\")
        self.assertEqual(result, "C:\\Users\\Robot")

    def test_11_absolute_posix_path(self):
        """Should handle absolute Posix paths"""
        result = self.keywords.appium_normalize_path("/usr/bin/python", sep="/")
        self.assertEqual(result, "/usr/bin/python")

    def test_12_tilde_expansion(self):
        """Should expand '~' to user home directory"""
        # Mock expanduser to return a fixed path for testing consistency
        expected_home = r"C:\Users\Tester"
        with patch("os.path.expanduser", return_value=os.path.join(expected_home, "Documents")):
            result = self.keywords.appium_normalize_path("~/Documents", sep="\\")
            self.assertTrue(result.endswith("Tester\\Documents") or result.endswith("Tester/Documents"))

    def test_13_pathlib_input(self):
        """Should accept pathlib.Path objects"""
        p = pathlib.Path("foo/bar")
        result = self.keywords.appium_normalize_path(p, sep="\\")
        self.assertEqual(result, "foo\\bar")

    def test_14_backtick_escaping_simple(self):
        """Should escape single backticks for PowerShell"""
        result = self.keywords.appium_normalize_path("foo`bar", sep="\\")
        self.assertEqual(result, "foo``bar")

    def test_15_backtick_pre_escaped(self):
        """Should NOT double-escape already escaped backticks"""
        result = self.keywords.appium_normalize_path("foo``bar", sep="\\")
        self.assertEqual(result, "foo``bar")

    def test_16_backtick_at_ends(self):
        """Should escape backticks at start/end of path components"""
        result = self.keywords.appium_normalize_path("`foo`", sep="\\")
        self.assertEqual(result, "``foo``")

    def test_17_disable_backtick_escaping(self):
        """Should ignore backticks if escape_backtick=False"""
        result = self.keywords.appium_normalize_path("foo`bar", sep="\\", escape_backtick=False)
        self.assertEqual(result, "foo`bar")

    def test_18_case_normalization_true(self):
        """Should lowercase path if case_normalize=True (Windows behavior)"""
        result = self.keywords.appium_normalize_path("FOO/Bar", sep="\\", case_normalize=True)
        self.assertEqual(result, "foo\\bar")

    def test_19_case_normalization_false(self):
        """Should preserve case if case_normalize=False"""
        result = self.keywords.appium_normalize_path("FOO/Bar", sep="\\", case_normalize=False)
        self.assertEqual(result, "FOO\\Bar")

    def test_20_empty_path(self):
        """Should handle empty strings by defaulting to current directory"""
        result = self.keywords.appium_normalize_path("", sep="\\")
        self.assertEqual(result, ".")

    def test_21_none_path(self):
        """Should handle None by defaulting to current directory"""
        result = self.keywords.appium_normalize_path(None, sep="\\")
        self.assertEqual(result, ".")
    
    def test_22_spaces_in_path(self):
        """Should handle spaces correctly"""
        result = self.keywords.appium_normalize_path("Program Files/Robot Framework", sep="\\")
        self.assertEqual(result, "Program Files\\Robot Framework")

    def test_23_weird_mixed_slashes_cleanup(self):
        """Should handle very messy input paths"""
        # Input: C:\Users/./Public//Documents\..\Downloads
        # Expected: C:\Users\Public\Downloads
        path = r"C:\Users/./Public//Documents\..\Downloads"
        result = self.keywords.appium_normalize_path(path, sep="\\")
        self.assertEqual(result, r"C:\Users\Public\Downloads")

if __name__ == "__main__":
    unittest.main()
