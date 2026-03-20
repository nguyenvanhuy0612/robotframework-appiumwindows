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
        """Hover over an element using the NovaWindows2 driver interface.
        
        This keyword moves the mouse pointer to visually hover over the center of the specified element.

        Arguments:
        - ``locator``: The target element to hover over.
        - ``start_locator``: An optional starting element to move the mouse cursor from.
        - ``timeout``: Time to wait for the element to appear.
        - ``kwargs``: Additional hover options (e.g. `durationMs` for hover time).
        
        Examples:
        | Appium Hover | id=Button1 |
        """
        self._info(f"Appium Hover '{locator}', timeout '{timeout}'")
        self._appium_hover_api(start_locator=start_locator, end_locator=locator, timeout=timeout, **kwargs)
    
    def appium_click_api(self, locator=None, x=0, y=0, timeout=None, **kwargs):
        """Click on the screen using absolute coordinates or element locators via the NovaWindows2 driver API.
        
        This provides low-level precision control over mouse clicks compared to standard web driver clicks.

        Arguments:
        - ``locator``: The target element to click on (if coordinates are not used).
        - ``x``: The specific X-coordinate to click.
        - ``y``: The specific Y-coordinate to click.
        - ``timeout``: Time to wait for the element to appear.
        
        Examples:
        | Appium Click API | x=100 | y=200 |
        | Appium Click API | locator=id=Button1 |
        """
        self._info(f"Appium Click API '{locator}', timeout '{timeout}', (x,y) '({x},{y})'")
        self._appium_click_api(locator=locator, timeout=timeout, x=x, y=y, **kwargs)

    def appium_click_offset(self, locator, x_offset=0, y_offset=0, timeout=None, **kwargs):
        """Click on an element with an exact X and Y offset from its relative top-left point.
        
        This is extremely useful when interacting with large canvases or maps where you need to click precisely within an element frame.

        Arguments:
        - ``locator``: The parent element.
        - ``x_offset``: The number of pixels to move right from the element's top-left corner.
        - ``y_offset``: The number of pixels to move down from the element's top-left corner.
        - ``timeout``: Maximum time to locate the element.
        
        Examples:
        | Appium Click Offset | id=Canvas | x_offset=50 | y_offset=50 |
        """
        self._info(f"Appium Click Offset '{locator}', (x_offset,y_offset) '({x_offset},{y_offset})', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, x_offset=x_offset, y_offset=y_offset, **kwargs)

    def appium_right_click(self, locator, timeout=None, **kwargs):
        """Perform a standard Mouse Right-Click (often used to open context menus).

        Arguments:
        - ``locator``: The element to right click.
        - ``timeout``: Maximum time to wait for the element.
        
        Examples:
        | Appium Right Click | id=MyFile |
        """
        self._info(f"Appium Right Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, button="right", **kwargs)

    def appium_left_click(self, locator, timeout=None, **kwargs):
        """Perform an explicit Mouse Left-Click.
        
        This behaves identically to a normal click, but forces the "left" mouse button argument.

        Arguments:
        - ``locator``: The element to left click.
        - ``timeout``: Maximum time to wait for the element.
        
        Examples:
        | Appium Left Click | id=SubmitButton |
        """
        self._info(f"Appium Left Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, button="left", **kwargs)

    def appium_double_click(self, locator, timeout=None, **kwargs):
        """Perform a fast double-click on the target element.

        Arguments:
        - ``locator``: The element to double-click on.
        - ``timeout``: Maximum time to wait for the element.
        
        Examples:
        | Appium Double Click | name=My Folder |
        """
        self._info(f"Appium Double Click '{locator}', timeout '{timeout}'")
        self._appium_click_api(locator=locator, timeout=timeout, times=2, **kwargs)

    def appium_drag_and_drop(self, start_locator=None, end_locator=None, timeout=None, **kwargs):
        """Drags an element and drops it onto another element using native Windows mouse commands.
        
        Arguments:
        - ``start_locator``: The element to click and hold (the source).
        - ``end_locator``: The element to drag the source over and release (the destination).
        - ``timeout``: Maximum time to locate both elements.
        
        Examples:
        | Appium Drag And Drop | id=File1 | id=Folder1 |
        """
        self._info(f"Appium Drag And Drop '{start_locator} -> {end_locator}', timeout '{timeout}'")
        self._appium_drag_and_drop_api(start_locator=start_locator, end_locator=end_locator, timeout=timeout, **kwargs)

    def appium_drag_and_drop_by_offset(self, x_start, y_start, x_end, y_end):
        """Drags the mouse purely using absolute X,Y screen coordinates.

        Arguments:
        - ``x_start``: The screen X-coordinate to begin the drag.
        - ``y_start``: The screen Y-coordinate to begin the drag.
        - ``x_end``: The screen X-coordinate to finish the drag.
        - ``y_end``: The screen Y-coordinate to finish the drag.
        
        Examples:
        | Appium Drag And Drop By Offset | 100 | 100 | 500 | 500 |
        """
        x_start, y_start, x_end, y_end = (int(x) for x in [x_start, y_start, x_end, y_end])
        self._info(f"Appium Drag And Drop By Offset ({x_start}, {y_start}) -> ({x_end}, {y_end})")
        self._appium_drag_and_drop_api(start_locator=None, end_locator=None, timeout=1, startX=x_start, startY=y_start, endX=x_end, endY=y_end)

    def appium_scroll(self, locator=None, x=0, y=0, deltaX=0, deltaY=0, timeout=None, **kwargs):
        """Scrolls the mouse wheel across the target interface.
        
        You can provide an element to scroll over, or absolute coordinates.

        Arguments:
        - ``locator``: The specific element to hover the mouse and scroll on.
        - ``x``: Fallback absolute X screen coordinate if locator is omitted.
        - ``y``: Fallback absolute Y screen coordinate if locator is omitted.
        - ``deltaX``: Horizontal scroll amount.
        - ``deltaY``: Vertical scroll amount (positive values scroll up, negative values scroll down).
        - ``timeout``: Maximum time to wait for the element.
        
        Examples:
        | Appium Scroll | id=ScrollPanel | deltaY=-120 |
        """
        self._info(f"Appium Scroll '{locator}', timeout '{timeout}', (x,y) '({x},{y})', (deltaX,deltaY) '({deltaX},{deltaY})'")
        self._appium_scroll_api(locator=locator, timeout=timeout, x=x, y=y, deltaX=deltaX, deltaY=deltaY, **kwargs)

    def appium_sendkeys(self, text=None, **kwargs):
        """Transmits raw hardware keystrokes using the NovaWindows2 Driver.
        
        Use this to bypass software-level keyboard inputs and mimic real hardware typing.

        Arguments:
        - ``text``: The literal characters (or special key codes) to type out.
        
        Examples:
        | Appium Sendkeys | Hello Universe |
        """
        self._info(f"Appium Sendkeys '{text}'")
        self._appium_keys_api(text=text, **kwargs)
    
    # TODO: temporary add, will be removed in the future
    def normalize_windows_path(self, path, sep="\\", case_normalize=False, escape_backtick=True):
        """Alias for `Appium Normalize Path`. Resolves OS-specific directory characters.

        Arguments:
        - ``path``: The input string path to normalize.
        - ``sep``: Desired separator (default '\\').
        - ``case_normalize``: Convert to lowercase if true.
        - ``escape_backtick``: Safely double backticks in path.
        

        Examples:
        | Normalize Windows Path | C:\\Folder\\path | sep=/ | case_normalize=True |
        """
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
    def _apply_modifier_keys(self, params: dict, kwargs: dict):
        """Normalize modifier keys and update params in place."""
        modifier_keys = kwargs.get("modifierKeys") or kwargs.get("modifier_keys")
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

        Arguments:
        - ``locator``: Element locator.
        - ``timeout``: Maximum time to retry locating and clicking the element (in seconds).
        - ``kwargs``: Additional click options.
        - ``button``: Mouse button to click. ("left", "middle", "right", "back", "forward")
        - ``modifierKeys``: Keys to hold during the click. ("Shift", "Ctrl", "Alt", "Win")
        - ``x_offset``: X offset relative to the element's top-left corner. Default: 0.
        - ``y_offset``: Y offset relative to the element's top-left corner. Default: 0.
        - ``is_center``: If True, click at the element's center. Default: False.
        - ``durationMs``: Duration of the click in milliseconds. Default: 100.
        - ``times``: Number of times to click. Default: 1.
        - ``interClickDelayMs``: Delay between multiple clicks in milliseconds. Default: 100.
        - ``post_delay``: Delay after click action (in seconds). Default: 0.5.

        Raises:
            Exception: If the element cannot be found or the click action fails within the timeout.
        """
        click_params = {
            "button": str(kwargs.pop("button", "left")),
            "durationMs": int(kwargs.pop("durationMs", 100)),
            "times": int(kwargs.pop("times", 1)),
            "interClickDelayMs": int(kwargs.pop("interClickDelayMs", 100)),
            "x": int(kwargs.pop("x", 0)) + int(kwargs.pop("x_offset", 0)),
            "y": int(kwargs.pop("y", 0)) + int(kwargs.pop("y_offset", 0)),
        }

        self._apply_modifier_keys(click_params, kwargs)
        post_delay = float(kwargs.pop("post_delay", 0.5))

        def func():
            params = click_params.copy()
            if locator:
                params["elementId"] = self._element_find(locator, True, True).id
                if params.get("x") == 0:
                    params.pop("x", None)
                if params.get("y") == 0:
                    params.pop("y", None)

            self._info(f"Click params {params}")
            self._current_application().execute_script("windows: click", params)
            time.sleep(post_delay)

        return self._retry(
            timeout,
            func,
            action=f"Failed to perform click action on '{locator}'",
            required=kwargs.pop("required", True),
            return_value=False,
            poll_interval=kwargs.pop("poll_interval", None)
        )

    def _appium_hover_api(self, start_locator, end_locator, timeout, **kwargs):
        """
        Perform a hover action using Platform-Specific Extensions.
        """
        hover_params = {
            "startX": int(kwargs.pop("startX", 0)),
            "startY": int(kwargs.pop("startY", 0)),
            "endX": int(kwargs.pop("endX", 0)),
            "endY": int(kwargs.pop("endY", 0)),
            "durationMs": int(kwargs.pop("durationMs", 100)),
        }

        self._apply_modifier_keys(hover_params, kwargs)
        post_delay = float(kwargs.pop("post_delay", 0.5))

        def func():
            params = hover_params.copy()
            if start_locator:
                params["startElementId"] = self._element_find(start_locator, True, True).id
                if params.get("startX") == 0:
                    params.pop("startX", None)
                if params.get("startY") == 0:
                    params.pop("startY", None)

            if end_locator:
                params["endElementId"] = self._element_find(end_locator, True, True).id
                if params.get("endX") == 0:
                    params.pop("endX", None)
                if params.get("endY") == 0:
                    params.pop("endY", None)

            self._info(f"Hover params {params}")
            self._current_application().execute_script("windows: hover", params)
            time.sleep(post_delay)

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
        https://github.com/nguyenvanhuy0612/appium-novawindows2-driver?tab=readme-ov-file#windows-clickanddrag
        """
        drag_params = {
            'startX': int(kwargs.pop("startX", 0)),
            'startY': int(kwargs.pop("startY", 0)),
            'endX': int(kwargs.pop("endX", 0)),
            'endY': int(kwargs.pop("endY", 0)),
            'durationMs': int(kwargs.pop("durationMs", 5000)),
            'button': str(kwargs.pop("button", "left")),
            'smoothPointerMove': str(kwargs.pop('smoothPointerMove', 'linear'))
        }

        self._apply_modifier_keys(drag_params, kwargs)
        post_delay = float(kwargs.pop("post_delay", 0.5))

        def func():
            params = drag_params.copy()
            if start_locator:
                params['startElementId'] = self._element_find(start_locator, True, True).id
                if params.get('startX') == 0:
                    params.pop("startX", None)
                if params.get('startY') == 0:
                    params.pop("startY", None)

            if end_locator:
                params['endElementId'] = self._element_find(end_locator, True, True).id
                if params.get('endX') == 0:
                    params.pop("endX", None)
                if params.get('endY') == 0:
                    params.pop("endY", None)

            self._info(f"Drag params {params}")
            self._current_application().execute_script('windows: clickAndDrag', params)
            time.sleep(post_delay)

        self._retry(
            timeout,
            func,
            action="Failed to perform drag and drop action",
            required=kwargs.pop("required", True),
            return_value=kwargs.pop("return_value", True),
            poll_interval=kwargs.pop("poll_interval", None)
        )
    
    def _appium_scroll_api(self, locator, timeout, **kwargs):
        """
        Perform a scroll action using Appium Windows Driver.
        https://github.com/nguyenvanhuy0612/appium-novawindows2-driver?tab=readme-ov-file#windows-scroll
        """
        scroll_params = {
            "x": int(kwargs.pop("x", 0)),
            "y": int(kwargs.pop("y", 0)),
            "deltaX": int(kwargs.pop("deltaX", 0)),
            "deltaY": int(kwargs.pop("deltaY", 0)),
        }

        self._apply_modifier_keys(scroll_params, kwargs)
        post_delay = float(kwargs.pop("post_delay", 0.5))

        def func():
            params = scroll_params.copy()
            if locator:
                params["elementId"] = self._element_find(locator, True, True).id
                if params.get("x") == 0:
                    params.pop("x", None)
                if params.get("y") == 0:
                    params.pop("y", None)

            self._info(f"Scroll params {params}")
            self._current_application().execute_script("windows: scroll", params)
            time.sleep(post_delay)

        return self._retry(
            timeout,
            func,
            action="Failed to perform scroll action",
            required=kwargs.pop("required", True),
            return_value=kwargs.pop("return_value", True),
            poll_interval=kwargs.pop("poll_interval", None)
        )

    def _appium_keys_api(self, text, **kwargs):
        """
        Perform a key input action using Appium Windows Driver.
        https://github.com/nguyenvanhuy0612/appium-novawindows2-driver?tab=readme-ov-file#windows-keys

        Arguments:
        - ``text``: The text to input
        - ``kwargs``: Additional parameters

        Returns:
        None
        """
        actions = kwargs.get("actions", [])
        # pause = int(kwargs.get("pause", 0))
        # virtual_key_code = int(kwargs.get("virtualKeyCode", 0))
        # down = bool(kwargs.get("down", False))
        if not actions:
            actions = [{"text": text}]
        self._current_application().execute_script("windows: keys", {"actions": actions})
        sleep = kwargs.pop("sleep", kwargs.pop("post_delay", 0.5))
        time.sleep(float(sleep))
