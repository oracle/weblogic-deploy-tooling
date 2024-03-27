+++
title = "Release 3.5.2"
date = 2019-02-22T15:27:38-05:00
weight = 77
pre = "<b> </b>"
+++


### Changes in Release 3.5.2
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1557 - Added support for provisioning the WebLogic Remote Console domain extension WAR file.

#### Bug Fixes
- #1547 -  Fixed a bug with password validation causing a `NullPointerException` when the `domainInfo` section was
  missing from the model.
- #1554 - Fixed a problem where the Discover Domain tool would hang when running in online mode and an edit lock exists.

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
