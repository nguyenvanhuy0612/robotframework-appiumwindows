import time

from appium import webdriver
from appium.options.common import AppiumOptions
from appium.options.windows import WindowsOptions
from appium.webdriver.common.appiumby import AppiumBy

remote_url = 'http://192.168.196.159:4723'


options = WindowsOptions()
options.app = 'Root'
driver = webdriver.Remote(command_executor=remote_url, options=options)

print(driver.page_source)

el = driver.find_element(AppiumBy.XPATH, "/*")
print(el.text)


time.sleep(5)
driver.quit()
