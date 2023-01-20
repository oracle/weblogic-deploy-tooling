+++
title = "Release 2.4.4"
date = 2023-01-20T14:39:00-05:00
weight = 5
pre = "<b> </b>"
+++

### Changes in Release 2.4.4
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
None

#### Bug Fixes
- #1361: Resolved issue where the custom Coherence configuration file was not placed in the WebLogic Server domain's expected location.

#### Known Issues
- Due to the changes made for WDT-663 in WDT 2.4.0, the resulting remotely discovered model contains extra fields that would not normally be there.
  This is an area of ongoing work to clean up the online aliases to not depend on these extra remote calls to produce a clean model.


