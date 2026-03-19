import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from AppiumLibrary import AppiumLibrary

appium = AppiumLibrary()
appium.open_application(remote_url="http://172.16.10.37:4723", app="Root", platformName="Windows", automationName="NovaWindows2")

process = appium.appium_execute_powershell('Get-Process')
print(process)

appium.close_all_applications()
