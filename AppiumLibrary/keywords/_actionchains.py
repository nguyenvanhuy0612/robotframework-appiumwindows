# -*- coding: utf-8 -*-
"""
ActionChains keywords for Selenium/Appium WebDriver ActionChains API.

Provides both one-shot action keywords and a chain-builder pattern
for composing multi-step actions across Robot Framework keyword calls.
"""

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from .keywordgroup import KeywordGroup


class _ActionChainsKeywords(KeywordGroup):

    def __init__(self):
        self._action_chain = None

    # =========================================================================
    # Private helpers
    # =========================================================================

    def _resolve_key(self, key_name):
        """Convert a key name string (e.g., 'CONTROL', 'SHIFT') to a Keys enum value.

        If the string matches a ``Keys`` attribute it is resolved to the
        corresponding constant.  Otherwise the string is returned as-is
        (plain text for ``send_keys``).
        """
        if isinstance(key_name, str) and len(key_name) > 1:
            upper = key_name.upper()
            if hasattr(Keys, upper):
                return getattr(Keys, upper)
        return key_name

    def _resolve_element(self, locator):
        """Resolve a locator string or WebElement to a WebElement instance."""
        if locator is None:
            return None
        if isinstance(locator, WebElement):
            return locator
        return self._element_find(locator, True, True)

    def _ensure_chain(self):
        """Raise if no action chain is currently in progress."""
        if self._action_chain is None:
            raise RuntimeError(
                "No action chain in progress. Call 'Appium Begin Action Chain' first."
            )

    # =========================================================================
    # One-Shot Action Keywords
    # =========================================================================

    def appium_action_click(self, locator=None):
        """Click an element using ActionChains.

        If ``locator`` is None, clicks at the current mouse position.

        Examples:
        | Appium Action Click | name=MyElement |
        | Appium Action Click |                |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).click(element).perform()

    def appium_action_context_click(self, locator=None):
        """Right-click an element using ActionChains.

        Examples:
        | Appium Action Context Click | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).context_click(element).perform()

    def appium_action_double_click(self, locator=None):
        """Double-click an element using ActionChains.

        Examples:
        | Appium Action Double Click | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).double_click(element).perform()

    def appium_action_click_and_hold(self, locator=None):
        """Click-and-hold on an element using ActionChains.

        Examples:
        | Appium Action Click And Hold | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).click_and_hold(element).perform()

    def appium_action_release(self, locator=None):
        """Release a held click using ActionChains.

        Examples:
        | Appium Action Release | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).release(element).perform()

    def appium_action_move_to_element(self, locator):
        """Move mouse to the center of an element.

        Examples:
        | Appium Action Move To Element | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).move_to_element(element).perform()

    def appium_action_move_by_offset(self, x_offset, y_offset):
        """Move mouse by offset from current position.

        Examples:
        | Appium Action Move By Offset | 100 | 200 |
        """
        driver = self._current_application()
        ActionChains(driver).move_by_offset(int(x_offset), int(y_offset)).perform()

    def appium_action_drag_and_drop(self, source_locator, target_locator):
        """Drag source element to target element.

        Examples:
        | Appium Action Drag And Drop | name=Source | name=Target |
        """
        source = self._resolve_element(source_locator)
        target = self._resolve_element(target_locator)
        driver = self._current_application()
        ActionChains(driver).drag_and_drop(source, target).perform()

    def appium_action_drag_and_drop_by_offset(self, locator, x_offset, y_offset):
        """Drag element by pixel offset.

        Examples:
        | Appium Action Drag And Drop By Offset | name=MyElement | 100 | 50 |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).drag_and_drop_by_offset(
            element, int(x_offset), int(y_offset)
        ).perform()

    def appium_action_key_down(self, key, locator=None):
        """Press a modifier key down.

        ``key`` is a key name string such as ``CONTROL``, ``SHIFT``, ``ALT``.

        Examples:
        | Appium Action Key Down | CONTROL |                |
        | Appium Action Key Down | SHIFT   | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).key_down(self._resolve_key(key), element).perform()

    def appium_action_key_up(self, key, locator=None):
        """Release a modifier key.

        Examples:
        | Appium Action Key Up | CONTROL |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).key_up(self._resolve_key(key), element).perform()

    def appium_action_send_keys(self, *keys, locator=None):
        """Send keys to the active element, or to a specific element if locator given.

        Keys can be regular text or special key names (e.g., ENTER, TAB).

        Examples:
        | Appium Action Send Keys | Hello World |                        |
        | Appium Action Send Keys | ENTER       |                        |
        | Appium Action Send Keys | some text   | locator=name=MyInput   |
        """
        resolved = [self._resolve_key(k) for k in keys]
        driver = self._current_application()
        if locator:
            element = self._resolve_element(locator)
            ActionChains(driver).send_keys_to_element(element, *resolved).perform()
        else:
            ActionChains(driver).send_keys(*resolved).perform()

    def appium_action_pause(self, seconds):
        """Pause for specified duration within an ActionChains context.

        Examples:
        | Appium Action Pause | 0.5 |
        """
        driver = self._current_application()
        ActionChains(driver).pause(float(seconds)).perform()

    def appium_action_scroll_to_element(self, locator):
        """Scroll to bring element into view using ActionChains.

        Examples:
        | Appium Action Scroll To Element | name=MyElement |
        """
        element = self._resolve_element(locator)
        driver = self._current_application()
        ActionChains(driver).scroll_to_element(element).perform()

    def appium_action_scroll_by_amount(self, delta_x, delta_y):
        """Scroll by pixel amount.

        Examples:
        | Appium Action Scroll By Amount | 0 | 300 |
        """
        driver = self._current_application()
        ActionChains(driver).scroll_by_amount(int(delta_x), int(delta_y)).perform()

    # =========================================================================
    # Chain Builder Keywords
    # =========================================================================

    def appium_begin_action_chain(self):
        """Create a new action chain. Discards any existing pending chain.

        Examples:
        | Appium Begin Action Chain |
        """
        driver = self._current_application()
        self._action_chain = ActionChains(driver)
        self._info("Action chain started")

    def appium_chain_click(self, locator=None):
        """Add a click action to the pending chain.

        Examples:
        | Appium Chain Click |                |
        | Appium Chain Click | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.click(element)

    def appium_chain_context_click(self, locator=None):
        """Add a right-click action to the pending chain.

        Examples:
        | Appium Chain Context Click | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.context_click(element)

    def appium_chain_double_click(self, locator=None):
        """Add a double-click action to the pending chain.

        Examples:
        | Appium Chain Double Click | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.double_click(element)

    def appium_chain_click_and_hold(self, locator=None):
        """Add a click-and-hold action to the pending chain.

        Examples:
        | Appium Chain Click And Hold | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.click_and_hold(element)

    def appium_chain_release(self, locator=None):
        """Add a release action to the pending chain.

        Examples:
        | Appium Chain Release | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.release(element)

    def appium_chain_move_to_element(self, locator):
        """Add a move-to-element action to the pending chain.

        Examples:
        | Appium Chain Move To Element | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.move_to_element(element)

    def appium_chain_move_by_offset(self, x_offset, y_offset):
        """Add a move-by-offset action to the pending chain.

        Examples:
        | Appium Chain Move By Offset | 100 | 200 |
        """
        self._ensure_chain()
        self._action_chain.move_by_offset(int(x_offset), int(y_offset))

    def appium_chain_drag_and_drop(self, source_locator, target_locator):
        """Add a drag-and-drop action to the pending chain.

        Examples:
        | Appium Chain Drag And Drop | name=Source | name=Target |
        """
        self._ensure_chain()
        source = self._resolve_element(source_locator)
        target = self._resolve_element(target_locator)
        self._action_chain.drag_and_drop(source, target)

    def appium_chain_drag_and_drop_by_offset(self, locator, x_offset, y_offset):
        """Add a drag-and-drop-by-offset action to the pending chain.

        Examples:
        | Appium Chain Drag And Drop By Offset | name=MyElement | 100 | 50 |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.drag_and_drop_by_offset(
            element, int(x_offset), int(y_offset)
        )

    def appium_chain_key_down(self, key, locator=None):
        """Add a key-down action to the pending chain.

        ``key`` is a key name string such as ``CONTROL``, ``SHIFT``, ``ALT``.

        Examples:
        | Appium Chain Key Down | CONTROL |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.key_down(self._resolve_key(key), element)

    def appium_chain_key_up(self, key, locator=None):
        """Add a key-up action to the pending chain.

        Examples:
        | Appium Chain Key Up | CONTROL |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.key_up(self._resolve_key(key), element)

    def appium_chain_send_keys(self, *keys):
        """Add send-keys to the pending chain (sends to active element).

        Examples:
        | Appium Chain Send Keys | Hello | ENTER |
        """
        self._ensure_chain()
        resolved = [self._resolve_key(k) for k in keys]
        self._action_chain.send_keys(*resolved)

    def appium_chain_send_keys_to_element(self, locator, *keys):
        """Add send-keys-to-element to the pending chain.

        Examples:
        | Appium Chain Send Keys To Element | name=MyInput | Hello |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        resolved = [self._resolve_key(k) for k in keys]
        self._action_chain.send_keys_to_element(element, *resolved)

    def appium_chain_pause(self, seconds):
        """Add a pause to the pending chain.

        Examples:
        | Appium Chain Pause | 0.5 |
        """
        self._ensure_chain()
        self._action_chain.pause(float(seconds))

    def appium_chain_scroll_to_element(self, locator):
        """Add a scroll-to-element action to the pending chain.

        Examples:
        | Appium Chain Scroll To Element | name=MyElement |
        """
        self._ensure_chain()
        element = self._resolve_element(locator)
        self._action_chain.scroll_to_element(element)

    def appium_chain_scroll_by_amount(self, delta_x, delta_y):
        """Add a scroll-by-amount action to the pending chain.

        Examples:
        | Appium Chain Scroll By Amount | 0 | 300 |
        """
        self._ensure_chain()
        self._action_chain.scroll_by_amount(int(delta_x), int(delta_y))

    def appium_chain_perform(self):
        """Execute and clear the pending action chain.

        Raises RuntimeError if no chain has been started.

        Examples:
        | Appium Chain Perform |
        """
        self._ensure_chain()
        self._info("Performing action chain")
        self._action_chain.perform()
        self._action_chain = None

    def appium_chain_reset(self):
        """Discard the pending action chain without executing it.

        Examples:
        | Appium Chain Reset |
        """
        if self._action_chain is not None:
            self._action_chain.reset_actions()
        self._action_chain = None
        self._info("Action chain reset")
