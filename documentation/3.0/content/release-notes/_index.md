+++
title = "Release Notes"
date = 2019-02-22T15:27:38-05:00
weight = 89
pre = "<b> </b>"
+++


### Changes in Release 3.2.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1450 - Added alias updates for April 2023 PSUs for 12.2.1.3, 12.2.1.4, and 14.1.1.
- #1454 - Added aliases for new fields introduced 14.1.2.
- #1457 - Deprecated `system-elements` section of typedef files and replaced it with new `discover-filters` section
          that supports filtering named elements in most top-level folders.
- #1458 - Updated Model and Archive documentation to reflect the current state of the code.

#### Bug Fixes
- #1459 - Fixed a type conversion issues for properties entries where boolean and integers were not being properly
          converted to strings in 14.1.1 and newer.

#### Known Issues
