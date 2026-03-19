import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from AppiumLibrary import AppiumLibrary

def main():
    appium = AppiumLibrary()
    remote_url = "http://192.168.196.128:4723"
    
    print(f"Connecting to Appium at {remote_url}...")
    appium.open_application(
        remote_url=remote_url, 
        app="Root", 
        platformName="Windows", 
        automationName="NovaWindows2"
    )

    try:
        print("--- Testing Single Actions ---")
        print("1. Move by offset (100, 100)")
        appium.appium_action_move_by_offset(100, 100)
        time.sleep(1)
        
        print("2. Click")
        appium.appium_action_click()
        time.sleep(1)

        print("--- Testing Chain Builder ---")
        print("1. Begin chain")
        appium.appium_begin_action_chain()
        
        print("2. Add move by offset (50, 50)")
        appium.appium_chain_move_by_offset(50, 50)
        
        print("3. Add pause")
        appium.appium_chain_pause(1)
        
        print("4. Add click")
        appium.appium_chain_click()
        
        print("5. Perform chain")
        appium.appium_chain_perform()
        
        print("Action chains tests completed successfully!")

    except Exception as e:
        print(f"Test failed with exception: {e}")
    finally:
        print("Closing application...")
        appium.close_all_applications()

if __name__ == "__main__":
    main()
