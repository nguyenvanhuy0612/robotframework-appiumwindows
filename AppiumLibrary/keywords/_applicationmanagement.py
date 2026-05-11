# -*- coding: utf-8 -*-
import base64
import inspect

import robot
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.client_config import AppiumClientConfig

from AppiumLibrary.utils import ApplicationCache
from .keywordgroup import KeywordGroup


class _ApplicationManagementKeywords(KeywordGroup):
    def __init__(self):
        self._cache = ApplicationCache()
        self._timeout_in_secs = float(5)

    # Public, open and close
    def appium_get_current_application(self):
        """Returns the current active Appium application instance.
        
        This keyword retrieves the internal WebDriver instance mapped to the active session. If no application is open, it returns `None`.

        Returns:
        The current ApplicationCache driver instance.
        
        Examples:
        | ${app}= | Appium Get Current Application |
        """
        current = self._cache.current
        if current is self._cache._no_current:
            return None
        return current

    def appium_get_session_index(self):
        """Returns the internal index of the current active Appium session.
        
        This is useful if you have multiple applications open and want to switch back to this one later using `Switch Application`.

        Returns:
        The integer index of the current session.
        
        Examples:
        | ${index}= | Appium Get Session Index |
        """
        current_index = self._cache.current_index
        return current_index

    def appium_close_application(self, ignore_fail=False, quit_app=True):
        """Closes the current Appium application session.
        
        Unlike `Close Application`, this keyword provides additional options to forcefully quit the underlying app or ignore failures.

        Arguments:
        - ``ignore_fail``: If True, suppresses exceptions if the keyword fails to close the application.
        - ``quit_app``: If True, specifically instructs the WebDriver to terminate the app process.
        
        Examples:
        | Appium Close Application | ignore_fail=True | quit_app=True |
        """
        self._cache.close(ignore_fail, quit_app)

    def appium_close_all_applications(self, ignore_fail=True, quit_app=True):
        """Closes all currently open Appium application sessions.
        
        This is typically used in test suite teardowns to ensure no orphaned applications are left running.

        Arguments:
        - ``ignore_fail``: If True (default), ignores any errors occurring during the process of closing multiple sessions.
        - ``quit_app``: If True (default), triggers termination of each underlying app process.
        
        Examples:
        | Appium Close All Applications |
        """
        self._cache.close_all(ignore_fail, quit_app)

    def appium_save_source(self, file_path='file_source.txt'):
        """Saves the current application's page source (XML UI tree) directly to a local file.
        
        This is incredibly useful for debugging element locators offline, as it writes the full `get_source()` text directly into a UTF-8 encoded file.

        Arguments:
        - ``file_path``: The local filepath to write the page source into. Defaults to 'file_source.txt' in the current executing directory.
        
        Examples:
        | Appium Save Source | C:/logs/app_tree.xml |
        """
        page_source = self.get_source()
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(page_source)

    def appium_activate_application(self, process):
        """Activates the application with the given process name.

        Arguments:
        - ``process``: The process name of the application to activate.

        Example:
        | Appium Activate Application | notepad.exe |
        """
        self._info(f"Activating application '{process}'")
        driver = self._current_application()
        driver.execute_script('windows: setProcessForeground', {'process': process})

    def appium_set_clipboard(self, content, content_type='plaintext', encode_base64=True):
        """Sets the clipboard content.

        Arguments:
        - ``content``: The content to set to the clipboard.
        - ``content_type``: The type of content to set to the clipboard.
        - ``encode_base64``: Whether to encode the clipboard content to base64.

        Example:
        | Appium Set Clipboard | Hello World |
        """
        self._info("Setting clipboard content")
        if content_type == 'text/plain':
            content_type = 'plaintext'
        elif content_type == 'image/png':
            content_type = 'image'

        if content_type not in ['plaintext', 'image']:
            raise ValueError("Invalid content type. Must be 'plaintext' or 'image'.")

        if encode_base64:
            content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        driver = self._current_application()
        result = driver.execute_script('windows: setClipboard', {'b64Content': content, 'contentType': content_type})
        return result

    def appium_get_clipboard(self, content_type='plaintext', decode_base64=True):
        """Gets the clipboard content.

        Arguments:
        - ``content_type``: The type of content to get from the clipboard.
        - ``decode_base64``: Whether to decode the clipboard content from base64.

        Returns:
        The clipboard content.

        Example:
        | ${clipboard}= | Appium Get Clipboard |
        """
        self._info("Getting clipboard content")
        if content_type == 'text/plain':
            content_type = 'plaintext'
        elif content_type == 'image/png':
            content_type = 'image'

        if content_type not in ['plaintext', 'image']:
            raise ValueError("Invalid content type. Must be 'plaintext' or 'image'.")

        driver = self._current_application()
        clipboard = driver.execute_script('windows: getClipboard', {'contentType': content_type})

        if decode_base64:
            clipboard = base64.b64decode(clipboard).decode('utf-8')
        return clipboard

    def close_application(self):
        """Closes the current application and also close webdriver session.

        Examples:
        | Close Application |
        """
        self._info('Closing application with session id %s' % self._current_application().session_id)
        self._cache.close()

    def close_all_applications(self, ignore_fail=True):
        """Closes all open applications.

        This keyword is meant to be used in test or suite teardown to
        make sure all the applications are closed before the test execution
        finishes.

        After this keyword, the application indices returned by `Open Application`
        are reset and start from `1`.
        

        Examples:
        | Close All Applications | ignore_fail=True |
        """

        self._info('Closing all applications')
        self._cache.close_all(ignore_fail)

    def open_application(self, remote_url, alias=None, **kwargs):
        """Opens a new application to given Appium server.
        Capabilities of appium server, Android and iOS,
        Please check https://appium.io/docs/en/2.1/cli/args/
        | *Option*            | *Man.* | *Description*     |
        | remote_url          | Yes    | Appium server url |
        | alias               | no     | alias             |
        | strict_ssl          | No     | allows you to send commands to an invalid certificate host like a self-signed one. |

        Examples:
        | Open Application | http://localhost:4723/wd/hub | alias=Myapp1         | platformName=iOS      | platformVersion=7.0            | deviceName='iPhone Simulator'           | app=your.app                         |
        | Open Application | http://localhost:4723/wd/hub | alias=Myapp1         | platformName=iOS      | platformVersion=7.0            | deviceName='iPhone Simulator'           | app=your.app                         | strict_ssl=False         |
        | Open Application | http://localhost:4723/wd/hub | platformName=Android | platformVersion=4.2.2 | deviceName=192.168.56.101:5555 | app=${CURDIR}/demoapp/OrangeDemoApp.apk | appPackage=com.netease.qa.orangedemo | appActivity=MainActivity |
        | Open Application | http://localhost:4723/wd/hub | platformName=Windows | automationName=NovaWindows2 | app=Root | # Connect to Windows Desktop using NovaWindows2 driver |
        """
        # Parse AppiumClientConfig arguments from kwargs
        ignore_certificates = kwargs.pop('ignore_certificates', True)

        # Handle strict_ssl alias for ignore_certificates (strict_ssl=False -> ignore_certificates=True)
        if 'strict_ssl' in kwargs:
            ignore_certificates = str(kwargs.pop('strict_ssl')).lower() == 'false'

        client_timeout = kwargs.pop('client_timeout', None)
        client_retries = kwargs.pop('client_retries', None)
        pool_manager_args = {}
        if client_retries is not None:
            client_retries = int(client_retries)
            pool_manager_args['retries'] = False if client_retries <= 0 else client_retries

        client_config_kwargs = {
            'direct_connection': kwargs.pop('direct_connection', True),
            'keep_alive': kwargs.pop('keep_alive', False),
            'ignore_certificates': ignore_certificates,
        }
        if client_timeout is not None:
            client_config_kwargs['timeout'] = float(client_timeout)
        if pool_manager_args:
            client_config_kwargs['init_args_for_pool_manager'] = {
                'init_args_for_pool_manager': pool_manager_args
            }

        client_config = AppiumClientConfig(remote_url, **client_config_kwargs)

        options = AppiumOptions().load_capabilities(caps=kwargs)
        application = webdriver.Remote(command_executor=str(remote_url), options=options, client_config=client_config)

        self._info(f'Opened application with session id {application.session_id}')

        if hasattr(self, "clear_search_context"):
            self.clear_search_context()

        return self._cache.register(application, alias)

    def switch_application(self, index_or_alias):
        """Switches the active application by index or alias.

        `index_or_alias` is either application index (an integer) or alias
        (a string). Index is got as the return value of `Open Application`.

        This keyword returns the index of the previous active application,
        which can be used to switch back to that application later.

        Example:
        | ${appium1}=              | Open Application  | http://localhost:4723/wd/hub                   | alias=MyApp1 | platformName=iOS | platformVersion=7.0 | deviceName='iPhone Simulator' | app=your.app |
        | ${appium2}=              | Open Application  | http://localhost:4755/wd/hub                   | alias=MyApp2 | platformName=iOS | platformVersion=7.0 | deviceName='iPhone Simulator' | app=your.app |
        | Click Element            | sendHello         | # Executed on appium running at localhost:4755 |
        | Switch Application       | ${appium1}        | # Switch using index                           |
        | Click Element            | ackHello          | # Executed on appium running at localhost:4723 |
        | Switch Application       | MyApp2            | # Switch using alias                           |
        | Page Should Contain Text | ackHello Received | # Executed on appium running at localhost:4755 |

        """
        old_index = self._cache.current_index
        if index_or_alias is None:
            self._cache.close()
        else:
            self._cache.switch(index_or_alias)
        return old_index

    def launch_application(self):
        """*DEPRECATED!!* in selenium v4, use `Activate Application` keyword.

        Launch application. Application can be launched while Appium session running.
        This keyword can be used to launch application during test case or between test cases.

        This keyword works while `Open Application` has a test running. This is good practice to `Launch Application`
        and `Quit Application` between test cases. As Suite Setup is `Open Application`, `Test Setup` can be used to `Launch Application`

        Example (syntax is just a representation, refer to RF Guide for usage of Setup/Teardown):
        | [Setup Suite] |
        |  | Open Application | http://localhost:4723/wd/hub | platformName=Android | deviceName=192.168.56.101:5555 | app=${CURDIR}/demoapp/OrangeDemoApp.apk |
        | [Test Setup] |
        |  | Launch Application |
        |  |  | <<<test execution>>> |
        |  |  | <<<test execution>>> |
        | [Test Teardown] |
        |  | Quit Application |
        | [Suite Teardown] |
        |  | Close Application |

        See `Quit Application` for quiting application but keeping Appium sesion running.
        """
        driver = self._current_application()
        driver.launch_app()

    def quit_application(self):
        """*DEPRECATED!!* in selenium v4, check `Close Application` keyword.

        Close application. Application can be quit while Appium session is kept alive.
        This keyword can be used to close application during test case or between test cases.

        See `Launch Application` for an explanation.

        

        Examples:
        | Quit Application |
        """
        driver = self._current_application()
        driver.close_app()

    def reset_application(self):
        """*DEPRECATED!!* in selenium v4, check `Terminate Application` keyword.

        Reset application. Open Application can be reset while Appium session is kept alive.
        

        Examples:
        | Reset Application |
        """
        driver = self._current_application()
        driver.reset()

    def remove_application(self, application_id):
        """ Removes the application that is identified with an application id

        Example:
        | Remove Application |  com.netease.qa.orangedemo |

        """
        driver = self._current_application()
        driver.remove_app(application_id)

    def get_appium_timeout(self):
        """Gets the timeout in seconds that is used by various keywords.

        See `Set Appium Timeout` for an explanation.

        Examples:
        | Get Appium Timeout |
        """
        return robot.utils.secs_to_timestr(self._timeout_in_secs)

    def set_appium_timeout(self, seconds):
        """Sets the timeout in seconds used by various keywords.

        There are several `Wait ...` keywords that take timeout as an
        argument. All of these timeout arguments are optional. The timeout
        used by all of them can be set globally using this keyword.

        The previous timeout value is returned by this keyword and can
        be used to set the old value back later. The default timeout
        is 5 seconds, but it can be altered in `importing`.

        Example:
        | ${orig timeout} = | Set Appium Timeout | 15 seconds |
        | Open page that loads slowly |
        | Set Appium Timeout | ${orig timeout} |
        """
        old_timeout = self.get_appium_timeout()
        self._timeout_in_secs = robot.utils.timestr_to_secs(seconds)
        return old_timeout

    def get_appium_sessionId(self):
        """Returns the current session ID as a reference

        Examples:
        | Get Appium Sessionid |
        """
        self._info("Appium Session ID: " + self._current_application().session_id)
        return self._current_application().session_id

    def get_source(self):
        """Returns the entire source of the current page.

        Examples:
        | Get Source |
        """
        return self._current_application().page_source

    def log_source(self, loglevel='INFO'):
        """Logs and returns the entire html source of the current page or frame.

        The `loglevel` argument defines the used log level. Valid log levels are
        `WARN`, `INFO` (default), `DEBUG`, `TRACE` and `NONE` (no logging).
        

        Examples:
        | Log Source | $loglevel_value |
        """
        ll = loglevel.upper()
        if ll == 'NONE':
            return ''
        else:
            if "run_keyword_and_ignore_error" not in [check_error_ignored[3] for check_error_ignored in inspect.stack()]:
                source = self._current_application().page_source
                self._log(source, ll)
                return source
            else:
                return ''

    def execute_script(self, script, **kwargs):
        """
        Execute a variety of native, mobile commands that aren't associated
        with a specific endpoint. See [https://appium.io/docs/en/commands/mobile-command/|Appium Mobile Command]
        for more details.

        Example:
        | &{scrollGesture}  |  create dictionary  |  left=${50}  |  top=${150}  |  width=${50}  |  height=${200}  |  direction=down  |  percent=${100}  |
        | Sleep             |  1                  |
        | Execute Script    |  mobile: scrollGesture  |  &{scrollGesture}  |

        Updated in AppiumLibrary 2
        """
        if kwargs:
            self._info(f"Provided dictionary: {kwargs}")

        return self._current_application().execute_script(script, kwargs)

    def execute_async_script(self, script, **kwargs):
        """
        Inject a snippet of Async-JavaScript into the page for execution in the
        context of the currently selected frame (Web context only).

        The executed script is assumed to be asynchronous and must signal that is done by
        invoking the provided callback, which is always provided as the final argument to the
        function.

        The value to this callback will be returned to the client.

        Check `Execute Script` for example kwargs usage

        Updated in AppiumLibrary 2
        """
        if kwargs:
            self._info(f"Provided dictionary: {kwargs}")

        return self._current_application().execute_async_script(script, kwargs)

    def execute_adb_shell(self, command, *args):
        """
        Execute ADB shell commands

        Android only.

        - _command_ - The ABD shell command
        - _args_ - Arguments to send to command

        Returns the exit code of ADB shell.

        Requires server flag --relaxed-security to be set on Appium server.
        

        Examples:
        | Execute Adb Shell | input keyevent 4 |
        """
        return self._current_application().execute_script('mobile: shell', {
            'command': command,
            'args': list(args)
        })

    def execute_adb_shell_timeout(self, command, timeout, *args):
        """
        Execute ADB shell commands

        Android only.

        - _command_ - The ABD shell command
        - _timeout_ - Timeout to be applied to command
        - _args_ - Arguments to send to command

        Returns the exit code of ADB shell.

        Requires server flag --relaxed-security to be set on Appium server.
        

        Examples:
        | Execute Adb Shell Timeout | input text 'hello' | 5000 |
        """
        return self._current_application().execute_script('mobile: shell', {
            'command': command,
            'args': list(args),
            'timeout': timeout
        })

    def go_back(self):
        """Goes one step backward in the browser history.

        Examples:
        | Go Back |
        """
        self._current_application().back()

    def lock(self, seconds=5):
        """
        Lock the device for a certain period of time. iOS only.
        

        Examples:
        | Lock | 5s |
        """
        self._current_application().lock(robot.utils.timestr_to_secs(seconds))

    def background_app(self, seconds=5):
        """*DEPRECATED!!*  use  `Background Application` instead.
        Puts the application in the background on the device for a certain
        duration.
        

        Examples:
        | Background App | 5s |
        """
        self._current_application().background_app(seconds)

    def background_application(self, seconds=5):
        """
        Puts the application in the background on the device for a certain
        duration.
        

        Examples:
        | Background Application | 5s |
        """
        self._current_application().background_app(seconds)

    def activate_application(self, app_id):
        """
        Activates the application if it is not running or is running in the background.
        Arguments:
        - ``app_id``: BundleId for iOS. Package name for Android.

        New in AppiumLibrary v2
        

        Examples:
        | Activate Application | com.apple.Preferences |
        """
        self._current_application().activate_app(app_id)

    def terminate_application(self, app_id):
        """
        Terminate the given app on the device

        Arguments:
        - ``app_id``: BundleId for iOS. Package name for Android.

        New in AppiumLibrary v2
        

        Examples:
        | Terminate Application | com.apple.Preferences |
        """
        return self._current_application().terminate_app(app_id)

    def stop_application(self, app_id, timeout=5000, include_stderr=True):
        """
        Stop the given app on the device

        Android only. New in AppiumLibrary v2
        

        Examples:
        | Stop Application | com.android.settings | 10s | include_stderr=True |
        """
        self._current_application().execute_script('mobile: shell', {
            'command': 'am force-stop',
            'args': [app_id],
            'includeStderr': include_stderr,
            'timeout': timeout
        })

    def touch_id(self, match=True):
        """
        Simulate Touch ID on iOS Simulator

        `match` (boolean) whether the simulated fingerprint is valid (default true)

        New in AppiumLibrary 1.5
        

        Examples:
        | Touch Id | match=True |
        """
        self._current_application().touch_id(match)

    def toggle_touch_id_enrollment(self):
        """
        Toggle Touch ID enrolled state on iOS Simulator

        New in AppiumLibrary 1.5
        

        Examples:
        | Toggle Touch Id Enrollment |
        """
        self._current_application().toggle_touch_id_enrollment()

    def shake(self):
        """
        Shake the device
        

        Examples:
        | Shake |
        """
        self._current_application().shake()

    def portrait(self):
        """
        Set the device orientation to PORTRAIT
        

        Examples:
        | Portrait |
        """
        self._rotate('PORTRAIT')

    def landscape(self):
        """
        Set the device orientation to LANDSCAPE
        

        Examples:
        | Landscape |
        """
        self._rotate('LANDSCAPE')

    def get_current_context(self):
        """Get current context.

        Examples:
        | Get Current Context |
        """
        return self._current_application().current_context

    def get_contexts(self):
        """Get available contexts.

        Examples:
        | Get Contexts |
        """
        contexts = self._current_application().contexts
        self._info(contexts)
        return contexts

    def get_window_height(self):
        """Get current device height.

        Example:
        | ${width}       | Get Window Width |
        | ${height}      | Get Window Height |
        | Click A Point  | ${width}         | ${height} |

        New in AppiumLibrary 1.4.5
        """
        return self._current_application().get_window_size()['height']

    def get_window_width(self):
        """Get current device width.

        Example:
        | ${width}       | Get Window Width |
        | ${height}      | Get Window Height |
        | Click A Point  | ${width}          | ${height} |

        New in AppiumLibrary 1.4.5
        """
        return self._current_application().get_window_size()['width']

    def switch_to_context(self, context_name):
        """Switch to a new context

        Examples:
        | Switch To Context | WEBVIEW_1 |
        """
        self._current_application().switch_to.context(context_name)

    def switch_to_frame(self, frame):
        """
        Switches focus to the specified frame, by index, name, or webelement.

        Example:
        | Go To Url | http://www.xxx.com |
        | Switch To Frame  | iframe_name|
        | Click Element | xpath=//*[@id="online-btn"] |
        """
        self._current_application().switch_to.frame(frame)

    def switch_to_parent_frame(self):
        """
        Switches focus to the parent context. If the current context is the top
        level browsing context, the context remains unchanged.
        

        Examples:
        | Switch To Parent Frame |
        """
        self._current_application().switch_to.parent_frame()

    def switch_to_window(self, window_name):
        """
        Switch to a new webview window if the application contains multiple webviews
        

        Examples:
        | Switch To Window | CDwindow-12345 |
        """
        self._current_application().switch_to.window(window_name)

    def go_to_url(self, url):
        """
        Opens URL in default web browser.

        Example:
        | Open Application  | http://localhost:4755/wd/hub | platformName=iOS | platformVersion=7.0 | deviceName='iPhone Simulator' | browserName=Safari |
        | Go To URL         | http://m.webapp.com          |
        """
        self._current_application().get(url)

    def get_capability(self, capability_name=None):
        """
        Return the desired capability value by desired capability name
        

        Examples:
        | Get Capability | platformName |
        """
        try:
            capabilities = self._current_application().capabilities
            capability = capabilities[capability_name] if capability_name else capabilities
        except Exception as e:
            raise e
        return capability

    def get_window_title(self):
        """Get the current Webview window title.

        Examples:
        | Get Window Title |
        """
        return self._current_application().title

    def get_window_url(self):
        """Get the current Webview window URL.

        Examples:
        | Get Window Url |
        """
        return self._current_application().current_url

    def get_windows(self):
        """Get available Webview windows.

        Examples:
        | Get Windows |
        """
        windows = self._current_application().window_handles
        self._info(windows)
        return windows

    # Private

    def _current_application(self):
        if not self._cache.current:
            raise RuntimeError('No application is open')
        return self._cache.current

    def _get_platform(self):
        try:
            platform_name = self._current_application().capabilities['platformName']
        except Exception as e:
            raise e
        return platform_name.lower()

    def _is_platform(self, platform):
        platform_name = self._get_platform()
        return platform.lower() == platform_name

    def _is_ios(self):
        return self._is_platform('ios')

    def _is_android(self):
        return self._is_platform('android')

    def _is_window(self):
        return self._is_platform('windows')

    def _rotate(self, orientation):
        driver = self._current_application()
        driver.orientation = orientation
