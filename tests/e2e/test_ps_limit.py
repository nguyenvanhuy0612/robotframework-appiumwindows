from AppiumLibrary import AppiumLibrary
import time

remote_url = "http://172.16.10.37:4723"
appium = AppiumLibrary()
appium.register_keyword_to_run_on_failure("Nothing")

try:
    appium.open_application(
        remote_url=remote_url,
        app="Root",
        platformName="Windows",
        automationName="NovaWindows2"
    )

    sizes_to_test_mb = [1, 2, 4, 8, 12, 16, 24, 32]
    
    for mb in sizes_to_test_mb:
        # Create a string of `mb` Megabytes.
        # Since base64 expands binary by ~33%, to test an `mb` chunk limit
        # we generate `mb` chars.
        byte_size = mb * 1024 * 1024
        print(f"Testing {mb}MB string payload...", flush=True)
        payload = "A" * byte_size
        script = f'Write-Output "Length: $($args[0].Length)"'
        
        try:
            start = time.time()
            driver = appium._current_application()
            # Send the script with the payload as an argument so we don't 
            # trigger Python/shell string parsing max limits, but we test Appium's HTTP limit
            res = driver.execute_script("powerShell", {"command": f'$s="{payload}"; $s.Length'})
            print(f"Success! {mb}MB completed in {time.time()-start:.2f}s. Result: {res}", flush=True)
        except Exception as e:
            print(f"Failed at {mb}MB! Error: {e}", flush=True)
            break

finally:
    appium.close_all_applications()
