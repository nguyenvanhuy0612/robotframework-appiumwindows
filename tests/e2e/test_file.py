import os
import time
from AppiumLibrary import AppiumLibrary

def create_dummy_file(filename, size_in_bytes):
    with open(filename, "wb") as f:
        f.write(os.urandom(size_in_bytes))

sizes = {
    "1kb": 1 * 1024,
    "5kb": 5 * 1024,
    "10kb": 10 * 1024,
    "1mb": 1 * 1024 * 1024,
    "10mb": 10 * 1024 * 1024,
    "25mb": 25 * 1024 * 1024,
    "50mb": 50 * 1024 * 1024,
    "100mb": 100 * 1024 * 1024
}

for name, size in sizes.items():
    local_path = f"tests/e2e/test_{name}.dat"
    if not os.path.exists(local_path):
        create_dummy_file(local_path, size)
        print(f"Created {local_path} ({size} bytes)", flush=True)

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

    for name in sizes.keys():
        local_file = f"tests/e2e/test_{name}.dat"
        remote_file = f"C:\\Users\\admin\\Documents\\test_{name}.dat"
        print(f"Transferring {local_file} to {remote_file}...", flush=True)
        start_time = time.time()
        
        appium.appium_transfer_file(local_file, remote_file)
        
        elapsed = time.time() - start_time
        print(f"Success! {name} transferred in {elapsed:.2f} seconds.", flush=True)

finally:
    print("Closing application...", flush=True)
    appium.close_all_applications()
