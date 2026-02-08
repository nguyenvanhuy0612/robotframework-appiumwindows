
import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from AppiumLibrary import AppiumLibrary

remote_url = "http://172.16.10.37:4723"

def test_appium():
    try:
        appium = AppiumLibrary()
        appium.open_application(remote_url=remote_url,
                            app="Root",
                            # app="explorer.exe",
                            platformName="Windows",
                        automationName="NovaWindows2")

        win_rect = appium.appium_get_rect()
        print(win_rect)

        #rect = appium.appium_get_rect("//ListItem[@Name='Desktop']")
        # print(rect)

        #appium.appium_click_offset("//ListItem[@Name='Desktop']", x=0, y=0)

        #appium.appium_click_api(x=403, y=403)

        appium.appium_scroll(x=200, y=240, deltaX=0, deltaY=-120)


    except Exception as e:
        print(e)
    finally:
        appium.close_all_applications()

if __name__ == "__main__":
    test_appium()
    