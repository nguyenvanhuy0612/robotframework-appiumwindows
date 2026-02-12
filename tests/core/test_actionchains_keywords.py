
import unittest
import sys
import os
sys.path.append(os.getcwd())
from unittest.mock import MagicMock, patch, call
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from AppiumLibrary.keywords._actionchains import _ActionChainsKeywords
import appium.webdriver


class TestResolveKey(unittest.TestCase):
    """Tests for _resolve_key helper."""

    def setUp(self):
        self.ak = _ActionChainsKeywords()

    def test_resolve_known_key(self):
        self.assertEqual(self.ak._resolve_key("CONTROL"), Keys.CONTROL)
        self.assertEqual(self.ak._resolve_key("SHIFT"), Keys.SHIFT)
        self.assertEqual(self.ak._resolve_key("ALT"), Keys.ALT)
        self.assertEqual(self.ak._resolve_key("ENTER"), Keys.ENTER)
        self.assertEqual(self.ak._resolve_key("TAB"), Keys.TAB)

    def test_resolve_key_case_insensitive(self):
        self.assertEqual(self.ak._resolve_key("control"), Keys.CONTROL)
        self.assertEqual(self.ak._resolve_key("Shift"), Keys.SHIFT)

    def test_resolve_single_char(self):
        self.assertEqual(self.ak._resolve_key("a"), "a")
        self.assertEqual(self.ak._resolve_key("Z"), "Z")
        self.assertEqual(self.ak._resolve_key("1"), "1")

    def test_resolve_unknown_key_passes_through(self):
        # Unknown multi-char strings are treated as plain text
        self.assertEqual(self.ak._resolve_key("NONEXISTENT_KEY"), "NONEXISTENT_KEY")
        self.assertEqual(self.ak._resolve_key("hello world"), "hello world")


class TestResolveElement(unittest.TestCase):
    """Tests for _resolve_element helper."""

    def setUp(self):
        self.builtin_patcher = patch('AppiumLibrary.keywords._element.BuiltIn')
        self.mock_builtin_class = self.builtin_patcher.start()
        self.mock_builtin_instance = self.mock_builtin_class.return_value
        self.mock_builtin_instance.get_variable_value.return_value = "5"

        self.ak = _ActionChainsKeywords()
        self.ak._timeout_in_secs = 5

    def tearDown(self):
        self.builtin_patcher.stop()

    def test_resolve_none_returns_none(self):
        self.assertIsNone(self.ak._resolve_element(None))

    def test_resolve_webelement_returns_same(self):
        mock_el = MagicMock(spec=WebElement)
        self.assertIs(self.ak._resolve_element(mock_el), mock_el)

    def test_resolve_string_calls_element_find(self):
        mock_el = MagicMock(spec=WebElement)
        self.ak._element_find = MagicMock(return_value=mock_el)
        result = self.ak._resolve_element("name=MyElement")
        self.assertIs(result, mock_el)
        self.ak._element_find.assert_called_once_with("name=MyElement", True, True)


class TestEnsureChain(unittest.TestCase):
    """Tests for _ensure_chain helper."""

    def setUp(self):
        self.ak = _ActionChainsKeywords()

    def test_raises_when_no_chain(self):
        with self.assertRaises(RuntimeError):
            self.ak._ensure_chain()

    def test_no_raise_when_chain_exists(self):
        self.ak._action_chain = MagicMock()
        self.ak._ensure_chain()  # should not raise


