# Robot Framework AppiumLibrary for Windows

This library extends the standard [AppiumLibrary](https://github.com/serhatbolsu/robotframework-appiumlibrary) to support **Windows Desktop Automation** using the **Appium NovaWindows2 Driver**. It bridges the gap between Robot Framework and the modern Windows automation ecosystem, providing robust tools for interacting with Windows applications via PowerShell integration and native Windows APIs.

---

## 🚀 Key Features

*   **Native Windows Interaction**: Seamless simulation of mouse events including Right Click, Double Click, Hover, and Drag & Drop.
*   **PowerShell Integration**: distinct capability to execute PowerShell commands and scripts directly on the target machine, allowing for advanced system manipulation and state checking.
*   **Resilient Automation**: Includes fallback mechanisms for clicking and typing when standard driver commands are intercepted or fail.
*   **Advanced File Transfer**: Bypass standard Appium limitations with specialized keywords to push/pull files and folders, including handling large files via chunked transfer.
*   **Remote Desktop Ready**: Optimized for running in headless or remote desktop environments where standard interaction methods might struggle.

---

## 🔧 Underlying Driver

This library is a Robot Framework wrapper specifically validated for the **[Appium NovaWindows2 Driver](https://github.com/nguyenvanhuy0612/appium-novawindows2-driver)**.

*   **Repository**: [nguyenvanhuy0612/appium-novawindows2-driver](https://github.com/nguyenvanhuy0612/appium-novawindows2-driver)
*   **Purpose**: Replaces the legacy WinAppDriver with a modern, PowerShell-backed engine.
*   **Mechanism**: Translates Appium commands into optimized PowerShell scripts, executing them directly on the Windows target. This approach allows for:
    *   Bypassing UI Automation limitations.
    *   Direct system control (registry, processes, files).
    *   Zero-dependency setup on the target (no "Developer Mode" required).

---

## 🏗️ Architecture

```text
+------------------------------+             +----------------------------------+
|    Test Runner (Local PC)    |             |    Target Machine (Windows)      |
|------------------------------|             |----------------------------------|
|                              |             |                                  |
|  [ Robot Framework ]         |             |  [ Appium Server 3.x+ ]          |
|          |                   |   HTTP      |           ^                      |
|  [ AppiumLibrary ]           |   JSON      |           |                      |
|          |                   |   Wire      |  [ Appium NovaWindows2 Driver ]  |
|  [ robotframework-           | ----------> |           |                      |
|    appiumwindows ]           |             |  [ PowerShell Session ]          |
|                              |             |           |                      |
|                              |             |      [ Application ]             |
|                              |             |                                  |
+------------------------------+             +----------------------------------+
```

---

## 📋 Prerequisites

### 1. On Test Runner (Local Machine)
*   **Python**: 3.10 or higher
*   **Robot Framework**: Installed via pip

### 2. On Target Machine (Remote Windows PC)
*   **Node.js**: [Download](https://nodejs.org/en/download)
*   **Appium Server**: Global installation (`npm install -g appium`)
*   **NovaWindows2 Driver**: `appium driver install --source=npm appium-novawindows2-driver`
*   **PowerShell**: Accessible and allowed by the Appium server context.

---

## 📦 Installation

To install the library on your test runner:

```bash
pip install robotframework-appiumwindows
```

---

## ⚙️ Configuration & Startup

On the **Target Machine**, start the Appium server with relaxed security to enable PowerShell execution:

```bash
appium --relaxed-security
```

*Note: `--relaxed-security` is required for the library to execute PowerShell commands, which powers many of the advanced features.*

---

## 💻 Example Test

Here is a comprehensive example demonstrating connection, application launching, efficient file transfer, and advanced user interactions.

```robot
*** Settings ***
Library    AppiumLibrary

Test Setup       Open Windows App
Test Teardown    Close All Applications

*** Variables ***
${REMOTE_URL}    http://192.168.1.10:4723
${APP_PATH}      C:\\Windows\\System32\\notepad.exe

*** Test Cases ***
Automate Notepad With Advanced Features
    [Documentation]    Demonstrates launching an app, typing, using right-click context menu, and verifying via PowerShell.
    
    # 1. Launch Application using PowerShell (more reliable for some Win apps)
    Appium Execute Powershell Command    Start-Process "${APP_PATH}"
    
    # 2. Attach to the "Root" session allows finding top-level windows
    Open Application    ${REMOTE_URL}    platformName=Windows    appium:automationName=NovaWindows2    appium:app=Root
    
    # 3. Wait for Notepad window
    Wait Until Page Contains Element    name=Untitled - Notepad
    
    # 4. Input Text (Standard)
    Appium Input    name=Text Editor    Hello from Robot Framework!
    
    # 5. Advanced Interaction: Right Click to open context menu
    Appium Right Click    name=Text Editor
    
    # 6. Select "Select All" from context menu
    Appium Click    name=Select All
    
    # 7. Use PowerShell to verify the process is running
    ${process}=    Appium Execute Powershell Command    Get-Process notepad | Select-Object -ExpandProperty Id
    Log    Notepad Process ID: ${process}
    
    # 8. Drag and Drop Example (Conceptual)
    # Appium Drag And Drop    name=SourceItem    name=TargetFolder

*** Keywords ***
Open Windows App
    [Arguments]    ${app_id}=Root
    &{capabilities}=    Create Dictionary
    ...    platformName=Windows
    ...    appium:automationName=NovaWindows2
    ...    appium:app=${app_id}
    ...    appium:newCommandTimeout=300
    Open Application    ${REMOTE_URL}    &{capabilities}
```

---

## 📚 Keyword Reference

### Windows Specific Keywords
*Extends standard interactions with Windows-specific mouse events.*

| Keyword | Arguments | Description |
| :--- | :--- | :--- |
| `Appium Right Click` | `locator`, `timeout=20`, `**kwargs` | Performs a mouse right-click on the element found by `locator`. |
| `Appium Double Click` | `locator`, `timeout=20`, `**kwargs` | Performs a mouse double-click on the element found by `locator`. |
| `Appium Hover` | `locator`, `start_locator=None`, `timeout=20` | Hovers the mouse cursor over the specified element. |
| `Appium Drag And Drop` | `start_locator`, `end_locator`, `timeout=20` | Drags an element from `start_locator` and drops it at `end_locator`. |
| `Appium Click Offset` | `locator`, `x_offset`, `y_offset` | Clicks at a specific coordinate offset relative to an element. |
| `Appium Sendkeys` | `text` | Sends keystrokes to the active window using native Windows APIs. |

### PowerShell & System Keywords
*Directly interact with the underlying OS for setup, teardown, and validation.*

| Keyword | Arguments | Description |
| :--- | :--- | :--- |
| `Appium Execute Powershell Command` | `command` | Executes a single-line PowerShell command and returns the output. |
| `Appium Execute Powershell Script` | `ps_script` OR `file_path` | Executes a full PowerShell script block or a `.ps1` file. |
| `Appium Ps Click` | `locator`, `x`, `y`, `button='left'` | Simulates a mouse click using PowerShell (useful as a fallback). |
| `Appium Ps Drag And Drop` | `start_locator`, `end_locator`, `...` | Simulates drag and drop using PowerShell mouse events. |
| `Appium Ps Sendkeys` | `text` | Sends keys using PowerShell `System.Windows.Forms.SendKeys`. |

### Advanced File Transfer
*Optimized for reliability and handling large files over the wire.*

| Keyword | Arguments | Description |
| :--- | :--- | :--- |
| `Appium Pull File` | `path`, `save_path=None` | Downloads a file from the target machine. |
| `Appium Pull Folder` | `path`, `save_path_as_zip=''` | Zips and downloads a folder from the target machine. |
| `Appium Push File` | `destination_path`, `source_path` | Uploads a file to the target machine. |
| `Appium Split And Push File` | `source_path`, `remote_path`, `chunk_size_mb` | Splits a large file, uploads chunks, and recombines on target. |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests to improve compatibility or add new features.

**Repository**: [nguyenvanhuy0612/robotframework-appiumwindows](https://github.com/nguyenvanhuy0612/robotframework-appiumwindows)