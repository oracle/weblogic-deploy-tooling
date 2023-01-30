+++
title = "Release 2.4.3"
date = 2023-01-13T15:27:38-05:00
weight = 97
pre = "<b> </b>"
+++

### Changes in Release 2.4.3
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
None

#### Bug Fixes
- #1356: Resolved Issue where the new ATP Database URL format was causing connections to fail.

#### Known Issues
- Due to the changes made for WDT-663 in WDT 2.4.0, the resulting remotely discovered model contains extra fields that would not normally be there.
  This is an area of ongoing work to clean up the online aliases to not depend on these extra remote calls to produce a clean model.
