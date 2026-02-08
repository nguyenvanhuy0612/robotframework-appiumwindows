*** Settings ***
Resource    ../../AppiumLibrary/AppiumLibrary.resource

Test Setup       Open Windows App
Test Teardown    Appium Close All Applications

*** Variables ***
${REMOTE_URL}    http://192.168.1.19:4723
${APP_PATH}      C:\\Windows\\System32\\notepad.exe

*** Test Cases ***
Automate Notepad
    [Documentation]    Demonstrates launching an app, typing, using right-click context menu

    # 1. Launch Notepad via PowerShell
    Appium Execute Powershell Command    Start-Process ${APP_PATH}

    # 2. Wait for Notepad window
    Wait Until Page Contains Element    name=Untitled - Notepad

    # 3. Input Text (Standard)
    Appium Input    name=Text Editor    Hello from Robot Framework!

    # 4. Advanced Interaction: Right Click to open context menu
    Appium Right Click    name\=Text Editor

    # 5. Select "Select All" from context menu
    Appium Click    name\=Select All

    # 6. Use PowerShell to verify the process is running
    ${process}    Appium Execute Powershell Command    Get-Process notepad | Select-Object -ExpandProperty Id
    Log    Notepad Process ID: ${process}

    # 7. Close Notepad
    Appium Execute Powershell Command    Stop-Process -Id ${process}

*** Keywords ***
Open Windows App
    &{capabilities}    Create Dictionary
    ...    platformName=Windows
    ...    appium:automationName=NovaWindows2
    ...    appium:app=Root
    ...    appium:newCommandTimeout=20
    Open Application    ${REMOTE_URL}    &{capabilities}