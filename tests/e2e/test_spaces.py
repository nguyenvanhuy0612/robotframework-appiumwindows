import os
import time
from AppiumLibrary import AppiumLibrary

file_name = "test [spaces] file.dat"
size_in_bytes = 100 * 1024

with open(file_name, "wb") as f:
    f.write(os.urandom(size_in_bytes))

remote_url = "http://172.16.10.37:4723"
appium = AppiumLibrary()
appium.register_keyword_to_run_on_failure("Nothing")

try:
    print("Opening application...", flush=True)
    appium.open_application(
        remote_url=remote_url,
        app="Root",
        platformName="Windows",
        automationName="NovaWindows2"
    )

    local_file = file_name
    remote_file = f"C:\\Users\\admin\\Documents\\{file_name}"
    print(f"Transferring '{local_file}' to '{remote_file}'...", flush=True)
    appium.appium_transfer_file(local_file, remote_file)
    print("Success!", flush=True)
finally:
    appium.close_all_applications()
