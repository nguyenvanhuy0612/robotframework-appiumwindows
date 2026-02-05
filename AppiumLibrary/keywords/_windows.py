import time
import os
import pathlib
import re
import ntpath
import posixpath

from AppiumLibrary.keywords.keywordgroup import KeywordGroup


class _WindowsKeywords(KeywordGroup):

    def __init__(self):
        super().__init__()

    # Public
    def appium_hover(self, locator, start_locator=None, timeout=None, **kwargs):
        self._info(f"Appium Hover '{locator}', timeout '{timeout}'")
        self._appium_hover_api(start_locator=start_locator, end_locator=locator, timeout=timeout, **kwargs)

    def appium_click_offset(self, locator, x_offset=0, y_offset=0, timeout=None, **kwargs):
        self._info(f"Appium Click Offset '{locator}', (x_offset,y_offset) '({x_offset},{y_offset})', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, x_offset=x_offset, y_offset=y_offset, **kwargs)

    def appium_right_click(self, locator, timeout=None, **kwargs):
        self._info(f"Appium Right Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, button="right", **kwargs)

    def appium_left_click(self, locator, timeout=None, **kwargs):
        self._info(f"Appium Left Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, button="left", **kwargs)

    def appium_double_click(self, locator, timeout=None, **kwargs):
        self._info(f"Appium Double Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, times=2, **kwargs)

    def appium_drag_and_drop(self, start_locator=None, end_locator=None, timeout=None, **kwargs):
        self._info(f"Appium Drag And Drop '{start_locator} -> {end_locator}', timeout '{timeout}'")
        self._appium_drag_and_drop_api(start_locator=start_locator, end_locator=end_locator, timeout=timeout, **kwargs)

    def appium_drag_and_drop_by_offset(self, x_start, y_start, x_end, y_end):
        x_start, y_start, x_end, y_end = (int(x) for x in [x_start, y_start, x_end, y_end])
        self._info(f"Appium Drag And Drop By Offset ({x_start}, {y_start}) -> ({x_end}, {y_end})")
        self._appium_drag_and_drop_api(start_locator=None, end_locator=None, timeout=1,
                                       startX=x_start, startY=y_start,
                                       endX=x_end, endY=y_end)

    def appium_sendkeys(self, text=None, **kwargs):
        self._info(f"Appium Sendkeys '{text}'")
        self._appium_keys_api(text=text, **kwargs)
    
    # TODO: temporary add, will be removed in the future
    def normalize_windows_path(self, path, sep="\\", case_normalize=False, escape_backtick=True):
        return self.appium_normalize_path(path=path, sep=sep, case_normalize=case_normalize, escape_backtick=escape_backtick)

    def appium_normalize_path(self, path, sep="\\", case_normalize=False, escape_backtick=True):
        """Normalizes the given path.
        - Collapses redundant separators and up-level references.
        - Set sep to ``/`` to Converts ``\\`` to ``/``
        - Replaces initial ``~`` or ``~user`` by that user's home directory.
        - If ``case_normalize`` is given a true value (see `Boolean arguments`)
          on Windows, converts the path to all lowercase.
        - Converts ``pathlib.Path`` instances to ``str``.

        Examples:
        | ${path1} = | Appium Normalize Path | abc/           |
        | ${path2} = | Appium Normalize Path | abc/../def     |
        | ${path3} = | Appium Normalize Path | abc/./def//ghi |
        | ${path4} = | Appium Normalize Path | ~robot/stuff   |
        =>
        - ${path1} = ``abc``
        - ${path2} = ``def``
        - ${path3} = ``abc\\def\\ghi``
        - ${path4} = ``\\home\\robot\\stuff``

        """
        # Determine strict library to use based on target separator
        if sep == "\\":
            path_module = ntpath
        else:
            path_module = posixpath

        if isinstance(path, pathlib.Path):
            path = str(path)

        path = path or "."
        path = os.path.expanduser(path)

        # If targeting Posix, ensure backslashes are converted to forward slashes 
        # BEFORE normalization, because posixpath treats backslash as a filename character.
        if path_module is posixpath:
            path = path.replace("\\", "/")

        path = path_module.normpath(path)

        if case_normalize:
            path = path_module.normcase(path)

        if escape_backtick:
            path = re.sub(r"(?<!`)`(?!`)", "``", path)

        # Force final separator just in case, though normpath usually handles it.
        # ntpath produces '\', posixpath produces '/'
        # The original code did a final cleaning, we can preserve rstrip.
        return path.rstrip()

    # Private
    def _apply_modifier_keys(self, params: dict, modifier_keys):
        """Normalize modifier keys and update params in place."""
        if modifier_keys:
            if isinstance(modifier_keys, (list, tuple)):
                params["modifierKeys"] = [str(k).lower() for k in modifier_keys]
            else:
                params["modifierKeys"] = str(modifier_keys).lower()

    def _appium_click_api(self, locator, timeout, **kwargs):
        """
        Perform a click action on a Windows element using Appium Windows Driver.

        References:
            https://github.com/appium/appium-windows-driver
            https://github.com/appium/appium-windows-driver?tab=readme-ov-file#windows-click

        Args:
            locator (str): Element locator.
            timeout (int): Maximum time to retry locating and clicking the element (in seconds).
            kwargs (dict): Additional click options.

        Keyword Args:
            button (str): Mouse button to click. One of:
                - "left" (default)
                - "middle"
                - "right"
                - "back"
                - "forward"
            modifierKeys (list|str): Keys to hold during the click. One or more of:
                - "Shift"
                - "Ctrl"
                - "Alt"
                - "Win"
            modifier_keys (list|str): Same as `modifierKeys` (snake_case alias).
            x_offset (int): X offset relative to the element's top-left corner. Default: 0.
            y_offset (int): Y offset relative to the element's top-left corner. Default: 0.
            is_center (bool): If True, click at the element's center. Default: False.
            durationMs (int): Duration of the click in milliseconds. Default: 100.
            times (int): Number of times to click. Default: 1.
            interClickDelayMs (int): Delay between multiple clicks in milliseconds. Default: 100.
            post_delay (float): Delay after click action (in seconds). Default: 0.5.

        Raises:
            Exception: If the element cannot be found or the click action fails within the timeout.
        """
        x_offset = int(kwargs.get("x_offset", 0))
        y_offset = int(kwargs.get("y_offset", 0))
        is_center = bool(kwargs.get("is_center", False))

        click_params = {
            "button": str(kwargs.get("button", "left")),
            "durationMs": int(kwargs.get("durationMs", 100)),
            "times": int(kwargs.get("times", 1)),
            "interClickDelayMs": int(kwargs.get("interClickDelayMs", 100)),
        }

        self._apply_modifier_keys(click_params, kwargs.get("modifierKeys"))

        def func():
            elements = self._element_find(locator, False, False)
            if not elements:
                raise Exception(f"Element not found: {locator}")

            driver = self._current_application()
            rect = driver.get_window_rect()
            e_rect = elements[0].rect

            x = rect['x'] + e_rect['x'] + x_offset
            y = rect['y'] + e_rect['y'] + y_offset
            if is_center:
                x += e_rect['width'] // 2
                y += e_rect['height'] // 2

            click_params.update({"x": x, "y": y})
            self._info(f"Click params {click_params}")

            driver.execute_script("windows: click", click_params)
            time.sleep(0.5)

        self._retry(
            timeout,
            func,
            action=f"Failed to perform click action on '{locator}'",
            required=kwargs.pop("required", True),
            return_value=kwargs.pop("return_value", True),
            poll_interval=kwargs.pop("poll_interval", None)
        )

    def _appium_hover_api(self, start_locator, end_locator, timeout, **kwargs):
        """
        Perform a hover action using Platform-Specific Extensions.
        """
        hover_params = {
            "startX": int(kwargs.get("startX", 0)),
            "startY": int(kwargs.get("startY", 0)),
            "endX": int(kwargs.get("endX", 0)),
            "endY": int(kwargs.get("endY", 0)),
            "durationMs": int(kwargs.get("durationMs", 100)),
        }

        self._apply_modifier_keys(hover_params, kwargs.get("modifierKeys"))

        def func():
            if start_locator:
                start_element = self._element_find(start_locator, True, False)
                if start_element:
                    hover_params["startElementId"] = start_element.id
                    hover_params.pop("startX", None)
                    hover_params.pop("startY", None)
                else:
                    raise Exception(f"Start element not found: {start_locator}")

            if end_locator:
                end_element = self._element_find(end_locator, True, False)
                if end_element:
                    hover_params["endElementId"] = end_element.id
                    hover_params.pop("endX", None)
                    hover_params.pop("endY", None)
                else:
                    raise Exception(f"End element not found: {end_locator}")

            self._current_application().execute_script("windows: hover", hover_params)
            time.sleep(0.5)

        self._retry(
            timeout,
            func,
            action="Failed to perform hover action",
            required=kwargs.pop("required", True),
            return_value=kwargs.pop("return_value", True),
            poll_interval=kwargs.pop("poll_interval", None)
        )

    def _appium_drag_and_drop_api(self, start_locator, end_locator, timeout, **kwargs):
        """
        Perform a drag and drop action using Appium Windows Driver.
        https://github.com/appium/appium-windows-driver?tab=readme-ov-file#windows-clickanddrag
        """
        drag_params = {
            "startX": int(kwargs.get("startX", 0)),
            "startY": int(kwargs.get("startY", 0)),
            "endX": int(kwargs.get("endX", 0)),
            "endY": int(kwargs.get("endY", 0)),
            "durationMs": int(kwargs.get("durationMs", 5000)),
        }

        self._apply_modifier_keys(drag_params, kwargs.get("modifierKeys"))

        def func():
            if start_locator:
                start_element = self._element_find(start_locator, True, False)
                if start_element:
                    drag_params["startElementId"] = start_element.id
                    drag_params.pop("startX", None)
                    drag_params.pop("startY", None)

            if end_locator:
                end_element = self._element_find(end_locator, True, False)
                if end_element:
                    drag_params["endElementId"] = end_element.id
                    drag_params.pop("endX", None)
                    drag_params.pop("endY", None)

            self._current_application().execute_script("windows: clickAndDrag", drag_params)
            time.sleep(0.5)

        self._retry(
            timeout,
            func,
            action="Failed to perform drag and drop action",
            required=kwargs.pop("required", True),
            return_value=kwargs.pop("return_value", True),
            poll_interval=kwargs.pop("poll_interval", None)
        )

    def _appium_keys_api(self, text, **kwargs):
        """
        Perform a key input action using Appium Windows Driver.
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
        self._current_application().execute_script("windows: keys", {"actions": actions})
        time.sleep(0.5)
