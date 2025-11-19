# -*- coding: utf-8 -*-
import fnmatch
import re

from appium.webdriver.common.appiumby import AppiumBy
from robot.api import logger

from AppiumLibrary import utils


class ElementFinder(object):

    def __init__(self):
        self._strategies = {
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

    def find_extra(self, application, locator, tag=None):
        """
        Find elements using a primary locator string plus optional
        attribute-based extra filters.

        Behavior:
            1. The input `locator` may contain:
                  - A standard locator string (e.g. "xpath=//button")
                  - Additional attribute-matching patterns:
                        name=submit*
                        class.lower=btn-primary
                        id.regex=^btn_[0-9]+$

            2. The locator is normalized using `_normalize_locator()`, which returns:
                  {
                      "locator": "<standard locator string>",
                      "extra": [ "<pattern1>", "<pattern2>", ... ]
                  }

            3. All elements matching the primary locator are retrieved via `find()`.

            4. The extra patterns are applied using `_match_extra()`, requiring
               **all** attribute rules to match (AND logic).

        Parameters:
            application  -- application/session handle used by `find()`
            locator      -- a compound locator string interpreted by
                            `_normalize_locator()`

        Returns:
            List of elements that match:
                - the primary locator AND
                - every pattern in the `extra` rules.

        Example:
            locator = "xpath=//button | name.lower=submit | class=*btn*"

            Steps:
              - normalize → locator="xpath=//button"
                            extra=["name.lower=submit", "class=*btn*"]
              - find()    → returns all buttons
              - filters   → keeps only buttons whose:
                                name.lower == "submit"
                                and class matches "*btn*"

            result = find_extra(app, locator)
        """
        standard_locator = self._normalize_locator(locator)
        locator_str = standard_locator.get("locator")
        extras = standard_locator.get("extra", [])

        all_elements = self.find(application, locator_str, tag)

        return [el for el in all_elements if self._match_extra(el, extras)]

    def find(self, application, locator, tag=None):
        assert application is not None
        assert locator is not None and len(locator) > 0

        (prefix, criteria) = self._parse_locator(locator)
        prefix = 'default' if prefix is None else prefix
        strategy = self._strategies.get(prefix)
        if strategy is None:
            raise ValueError("Element locator with prefix '" + prefix + "' is not supported")
        (tag, constraints) = self._get_tag_and_constraints(tag)
        return strategy(application, criteria, tag, constraints)

    # Strategy routines, private

    def _find_by_identifier(self, application, criteria, tag, constraints):
        elements = self._normalize_result(application.find_elements(by=AppiumBy.ID, value=criteria))
        elements.extend(self._normalize_result(application.find_elements(by=AppiumBy.NAME, value=criteria)))
        return self._filter_elements(elements, tag, constraints)

    def _find_by_id(self, application, criteria, tag, constraints):
        # print(f"criteria is {criteria}")
        return self._filter_elements(
            application.find_elements(by=AppiumBy.ID, value=criteria),
            tag, constraints)

    def _find_by_name(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.NAME, value=criteria),
            tag, constraints)

    def _find_by_xpath(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.XPATH, value=criteria),
            tag, constraints)

    def _find_by_dom(self, application, criteria, tag, constraints):
        result = application.execute_script("return %s;" % criteria)
        if result is None:
            return []
        if not isinstance(result, list):
            result = [result]
        return self._filter_elements(result, tag, constraints)

    def _find_by_sizzle_selector(self, application, criteria, tag, constraints):
        js = "return jQuery('%s').get();" % criteria.replace("'", "\\'")
        return self._filter_elements(
            application.execute_script(js),
            tag, constraints)

    def _find_by_link_text(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.LINK_TEXT, value=criteria),
            tag, constraints)

    def _find_by_css_selector(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.CSS_SELECTOR, value=criteria),
            tag, constraints)

    def _find_by_tag_name(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.TAG_NAME, value=criteria),
            tag, constraints)

    def _find_by_class_name(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.CLASS_NAME, value=criteria),
            tag, constraints)

    def _find_element_by_accessibility_id(self, application, criteria, tag, constraints):
        return self._filter_elements(
            application.find_elements(by=AppiumBy.ACCESSIBILITY_ID, value=criteria),
            tag, constraints)

    def _find_by_android(self, application, criteria, tag, constraints):
        """Find element matches by UI Automator."""
        return self._filter_elements(
            application.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value=criteria),
            tag, constraints)

    def _find_by_android_viewtag(self, application, criteria, tag, constraints):
        """Find element matches by its view tag
        Espresso only
        """
        return self._filter_elements(
            application.find_elements(by=AppiumBy.ANDROID_VIEWTAG, value=criteria),
            tag, constraints)

    def _find_by_android_data_matcher(self, application, criteria, tag, constraints):
        """Find element matches by Android Data Matcher
        Espresso only
        """
        return self._filter_elements(
            application.find_elements(by=AppiumBy.ANDROID_DATA_MATCHER, value=criteria),
            tag, constraints)

    def _find_by_android_view_matcher(self, application, criteria, tag, constraints):
        """Find element matches by  Android View Matcher
        Espresso only
        """
        return self._filter_elements(
            application.find_elements(by=AppiumBy.ANDROID_VIEW_MATCHER, value=criteria),
            tag, constraints)

    def _find_by_ios(self, application, criteria, tag, constraints):
        """Find element matches by UI Automation."""
        return self._filter_elements(
            application.find_elements(by=AppiumBy.IOS_UIAUTOMATION, value=criteria),
            tag, constraints)

    def _find_by_ios_predicate(self, application, criteria, tag, constraints):
        """Find element matches by  iOSNsPredicateString."""
        return self._filter_elements(
            application.find_elements(by=AppiumBy.IOS_PREDICATE, value=criteria),
            tag, constraints)

    def _find_by_chain(self, application, criteria, tag, constraints):
        """Find element matches by  iOSChainString."""
        return self._filter_elements(
            application.find_elements(by=AppiumBy.IOS_CLASS_CHAIN, value=criteria),
            tag, constraints)

    def _find_by_default(self, application, criteria, tag, constraints):
        if self._is_xpath(criteria):
            return self._find_by_xpath(application, criteria, tag, constraints)
        # Used `id` instead of _find_by_key_attrs since iOS and Android internal `id` alternatives are
        # different and inside appium python client. Need to expose these and improve in order to make
        # _find_by_key_attrs useful.
        return self._find_by_id(application, criteria, tag, constraints)

    # TODO: Not in use after conversion from Selenium2Library need to make more use of multiple auto selector strategy
    def _find_by_key_attrs(self, application, criteria, tag, constraints):
        key_attrs = self._key_attrs.get(None)
        if tag is not None:
            key_attrs = self._key_attrs.get(tag, key_attrs)

        xpath_criteria = utils.escape_xpath_value(criteria)
        xpath_tag = tag if tag is not None else '*'
        xpath_constraints = ["@%s='%s'" % (name, constraints[name]) for name in constraints]
        xpath_searchers = ["%s=%s" % (attr, xpath_criteria) for attr in key_attrs]
        xpath_searchers.extend(
            self._get_attrs_with_url(key_attrs, criteria, application))
        xpath = "//%s[%s(%s)]" % (
            xpath_tag,
            ' and '.join(xpath_constraints) + ' and ' if len(xpath_constraints) > 0 else '',
            ' or '.join(xpath_searchers))
        return self._normalize_result(application.find_elements(by=AppiumBy.XPATH, value=xpath))

    # Private
    _key_attrs = {
        None: ['@id', '@name'],
        'a': ['@id', '@name', '@href', 'normalize-space(descendant-or-self::text())'],
        'img': ['@id', '@name', '@src', '@alt'],
        'input': ['@id', '@name', '@value', '@src'],
        'button': ['@id', '@name', '@value', 'normalize-space(descendant-or-self::text())']
    }

    def _get_tag_and_constraints(self, tag):
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

    def _element_matches(self, element, tag, constraints):
        if not element.tag_name.lower() == tag:
            return False
        for name in constraints:
            if not element.get_attribute(name) == constraints[name]:
                return False
        return True

    def _filter_elements(self, elements, tag, constraints):
        elements = self._normalize_result(elements)
        if tag is None:
            return elements
        return filter(
            lambda element: self._element_matches(element, tag, constraints),
            elements)

    def _get_attrs_with_url(self, key_attrs, criteria, browser):
        attrs = []
        url = None
        xpath_url = None
        for attr in ['@src', '@href']:
            if attr in key_attrs:
                if url is None or xpath_url is None:
                    url = self._get_base_url(browser) + "/" + criteria
                    xpath_url = utils.escape_xpath_value(url)
                attrs.append("%s=%s" % (attr, xpath_url))
        return attrs

    def _get_base_url(self, browser):
        url = browser.get_current_url()
        if '/' in url:
            url = '/'.join(url.split('/')[:-1])
        return url

    def _parse_locator(self, locator):
        prefix = None
        criteria = locator
        if not self._is_xpath(locator):
            locator_parts = locator.partition('=')
            if len(locator_parts[1]) > 0:
                prefix = locator_parts[0].strip().lower()
                criteria = locator_parts[2].strip()
        return (prefix, criteria)

    def _is_xpath(self, locator):
        return locator and locator.startswith('/')

    def _normalize_result(self, elements):
        if not isinstance(elements, list):
            logger.debug("WebDriver find returned %s" % elements)
            return []
        return elements

    def _normalize_locator(self, raw_locator):
        """
        Normalize locator input into standard form:
        {
            "locator": "<strategy>=<value>",
            "extra": [<extra filters>]
        }
        """
        if isinstance(raw_locator, str):
            return {"locator": raw_locator, "extra": []}

        if isinstance(raw_locator, dict):
            locator = raw_locator.get("locator")
            extra = raw_locator.get("extra")

            if isinstance(extra, str):
                extra = [extra]
            elif extra is None:
                extra = []
            elif not isinstance(extra, list):
                raise TypeError(f"Invalid 'extra' type: {type(extra)}")

            if not locator:
                raise ValueError(f"Invalid locator: {locator}")

            return {"locator": locator, "extra": extra}

        raise TypeError(f"Unsupported locator type: {type(raw_locator)}")

    def _match_pattern(self, element, pattern: str) -> bool:
        """
        Match a single element attribute against a pattern rule.

        Pattern formats:
            - exact:     name=abc
            - glob:      name=*abc*        (default mode)
                          name=a?c
            - regex:     name.regex=^abc[0-9]+$
            - case mods: name.lower=abc    (case-insensitive compare)

        Notes:
            - If pattern does not specify mode (e.g. "name=abc"),
              the default mode is **glob**.
            - Supports shorthand attributes:
                  "name"  -> "Name"
                  "class" -> "ClassName"
                  (via alias map: self._alias_map)
            - If the element attribute value is None → returns False.
            - Regex uses re.fullmatch().

        Examples:
            "text=Hello"             → glob match
            "text.exact=Hello"       → exact match
            "id.regex=^btn_[0-9]+$"  → regex match
            "name.lower=submit"      → lowercase comparison
        """
        if element is None:
            return False

        if "=" not in pattern:
            return False

        raw_key, expected = pattern.split("=", 1)
        raw_key, expected = raw_key.strip(), expected.strip()

        # extract mode
        if "." in raw_key:
            key, mode = raw_key.split(".", 1)
            mode = mode.lower()
        else:
            key = raw_key
            mode = "glob"  # default mode

        # alias: name -> Name, class -> ClassName, etc.
        key = key.replace('name', 'Name').replace('class', 'ClassName')

        # retrieve element attribute
        value = element.get_attribute(key)
        if value is None:
            return False

        # perform match
        if mode == "exact":
            return value == expected

        elif mode == "lower":
            return value.lower() == expected.lower()

        elif mode == "glob":
            return fnmatch.fnmatch(value, expected)

        elif mode == "regex":
            return re.fullmatch(expected, value or "") is not None

        return False

    def _match_extra(self, element, extra) -> bool:
        """
        Check whether an element satisfies **all** extra attribute rules.

        This function applies AND logic:
            - Every pattern in `extra` must match for the element to pass.
            - Each pattern is evaluated by `_match_pattern()`.

        Parameters:
            element -- the WebElement-like object
            extra   -- list of pattern strings:
                           ["name=submit*", "class.lower=btn-primary", "id.regex=^btn_[0-9]+$"]

        Returns:
            True  if all patterns match,
            False if any pattern fails.

        Example:
            extra = [
                "name.lower=submit",
                "class.glob=*primary*",
                "id.regex=^btn_[0-9]+$"
            ]

            _match_extra(element, extra) → True only if all conditions are satisfied.
        """
        if not extra:
            return True

        for pattern in extra:
            if not self._match_pattern(element, pattern):
                return False

        return True
