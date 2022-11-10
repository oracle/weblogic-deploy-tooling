+++
title = "Release 2.4.2"
date = 2022-11-10T15:27:38-05:00
weight = 5
pre = "<b> </b>"
+++

### Changes in Release 2.4.2
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
None

#### Bug Fixes
- #1241: Resolved Issue #1240 that was causing a NullPointerException with discoverDomain.
- #1252: Reworked the unicode handling to resolve customer issues with 14.1.1 when using non-ASCII characters.

#### Known Issues
- Due to the changes made for WDT-663 in WDT 2.4.0, the resulting remotely discovered model contains extra fields that would not normally be there.
  This is an area of ongoing work to clean up the online aliases to not depend on these extra remote calls to produce a clean model.


