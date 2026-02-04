from AppiumLibrary import AppiumLibrary

remote_url = "http://192.168.196.158:4723"

appium = AppiumLibrary()

appium.open_application(remote_url=remote_url,
                        app="Root",
                        platformName="Windows",
                        automationName="NovaWindows"
                        )

appium.appium_execute_powershell_command("Start-Process \"notepad\"")
appium.appium_input("class=Notepad", "This is example{enter 3}Close without save")
appium.appium_click("//Window[@ClassName='Notepad']//Button[@Name='Close']")
appium.appium_click("name=Don't Save")

appium.close_all_applications()
