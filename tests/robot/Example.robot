*** Settings ***
Library    AppiumLibrary

Test Setup    Open Root Session
Test Teardown    Appium Close All Applications

*** Test Cases ***
Type To Notepad
    Appium Execute Powershell Command    Start-Process "notepad"
    Appium Input    class\=Notepad    This is example{enter 3}Close without save
    Appium Click    //Window[@ClassName\='Notepad']//Button[@Name\='Close']
    Appium Click    name\=Don't Save

*** Keywords ***
Open Root Session
    ${parameters}    Create Dictionary
    ...    remote_url=http://192.168.196.158:4723
    ...    platformName=Windows
    ...    appium:app=Root
    ...    appium:automationName=NovaWindows
    ...    appium:newCommandTimeout=30
    Open Application    &{parameters}