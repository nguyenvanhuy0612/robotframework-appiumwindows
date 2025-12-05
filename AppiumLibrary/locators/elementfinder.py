# -*- coding: utf-8 -*-
import fnmatch
import re
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from appium.webdriver import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from robot.api import logger

from AppiumLibrary import utils


class ElementFinder:
    """Element finder for Appium-based mobile and desktop testing.

    Provides various strategies for locating elements using different locator types
    and supports advanced filtering with extra attribute matching.
    """

    def __init__(self) -> None:
        self._strategies: Dict[str, Callable[..., List[WebElement]]] = {
            'identifier': self._find_by_identifier,
            'id': self._find_by_id,
            'name': self._find_by_name,
            'xpath': self._find_by_xpath,
            'class': self._find_by_class_name,
            'accessibility_id': self._find_element_by_accessibility_id,
            'android': self._find_by_android,
            'viewtag': self._find_by_android_viewtag,
            'data_matcher': self._find_by_android_data_matcher,
            'view_matcher': self._find_by_android_view_matcher,
            'ios': self._find_by_ios,
            'css': self._find_by_css_selector,
            'jquery': self._find_by_sizzle_selector,
            'predicate': self._find_by_ios_predicate,
            'chain': self._find_by_chain,
            'default': self._find_by_default
        }

    def find_extra(
        self,
        application: Any,
        locator: Union[str, Dict[str, Any]],
        tag: Optional[str] = None
    ) -> List[WebElement]:
        """Find elements using enhanced locator with extra attribute filters.

        Supports compound locators with primary locator and additional attribute
        matching patterns using AND logic.

        Args:
            application: WebDriver application instance
            locator: Locator string or dict with 'locator' and 'extra' keys
            tag: Optional tag filter for elements

        Returns:
            List of WebElements matching all criteria

        Raises:
            ValueError: If application or locator is invalid

        Example:
            # Simple locator
            find_extra(app, "xpath=//button")

            # Compound locator with extra filters
            find_extra(app, "xpath=//button | name.lower=submit | class=*btn*")
        """
        if application is None:
            raise ValueError("Application instance cannot be None")
        if locator is None:
            raise ValueError("Locator cannot be None")

        normalized_locator = self._normalize_locator(locator)
        primary_locator = normalized_locator.get("locator")
        extra_filters = normalized_locator.get("extra", [])

        # Find elements using primary locator
        elements = self.find(application, primary_locator, tag)

        # Apply extra filters if any
        if extra_filters:
            elements = [el for el in elements if self._match_extra(el, extra_filters)]

        return elements

    def find(
        self,
        application: Any,
        locator: str,
        tag: Optional[str] = None
    ) -> List[WebElement]:
        """Find elements using the specified locator strategy.

        Args:
            application: WebDriver application instance
            locator: Element locator string (e.g., "id=myId", "xpath=//div")
            tag: Optional tag filter for elements

        Returns:
            List of found WebElements

        Raises:
            ValueError: If application or locator is invalid, or strategy not supported
        """
        if application is None:
            raise ValueError("Application instance cannot be None")
        if not locator or not isinstance(locator, str):
            raise ValueError(f"Locator must be a non-empty string, got: {locator}")

        prefix, criteria = self._parse_locator(locator)
        prefix = 'default' if prefix is None else prefix
        strategy = self._strategies.get(prefix)
        if strategy is None:
            available_strategies = sorted(self._strategies.keys())
            raise ValueError(
                f"Unsupported locator strategy '{prefix}'. "
                f"Available strategies: {', '.join(available_strategies)}. "
                f"Use format 'strategy=value' (e.g., 'id=myId', 'xpath=//div')."
            )

        normalized_tag, constraints = self._get_tag_and_constraints(tag)
        return strategy(application, criteria, normalized_tag, constraints)

    def _find_and_filter(
        self,
        application: Any,
        by: str,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Helper method to find elements by locator strategy and apply filters.

        Args:
            application: WebDriver application instance
            by: AppiumBy locator strategy
            criteria: Locator criteria/value
            tag: Optional tag filter
            constraints: Attribute constraints

        Returns:
            Filtered list of WebElements
        """
        elements = application.find_elements(by=by, value=criteria)
        return self._filter_elements(elements, tag, constraints)

    # Strategy routines, private

    def _find_by_identifier(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by identifier (searches both ID and NAME attributes)."""
        elements = self._normalize_result(application.find_elements(by=AppiumBy.ID, value=criteria))
        elements.extend(self._normalize_result(application.find_elements(by=AppiumBy.NAME, value=criteria)))
        return self._filter_elements(elements, tag, constraints)

    def _find_by_id(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by ID attribute."""
        return self._find_and_filter(application, AppiumBy.ID, criteria, tag, constraints)

    def _find_by_name(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by NAME attribute."""
        return self._find_and_filter(application, AppiumBy.NAME, criteria, tag, constraints)

    def _find_by_xpath(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by XPath expression."""
        return self._find_and_filter(application, AppiumBy.XPATH, criteria, tag, constraints)

    def _find_by_dom(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by executing JavaScript DOM query."""
        result = application.execute_script("return %s;" % criteria)
        if result is None:
            return []
        if not isinstance(result, list):
            result = [result]
        return self._filter_elements(result, tag, constraints)

    def _find_by_sizzle_selector(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements using jQuery/Sizzle selector syntax."""
        js = "return jQuery('%s').get();" % criteria.replace("'", "\\'")
        return self._filter_elements(
            application.execute_script(js),
            tag, constraints)

    def _find_by_link_text(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by exact link text."""
        return self._find_and_filter(application, AppiumBy.LINK_TEXT, criteria, tag, constraints)

    def _find_by_css_selector(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by CSS selector."""
        return self._find_and_filter(application, AppiumBy.CSS_SELECTOR, criteria, tag, constraints)

    def _find_by_tag_name(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by HTML tag name."""
        return self._find_and_filter(application, AppiumBy.TAG_NAME, criteria, tag, constraints)

    def _find_by_class_name(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by CSS class name."""
        return self._find_and_filter(application, AppiumBy.CLASS_NAME, criteria, tag, constraints)

    def _find_element_by_accessibility_id(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements by accessibility ID."""
        return self._find_and_filter(application, AppiumBy.ACCESSIBILITY_ID, criteria, tag, constraints)

    def _find_by_android(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by UI Automator."""
        return self._find_and_filter(application, AppiumBy.ANDROID_UIAUTOMATOR, criteria, tag, constraints)

    def _find_by_android_viewtag(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by its view tag (Espresso only)."""
        return self._find_and_filter(application, AppiumBy.ANDROID_VIEWTAG, criteria, tag, constraints)

    def _find_by_android_data_matcher(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by Android Data Matcher (Espresso only)."""
        return self._find_and_filter(application, AppiumBy.ANDROID_DATA_MATCHER, criteria, tag, constraints)

    def _find_by_android_view_matcher(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by Android View Matcher (Espresso only)."""
        return self._find_and_filter(application, AppiumBy.ANDROID_VIEW_MATCHER, criteria, tag, constraints)

    def _find_by_ios(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by UI Automation."""
        return self._find_and_filter(application, AppiumBy.IOS_UIAUTOMATION, criteria, tag, constraints)

    def _find_by_ios_predicate(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by iOS NSPredicateString."""
        return self._find_and_filter(application, AppiumBy.IOS_PREDICATE, criteria, tag, constraints)

    def _find_by_chain(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find element matches by iOS Class Chain."""
        return self._find_and_filter(application, AppiumBy.IOS_CLASS_CHAIN, criteria, tag, constraints)

    def _find_by_default(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Default locator strategy - uses xpath if criteria looks like xpath, otherwise id."""
        if self._is_xpath(criteria):
            return self._find_by_xpath(application, criteria, tag, constraints)
        # Use id instead of _find_by_key_attrs since iOS and Android internal id alternatives are
        # different and inside appium python client. Need to expose these and improve in order to make
        # _find_by_key_attrs useful.
        return self._find_by_id(application, criteria, tag, constraints)

    # TODO: Not in use after conversion from Selenium2Library need to make more use of multiple auto selector strategy
    def _find_by_key_attrs(
        self,
        application: Any,
        criteria: str,
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Find elements using key attributes strategy (currently unused)."""
        # Get key attributes for the specified tag or default
        key_attributes = self._key_attrs.get(None)
        if tag is not None:
            key_attributes = self._key_attrs.get(tag, key_attributes)

        # Build XPath components
        escaped_criteria = utils.escape_xpath_value(criteria)
        xpath_tag = tag if tag is not None else '*'

        # Create constraint conditions
        constraint_conditions = [f"@{name}='{value}'" for name, value in constraints.items()]

        # Create search conditions for key attributes
        search_conditions = [f"{attr}={escaped_criteria}" for attr in key_attributes]
        search_conditions.extend(self._get_attrs_with_url(key_attributes, criteria, application))

        # Build final XPath expression
        constraints_part = ' and '.join(constraint_conditions) + ' and ' if constraint_conditions else ''
        search_part = ' or '.join(search_conditions)
        xpath_expression = f"//{xpath_tag}[{constraints_part}({search_part})]"

        return self._normalize_result(application.find_elements(by=AppiumBy.XPATH, value=xpath_expression))

    # Private
    _key_attrs = {
        None: ['@id', '@name'],
        'a': ['@id', '@name', '@href', 'normalize-space(descendant-or-self::text())'],
        'img': ['@id', '@name', '@src', '@alt'],
        'input': ['@id', '@name', '@value', '@src'],
        'button': ['@id', '@name', '@value', 'normalize-space(descendant-or-self::text())']
    }

    def _get_tag_and_constraints(self, tag: Optional[str]) -> Tuple[Optional[str], Dict[str, str]]:
        """Convert user-friendly tag names to HTML tags and extract constraints."""
        if tag is None:
            return None, {}

        tag = tag.lower()
        constraints = {}
        if tag == 'link':
            tag = 'a'
        elif tag == 'image':
            tag = 'img'
        elif tag == 'list':
            tag = 'select'
        elif tag == 'radio button':
            tag = 'input'
            constraints['type'] = 'radio'
        elif tag == 'checkbox':
            tag = 'input'
            constraints['type'] = 'checkbox'
        elif tag == 'text field':
            tag = 'input'
            constraints['type'] = 'text'
        elif tag == 'file upload':
            tag = 'input'
            constraints['type'] = 'file'
        return tag, constraints

    def _element_matches(self, element: WebElement, tag: Optional[str], constraints: Dict[str, str]) -> bool:
        """Check if an element matches the specified tag and constraints."""
        if tag is not None and element.tag_name.lower() != tag:
            return False
        for name, value in constraints.items():
            if element.get_attribute(name) != value:
                return False
        return True

    def _filter_elements(
        self,
        elements: List[WebElement],
        tag: Optional[str],
        constraints: Dict[str, str]
    ) -> List[WebElement]:
        """Filter elements by tag and attribute constraints."""
        elements = self._normalize_result(elements)
        if tag is None:
            return elements
        return list(filter(
            lambda element: self._element_matches(element, tag, constraints),
            elements))

    def _get_attrs_with_url(self, key_attrs: List[str], criteria: str, browser: Any) -> List[str]:
        """Generate xpath attribute selectors for URL-based attributes."""
        url_selectors = []
        base_url = None
        escaped_url = None

        for attr in ['@src', '@href']:
            if attr in key_attrs:
                # Lazy initialization of URL strings
                if base_url is None:
                    base_url = self._get_base_url(browser) + "/" + criteria
                    escaped_url = utils.escape_xpath_value(base_url)
                url_selectors.append(f"{attr}={escaped_url}")

        return url_selectors

    def _get_base_url(self, browser: Any) -> str:
        """Extract base URL from browser's current URL."""
        url = browser.get_current_url()
        if '/' in url:
            url = '/'.join(url.split('/')[:-1])
        return url

    def _parse_locator(self, locator: str) -> Tuple[Optional[str], str]:
        """Parse locator string into prefix and criteria."""
        prefix = None
        criteria = locator
        if not self._is_xpath(locator):
            locator_parts = locator.partition('=')
            if len(locator_parts[1]) > 0:
                prefix = locator_parts[0].strip().lower()
                criteria = locator_parts[2].strip()
        return (prefix, criteria)

    def _is_xpath(self, locator: str) -> bool:
        """Check if locator string appears to be an XPath expression."""
        return bool(locator and locator.startswith('/'))

    def _normalize_result(self, elements: Any) -> List[WebElement]:
        """Normalize WebDriver find results to a list of WebElements."""
        if not isinstance(elements, list):
            logger.debug("WebDriver find returned %s" % elements)
            return []
        return elements

    def _normalize_locator(self, raw_locator: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize locator input into standard form.

        Args:
            raw_locator: Raw locator input (string or dict)

        Returns:
            Normalized locator dict with 'locator' and 'extra' keys

        Raises:
            TypeError: If locator type is unsupported
            ValueError: If locator is invalid
        """
        if isinstance(raw_locator, str):
            return {"locator": raw_locator, "extra": []}

        if isinstance(raw_locator, dict):
            locator = raw_locator.get("locator")
            extra = raw_locator.get("extra")

            # Normalize extra filters to list format
            if isinstance(extra, str):
                extra = [extra]
            elif extra is None:
                extra = []
            elif not isinstance(extra, list):
                raise TypeError(
                    f"Invalid 'extra' type: {type(extra).__name__}. "
                    "Expected list of strings or single string."
                )

            # Validate locator is not empty
            if not locator or not isinstance(locator, str) or locator.strip() == "":
                raise ValueError(
                    f"Invalid locator: '{locator}'. Locator must be a non-empty string."
                )

            return {"locator": locator, "extra": extra}

        raise TypeError(
            f"Unsupported locator type: {type(raw_locator).__name__}. "
            "Expected string locator or dict with 'locator' and 'extra' keys."
        )

    def _match_pattern(self, element: Optional[WebElement], pattern: str) -> bool:
        """Match element attribute against a pattern rule.

        Supports exact, glob, regex, and case-insensitive matching.

        Args:
            element: WebElement to check (None returns False)
            pattern: Pattern string in format "attribute[=mode]=value"

        Returns:
            True if pattern matches, False otherwise

        Examples:
            "text=Hello"             # glob match (default)
            "text.exact=Hello"       # exact match
            "id.regex=^btn_[0-9]+$"  # regex match
            "name.lower=submit"      # case-insensitive
        """
        if element is None:
            return False

        if "=" not in pattern:
            return False

        # Parse pattern into key, mode, and expected value
        raw_key, expected = pattern.split("=", 1)
        raw_key, expected = raw_key.strip(), expected.strip()

        # Extract matching mode (default is glob)
        if "." in raw_key:
            key, mode = raw_key.split(".", 1)
            mode = mode.lower()
        else:
            key = raw_key
            mode = "glob"

        # Apply attribute aliases
        key = key.replace('name', 'Name').replace('class', 'ClassName')

        # Get attribute value
        value = element.get_attribute(key)
        if value is None:
            return False

        # Perform matching based on mode
        if mode == "exact":
            return value == expected
        elif mode == "lower":
            return value.lower() == expected.lower()
        elif mode == "glob":
            return fnmatch.fnmatch(value, expected)
        elif mode == "regex":
            try:
                return re.fullmatch(expected, value) is not None
            except re.error:
                # Invalid regex pattern - treat as no match
                return False

        return False

    def _match_extra(self, element: WebElement, extra: List[str]) -> bool:
        """Check if element matches all extra attribute patterns (AND logic).

        Args:
            element: WebElement to test
            extra: List of attribute pattern strings

        Returns:
            True if all patterns match, False otherwise

        Example:
            _match_extra(element, ["name=submit*", "class=*btn*"])
        """
        # Early return for empty extra filters
        if not extra:
            return True

        # Check each pattern - all must match (AND logic)
        for pattern in extra:
            if not self._match_pattern(element, pattern):
                return False

        return True
