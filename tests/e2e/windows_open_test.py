from AppiumLibrary import AppiumLibrary
import sys

remote_url = "http://192.168.8.245:4723"
appium = AppiumLibrary()

print(f"Attempting to connect to {remote_url} with Windows platform...")

try:
    # Test with new parameters explicitly to verify they are accepted and processed
    appium.open_application(
        remote_url=remote_url,
        platformName="Windows",
        automationName="NovaWindows2",
        app="Root",
        ignore_certificates=True, # Validating ClientConfig param
        direct_connection=True    # Validating ClientConfig param
    )
    print("Successfully opened Windows application with new AppiumClientConfig parameters.")
    appium.close_application()
except Exception as e:
    print(f"Failed to open application: {e}")
    sys.exit(1)
