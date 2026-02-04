from AppiumLibrary import AppiumLibrary

remote_url = "http://192.168.8.245:4723"

appium = AppiumLibrary()

appium.open_application(remote_url=remote_url, 
                        app="Root", 
                        platformName="Windows", 
                        automationName="NovaWindows2")

appium.appium_activate_application("notepad.exe")

appium.close_all_applications()
