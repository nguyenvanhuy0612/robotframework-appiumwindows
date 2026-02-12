# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Robot Framework library for Windows desktop automation via Appium NovaWindows2 Driver. Extends the standard AppiumLibrary with Windows-specific interactions (right-click, drag-and-drop, hover), PowerShell integration, and advanced file transfer. Currently alpha (v0.1.8).

**Dependencies:** Python >= 3.10, robotframework >= 7.0.0, Appium-Python-Client >= 5.0.0

## Build & Test Commands

```bash
# Install dependencies
pip install -e .

# Run unit tests
python -m unittest discover tests/core/

# Run a single test file
python -m unittest tests/core/test_element_keywords.py

# Run Robot Framework tests (requires Appium server running with --relaxed-security)
robot tests/robot/Automate_Notepad.robot

# Build package for distribution
python -m build

# Check and publish
python -m twine check dist/*
python -m twine upload dist/*
```

## Architecture

### Mixin Inheritance Pattern

`AppiumLibrary` (in `AppiumLibrary/__init__.py`) aggregates all functionality through multiple inheritance from keyword group classes. Each keyword group lives in `AppiumLibrary/keywords/` and focuses on one concern:

- `_ApplicationManagementKeywords` — session lifecycle, open/close/switch apps, clipboard
- `_ElementKeywords` — element finding, interaction, validation, search context management
- `_WindowsKeywords` — Windows-native mouse events (right-click, double-click, hover, drag-and-drop, scroll)
- `_PowershellKeywords` — PowerShell command/script execution, file transfer (including chunked large files)
- `_WaitingKeywords` — wait-until conditions with configurable timeouts
- `_ScreenshotKeywords` / `_ScreenrecordKeywords` — capture screenshots and recordings
- `_LoggingKeywords` / `_RunOnFailureKeywords` — logging and failure handlers

### KeywordGroup Metaclass

`KeywordGroup` (`keywords/keywordgroup.py`) uses `KeywordGroupMetaClass` to automatically wrap all public methods with `_run_on_failure` error handling. Methods decorated with `@ignore_on_fail` are excluded. This means any new public method on a keyword group automatically gets failure capture behavior.

### Element Finding

`ElementFinder` (`locators/elementfinder.py`) parses locator strings with `prefix=value` syntax (e.g., `name=Notepad`, `xpath=//Button`). Supported prefixes: `id`, `name`, `xpath`, `class`, `accessibility_id`, `android`, `ios`, `css`, `predicate`, `chain`. Unprefixed locators starting with `/` are treated as xpath; otherwise they fall back to `id`.

### Session Management

`ApplicationCache` (`utils/applicationcache.py`) extends Robot Framework's `ConnectionCache` to manage multiple Appium sessions. Keywords like `open_application`, `switch_application`, and `close_application` operate on this cache. Library scope is GLOBAL.

## Conventions

- Keyword files are prefixed with underscore (e.g., `_element.py`) and classes with underscore (e.g., `_ElementKeywords`)
- Public methods on keyword groups become Robot Framework keywords; private methods (prefixed `_`) do not
- Locator arguments follow Robot Framework AppiumLibrary conventions: `locator` string or `WebElement` instance
- Version is maintained in both `AppiumLibrary/version.py` and `pyproject.toml` — keep them in sync
