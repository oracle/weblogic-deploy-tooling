+++
title = "Release 2.4.1"
date = 2022-11-03T15:27:38-05:00
weight = 5
pre = "<b> </b>"
+++

### Changes in Release 2.4.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
- None

#### Other Changes
None

#### Bug Fixes
- #1237: Resolved an issue where the tools supporting the `-target` parameter were doing target-related work even if the parameter was not specified.

#### Known Issues
- Due to the changes made for WDT-663 in WDT 2.4.0, the resulting remotely discovered model contains extra fields that would not normally be there.
  This is an area of ongoing work to clean up the online aliases to not depend on these extra remote calls to produce a clean model.