class TestOneShotKeywords(unittest.TestCase):
    """Tests for one-shot ActionChains keywords."""

    def setUp(self):
        self.builtin_patcher = patch('AppiumLibrary.keywords._element.BuiltIn')
        self.mock_builtin_class = self.builtin_patcher.start()
        self.mock_builtin_instance = self.mock_builtin_class.return_value
        self.mock_builtin_instance.get_variable_value.return_value = "5"

        self.ak = _ActionChainsKeywords()
        self.ak._timeout_in_secs = 5
        self.ak._info = MagicMock()
        self.ak._debug = MagicMock()

        self.mock_driver = MagicMock(spec=appium.webdriver.Remote)
        self.ak._current_application = MagicMock(return_value=self.mock_driver)

        self.mock_element = MagicMock(spec=WebElement)
        self.ak._element_find = MagicMock(return_value=self.mock_element)

    def tearDown(self):
        self.builtin_patcher.stop()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_click_with_locator(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.click.return_value = mock_chain
        self.ak.appium_action_click("name=Btn")
        MockAC.assert_called_once_with(self.mock_driver)
        mock_chain.click.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_click_without_locator(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.click.return_value = mock_chain
        self.ak.appium_action_click()
        mock_chain.click.assert_called_once_with(None)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_context_click(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.context_click.return_value = mock_chain
        self.ak.appium_action_context_click("name=Btn")
        mock_chain.context_click.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_double_click(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.double_click.return_value = mock_chain
        self.ak.appium_action_double_click("name=Btn")
        mock_chain.double_click.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_click_and_hold(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.click_and_hold.return_value = mock_chain
        self.ak.appium_action_click_and_hold("name=Btn")
        mock_chain.click_and_hold.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_release(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.release.return_value = mock_chain
        self.ak.appium_action_release("name=Btn")
        mock_chain.release.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_move_to_element(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.move_to_element.return_value = mock_chain
        self.ak.appium_action_move_to_element("name=Btn")
        mock_chain.move_to_element.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_move_by_offset(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.move_by_offset.return_value = mock_chain
        self.ak.appium_action_move_by_offset(100, 200)
        mock_chain.move_by_offset.assert_called_once_with(100, 200)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_drag_and_drop(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.drag_and_drop.return_value = mock_chain
        mock_target = MagicMock(spec=WebElement)
        self.ak._element_find = MagicMock(side_effect=[self.mock_element, mock_target])
        self.ak.appium_action_drag_and_drop("name=Src", "name=Tgt")
        mock_chain.drag_and_drop.assert_called_once_with(self.mock_element, mock_target)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_drag_and_drop_by_offset(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.drag_and_drop_by_offset.return_value = mock_chain
        self.ak.appium_action_drag_and_drop_by_offset("name=El", 50, 75)
        mock_chain.drag_and_drop_by_offset.assert_called_once_with(self.mock_element, 50, 75)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_key_down(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.key_down.return_value = mock_chain
        self.ak.appium_action_key_down("CONTROL")
        mock_chain.key_down.assert_called_once_with(Keys.CONTROL, None)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_key_up(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.key_up.return_value = mock_chain
        self.ak.appium_action_key_up("SHIFT")
        mock_chain.key_up.assert_called_once_with(Keys.SHIFT, None)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_send_keys(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.send_keys.return_value = mock_chain
        self.ak.appium_action_send_keys("hello")
        mock_chain.send_keys.assert_called_once_with("hello")
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_send_keys_to_element(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.send_keys_to_element.return_value = mock_chain
        self.ak.appium_action_send_keys("hello", locator="name=Input")
        mock_chain.send_keys_to_element.assert_called_once_with(self.mock_element, "hello")
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_pause(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.pause.return_value = mock_chain
        self.ak.appium_action_pause(0.5)
        mock_chain.pause.assert_called_once_with(0.5)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_scroll_to_element(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.scroll_to_element.return_value = mock_chain
        self.ak.appium_action_scroll_to_element("name=El")
        mock_chain.scroll_to_element.assert_called_once_with(self.mock_element)
        mock_chain.perform.assert_called_once()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_action_scroll_by_amount(self, MockAC):
        mock_chain = MockAC.return_value
        mock_chain.scroll_by_amount.return_value = mock_chain
        self.ak.appium_action_scroll_by_amount(0, 300)
        mock_chain.scroll_by_amount.assert_called_once_with(0, 300)
        mock_chain.perform.assert_called_once()


class TestChainBuilderKeywords(unittest.TestCase):
    """Tests for chain builder keywords."""

    def setUp(self):
        self.builtin_patcher = patch('AppiumLibrary.keywords._element.BuiltIn')
        self.mock_builtin_class = self.builtin_patcher.start()
        self.mock_builtin_instance = self.mock_builtin_class.return_value
        self.mock_builtin_instance.get_variable_value.return_value = "5"

        self.ak = _ActionChainsKeywords()
        self.ak._timeout_in_secs = 5
        self.ak._info = MagicMock()
        self.ak._debug = MagicMock()

        self.mock_driver = MagicMock(spec=appium.webdriver.Remote)
        self.ak._current_application = MagicMock(return_value=self.mock_driver)

        self.mock_element = MagicMock(spec=WebElement)
        self.ak._element_find = MagicMock(return_value=self.mock_element)

    def tearDown(self):
        self.builtin_patcher.stop()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_begin_creates_chain(self, MockAC):
        self.ak.appium_begin_action_chain()
        MockAC.assert_called_once_with(self.mock_driver)
        self.assertIsNotNone(self.ak._action_chain)

    def test_chain_methods_fail_without_begin(self):
        with self.assertRaises(RuntimeError):
            self.ak.appium_chain_click()
        with self.assertRaises(RuntimeError):
            self.ak.appium_chain_perform()

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_click(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_click("name=Btn")
        mock_chain.click.assert_called_once_with(self.mock_element)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_context_click(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_context_click("name=Btn")
        mock_chain.context_click.assert_called_once_with(self.mock_element)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_double_click(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_double_click("name=Btn")
        mock_chain.double_click.assert_called_once_with(self.mock_element)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_key_down_up(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_key_down("CONTROL")
        self.ak.appium_chain_key_up("CONTROL")
        mock_chain.key_down.assert_called_once_with(Keys.CONTROL, None)
        mock_chain.key_up.assert_called_once_with(Keys.CONTROL, None)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_send_keys(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_send_keys("hello", "ENTER")
        mock_chain.send_keys.assert_called_once_with("hello", Keys.ENTER)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_send_keys_to_element(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_send_keys_to_element("name=Input", "text")
        mock_chain.send_keys_to_element.assert_called_once_with(self.mock_element, "text")

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_move_to_element(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_move_to_element("name=El")
        mock_chain.move_to_element.assert_called_once_with(self.mock_element)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_move_by_offset(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_move_by_offset(10, 20)
        mock_chain.move_by_offset.assert_called_once_with(10, 20)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_pause(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_pause(0.5)
        mock_chain.pause.assert_called_once_with(0.5)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_perform_executes_and_clears(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_click()
        self.ak.appium_chain_perform()
        mock_chain.perform.assert_called_once()
        self.assertIsNone(self.ak._action_chain)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_reset_discards_without_performing(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_click()
        self.ak.appium_chain_reset()
        mock_chain.perform.assert_not_called()
        mock_chain.reset_actions.assert_called_once()
        self.assertIsNone(self.ak._action_chain)

    def test_chain_reset_when_no_chain(self):
        self.ak.appium_chain_reset()  # should not raise
        self.assertIsNone(self.ak._action_chain)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_multi_step_workflow(self, MockAC):
        """Test a realistic multi-step chain: Ctrl+Click."""
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_key_down("CONTROL")
        self.ak.appium_chain_click("name=Row2")
        self.ak.appium_chain_key_up("CONTROL")
        self.ak.appium_chain_perform()

        mock_chain.key_down.assert_called_once_with(Keys.CONTROL, None)
        mock_chain.click.assert_called_once_with(self.mock_element)
        mock_chain.key_up.assert_called_once_with(Keys.CONTROL, None)
        mock_chain.perform.assert_called_once()
        self.assertIsNone(self.ak._action_chain)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_drag_and_drop(self, MockAC):
        mock_chain = MockAC.return_value
        mock_target = MagicMock(spec=WebElement)
        self.ak._element_find = MagicMock(side_effect=[self.mock_element, mock_target])
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_drag_and_drop("name=Src", "name=Tgt")
        mock_chain.drag_and_drop.assert_called_once_with(self.mock_element, mock_target)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_drag_and_drop_by_offset(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_drag_and_drop_by_offset("name=El", 50, 75)
        mock_chain.drag_and_drop_by_offset.assert_called_once_with(self.mock_element, 50, 75)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_click_and_hold_release(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_click_and_hold("name=El")
        self.ak.appium_chain_release()
        mock_chain.click_and_hold.assert_called_once_with(self.mock_element)
        mock_chain.release.assert_called_once_with(None)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_scroll_to_element(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_scroll_to_element("name=El")
        mock_chain.scroll_to_element.assert_called_once_with(self.mock_element)

    @patch('AppiumLibrary.keywords._actionchains.ActionChains')
    def test_chain_scroll_by_amount(self, MockAC):
        mock_chain = MockAC.return_value
        self.ak.appium_begin_action_chain()
        self.ak.appium_chain_scroll_by_amount(0, 300)
        mock_chain.scroll_by_amount.assert_called_once_with(0, 300)


if __name__ == "__main__":
    unittest.main()
