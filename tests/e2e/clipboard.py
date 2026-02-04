from AppiumLibrary import AppiumLibrary

remote_url = "http://192.168.8.245:4723"

appium = AppiumLibrary()

appium.open_application(remote_url=remote_url, 
                        app="Root", 
                        platformName="Windows", 
                        automationName="NovaWindows2")

text = "Hello World"
appium.appium_set_clipboard(text)

retrieved_text = appium.appium_get_clipboard()

print(f"Original text: {text}")
print(f"Retrieved text: {retrieved_text}")

assert text == retrieved_text

appium.close_all_applications()
